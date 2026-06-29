class TestDateEdgeCases:
    """Edge cases: dates"""

    def test_leap_year_valid(self, client):
        """29/02/2000 is valid — 2000 is a leap year"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "29/02/2000"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        fixed = res.json().get("fixed_resource", {})
        assert fixed.get("birthDate") == "2000-02-29"

    def test_leap_year_invalid(self, client):
        """29/02/2001 is invalid — 2001 is not a leap year"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "29/02/2001"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]
        date_errors = [
            e for e in errors if e["field"] == "birthDate"
        ]
        assert len(date_errors) > 0

    def test_future_birth_date(self, client):
        """Birth date in future triggers warning"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "2099-01-01"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        assert any(
            "future" in w["message"].lower() or
            "born" in w["message"].lower()
            for w in warnings
        )

    def test_partial_date_year_only(self, client):
        """Year only date handled gracefully"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "1990"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200

    def test_partial_date_year_month(self, client):
        """Year-month partial date handled"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "1990-04"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200

    def test_iso_date_with_time(self, client):
        """ISO datetime converted to date only"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "1990-04-15T00:00:00Z"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        fixed = res.json().get("fixed_resource", {})
        assert fixed.get("birthDate") == "1990-04-15"

    def test_two_digit_year(self, client):
        """Two digit year expanded correctly"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "15/04/90"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        fixed = res.json().get("fixed_resource", {})
        # Should expand to 1990 not 2090
        assert fixed.get("birthDate") == "1990-04-15"

    def test_observation_future_date(self, client):
        """Observation with future date triggers warning"""
        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Blood Pressure",
                "Value": "120",
                "Unit": "mmHg",
                "PatientID": "P101",
                "Date": "2099-01-01",
                "Status": "final"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        assert any(
            "future" in w["message"].lower()
            for w in warnings
        )

    def test_encounter_same_start_end_date(self, client):
        """Encounter with same start and end date is valid"""
        res = client.post("/encounter/map-validate", json={
            "data": {
                "PatientID": "P101",
                "Status": "finished",
                "VisitType": "ambulatory",
                "AdmissionDate": "2024-01-15",
                "DischargeDate": "2024-01-15"
            },
            "resource_type": "Encounter"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        date_warnings = [
            w for w in warnings
            if "after" in w["message"].lower()
        ]
        assert len(date_warnings) == 0

    def test_condition_abatement_before_onset(self, client):
        """Condition where abatement before onset triggers warning"""
        res = client.post("/condition/map-validate", json={
            "data": {
                "PatientID": "P101",
                "Diagnosis": "Hypertension",
                "Status": "resolved",
                "VerificationStatus": "confirmed",
                "OnsetDate": "2023-06-01",
                "AbatementDate": "2022-01-01"
            },
            "resource_type": "Condition"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        assert any(
            "onset" in w["message"].lower() or
            "abatement" in w["message"].lower() or
            "after" in w["message"].lower()
            for w in warnings
        )

    def test_medication_end_before_start(self, client):
        """Medication end date before start triggers warning"""
        res = client.post("/medication/map-validate", json={
            "data": {
                "PatientID": "P101",
                "MedicationName": "Metformin",
                "Status": "active",
                "OrderType": "order",
                "Dose": "500",
                "Unit": "mg",
                "StartDate": "2024-06-01",
                "EndDate": "2024-01-01"
            },
            "resource_type": "MedicationRequest"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        assert any(
            "start" in w["message"].lower() or
            "end" in w["message"].lower() or
            "after" in w["message"].lower()
            for w in warnings
        )


class TestBoundaryValues:
    """Edge cases: boundary values"""

    def test_age_exactly_120(self, client):
        """Age exactly 120 years is valid — no warning"""
        from datetime import datetime, timedelta
        dob = (datetime.now().replace(
            year=datetime.now().year - 120
        )).strftime("%Y-%m-%d")

        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": dob
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        age_warnings = [
            w for w in warnings
            if "age" in w["message"].lower() or
               "unrealistic" in w["message"].lower()
        ]
        assert len(age_warnings) == 0

    def test_age_121_triggers_warning(self, client):
        """Age 121 triggers unrealistic age warning"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "1900-01-01"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        assert any(
            "age" in w["message"].lower() or
            "unrealistic" in w["message"].lower()
            for w in warnings
        )

    def test_dose_zero(self, client):
        """Dose of zero triggers warning"""
        res = client.post("/medication/map-validate", json={
            "data": {
                "PatientID": "P101",
                "MedicationName": "Metformin",
                "Status": "active",
                "OrderType": "order",
                "Dose": "0",
                "Unit": "mg"
            },
            "resource_type": "MedicationRequest"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        assert any(
            "dose" in w["message"].lower() or
            "zero" in w["message"].lower() or
            "greater" in w["message"].lower()
            for w in warnings
        )

    def test_dose_negative(self, client):
        """Negative dose triggers warning"""
        res = client.post("/medication/map-validate", json={
            "data": {
                "PatientID": "P101",
                "MedicationName": "Metformin",
                "Status": "active",
                "OrderType": "order",
                "Dose": "-500",
                "Unit": "mg"
            },
            "resource_type": "MedicationRequest"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        assert any(
            "dose" in w["message"].lower() or
            "negative" in w["message"].lower() or
            "greater" in w["message"].lower()
            for w in warnings
        )

    def test_empty_string_patient_id(self, client):
        """Empty string patient ID flagged as missing"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "",
                "Sex": "male",
                "DOB": "1990-04-15"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]
        id_errors = [e for e in errors if e["field"] == "id"]
        assert len(id_errors) > 0

    def test_very_long_patient_id(self, client):
        """Very long patient ID handled without crash"""
        res = client.post("/map", json={
            "data": {"PtID": "P" + "1" * 1000},
            "resource_type": "Patient"
        })
        assert res.status_code == 200

    def test_very_long_note(self, client):
        """Very long note handled without crash"""
        res = client.post("/medication/map-validate", json={
            "data": {
                "PatientID": "P101",
                "MedicationName": "Metformin",
                "Status": "active",
                "OrderType": "order",
                "Dose": "500",
                "Unit": "mg",
                "Note": "Take with food. " * 1000
            },
            "resource_type": "MedicationRequest"
        })
        assert res.status_code == 200

    def test_observation_value_zero(self, client):
        """Observation value of zero is valid"""
        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Blood Pressure",
                "Value": "0",
                "Unit": "mmHg",
                "PatientID": "P101",
                "Date": "2024-01-15",
                "Status": "final"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        bp_warnings = [
            w for w in warnings
            if "blood pressure" in w["message"].lower() or
               "unrealistic" in w["message"].lower()
        ]
        assert len(bp_warnings) > 0

    def test_extremely_high_dose(self, client):
        """Extremely high dose triggers warning"""
        res = client.post("/medication/map-validate", json={
            "data": {
                "PatientID": "P101",
                "MedicationName": "Aspirin",
                "Status": "active",
                "OrderType": "order",
                "Dose": "99999",
                "Unit": "mg"
            },
            "resource_type": "MedicationRequest"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        assert any(
            "high" in w["message"].lower() or
            "dose" in w["message"].lower()
            for w in warnings
        )

    def test_blood_pressure_unrealistic_high(self, client):
        """Blood pressure of 999 triggers business rule warning"""
        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Blood Pressure",
                "Value": "999",
                "Unit": "mmHg",
                "PatientID": "P101",
                "Date": "2024-01-15",
                "Status": "final"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        assert any(
            "blood pressure" in w["message"].lower() or
            "unrealistic" in w["message"].lower()
            for w in warnings
        )


class TestReferenceEdgeCases:
    """Edge cases: patient references and IDs"""

    def test_duplicate_patient_registration(self, client):
        """Registering same patient twice doesn't crash"""
        payload = {
            "resource": {
                "resourceType": "Patient",
                "id": "P101",
                "gender": "male",
                "birthDate": "1990-04-15"
            }
        }
        res1 = client.post("/patient/register", json=payload)
        res2 = client.post("/patient/register", json=payload)
        assert res1.status_code == 200
        assert res2.status_code == 200

    def test_observation_wrong_patient_format(self, client):
        """Observation with wrong patient format auto-corrected"""
        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Glucose",
                "Value": "95",
                "Unit": "mg/dL",
                "PatientID": "P101",
                "Date": "2024-01-15",
                "Status": "final"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200
        resource = res.json()["fhir_resource"]
        # Should be Patient/P101 not just P101
        assert resource["subject"]["reference"] == "Patient/P101"

    def test_condition_nonexistent_patient(self, client):
        """Condition for nonexistent patient flagged"""
        res = client.post("/condition/map-validate", json={
            "data": {
                "PatientID": "GHOST999",
                "Diagnosis": "Diabetes Type 2",
                "Status": "active",
                "VerificationStatus": "confirmed"
            },
            "resource_type": "Condition"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]
        subject_errors = [
            e for e in errors if e["field"] == "subject"
        ]
        assert len(subject_errors) > 0
        assert "not found" in subject_errors[0]["message"].lower()

    def test_encounter_nonexistent_patient(self, client):
        """Encounter for nonexistent patient flagged"""
        res = client.post("/encounter/map-validate", json={
            "data": {
                "PatientID": "GHOST999",
                "Status": "finished",
                "VisitType": "ambulatory",
                "AdmissionDate": "2024-01-15"
            },
            "resource_type": "Encounter"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]
        subject_errors = [
            e for e in errors if e["field"] == "subject"
        ]
        assert len(subject_errors) > 0

    def test_medication_nonexistent_patient(self, client):
        """MedicationRequest for nonexistent patient flagged"""
        res = client.post("/medication/map-validate", json={
            "data": {
                "PatientID": "GHOST999",
                "MedicationName": "Metformin",
                "Status": "active",
                "OrderType": "order",
                "Dose": "500",
                "Unit": "mg"
            },
            "resource_type": "MedicationRequest"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]
        subject_errors = [
            e for e in errors if e["field"] == "subject"
        ]
        assert len(subject_errors) > 0

    def test_multiple_observations_same_patient(self, client):
        """Multiple observations for same patient all valid"""
        observations = [
            {"TestName": "Blood Pressure", "Value": "120",
             "Unit": "mmHg"},
            {"TestName": "Glucose", "Value": "95",
             "Unit": "mg/dL"},
            {"TestName": "Hemoglobin", "Value": "13.5",
             "Unit": "g/dL"},
        ]
        for obs in observations:
            res = client.post("/observation/map-validate", json={
                "data": {
                    **obs,
                    "PatientID": "P101",
                    "Date": "2024-01-15",
                    "Status": "final"
                },
                "resource_type": "Observation"
            })
            assert res.status_code == 200
            assert res.json()["fhir_resource"][
                "subject"
            ]["reference"] == "Patient/P101"

    def test_patient_id_with_special_chars(self, client):
        """Patient ID with hyphens and letters handled"""
        res = client.post("/patient/register", json={
            "resource": {
                "resourceType": "Patient",
                "id": "PT-2024-001",
                "gender": "female",
                "birthDate": "1985-03-20"
            }
        })
        assert res.status_code == 200

        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Blood Pressure",
                "Value": "110",
                "Unit": "mmHg",
                "PatientID": "PT-2024-001",
                "Date": "2024-01-15",
                "Status": "final"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]
        subject_errors = [
            e for e in errors
            if e["field"] == "subject" and
               "not found" in e["message"].lower()
        ]
        assert len(subject_errors) == 0

    def test_same_id_different_resources(self, client):
        """Same ID for Patient and Observation doesn't conflict"""
        client.post("/patient/register", json={
            "resource": {
                "resourceType": "Patient",
                "id": "001",
                "gender": "male",
                "birthDate": "1990-01-01"
            }
        })

        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Glucose",
                "Value": "95",
                "Unit": "mg/dL",
                "PatientID": "001",
                "Date": "2024-01-15",
                "Status": "final"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]
        subject_errors = [
            e for e in errors
            if e["field"] == "subject" and
               "not found" in e["message"].lower()
        ]
        assert len(subject_errors) == 0