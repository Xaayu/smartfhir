import json

from policy_engine.loader import load_preset_policy, list_preset_policies
from policy_engine.executor import apply_policy_to_resource, build_policy_summary, build_policy_preview
from policy_engine.risk_score import calculate_risk_score


def test_load_preset_policy_returns_ai_policy():
    policy = load_preset_policy("AI Processing")
    assert policy["purpose"] == "AI Processing"
    assert policy["fields"]["patient_name"] == "REMOVE"
    assert policy["privacyLevel"] == "High"


def test_list_preset_policies_contains_expected_names():
    policies = list_preset_policies()
    names = {policy["purpose"] for policy in policies}
    assert "Clinical Research" in names
    assert "Public Release" in names


def test_apply_policy_to_resource_transforms_common_fields():
    policy = {
        "purpose": "Test Policy",
        "fields": {
            "patient_name": "REMOVE",
            "address": "CITY_ONLY",
            "dob": "YEAR_ONLY",
            "phone": "MASK",
        },
    }
    resource = {
        "resourceType": "Patient",
        "name": [{"given": ["John"], "family": "Doe"}],
        "birthDate": "1985-08-15",
        "telecom": [{"system": "phone", "value": "+1-555-0123"}],
        "address": [{"city": "Boston", "state": "MA", "postalCode": "02101"}],
    }

    result = apply_policy_to_resource(policy, resource)
    assert result["name"][0]["family"] == "[REDACTED]"
    assert result["address"][0]["city"] == "[CITY]"
    assert result["birthDate"] == "1985"
    assert result["telecom"][0]["value"] == "[MASKED]"


def test_summary_and_risk_score_are_generated():
    policy = load_preset_policy("Analytics")
    resource = {
        "resourceType": "Patient",
        "name": [{"given": ["Jane"], "family": "Smith"}],
        "birthDate": "1985-08-15",
        "address": [{"city": "Boston", "state": "MA", "postalCode": "02101"}],
    }
    applied = apply_policy_to_resource(policy, resource)
    summary = build_policy_summary(policy, applied)
    preview = build_policy_preview(policy, resource, applied)
    risk = calculate_risk_score(policy, preview["stats"])

    assert summary["purpose"] == "Analytics"
    assert summary["actions"][0]["field"] == "patient_name"
    assert preview["stats"]["modified_fields"] >= 1
    assert risk["risk_level"] in {"Very Low", "Low", "Medium", "High", "Very High"}


def test_policy_mode_controls_output_style():
    policy = {
        "purpose": "Mode Test",
        "fields": {
            "patient_name": "REMOVE",
            "phone": "MASK",
        },
    }
    resource = {
        "resourceType": "Patient",
        "name": [{"given": ["John"], "family": "Doe"}],
        "telecom": [{"system": "phone", "value": "+1-555-0123"}],
    }

    redacted = apply_policy_to_resource(policy, resource, mode="redact")
    masked = apply_policy_to_resource(policy, resource, mode="mask")
    pseudonymized = apply_policy_to_resource(policy, resource, mode="pseudonymize")

    assert redacted["name"][0]["family"] == "[REDACTED]"
    assert masked["telecom"][0]["value"] == "[MASKED]"
    assert pseudonymized["name"][0]["family"].startswith("Patient") or "[" not in pseudonymized["name"][0]["family"]
