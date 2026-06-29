from validators.observation_validator import validate_observation


def make_obs(subject):
    return {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [{"system": "http://loinc.org", "code": "55284-4", "display": "Blood pressure systolic and diastolic"}],
            "text": "Blood Pressure"
        },
        "subject": subject,
        "effectiveDateTime": "2024-01-15",
        "valueQuantity": {"value": 120, "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mmHg"},
    }


def test_subject_string_normalizes(monkeypatch):
    # Ensure the patient exists in the store to avoid patient-not-found errors
    monkeypatch.setattr("observation_validator.load_patients", lambda: {"P101": {}})
    res = validate_observation(make_obs("P101"))
    assert not any(e.get("field") == "subject" for e in res["errors"]), "Subject errors were reported for a plain ID"


def test_subject_reference_dict(monkeypatch):
    monkeypatch.setattr("observation_validator.load_patients", lambda: {"P101": {}})
    res = validate_observation(make_obs({"reference": "Patient/P101"}))
    assert not any(e.get("field") == "subject" for e in res["errors"]), "Subject errors were reported for a reference dict"
