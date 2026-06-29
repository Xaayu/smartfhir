import pytest
import httpx

BASE_URL = "http://localhost:8000"


class TestBuiltInMapping:
    """Test built-in rule-based mapping"""

    def test_patient_basic_fields(self, client):
        """Standard patient fields map correctly"""
        res = client.post("/map", json={
            "data": {
                "PtID": "P101",
                "Sex": "M",
                "DOB": "15/04/1990"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        data = res.json()
        mapped = data["mapped_resource"]

        assert mapped["id"] == "P101"
        assert mapped["gender"] == "M"
        assert mapped["birthDate"] == "15/04/1990"

    def test_patient_name_fields(self, client):
        """First and last name map to FHIR name structure"""
        res = client.post("/map", json={
            "data": {
                "first_name": "John",
                "last_name": "Doe"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        data = res.json()
        mapped = data["mapped_resource"]

        # Should be nested FHIR structure
        assert "name" in mapped
        assert mapped["name"][0]["given"] == ["John"]
        assert mapped["name"][0]["family"] == "Doe"

    def test_patient_telecom_fields(self, client):
        """Phone and email map to telecom array"""
        res = client.post("/map", json={
            "data": {
                "phone": "555-1234",
                "email": "john@example.com"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        data = res.json()
        mapped = data["mapped_resource"]

        assert "telecom" in mapped
        systems = [t["system"] for t in mapped["telecom"]]
        assert "phone" in systems
        assert "email" in systems

    def test_patient_alias_fields(self, client):
        """Common aliases all map to correct FHIR fields"""
        aliases = [
            {"PatientID": "P101"},
            {"patient_id": "P101"},
            {"pid": "P101"},
            {"PtID": "P101"},
        ]
        for alias in aliases:
            res = client.post("/map", json={
                "data": alias,
                "resource_type": "Patient"
            })
            assert res.status_code == 200
            mapped = res.json()["mapped_resource"]
            assert mapped.get("id") == "P101", \
                f"Alias {list(alias.keys())[0]} failed to map to id"

    def test_gender_aliases(self, client):
        """All gender aliases map correctly"""
        aliases = ["sex", "Sex", "SEX", "patient_sex"]
        for alias in aliases:
            res = client.post("/map", json={
                "data": {alias: "M"},
                "resource_type": "Patient"
            })
            assert res.status_code == 200
            mapped = res.json()["mapped_resource"]
            assert mapped.get("gender") == "M", \
                f"Alias '{alias}' failed"

    def test_dob_aliases(self, client):
        """All date of birth aliases map correctly"""
        aliases = ["dob", "DOB", "dateofbirth",
                   "date_of_birth", "birthdate"]
        for alias in aliases:
            res = client.post("/map", json={
                "data": {alias: "1990-04-15"},
                "resource_type": "Patient"
            })
            assert res.status_code == 200
            mapped = res.json()["mapped_resource"]
            assert mapped.get("birthDate") == "1990-04-15", \
                f"Alias '{alias}' failed"

    def test_marital_status_mapping(self, client):
        """Marital status maps to proper CodeableConcept"""
        res = client.post("/map", json={
            "data": {"marital": "married"},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        mapped = res.json()["mapped_resource"]
        assert "maritalStatus" in mapped
        assert mapped["maritalStatus"]["coding"][0]["code"] == "M"

    def test_unmapped_fields_flagged(self, client):
        """Unknown fields are flagged as unmapped"""
        res = client.post("/map", json={
            "data": {
                "PtID": "P101",
                "RandomField": "some_value",
                "UnknownField": "another_value"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        data = res.json()
        unmapped = data["unmapped_fields"]

        unmapped_names = [u["field"] for u in unmapped]
        assert "RandomField" in unmapped_names
        assert "UnknownField" in unmapped_names
        assert data["mapping_complete"] is False

    def test_mapping_complete_when_all_mapped(self, client):
        """mapping_complete is True when no unmapped fields"""
        res = client.post("/map", json={
            "data": {
                "PtID": "P101",
                "Sex": "M",
                "DOB": "1990-04-15"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["mapping_complete"] is True

    def test_applied_rules_returned(self, client):
        """Applied rules are returned with rule type"""
        res = client.post("/map", json={
            "data": {"PtID": "P101", "Sex": "M"},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        rules = res.json()["applied_rules"]
        assert len(rules) == 2

        rule_types = [r["rule_type"] for r in rules]
        assert all(rt == "built_in" for rt in rule_types)

    def test_observation_mapping(self, client):
        """Observation fields map correctly"""
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
        resource = res.json()["fhir_resource"]
        assert resource["resourceType"] == "Observation"
        assert resource["subject"]["reference"] == "Patient/P101"
        assert resource["valueQuantity"]["value"] == 120
        assert resource["valueQuantity"]["unit"] == "mmHg"

    def test_condition_mapping(self, client):
        """Condition fields map correctly"""
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
        resource = res.json()["fhir_resource"]
        assert resource["resourceType"] == "Condition"
        assert resource["subject"]["reference"] == "Patient/P101"
        assert "code" in resource

    def test_encounter_mapping(self, client):
        """Encounter fields map correctly"""
        res = client.post("/encounter/map-validate", json={
            "data": {
                "PatientID": "P101",
                "Status": "finished",
                "VisitType": "emergency",
                "AdmissionDate": "2024-01-15",
                "DischargeDate": "2024-01-18"
            },
            "resource_type": "Encounter"
        })
        assert res.status_code == 200
        resource = res.json()["fhir_resource"]
        assert resource["resourceType"] == "Encounter"
        assert resource["class"]["code"] == "EMER"
        assert resource["period"]["start"] == "2024-01-15"
        assert resource["period"]["end"] == "2024-01-18"

    def test_medication_mapping(self, client):
        """MedicationRequest fields map correctly"""
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
        resource = res.json()["fhir_resource"]
        assert resource["resourceType"] == "MedicationRequest"
        assert resource["status"] == "active"
        assert resource["intent"] == "order"


class TestUserDefinedMapping:
    """Test user-defined custom mappings"""

    def test_save_user_mapping(self, client):
        """User can save a custom mapping"""
        res = client.post("/mappings/save", json={
            "field": "HospitalPatientNumber",
            "fhir_field": "id",
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        assert res.json()["saved"] is True

    def test_saved_mapping_applied(self, client):
        """Saved mapping is applied on next run"""
        # Save first
        client.post("/mappings/save", json={
            "field": "CustomPatientID",
            "fhir_field": "id",
            "resource_type": "Patient"
        })

        # Now map using saved field
        res = client.post("/map", json={
            "data": {"CustomPatientID": "P999"},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        data = res.json()
        mapped = data["mapped_resource"]
        rules = data["applied_rules"]

        assert mapped.get("id") == "P999"
        rule_types = [r["rule_type"] for r in rules]
        assert "user_defined" in rule_types

    def test_user_mapping_priority_over_builtin(self, client):
        """User mapping takes priority over built-in"""
        # Override built-in: map "Sex" to identifier instead of gender
        client.post("/mappings/save", json={
            "field": "SpecialField",
            "fhir_field": "identifier",
            "resource_type": "Patient"
        })

        res = client.post("/map", json={
            "data": {"SpecialField": "VALUE123"},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        rules = res.json()["applied_rules"]
        special_rule = next(
            (r for r in rules if r["original_field"] == "SpecialField"),
            None
        )
        assert special_rule is not None
        assert special_rule["rule_type"] == "user_defined"

    def test_delete_user_mapping(self, client):
        """User can delete a custom mapping"""
        # Save first
        client.post("/mappings/save", json={
            "field": "TempField",
            "fhir_field": "id",
            "resource_type": "Patient"
        })

        # Delete it
        res = client.request("DELETE", "/mappings/delete", json={
            "field": "TempField",
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        assert res.json()["deleted"] is True

    def test_deleted_mapping_not_applied(self, client):
        """Deleted mapping is no longer applied"""
        # Save then delete
        client.post("/mappings/save", json={
            "field": "DeleteMe",
            "fhir_field": "id",
            "resource_type": "Patient"
        })
        client.request("DELETE", "/mappings/delete", json={
            "field": "DeleteMe",
            "resource_type": "Patient"
        })

        # Now map — should be unmapped
        res = client.post("/map", json={
            "data": {"DeleteMe": "VALUE"},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        unmapped = res.json()["unmapped_fields"]
        unmapped_names = [u["field"] for u in unmapped]
        assert "DeleteMe" in unmapped_names

    def test_view_all_mappings(self, client):
        """Can view all mappings for a resource type"""
        res = client.get("/mappings/Patient")
        assert res.status_code == 200
        data = res.json()
        assert "built_in_mappings" in data
        assert "user_defined_mappings" in data
        assert data["total_built_in"] > 0


class TestNormalization:
    """Test field name normalization"""

    def test_uppercase_field_normalized(self, client):
        """UPPERCASE fields are normalized"""
        res = client.post("/map", json={
            "data": {"PATIENTID": "P101"},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        assert res.json()["mapped_resource"].get("id") == "P101"

    def test_spaces_in_field_normalized(self, client):
        """Fields with spaces are normalized"""
        res = client.post("/map", json={
            "data": {"patient id": "P101"},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        assert res.json()["mapped_resource"].get("id") == "P101"

    def test_mixed_case_normalized(self, client):
        """Mixed case fields are normalized"""
        res = client.post("/map", json={
            "data": {"PatientId": "P101"},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        assert res.json()["mapped_resource"].get("id") == "P101"

    def test_underscores_normalized(self, client):
        """Fields with underscores are normalized"""
        res = client.post("/map", json={
            "data": {"patient_id": "P101"},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        assert res.json()["mapped_resource"].get("id") == "P101"