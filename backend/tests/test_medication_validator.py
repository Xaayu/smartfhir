from validators.medication_validator import validate_medication, build_medication_resource


def test_validate_medication_missing_fields():
    result = validate_medication({})
    assert result["valid"] is False
    assert any(e["field"] == "medicationCodeableConcept" for e in result["errors"])
    assert any(e["field"] == "subject" for e in result["errors"])
    assert any(e["field"] == "status" for e in result["errors"])


def test_validate_medication_with_rxnorm(monkeypatch):
    monkeypatch.setattr(
        "medication_validator.lookup_rxnorm",
        lambda medication_name: {
            "found": True,
            "code": "12345",
            "display": "TestMed 10 MG Oral Tablet",
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "source": "test"
        }
    )

    payload = {
        "medicationCodeableConcept": "TestMed",
        "subject": "P101",
        "status": "active",
        "intent": "order"
    }
    result = validate_medication(payload)

    assert result["valid"] is True
    assert result["rxnorm_result"]["found"] is True
    assert result["rxnorm_result"]["code"] == "12345"


def test_build_medication_resource_includes_rxnorm():
    rxnorm_result = {
        "found": True,
        "code": "12345",
        "display": "TestMed 10 MG Oral Tablet",
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "source": "test"
    }
    payload = {
        "id": "M101",
        "medicationCodeableConcept": "TestMed",
        "subject": "P101",
        "status": "active",
        "intent": "order"
    }

    resource = build_medication_resource(payload, rxnorm_result)
    assert resource["resourceType"] == "MedicationRequest"
    assert resource["medicationCodeableConcept"]["coding"][0]["code"] == "12345"
    assert resource["subject"]["reference"] == "Patient/P101"
