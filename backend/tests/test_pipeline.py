import pytest


class TestFullPipeline:
    """Test the full map + validate + fix + score pipeline"""

    def test_patient_full_pipeline(self, client):
        """Patient full pipeline returns all expected fields"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "M",
                "DOB": "15/04/1990"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        data = res.json()
        assert "mapping" in data
        assert "validation" in data
        assert "quality" in data
        assert "fixed_resource" in data

    def test_patient_errors_auto_fixed(self, client):
        """Known errors are auto-fixed in pipeline"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "M",
                "DOB": "15/04/1990"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        data = res.json()
        quality = data["quality"]

        assert quality["errors_auto_fixed"] > 0
        assert quality["remaining_errors"] == 0
        assert data["validation"]["final_valid"] is True

    def test_quality_grade_all_fixed(self, client):
        """Grade is A when all errors auto-fixed"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "M",
                "DOB": "15/04/1990"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        quality = res.json()["quality"]
        assert quality["grade"] in ["A", "A+"]

    def test_quality_grade_no_errors(self, client):
        """Grade is A+ when no errors at all"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P202",
                "Sex": "male",
                "DOB": "1990-04-15"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        quality = res.json()["quality"]
        assert quality["grade"] == "A+"
        assert quality["total_errors_found"] == 0

    def test_invalid_patient_not_fixed(self, client):
        """Impossible date cannot be auto-fixed"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "M",
                "DOB": "30/02/1990"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        quality = res.json()["quality"]
        assert quality["remaining_errors"] > 0
        assert quality["grade"] in ["C", "D"]

    def test_observation_loinc_lookup(self, client):
        """Observation pipeline includes LOINC lookup"""
        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Blood Pressure",
                "Value": "120",
                "Unit": "mmHg",
                "PatientID": "P101",
                "Date": "2024-01-15",
                "Status": "final"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200
        data = res.json()
        loinc = data["loinc_lookup"]
        assert loinc["found"] is True
        assert loinc["code"] == "55284-4"

    def test_condition_snomed_lookup(self, client):
        """Condition pipeline includes SNOMED lookup"""
        res = client.post("/condition/map-validate", json={
            "data": {
                "PatientID": "P101",
                "Diagnosis": "Diabetes Type 2",
                "Status": "active",
                "Severity": "moderate",
                "VerificationStatus": "confirmed"
            },
            "resource_type": "Condition"
        })
        assert res.status_code == 200
        data = res.json()
        snomed = data["snomed_lookup"]
        assert snomed["found"] is True
        assert snomed["code"] == "44054006"

    def test_medication_rxnorm_lookup(self, client):
        """Medication pipeline includes RxNorm lookup"""
        res = client.post("/medication/map-validate", json={
            "data": {
                "PatientID": "P101",
                "MedicationName": "Metformin",
                "Status": "active",
                "OrderType": "order",
                "Dose": "500",
                "Unit": "mg",
                "Frequency": "twice daily",
                "Route": "oral"
            },
            "resource_type": "MedicationRequest"
        })
        assert res.status_code == 200
        rxnorm = res.json()["rxnorm_lookup"]
        assert rxnorm["found"] is True
        assert rxnorm["code"] == "860975"

    def test_patient_reference_validated(self, client):
        """Observation fails if patient doesn't exist"""
        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Glucose",
                "Value": "95",
                "Unit": "mg/dL",
                "PatientID": "NONEXISTENT",
                "Date": "2024-01-15",
                "Status": "final"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]
        subject_errors = [
            e for e in errors if e["field"] == "subject"
        ]
        assert len(subject_errors) > 0
        assert "not found" in subject_errors[0]["message"]

    def test_business_rule_age_warning(self, client):
        """Unrealistic age triggers business rule warning"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "1800-01-01"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        assert len(warnings) > 0
        assert any("age" in w["message"].lower() or
                   "unrealistic" in w["message"].lower()
                   for w in warnings)

    def test_encounter_date_order_warning(self, client):
        """Encounter warns when admission after discharge"""
        res = client.post("/encounter/map-validate", json={
            "data": {
                "PatientID": "P101",
                "Status": "finished",
                "VisitType": "emergency",
                "AdmissionDate": "2024-01-18",
                "DischargeDate": "2024-01-15"
            },
            "resource_type": "Encounter"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        assert any("after" in w["message"].lower() or
                   "before" in w["message"].lower()
                   for w in warnings)

    def test_bundle_generation_with_medication_request(self, client):
        """Bundle generation should support medication requests without crashing"""
        key_res = client.post("/register", json={"email": "bundle-test@example.com"})
        assert key_res.status_code == 200
        api_key = key_res.json()["api_key"]

        res = client.post("/bundle", json={
            "patient": {
                "id": "P101",
                "resourceType": "Patient",
                "name": [{"family": "Doe", "given": ["John"]}],
                "birthDate": "1990-04-15"
            },
            "observations": [{
                "resourceType": "Observation",
                "status": "final",
                "code": {"text": "Blood Pressure"},
                "subject": {"reference": "Patient/P101"},
                "valueQuantity": {"value": 120, "unit": "mmHg"}
            }],
            "conditions": [{
                "resourceType": "Condition",
                "subject": {"reference": "Patient/P101"},
                "code": {"text": "Diabetes Type 2"},
                "clinicalStatus": {"coding": [{"code": "active"}]}
            }],
            "encounters": [{
                "resourceType": "Encounter",
                "subject": {"reference": "Patient/P101"},
                "status": "finished",
                "class": {"code": "ambulatory"}
            }],
            "medications": [{
                "resourceType": "MedicationRequest",
                "subject": {"reference": "Patient/P101"},
                "status": "active",
                "intent": "order",
                "medicationCodeableConcept": {"text": "Metformin"}
            }]
        }, headers={"X-API-Key": api_key})

        assert res.status_code == 200
        data = res.json()
        assert data["resourceType"] == "Bundle"
        assert len(data["entry"]) == 5
        assert "medications" in data["summary"]
        assert len(data["summary"]["medications"]) == 1