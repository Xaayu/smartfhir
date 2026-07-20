from typing import Any, Dict

from .executor import apply_policy_to_resource, build_policy_preview
from .risk_score import calculate_risk_score
from .validator import validate_policy


def create_policy_preview(policy: Dict[str, Any], resource: Dict[str, Any], mode: str = "pseudonymize") -> Dict[str, Any]:
    validated = validate_policy(policy)
    processed = apply_policy_to_resource(validated, resource, mode)
    preview = build_policy_preview(validated, resource, processed)
    preview["risk"] = calculate_risk_score(validated, preview["stats"])
    return preview
