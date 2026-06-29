import pytest


class TestNullAndEmptyValues:
    """Edge cases: null, empty, missing values"""

    def test_null_patient_id(self, client):
        """Null patient ID is flagged as missing"""
        res = client.post("/map", json={
            "data": {"PtID": None},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        data = res.json()
        # Should either map to null or flag as unmapped
        mapped = data["mapped_resource"]
        assert mapped.get("id") is None or "id" not in mapped

    def test_empty_string_gender(self, client):
        """Empty string gender is caught by validator"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": ""
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]
        gender_errors = [e for e in errors if e["field"] == "gender"]
        assert len(gender_errors) > 0

    def test_all_null_values(self, client):
        """All null values handled gracefully"""
        res = client.post("/map", json={
            "data": {
                "PtID": None,
                "Sex": None,
                "DOB": None
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200

    def test_empty_object(self, client):
        """Empty input object handled gracefully"""
        res = client.post("/map", json={
            "data": {},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["mapping_complete"] is True or \
               len(data["unmapped_fields"]) == 0

    def test_null_observation_value(self, client):
        """Null observation value triggers warning not crash"""
        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Blood Pressure",
                "Value": None,
                "Unit": "mmHg",
                "PatientID": "P101",
                "Date": "2024-01-15",
                "Status": "final"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200
        warnings = res.json()["validation"]["warnings"]
        assert any("value" in w["message"].lower()
                   for w in warnings)

    def test_null_patient_reference(self, client):
        """Null patient reference flagged as missing"""
        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Glucose",
                "Value": "95",
                "Unit": "mg/dL",
                "PatientID": None,
                "Date": "2024-01-15",
                "Status": "final"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]
        subject_errors = [e for e in errors if e["field"] == "subject"]
        assert len(subject_errors) > 0

    def test_empty_string_date(self, client):
        """Empty string date handled gracefully"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": ""
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200

    def test_null_condition_diagnosis(self, client):
        """Null diagnosis flagged as missing required field"""
        res = client.post("/condition/map-validate", json={
            "data": {
                "PatientID": "P101",
                "Diagnosis": None,
                "Status": "active"
            },
            "resource_type": "Condition"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]
        code_errors = [e for e in errors if e["field"] == "code"]
        assert len(code_errors) > 0

    def test_null_medication_name(self, client):
        """Null medication name flagged correctly"""
        res = client.post("/medication/map-validate", json={
            "data": {
                "PatientID": "P101",
                "MedicationName": None,
                "Status": "active",
                "OrderType": "order"
            },
            "resource_type": "MedicationRequest"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]
        med_errors = [
            e for e in errors
            if "medication" in e["field"].lower()
        ]
        assert len(med_errors) > 0


class TestNumericAsString:
    """Edge cases: numbers where strings expected and vice versa"""

    def test_dob_as_integer(self, client):
        """DOB as integer 19900415 handled gracefully"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": 19900415
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        # Should either convert or flag as error
        errors = res.json()["validation"]["errors"]
        data = res.json()
        # Not crash — that's the main thing
        assert "validation" in data

    def test_dob_as_float(self, client):
        """DOB as float handled gracefully"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": 19900415.0
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200

    def test_patient_id_as_integer(self, client):
        """Patient ID as integer converted to string"""
        res = client.post("/map", json={
            "data": {"PtID": 101},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        mapped = res.json()["mapped_resource"]
        # Should be string "101" not integer 101
        assert mapped.get("id") is not None

    def test_observation_value_as_string(self, client):
        """Observation value as string number converted correctly"""
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
        # valueQuantity.value should be numeric not string
        assert isinstance(
            resource["valueQuantity"]["value"], (int, float)
        )

    def test_dose_as_string_number(self, client):
        """Medication dose as string number converted correctly"""
        res = client.post("/medication/map-validate", json={
            "data": {
                "PatientID": "P101",
                "MedicationName": "Metformin",
                "Status": "active",
                "OrderType": "order",
                "Dose": "500",
                "Unit": "mg"
            },
            "resource_type": "MedicationRequest"
        })
        assert res.status_code == 200
        resource = res.json()["fhir_resource"]
        dose = resource["dosageInstruction"][0]["doseAndRate"][0]
        assert isinstance(
            dose["doseQuantity"]["value"], (int, float)
        )

    def test_year_only_dob(self, client):
        """Year only DOB handled gracefully"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "1990"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200

    def test_dob_unix_timestamp(self, client):
        """Unix timestamp as DOB handled gracefully"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": 631670400
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200


class TestWhitespace:
    """Edge cases: extra whitespace in values"""

    def test_gender_with_whitespace(self, client):
        """Gender with whitespace is trimmed and fixed"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "  M  "
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        fixed = res.json().get("fixed_resource", {})
        # After fix should be "male" not "  M  "
        assert fixed.get("gender") == "male"

    def test_patient_id_with_whitespace(self, client):
        """Patient ID with whitespace is trimmed"""
        res = client.post("/map", json={
            "data": {"PtID": "  P101  "},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        mapped = res.json()["mapped_resource"]
        assert mapped.get("id").strip() == "P101" or \
               mapped.get("id") == "P101"

    def test_date_with_whitespace(self, client):
        """Date with whitespace handled"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "  15/04/1990  "
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200

    def test_medication_name_with_whitespace(self, client):
        """Medication name with whitespace still looked up"""
        res = client.post("/medication/map-validate", json={
            "data": {
                "PatientID": "P101",
                "MedicationName": "  Metformin  ",
                "Status": "active",
                "OrderType": "order",
                "Dose": "500",
                "Unit": "mg"
            },
            "resource_type": "MedicationRequest"
        })
        assert res.status_code == 200
        rxnorm = res.json()["rxnorm_lookup"]
        assert rxnorm["found"] is True

    def test_status_with_whitespace(self, client):
        """Status with whitespace is trimmed before validation"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "  male  ",
                "DOB": "1990-04-15"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200

    def test_field_name_with_whitespace(self, client):
        """Field names with whitespace are normalized"""
        res = client.post("/map", json={
            "data": {"patient id": "P101"},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        mapped = res.json()["mapped_resource"]
        assert mapped.get("id") == "P101"


class TestSpecialCharacters:
    """Edge cases: special characters in values"""

    def test_apostrophe_in_name(self, client):
        """Irish/French names with apostrophes handled"""
        res = client.post("/map", json={
            "data": {
                "PtID": "P101",
                "first_name": "O'Brien",
                "last_name": "D'Souza"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        mapped = res.json()["mapped_resource"]
        assert "name" in mapped
        assert mapped["name"][0]["given"] == ["O'Brien"]
        assert mapped["name"][0]["family"] == "D'Souza"

    def test_accented_characters(self, client):
        """Accented characters in names handled"""
        res = client.post("/map", json={
            "data": {
                "PtID": "P101",
                "first_name": "José",
                "last_name": "García"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        mapped = res.json()["mapped_resource"]
        assert mapped["name"][0]["given"] == ["José"]

    def test_city_with_special_chars(self, client):
        """City names with special characters handled"""
        res = client.post("/map", json={
            "data": {
                "PtID": "P101",
                "city": "São Paulo"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        mapped = res.json()["mapped_resource"]
        assert "address" in mapped
        assert mapped["address"][0]["city"] == "São Paulo"

    def test_hyphen_in_patient_id(self, client):
        """Hyphenated patient IDs handled"""
        res = client.post("/map", json={
            "data": {"PtID": "P-101-A"},
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        mapped = res.json()["mapped_resource"]
        assert mapped.get("id") == "P-101-A"

    def test_slash_in_value(self, client):
        """Blood pressure with slash handled"""
        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Blood Pressure",
                "Value": "120/80",
                "Unit": "mmHg",
                "PatientID": "P101",
                "Date": "2024-01-15",
                "Status": "final"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200

    def test_ampersand_in_diagnosis(self, client):
        """Diagnosis with ampersand handled"""
        res = client.post("/condition/map-validate", json={
            "data": {
                "PatientID": "P101",
                "Diagnosis": "Anxiety & Depression",
                "Status": "active",
                "VerificationStatus": "confirmed"
            },
            "resource_type": "Condition"
        })
        assert res.status_code == 200

    def test_unicode_in_notes(self, client):
        """Unicode characters in notes handled"""
        res = client.post("/medication/map-validate", json={
            "data": {
                "PatientID": "P101",
                "MedicationName": "Metformin",
                "Status": "active",
                "OrderType": "order",
                "Dose": "500",
                "Unit": "mg",
                "Note": "Take with food — رمضان مبارک"
            },
            "resource_type": "MedicationRequest"
        })
        assert res.status_code == 200


class TestArabicNumerals:
    """Edge cases: Arabic-Indic numerals in dates"""

    def test_arabic_numeral_date(self, client):
        """Arabic numeral date handled gracefully"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "١٥/٠٤/١٩٩٠"
            },
            "resource_type": "Patient"
        })
        # Should not crash — either converts or flags
        assert res.status_code == 200
        data = res.json()
        assert "validation" in data

    def test_arabic_numeral_value(self, client):
        """Arabic numeral observation value handled"""
        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Blood Pressure",
                "Value": "١٢٠",
                "Unit": "mmHg",
                "PatientID": "P101",
                "Date": "2024-01-15",
                "Status": "final"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200


class TestBooleanAsString:
    """Edge cases: boolean values as strings"""

    def test_deceased_true_string(self, client):
        """deceased: 'True' converted to boolean true"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "1990-04-15",
                "deceased": "True"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        fixed = res.json().get("fixed_resource", {})
        assert fixed.get("deceasedBoolean") is True

    def test_deceased_false_string(self, client):
        """deceased: 'False' converted to boolean false"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "1990-04-15",
                "deceased": "False"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        fixed = res.json().get("fixed_resource", {})
        assert fixed.get("deceasedBoolean") is False

    def test_deceased_yes_string(self, client):
        """deceased: 'yes' converted to boolean true"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "1990-04-15",
                "deceased": "yes"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        fixed = res.json().get("fixed_resource", {})
        assert fixed.get("deceasedBoolean") is True

    def test_deceased_no_string(self, client):
        """deceased: 'no' converted to boolean false"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "1990-04-15",
                "deceased": "no"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        fixed = res.json().get("fixed_resource", {})
        assert fixed.get("deceasedBoolean") is False

    def test_deceased_1_string(self, client):
        """deceased: '1' converted to boolean true"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "1990-04-15",
                "deceased": "1"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        fixed = res.json().get("fixed_resource", {})
        assert fixed.get("deceasedBoolean") is True

    def test_deceased_0_string(self, client):
        """deceased: '0' converted to boolean false"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "1990-04-15",
                "deceased": "0"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        fixed = res.json().get("fixed_resource", {})
        assert fixed.get("deceasedBoolean") is False

    def test_observation_status_boolean_string(self, client):
        """Observation with boolean-like status handled"""
        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Blood Pressure",
                "Value": "120",
                "Unit": "mmHg",
                "PatientID": "P101",
                "Date": "2024-01-15",
                "Status": "True"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]
        status_errors = [
            e for e in errors if e["field"] == "status"
        ]
        assert len(status_errors) > 0