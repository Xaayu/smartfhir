from phi_deidentifier import deidentify


def test_deidentify_recurses_into_contained_related_persons_and_narrative():
    resource = {
        "resourceType": "Patient",
        "id": "patient-001",
        "contained": [
            {
                "resourceType": "RelatedPerson",
                "id": "rp-001",
                "name": [{"given": ["John"], "family": "Doe"}],
                "telecom": [{"system": "phone", "value": "+1-555-0123"}],
                "identifier": [{"system": "urn:mrn", "value": "1234567"}],
            }
        ],
        "text": {
            "status": "generated",
            "div": "<div>Patient John Doe was seen at Boston General. MRN 1234567</div>",
        },
        "identifier": [
            {
                "type": {"text": "MRN"},
                "value": "1234567",
            }
        ],
    }

    result = deidentify(resource, mode="pseudonymize", include_audit=False)["deidentified_resource"]

    contained = result["contained"][0]
    assert contained["name"][0]["family"] != "Doe"
    assert contained["telecom"][0]["value"] != "+1-555-0123"
    assert "John Doe" not in result["text"]["div"]
    assert result["identifier"][0]["value"] != "1234567"
    assert contained["identifier"][0]["value"] != "1234567"
