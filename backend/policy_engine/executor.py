import copy
import hashlib
import re
from typing import Any, Dict, List, Tuple

from fake_data_genrator import fake_first_name, fake_last_name

from .validator import validate_policy


def _mode_to_policy_action(action: str, mode: str | None) -> str:
    """Translate a selected de-id mode into the policy action behavior."""
    normalized = (action or "KEEP").upper()
    if normalized == "KEEP" or not mode:
        return normalized

    if mode == "redact":
        return "REMOVE"
    if mode == "mask":
        if normalized in {"REMOVE", "REPLACE_FAKE", "GENERALIZE", "HASH", "YEAR_ONLY", "MONTH_YEAR", "CITY_ONLY", "STATE_ONLY", "BLUR_FACE", "SCAN_FREE_TEXT", "SHIFT_DATE", "REMOVE_METADATA"}:
            return "MASK"
        return normalized
    if mode == "pseudonymize":
        if normalized in {"REMOVE", "MASK"}:
            return "REPLACE_FAKE"
        return normalized
    return normalized


def _normalize_action(action: Any) -> str:
    return str(action or "KEEP").upper()


def _mask_value(value: str) -> str:
    if not value:
        return value
    if len(value) <= 2:
        return "[MASKED]"
    return "[MASKED]"


def _fake_value(value: str, field_name: str) -> str:
    if not value:
        return value
    digest = hashlib.sha256(f"{field_name}:{value}".encode("utf-8")).hexdigest()[:8]
    if field_name in {"email", "phone"}:
        return f"fake-{digest}@example.org"
    if field_name == "name":
        return f"{fake_first_name(value)} {fake_last_name(value)}"
    if field_name == "address":
        return f"{digest[:4]} Example Street"
    return f"[{field_name.upper()}_{digest[:4]}]"


def _transform_string(value: Any, action: str, field_name: str = "value") -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        if action == "REMOVE":
            return "[REDACTED]"
        if action == "MASK":
            return _mask_value(value)
        if action == "REPLACE_FAKE":
            return _fake_value(value, field_name)
        if action == "GENERALIZE":
            return "[GENERALIZED]"
        if action == "HASH":
            return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
        if action == "YEAR_ONLY":
            match = re.match(r"(\d{4})", value)
            return match.group(1) if match else value
        if action == "MONTH_YEAR":
            match = re.match(r"(\d{4})[-/](\d{2})", value)
            return f"{match.group(1)}-{match.group(2)}" if match else value
        if action == "CITY_ONLY":
            return "[CITY]"
        if action == "STATE_ONLY":
            return "[STATE]"
        if action == "BLUR_FACE":
            return "[BLURRED]"
        if action == "SCAN_FREE_TEXT":
            cleaned = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[REDACTED_EMAIL]", value)
            cleaned = re.sub(r"(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})", "[REDACTED_PHONE]", cleaned)
            return cleaned
        if action == "SHIFT_DATE":
            return value
        if action == "REMOVE_METADATA":
            return ""
        return value
    if isinstance(value, list):
        return [_transform_string(item, action, field_name) for item in value]
    if isinstance(value, dict):
        return {k: _transform_string(v, action, field_name) for k, v in value.items()}
    return value


def _apply_action_to_name(name_list: List[Dict[str, Any]], action: str) -> List[Dict[str, Any]]:
    if not isinstance(name_list, list):
        return name_list
    result = []
    for entry in name_list:
        if not isinstance(entry, dict):
            result.append(entry)
            continue
        updated = copy.deepcopy(entry)
        if "family" in updated:
            updated["family"] = _transform_string(updated.get("family"), action, "name")
        if "given" in updated:
            updated["given"] = [
                _transform_string(item, action, "name") if isinstance(item, str) else item
                for item in updated.get("given", [])
            ]
        if "text" in updated:
            updated["text"] = _transform_string(updated.get("text"), action, "name")
        result.append(updated)
    return result


def _apply_action_to_telecom(telecom_list: List[Dict[str, Any]], action: str, system: str) -> List[Dict[str, Any]]:
    if not isinstance(telecom_list, list):
        return telecom_list
    result = []
    for entry in telecom_list:
        if not isinstance(entry, dict):
            result.append(entry)
            continue
        updated = copy.deepcopy(entry)
        entry_system = str(updated.get("system") or "").lower()
        if system and entry_system != system:
            result.append(updated)
            continue
        if "value" in updated:
            updated["value"] = _transform_string(updated.get("value"), action, system or "telecom")
        result.append(updated)
    return result


