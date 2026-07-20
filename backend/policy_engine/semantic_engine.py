import copy
import hashlib
from typing import Any, Dict

from fake_data_genrator import fake_first_name, fake_last_name
from phi_deidentifier import PHIDeidentifier
from .compiler import compile_policy


def _normalize_year(value: str) -> str:
    if not value:
        return value
    try:
        return str(value)[:4]
    except Exception:
        return value


def _apply_date_action(value: str, action: str) -> str:
    if not value:
        return value
    if action == "YEAR_ONLY":
        return _normalize_year(value)
    if action == "MONTH_YEAR":
        try:
            parts = str(value).split("-")
            if len(parts) >= 2:
                return f"{parts[0]}-{parts[1]}"
        except Exception:
            return value
    if action == "SHIFT_DATE":
        return value
    if action == "REMOVE":
        return "[REDACTED]"
    if action == "MASK":
        return "[MASKED]"
    return value


def apply_semantic_policy(policy: Dict[str, Any], resource: Dict[str, Any], mode: str | None = None) -> Dict[str, Any]:
    compiled = compile_policy(policy)
    engine = PHIDeidentifier(mode=mode or "pseudonymize")
    result = engine.deidentify_resource(copy.deepcopy(resource))

    actions = compiled.get("actions", {})

    purpose = (policy.get("purpose") or "Custom Policy").lower()

    patient_name_action = actions.get("patient_name", "KEEP")
    if patient_name_action != "KEEP" and isinstance(result.get("name"), list):
        updated_names = []
        for entry in result["name"]:
            if not isinstance(entry, dict):
                updated_names.append(entry)
                continue
            updated = copy.deepcopy(entry)
            if patient_name_action == "REMOVE":
                updated["family"] = "[REDACTED]"
                updated["given"] = ["[REDACTED]"]
                updated["text"] = "[REDACTED]"
            elif patient_name_action == "MASK":
                updated["family"] = "[MASKED]"
                updated["given"] = ["[MASKED]"]
                updated["text"] = "[MASKED]"
            elif patient_name_action == "REPLACE_FAKE":
                original_family = updated.get("family") or "Doe"
                original_given = updated.get("given", ["John"])
                given_value = original_given[0] if isinstance(original_given, list) and original_given else "John"
                updated["family"] = fake_last_name(str(original_family))
                updated["given"] = [fake_first_name(str(given_value))]
                updated["text"] = f"{updated['given'][0]} {updated['family']}"
            updated_names.append(updated)
        result["name"] = updated_names

    government_identifier_action = actions.get("government_identifier", "KEEP")
    insurance_identifier_action = actions.get("insurance_identifier", "KEEP")
    employee_identifier_action = actions.get("employee_identifier", "KEEP")
    if isinstance(result.get("identifier"), list):
        for item in result["identifier"]:
            if not isinstance(item, dict) or not item.get("value"):
                continue
            category = engine._classify_identifier(item)
            action = "KEEP"
            if category in {"social_security", "passport", "driver_license", "national_identifier"}:
                action = government_identifier_action
            elif category == "insurance_number":
                action = insurance_identifier_action or government_identifier_action
            elif category == "employee_id":
                action = employee_identifier_action or government_identifier_action
            elif category in {"medical_record_number"}:
                action = actions.get("patient_identifier", "KEEP") or government_identifier_action
            if action == "REMOVE":
                item["value"] = "[REDACTED]"
            elif action == "HASH":
                item["value"] = hashlib.sha256(str(item["value"]).encode("utf-8")).hexdigest()[:16]
            elif action == "MASK":
                item["value"] = "[MASKED]"
            elif action == "REPLACE_FAKE":
                item["value"] = "FAKE-ID"

    address_action = actions.get("address", "KEEP")
    if address_action != "KEEP" and isinstance(result.get("address"), list):
        updated_addresses = []
        for item in result["address"]:
            if not isinstance(item, dict):
                updated_addresses.append(item)
                continue
            updated = copy.deepcopy(item)
            if address_action == "CITY_ONLY":
                updated["city"] = "[CITY]"
                updated["state"] = "[STATE]"
                updated["postalCode"] = "[REDACTED]"
                updated["line"] = ["[REDACTED]"]
            elif address_action == "STATE_ONLY":
                updated["city"] = "[CITY]"
                updated["state"] = "[STATE]"
            elif address_action == "COUNTRY_ONLY":
                updated["city"] = "[CITY]"
                updated["state"] = "[STATE]"
                updated["country"] = "[COUNTRY]"
            elif address_action == "REMOVE_LINE":
                updated["line"] = []
            elif address_action == "REMOVE_POSTAL_CODE":
                updated["postalCode"] = "[REDACTED]"
            elif address_action in {"REMOVE", "GENERALIZE"}:
                updated["city"] = "[REDACTED]"
                updated["state"] = "[REDACTED]"
                updated["postalCode"] = "[REDACTED]"
                updated["line"] = ["[REDACTED]"]
            updated_addresses.append(updated)
        result["address"] = updated_addresses

    birth_date_action = actions.get("birth_date", "KEEP")
    if birth_date_action != "KEEP" and result.get("birthDate"):
        result["birthDate"] = _apply_date_action(result["birthDate"], birth_date_action)

    free_text_action = actions.get("free_text", "KEEP") or actions.get("clinical_notes", "KEEP") or actions.get("narrative", "KEEP")
    if free_text_action != "KEEP" and isinstance(result.get("text"), dict):
        if free_text_action == "REMOVE":
            result["text"]["div"] = "[REDACTED]"
        else:
            result["text"]["div"] = engine._enhanced_nlp_scan(result["text"].get("div", ""), "text.div", result.get("id", ""), None)

    practitioner_action = actions.get("practitioner", "KEEP")
    if practitioner_action != "KEEP":
        transforms = [
            result.get("generalPractitioner"),
            result.get("managingOrganization"),
            result.get("serviceProvider"),
        ]
        for item in transforms:
            if isinstance(item, dict) and "display" in item:
                if practitioner_action == "REMOVE":
                    item["display"] = "[REDACTED]"
                elif practitioner_action == "MASK":
                    item["display"] = "[MASKED]"
        if isinstance(result.get("participant"), list):
            for part in result["participant"]:
                if isinstance(part, dict):
                    individual = part.get("individual")
                    if isinstance(individual, dict) and "display" in individual:
                        if practitioner_action == "REMOVE":
                            individual["display"] = "[REDACTED]"
                        elif practitioner_action == "MASK":
                            individual["display"] = "[MASKED]"
        for key in ["performer", "requester", "recorder", "asserter"]:
            if isinstance(result.get(key), list):
                for entry in result[key]:
                    if isinstance(entry, dict) and "display" in entry:
                        if practitioner_action == "REMOVE":
                            entry["display"] = "[REDACTED]"
                        elif practitioner_action == "MASK":
                            entry["display"] = "[MASKED]"
            elif isinstance(result.get(key), dict) and "display" in result[key]:
                if practitioner_action == "REMOVE":
                    result[key]["display"] = "[REDACTED]"
                elif practitioner_action == "MASK":
                    result[key]["display"] = "[MASKED]"

    organization_action = actions.get("organization", "KEEP")
    if organization_action != "KEEP":
        for key in ["managingOrganization", "serviceProvider"]:
            if isinstance(result.get(key), dict):
                if organization_action == "REMOVE":
                    result[key]["display"] = "[REDACTED]"
                elif organization_action == "GENERALIZE":
                    result[key]["display"] = "Generalized Organization"

    return result
