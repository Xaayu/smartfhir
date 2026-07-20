from typing import Any, Dict

SUPPORTED_ACTIONS = {
    "KEEP",
    "REMOVE",
    "MASK",
    "REPLACE_FAKE",
    "GENERALIZE",
    "HASH",
    "SHIFT_DATE",
    "YEAR_ONLY",
    "MONTH_YEAR",
    "CITY_ONLY",
    "STATE_ONLY",
    "REMOVE_METADATA",
    "BLUR_FACE",
    "SCAN_FREE_TEXT",
}


def validate_policy(policy: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(policy, dict):
        raise ValueError("Policy must be an object")

    purpose = policy.get("purpose") or "Custom Policy"
    fields = policy.get("fields") or {}
    if not isinstance(fields, dict):
        raise ValueError("Policy fields must be an object")

    invalid_actions = [
        action for action in fields.values() if isinstance(action, str) and action.upper() not in SUPPORTED_ACTIONS
    ]
    if invalid_actions:
        raise ValueError(f"Unsupported policy actions: {sorted(set(invalid_actions))}")

    objectives = policy.get("objectives") or [
        "Remove direct identifiers",
        "Reduce quasi-identifiers",
        "Minimize re-identification risk",
        "Preserve clinical usefulness where possible",
    ]
    recommended_for = policy.get("recommendedFor") or []
    not_recommended_for = policy.get("notRecommendedFor") or []

    if not isinstance(objectives, list) or not all(isinstance(item, str) for item in objectives):
        raise ValueError("Policy objectives must be a list of strings")
    if not isinstance(recommended_for, list) or not all(isinstance(item, str) for item in recommended_for):
        raise ValueError("Recommended use cases must be a list of strings")
    if not isinstance(not_recommended_for, list) or not all(isinstance(item, str) for item in not_recommended_for):
        raise ValueError("Not recommended use cases must be a list of strings")

    return {
        "purpose": purpose,
        "fields": {str(k): str(v).upper() for k, v in fields.items()},
        "description": str(policy.get("description") or f"Designed for {purpose.lower()} workflows with privacy-preserving transformations."),
        "privacyLevel": str(policy.get("privacyLevel") or "Medium"),
        "objectives": [str(item) for item in objectives],
        "recommendedFor": [str(item) for item in recommended_for],
        "notRecommendedFor": [str(item) for item in not_recommended_for],
    }
