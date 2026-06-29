import json
import os

BUILT_IN_PATH = "mappings/built_in.json"
USER_MAPPINGS_PATH = "mappings/user_mappings.json"


def load_mappings(resource_type: str = "Patient") -> tuple:
    """Load both built-in and user-defined mappings"""

    with open(BUILT_IN_PATH, "r") as f:
        built_in = json.load(f).get(resource_type, {})

    with open(USER_MAPPINGS_PATH, "r") as f:
        user = json.load(f).get(resource_type, {})

    return built_in, user



def convert_flat_to_nested(data: dict) -> dict:
    """Convert flat dot-notation keys to nested dict structure.
    Example: {"code.display": "Blood Pressure"} -> {"code": {"display": "Blood Pressure"}}
    """
    result = {}
    for key, value in data.items():
        if '.' in key:
            parts = key.split('.')
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    # If intermediate part exists but is not a dict, convert it
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            result[key] = value
    return result


def map_to_fhir(input_data: dict, resource_type: str = "Patient") -> dict:
    built_in, user_mappings = load_mappings(resource_type)

    raw_mapped = {}
    unmapped = []
    applied_rules = []

    for field, value in input_data.items():
        if field == "resourceType":
            continue

        normalized = field.lower().replace(" ", "").replace("_", "")

        if field in user_mappings or normalized in user_mappings:
            fhir_field = user_mappings.get(field) or user_mappings.get(normalized)
            raw_mapped[fhir_field] = value
            applied_rules.append({
                "original_field": field,
                "mapped_to": fhir_field,
                "rule_type": "user_defined"
            })

        elif field in built_in or normalized in built_in:
            fhir_field = built_in.get(field) or built_in.get(normalized)
            raw_mapped[fhir_field] = value
            applied_rules.append({
                "original_field": field,
                "mapped_to": fhir_field,
                "rule_type": "built_in"
            })

        else:
            unmapped.append({
                "field": field,
                "value": value,
                "status": "unmapped",
                "message": f"No mapping rule found for '{field}'.",
                "action_required": "Please provide a manual mapping."
            })

    # Convert flat mapped fields to proper FHIR structure
    fhir_resource = build_fhir_structure(raw_mapped, resource_type)

    return {
        "mapped_resource": fhir_resource,
        "unmapped_fields": unmapped,
        "applied_rules": applied_rules,
        "mapping_complete": len(unmapped) == 0
    }


def build_fhir_structure(raw: dict, resource_type: str) -> dict:
    """
    Convert flat dot-notation mapped fields
    into proper nested FHIR resource structure
    """
    resource = {"resourceType": resource_type}

    # --- Simple flat fields ---
    simple_fields = [
        "id", "gender", "birthDate",
        "deceasedBoolean", "deceasedDateTime"
    ]
    for field in simple_fields:
        if field in raw:
            resource[field] = raw[field]

    # --- Name (HumanName) ---
    name_entry = {}
    if "name.given" in raw:
        value = raw["name.given"]
        name_entry["given"] = [value] if isinstance(value, str) else value
    if "name.family" in raw:
        name_entry["family"] = raw["name.family"]
    if "name" in raw:
        name_entry["text"] = raw["name"]
    if name_entry:
        resource["name"] = [name_entry]

    # --- Telecom ---
    telecom_list = []
    if "telecom" in raw:
        telecom_list.append({
            "system": "phone",
            "value": str(raw["telecom"]),
            "use": "mobile"
        })
    if "telecom.email" in raw:
        telecom_list.append({
            "system": "email",
            "value": raw["telecom.email"]
        })
    if telecom_list:
        resource["telecom"] = telecom_list

    # --- Address ---
    address_entry = {}
    if "address" in raw:
        address_entry["text"] = raw["address"]
    if "address.city" in raw:
        address_entry["city"] = raw["address.city"]
    if "address.state" in raw:
        address_entry["state"] = raw["address.state"]
    if "address.postalCode" in raw:
        address_entry["postalCode"] = raw["address.postalCode"]
    if "address.country" in raw:
        address_entry["country"] = raw["address.country"]
    if address_entry:
        resource["address"] = [address_entry]

    # --- MaritalStatus (CodeableConcept) ---
    MARITAL_CODES = {
        "married": {"system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus", "code": "M", "display": "Married"},
        "single": {"system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus", "code": "S", "display": "Never Married"},
        "divorced": {"system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus", "code": "D", "display": "Divorced"},
        "widowed": {"system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus", "code": "W", "display": "Widowed"},
        "separated": {"system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus", "code": "L", "display": "Legally Separated"},
    }
    if "maritalStatus" in raw:
        value = raw["maritalStatus"].lower()
        coding = MARITAL_CODES.get(value, {
            "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
            "code": value.upper()[0] if value else "U",
            "display": value.title()
        })
        resource["maritalStatus"] = {"coding": [coding]}

    # --- Communication / Language ---
    if "communication.language" in raw:
        resource["communication"] = [{
            "language": {
                "coding": [{
                    "system": "urn:ietf:bcp:47",
                    "code": raw["communication.language"].lower()[:2],
                    "display": raw["communication.language"]
                }]
            },
            "preferred": True
        }]

    # --- DeceasedBoolean fix ---
    if "deceasedBoolean" in resource:
        val = str(resource["deceasedBoolean"]).lower()
        if val in ["yes", "true", "1"]:
            resource["deceasedBoolean"] = True
        elif val in ["no", "false", "0"]:
            resource["deceasedBoolean"] = False

    return resource


