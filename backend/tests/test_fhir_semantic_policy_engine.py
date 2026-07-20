from phi_deidentifier import deidentify
from policy_engine.compiler import compile_policy
from policy_engine.executor import apply_policy_to_resource
from policy_engine.semantic_engine import apply_semantic_policy


def test_compile_policy_converts_semantic_categories_to_rules():
    policy = {
        "purpose": "Semantic Test",
        "fields": {
            "patient_name": "REMOVE",
            "government_identifier": "HASH",
            "address": "CITY_ONLY",
            "birth_date": "YEAR_ONLY",
            "free_text": "REMOVE",
        },
    }

    compiled = compile_policy(policy)

    assert compiled["patient_name"] == "REMOVE"
    assert compiled["government_identifier"] == "HASH"
    assert compiled["address"] == "CITY_ONLY"
    assert compiled["birth_date"] == "YEAR_ONLY"


def test_semantic_policy_handles_identifiers_and_narrative():
    policy = {
        "purpose": "Semantic Test",
        "fields": {
            "patient_name": "REMOVE",
            "government_identifier": "HASH",
            "address": "CITY_ONLY",
            "birth_date": "YEAR_ONLY",
            "free_text": "REMOVE",
        },
    }
    resource = {
        "resourceType": "Patient",
        "id": "pt-001",
        "name": [{"given": ["John"], "family": "Doe"}],
        "birthDate": "1985-08-15",
        "address": [{"line": ["1 Main St"], "city": "Boston", "state": "MA", "postalCode": "02101"}],
        "identifier": [
            {
                "use": "official",
                "system": "urn:ssn",
                "type": {"text": "SSN"},
                "value": "123-45-6789",
            }
        ],
        "text": {
            "status": "generated",
            "div": "<div>Patient John Doe was seen at Boston General.</div>",
        },
    }

    deidentified = deidentify(resource, mode="pseudonymize", include_audit=False, policy=policy)["deidentified_resource"]

    assert deidentified["name"][0]["family"] == "[REDACTED]"
    assert deidentified["identifier"][0]["value"] != "123-45-6789"
    assert deidentified["identifier"][0]["system"] == "urn:ssn"
    assert deidentified["identifier"][0]["type"]["text"] == "SSN"
    assert deidentified["address"][0]["city"] == "[CITY]"
    assert deidentified["birthDate"] == "1985"
    assert "John Doe" not in deidentified["text"]["div"]


def test_identifier_values_are_transformed_by_semantic_type_only():
    resource = {
        "resourceType": "Patient",
        "identifier": [
            {
                "use": "official",
                "system": "urn:mrn",
                "type": {"text": "Medical Record Number"},
                "value": "MRN-001",
                "assigner": {"display": "General Hospital"},
            },
            {
                "use": "secondary",
                "system": "urn:ssn",
                "type": {"text": "Social Security Number"},
                "value": "123-45-6789",
            },
            {
                "use": "secondary",
                "system": "urn:passport",
                "type": {"text": "Passport Number"},
                "value": "P12345",
            },
            {
                "use": "secondary",
                "system": "urn:driver-license",
                "type": {"text": "Driver License"},
                "value": "DL-12345",
            },
            {
                "use": "secondary",
                "system": "urn:national-id",
                "type": {"text": "National Identifier"},
                "value": "NAT-001",
            },
            {
                "use": "secondary",
                "system": "urn:employee-id",
                "type": {"text": "Employee ID"},
                "value": "EMP-001",
            },
            {
                "use": "secondary",
                "system": "urn:insurance",
                "type": {"text": "Insurance Number"},
                "value": "INS-001",
            },
        ],
    }

    deidentified = deidentify(resource, mode="pseudonymize", include_audit=False)["deidentified_resource"]
    identifiers = deidentified["identifier"]

    assert identifiers[0]["use"] == "official"
    assert identifiers[0]["type"]["text"] == "Medical Record Number"
    assert identifiers[0]["assigner"]["display"] == "General Hospital"
    assert identifiers[0]["value"] != "MRN-001"

    assert identifiers[1]["value"] is None
    assert identifiers[2]["value"] is None
    assert identifiers[3]["value"] is None
    assert identifiers[4]["value"] is None
    assert identifiers[5]["value"] != "EMP-001"
    assert identifiers[6]["value"] != "INS-001"


def test_policy_replacement_names_use_realistic_fake_names():
    policy = {
        "purpose": "AI Processing",
        "fields": {
            "patient_name": "REPLACE_FAKE",
        },
    }
    resource = {
        "resourceType": "Patient",
        "name": [{"given": ["John"], "family": "Doe"}],
    }

    result = apply_policy_to_resource(policy, resource)
    name = result["name"][0]

    assert name["family"] != "Doe"
    assert name["family"] != "Patient"
    assert name["family"] != ""
    assert name["given"][0] != "John"