def _apply_action_to_address(address_list: List[Dict[str, Any]], action: str) -> List[Dict[str, Any]]:
    if not isinstance(address_list, list):
        return address_list
    result = []
    for entry in address_list:
        if not isinstance(entry, dict):
            result.append(entry)
            continue
        updated = copy.deepcopy(entry)
        if action == "CITY_ONLY" and "city" in updated:
            updated["city"] = _transform_string(updated.get("city"), action, "address")
        if action == "STATE_ONLY" and "state" in updated:
            updated["state"] = _transform_string(updated.get("state"), action, "address")
        if action in {"GENERALIZE", "REMOVE", "MASK", "REPLACE_FAKE", "HASH", "YEAR_ONLY", "MONTH_YEAR"}:
            if "line" in updated:
                updated["line"] = [
                    _transform_string(item, action, "address") if isinstance(item, str) else item
                    for item in updated.get("line", [])
                ]
            if "text" in updated:
                updated["text"] = _transform_string(updated.get("text"), action, "address")
            if "city" in updated:
                updated["city"] = _transform_string(updated.get("city"), action, "address")
            if "state" in updated:
                updated["state"] = _transform_string(updated.get("state"), action, "address")
        result.append(updated)
    return result


def _apply_action_to_note(note_list: List[Dict[str, Any]], action: str) -> List[Dict[str, Any]]:
    if not isinstance(note_list, list):
        return note_list
    result = []
    for entry in note_list:
        if not isinstance(entry, dict):
            result.append(entry)
            continue
        updated = copy.deepcopy(entry)
        if "text" in updated:
            updated["text"] = _transform_string(updated.get("text"), action, "note")
        result.append(updated)
    return result


def _apply_to_resource_fields(resource: Dict[str, Any], rules: Dict[str, str], mode: str | None = None) -> Dict[str, Any]:
    result = copy.deepcopy(resource)

    if not isinstance(result, dict):
        return result

    if "patient_name" in rules:
        action = _normalize_action(rules["patient_name"])
        effective_action = _mode_to_policy_action(action, mode)
        if effective_action != "KEEP":
            if "name" in result:
                result["name"] = _apply_action_to_name(result.get("name", []), effective_action)

    if "phone" in rules:
        action = _normalize_action(rules["phone"])
        effective_action = _mode_to_policy_action(action, mode)
        if effective_action != "KEEP":
            if "telecom" in result:
                result["telecom"] = _apply_action_to_telecom(result.get("telecom", []), effective_action, "phone")

    if "email" in rules:
        action = _normalize_action(rules["email"])
        effective_action = _mode_to_policy_action(action, mode)
        if effective_action != "KEEP":
            if "telecom" in result:
                result["telecom"] = _apply_action_to_telecom(result.get("telecom", []), effective_action, "email")

    if "address" in rules:
        action = _normalize_action(rules["address"])
        effective_action = _mode_to_policy_action(action, mode)
        if effective_action != "KEEP":
            if "address" in result:
                result["address"] = _apply_action_to_address(result.get("address", []), effective_action)

    if "dob" in rules or "birthDate" in rules:
        action = _normalize_action(rules.get("dob") or rules.get("birthDate") or "KEEP")
        effective_action = _mode_to_policy_action(action, mode)
        if effective_action != "KEEP" and "birthDate" in result:
            result["birthDate"] = _transform_string(result.get("birthDate"), effective_action, "dob")

    if "dates" in rules:
        action = _normalize_action(rules["dates"])
        effective_action = _mode_to_policy_action(action, mode)
        if effective_action != "KEEP":
            for key in list(result.keys()):
                if "date" in key.lower() or key.lower() in {"effective_datetime", "issued", "recorded", "start", "end"}:
                    result[key] = _transform_string(result.get(key), effective_action, key)
            if isinstance(result.get("identifier"), list):
                result["identifier"] = [
                    _transform_string(item, effective_action, "date") if isinstance(item, dict) else item
                    for item in result.get("identifier", [])
                ]

    if "patient_id" in rules:
        action = _normalize_action(rules["patient_id"])
        effective_action = _mode_to_policy_action(action, mode)
        if effective_action != "KEEP":
            if "id" in result:
                result["id"] = _transform_string(result.get("id"), effective_action, "patient_id")

    if "medical_record_number" in rules:
        action = _normalize_action(rules["medical_record_number"])
        effective_action = _mode_to_policy_action(action, mode)
        if effective_action != "KEEP":
            if isinstance(result.get("identifier"), list):
                new_identifiers = []
                for item in result.get("identifier", []):
                    if isinstance(item, dict):
                        updated = copy.deepcopy(item)
                        if "type" in updated:
                            updated["type"] = _transform_string(updated.get("type"), effective_action, "identifier")
                        if "value" in updated:
                            updated["value"] = _transform_string(updated.get("value"), effective_action, "identifier")
                        new_identifiers.append(updated)
                    else:
                        new_identifiers.append(item)
                result["identifier"] = new_identifiers

    if "organization" in rules:
        action = _normalize_action(rules["organization"])
        effective_action = _mode_to_policy_action(action, mode)
        if effective_action != "KEEP":
            for key in ["managingOrganization", "organization", "serviceProvider"]:
                if key in result:
                    result[key] = _transform_string(result.get(key), effective_action, key)

    if "clinical_notes" in rules:
        action = _normalize_action(rules["clinical_notes"])
        effective_action = _mode_to_policy_action(action, mode)
        if effective_action != "KEEP":
            if "note" in result:
                result["note"] = _apply_action_to_note(result.get("note", []), effective_action)
            for key in ["text", "description", "summary"]:
                if key in result:
                    result[key] = _transform_string(result.get(key), effective_action, key)

    if "lab_results" in rules:
        action = _normalize_action(rules["lab_results"])
        effective_action = _mode_to_policy_action(action, mode)
        if effective_action != "KEEP":
            for key in ["value", "component"]:
                if key in result:
                    result[key] = _transform_string(result.get(key), effective_action, key)

    if "medications" in rules:
        action = _normalize_action(rules["medications"])
        effective_action = _mode_to_policy_action(action, mode)
        if effective_action != "KEEP":
            if "medicationCodeableConcept" in result:
                result["medicationCodeableConcept"] = _transform_string(result.get("medicationCodeableConcept"), effective_action, "medication")

    return result