def save_user_mapping(field: str, fhir_field: str, resource_type: str = "Patient") -> dict:
    """Save a user-defined mapping to the user mappings JSON file."""
    path = os.path.join(os.path.dirname(__file__), USER_MAPPINGS_PATH)

    if not os.path.exists(path):
        mappings = {}
    else:
        with open(path, "r", encoding="utf-8") as f:
            mappings = json.load(f)

    if resource_type not in mappings:
        mappings[resource_type] = {}

    normalized = field.lower().replace(" ", "").replace("_", "")
    mappings[resource_type][normalized] = fhir_field

    with open(path, "w", encoding="utf-8") as f:
        json.dump(mappings, f, indent=2)

    return {
        "saved": True,
        "message": f"Saved mapping '{field}' -> '{fhir_field}' for resource type '{resource_type}'.",
        "mapping": {field: fhir_field}
    }


def get_all_mappings(resource_type: str = "Patient") -> dict:
    """Return all saved user-defined mappings for a given resource type."""
    path = os.path.join(os.path.dirname(__file__), USER_MAPPINGS_PATH)

    built_in, _ = load_mappings(resource_type)

    if not os.path.exists(path):
        return {
            "resource_type": resource_type,
            "built_in_mappings": built_in,
            "user_defined_mappings": {}
        }

    with open(path, "r", encoding="utf-8") as f:
        mappings = json.load(f)

    user_defined = mappings.get(resource_type, {}) if isinstance(mappings, dict) else {}
    return {
        "resource_type": resource_type,
        "built_in_mappings": built_in,
        "user_defined_mappings": user_defined,
        "total_built_in": len(built_in),
        "total_user_defined": len(user_defined)
    }


def delete_user_mapping(field: str, resource_type: str = "Patient") -> dict:
    """Delete a saved user-defined mapping for a given field."""
    path = os.path.join(os.path.dirname(__file__), USER_MAPPINGS_PATH)

    if not os.path.exists(path):
        return {
            "success": False,
            "message": f"User mappings file not found for resource type '{resource_type}'."
        }

    with open(path, "r", encoding="utf-8") as f:
        mappings = json.load(f)

    normalized = field.lower().replace(" ", "").replace("_", "")
    resource_mappings = mappings.get(resource_type, {})

    if normalized not in resource_mappings:
        return {
            "success": False,
            "message": f"Mapping for field '{field}' not found in resource type '{resource_type}'."
        }

    del resource_mappings[normalized]
    mappings[resource_type] = resource_mappings

    with open(path, "w", encoding="utf-8") as f:
        json.dump(mappings, f, indent=2)

    return {
        "deleted": True,
        "message": f"Deleted mapping for field '{field}' from resource type '{resource_type}'."
    }