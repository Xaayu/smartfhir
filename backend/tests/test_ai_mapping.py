import pytest
import time


class TestAIMappingReal:
    """
    Tests that call real Gemini API.
    These verify AI explanation quality for complex errors.
    Note: These are slower and cost API tokens.
    """

    def test_gemini_explains_unknown_error(self, client):
        """Gemini provides explanation for complex unknown errors"""
        res = client.post("/explain-errors", json={
            "resource": {
                "resourceType": "Patient",
                "id": "P101",
                "gender": "male",
                "birthDate": "1990-04-15",
                "unknownComplexField": {"nested": "value"}
            }
        })
        assert res.status_code == 200
        data = res.json()

        # If there are ai_needed errors they should have explanations
        for error in data.get("errors", []):
            if error.get("type") == "ai_needed":
                assert error.get("explanation") is not None
                assert "Could not generate" not in error["explanation"]

    def test_gemini_explains_date_error(self, client):
        """Gemini explains impossible date clearly"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "male",
                "DOB": "30/02/1990"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]

        date_errors = [
            e for e in errors if e["field"] == "birthDate"
        ]
        if date_errors:
            error = date_errors[0]
            if error.get("type") == "ai_needed":
                explanation = error.get("explanation", "")
                # Should mention February or invalid date
                assert any(word in explanation.lower() for word in
                           ["february", "invalid", "format", "date"])

    def test_gemini_suggests_fix(self, client):
        """Gemini provides a suggested fix not just explanation"""
        res = client.post("/explain-errors", json={
            "resource": {
                "resourceType": "Patient",
                "id": "P101",
                "gender": "male",
                "birthDate": "30/02/1990"
            }
        })
        assert res.status_code == 200

        for error in res.json().get("errors", []):
            if error.get("type") == "ai_needed":
                assert error.get("suggested_fix") is not None
                assert len(error["suggested_fix"]) > 0

    def test_gemini_response_time(self, client):
        """Gemini responds within acceptable time"""
        start = time.time()
        res = client.post("/explain-errors", json={
            "resource": {
                "resourceType": "Patient",
                "id": "P101",
                "gender": "male",
                "birthDate": "30/02/1990"
            }
        })
        elapsed = time.time() - start

        assert res.status_code == 200
        # Should respond within 30 seconds
        assert elapsed < 30, f"Gemini took too long: {elapsed:.1f}s"

    def test_gemini_handles_multiple_errors(self, client):
        """Gemini handles multiple ai_needed errors"""
        res = client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "M",
                "DOB": "30/02/1890",
                "deceased": "yes"
            },
            "resource_type": "Patient"
        })
        assert res.status_code == 200
        errors = res.json()["validation"]["errors"]

        ai_errors = [e for e in errors if e.get("type") == "ai_needed"]
        for error in ai_errors:
            assert error.get("explanation") is not None
            assert "Could not generate" not in error.get("explanation", "")

    def test_rule_based_faster_than_ai(self, client):
        """Rule-based errors resolve faster than AI errors"""
        # Rule-based only request
        start = time.time()
        client.post("/map-and-validate", json={
            "data": {
                "PtID": "P101",
                "Sex": "M",
                "DOB": "15/04/1990"
            },
            "resource_type": "Patient"
        })
        rule_time = time.time() - start

        # AI needed request
        start = time.time()
        client.post("/explain-errors", json={
            "resource": {
                "resourceType": "Patient",
                "id": "P101",
                "gender": "male",
                "birthDate": "30/02/1990"
            }
        })
        ai_time = time.time() - start

        # AI should take longer
        assert ai_time > rule_time, \
            f"Expected AI ({ai_time:.1f}s) > rule ({rule_time:.1f}s)"

    def test_loinc_lookup_with_ai_fallback(self, client):
        """Unknown test name falls back gracefully"""
        res = client.post("/observation/map-validate", json={
            "data": {
                "TestName": "Rare Exotic Blood Test XYZ",
                "Value": "5",
                "Unit": "units",
                "PatientID": "P101",
                "Date": "2024-01-15",
                "Status": "final"
            },
            "resource_type": "Observation"
        })
        assert res.status_code == 200
        loinc = res.json()["loinc_lookup"]
        # Either found via API or gracefully not found
        assert "found" in loinc
        assert "system" in loinc

    def test_snomed_lookup_with_api(self, client):
        """Unknown condition uses SNOMED API"""
        res = client.post("/condition/map-validate", json={
            "data": {
                "PatientID": "P101",
                "Diagnosis": "Rare Tropical Disease",
                "Status": "active",
                "VerificationStatus": "confirmed"
            },
            "resource_type": "Condition"
        })
        assert res.status_code == 200
        snomed = res.json()["snomed_lookup"]
        assert "found" in snomed

    def test_rxnorm_api_fallback(self, client):
        """Unknown medication uses RxNorm API"""
        res = client.post("/medication/map-validate", json={
            "data": {
                "PatientID": "P101",
                "MedicationName": "Hydroxychloroquine",
                "Status": "active",
                "OrderType": "order",
                "Dose": "200",
                "Unit": "mg"
            },
            "resource_type": "MedicationRequest"
        })
        assert res.status_code == 200
        rxnorm = res.json()["rxnorm_lookup"]
        assert "found" in rxnorm