def apply_policy_to_resource(policy: Dict[str, Any], resource: Dict[str, Any], mode: str | None = None) -> Dict[str, Any]:
    validated = validate_policy(policy)
    resource_copy = copy.deepcopy(resource)
    if isinstance(resource_copy, dict) and resource_copy.get("resourceType") == "Bundle":
        entries = resource_copy.get("entry", [])
        if isinstance(entries, list):
            resource_copy["entry"] = [
                {
                    **entry,
                    "resource": _apply_to_resource_fields(entry.get("resource", {}), validated.get("fields", {}), mode),
                }
                if isinstance(entry, dict)
                else entry
                for entry in entries
            ]
        return resource_copy
    return _apply_to_resource_fields(resource_copy, validated.get("fields", {}), mode)


def build_policy_summary(policy: Dict[str, Any], processed_resource: Dict[str, Any]) -> Dict[str, Any]:
    validated = validate_policy(policy)
    actions = []
    for field, action in validated.get("fields", {}).items():
        action_name = _normalize_action(action)
        if action_name == "KEEP":
            continue
        descriptions = {
            "REMOVE": f"Remove {field.replace('_', ' ')}",
            "MASK": f"Mask {field.replace('_', ' ')}",
            "REPLACE_FAKE": f"Replace {field.replace('_', ' ')} with fake values",
            "GENERALIZE": f"Generalize {field.replace('_', ' ')}",
            "HASH": f"Hash {field.replace('_', ' ')}",
            "SHIFT_DATE": f"Shift {field.replace('_', ' ')} values",
            "YEAR_ONLY": f"Keep only the year for {field.replace('_', ' ')}",
            "MONTH_YEAR": f"Keep month and year for {field.replace('_', ' ')}",
            "CITY_ONLY": f"Limit {field.replace('_', ' ')} to city level",
            "STATE_ONLY": f"Limit {field.replace('_', ' ')} to state level",
            "REMOVE_METADATA": f"Remove metadata for {field.replace('_', ' ')}",
            "BLUR_FACE": f"Blur face-related content in {field.replace('_', ' ')}",
            "SCAN_FREE_TEXT": f"Scan free text in {field.replace('_', ' ')}",
        }
        actions.append({"field": field, "action": action_name, "description": descriptions.get(action_name, f"Apply {action_name} to {field}")})

    return {
        "purpose": validated.get("purpose") or "Custom Policy",
        "privacyLevel": validated.get("privacyLevel") or "Medium",
        "actions": actions,
        "description": validated.get("description"),
        "processed_resource_type": type(processed_resource).__name__,
    }


def build_policy_preview(policy: Dict[str, Any], original_resource: Dict[str, Any], processed_resource: Dict[str, Any]) -> Dict[str, Any]:
    summary = build_policy_summary(policy, processed_resource)
    stats = {
        "modified_fields": 0,
        "removed_values": 0,
        "generalized_values": 0,
        "hashed_values": 0,
    }

    def walk(original: Any, updated: Any) -> None:
        if isinstance(original, dict) and isinstance(updated, dict):
            for key in original.keys():
                if key not in updated:
                    continue
                walk(original[key], updated[key])
            return
        if isinstance(original, list) and isinstance(updated, list):
            for left, right in zip(original, updated):
                walk(left, right)
            return
        if original != updated:
            stats["modified_fields"] += 1
            if updated is None:
                stats["removed_values"] += 1
            if isinstance(updated, str) and updated == "[GENERALIZED]":
                stats["generalized_values"] += 1
            if isinstance(updated, str) and len(updated) == 16 and re.fullmatch(r"[0-9a-f]+", updated):
                stats["hashed_values"] += 1

    walk(original_resource, processed_resource)
    return {
        "policy": validated_policy(policy),
        "summary": summary,
        "stats": stats,
        "processed_resource": processed_resource,
    }


def validated_policy(policy: Dict[str, Any]) -> Dict[str, Any]:
    return validate_policy(policy)
