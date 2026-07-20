from typing import Any, Dict

from .validator import validate_policy


def build_policy_summary(policy: Dict[str, Any], processed_resource: Dict[str, Any]) -> Dict[str, Any]:
    validated = validate_policy(policy)
    actions = []
    for field, action in validated.get("fields", {}).items():
        if action.upper() == "KEEP":
            continue
        actions.append({
            "field": field,
            "action": action.upper(),
            "description": f"Apply {action.upper()} to {field}",
        })
    return {
        "purpose": validated.get("purpose") or "Custom Policy",
        "privacyLevel": validated.get("privacyLevel") or "Medium",
        "actions": actions,
        "description": validated.get("description"),
        "processed_resource_type": type(processed_resource).__name__,
    }
