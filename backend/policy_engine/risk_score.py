from typing import Any, Dict


def calculate_risk_score(policy: Dict[str, Any], stats: Dict[str, Any]) -> Dict[str, Any]:
    score = 40
    modified_fields = stats.get("modified_fields", 0)
    removed_values = stats.get("removed_values", 0)
    generalized_values = stats.get("generalized_values", 0)
    hashed_values = stats.get("hashed_values", 0)

    score += min(25, modified_fields * 2)
    score += min(20, removed_values * 2)
    score += min(10, generalized_values)
    score += min(10, hashed_values)

    privacy_level = "Very High"
    explanation = ["Sensitive fields remain visible in the output."]

    if score >= 80:
        privacy_level = "Very Low"
        explanation = ["Direct identifiers were removed and many quasi-identifiers were generalized."]
    elif score >= 60:
        privacy_level = "Low"
        explanation = ["Most identifiers were removed, but some detail remains in the output."]
    elif score >= 40:
        privacy_level = "Medium"
        explanation = ["The policy reduces re-identification risk but leaves some temporal or geographic detail intact."]
    elif score >= 20:
        privacy_level = "High"
        explanation = ["The output retains significant identifying detail and should be reviewed before sharing."]

    if stats.get("generalized_values", 0) == 0 and stats.get("removed_values", 0) == 0:
        explanation.append("Remaining dates or geographic information may still increase re-identification risk.")

    return {
        "score": score,
        "risk_level": privacy_level,
        "explanation": explanation,
        "policy": policy.get("purpose") if isinstance(policy, dict) else None,
    }
