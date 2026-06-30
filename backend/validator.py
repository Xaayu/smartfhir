from fhir.resources.patient import Patient
from pydantic import ValidationError
import json
from datetime import datetime
import re
from cross_resource_validator import CrossResourceValidator

# Known rule-based error patterns


def safe_float(value):
    """Safely convert string to float if possible"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return value


def normalize_boolean(value):
    """Normalize various boolean representations to True/False"""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    val_str = str(value).lower().strip()
    if val_str in ['true', 'yes', 'y', '1', 'on']:
        return True
    if val_str in ['false', 'no', 'n', '0', 'off']:
        return False
    return value


KNOWN_FIXES = {
    "gender": {
        "M": "male",
        "F": "female",
        "m": "male",
        "f": "female",
    }
}


def fix_date(date_str: str) -> str | None:
    """Normalize common date formats to FHIR's YYYY-MM-DD date format."""
    if date_str is None:
        return None

    raw = str(date_str).strip()
    if not raw:
        return None

    if raw.endswith(".0") and raw[:-2].isdigit():
        raw = raw[:-2]

    if re.fullmatch(r"\d{8}", raw):
        for fmt in ("%Y%m%d", "%d%m%Y"):
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass

    if re.fullmatch(r"\d{9,10}", raw):
        try:
            return datetime.fromtimestamp(int(raw)).strftime("%Y-%m-%d")
        except (OSError, OverflowError, ValueError):
            pass

    iso_match = re.match(r"^(\d{4}-\d{2}-\d{2})[T ]", raw)
    if iso_match:
        return iso_match.group(1)

    formats = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d/%m/%y",
        "%m/%d/%y",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%d-%m-%y",
        "%m-%d-%y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%d.%m.%y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return raw

def business_rule_checks(data: dict) -> list:
    warnings = []
    from datetime import datetime

    birth_date = data.get("birthDate")
    if birth_date:
        try:
            dob = datetime.strptime(
                fix_date(birth_date), "%Y-%m-%d"
            )
            age = (datetime.now() - dob).days // 365

            if age > 120:
                warnings.append({
                    "field": "birthDate",
                    "message": f"Patient age ({age} years) is unrealistic.",
                    "suggestion": "Please verify the birth date."
                })
            if dob > datetime.now():        # ← ADD THIS
                warnings.append({
                    "field": "birthDate",
                    "message": "Birth date is in the future.",
                    "suggestion": "Patient cannot be born in the future."
                })
        except:
            pass

    return warnings


def validate_patient(data: dict) -> dict:
    errors = []
    warnings = []

    gender = data.get("gender")
    if gender is not None:
        gender = str(gender).strip()
        if gender == "":
            errors.append({
                "field": "gender",
                "type": "rule_based",
                "received": "",
                "fix": None,
                "message": "Gender cannot be empty string.",
                "explanation": "FHIR accepts: male, female, other, unknown.",
                "suggested_fix": "Provide a valid gender value."
            })
        elif gender not in ["male", "female", "other", "unknown"]:
            fix = KNOWN_FIXES["gender"].get(gender)
            errors.append({
                "field": "gender",
                "type": "rule_based",
                "received": gender,
                "fix": fix,
                "message": f"Invalid gender value '{gender}'.",
                "explanation": "FHIR accepts only: male, female, other, unknown.",
                "suggested_fix": f"Change '{gender}' to '{fix}'" if fix
                else "Use a valid FHIR gender value."
            })

    birth_date = data.get("birthDate")
    if birth_date is not None:
        birth_date = str(birth_date).strip()
        if birth_date:
            fixed_date = fix_date(birth_date)
            if fixed_date != birth_date and fixed_date:
                errors.append({
                    "field": "birthDate",
                    "type": "rule_based",
                    "received": birth_date,
                    "fix": fixed_date,
                    "message": f"Invalid date format '{birth_date}'.",
                    "explanation": "FHIR requires date in YYYY-MM-DD format.",
                    "suggested_fix": f"Change '{birth_date}' to '{fixed_date}'"
                })

    # Empty string ID check
    patient_id = data.get("id")
    if patient_id is not None and str(patient_id).strip() == "":
        errors.append({
            "field": "id",
            "type": "rule_based",
            "received": "",
            "fix": None,
            "message": "Patient id cannot be empty.",
            "explanation": "Every FHIR Patient must have a non-empty id.",
            "suggested_fix": "Provide a valid unique patient identifier."
        })
    elif not data.get("id"):
        import uuid
        generated_id = f"patient-{uuid.uuid4().hex[:8]}"
        errors.append({
            "field": "id",
            "type": "rule_based",
            "received": None,
            "fix": generated_id,
            "message": "Missing required field 'id'.",
            "explanation": "Every FHIR Patient resource must have a unique id.",
            "suggested_fix": f"Add a unique identifier like 'id': '{generated_id}'"
        })

    # Choice field validation: deceasedBoolean vs deceasedDateTime (mutually exclusive)
    has_deceased_boolean = "deceasedBoolean" in data and data["deceasedBoolean"] is not None
    has_deceased_datetime = "deceasedDateTime" in data and data["deceasedDateTime"] is not None
    if has_deceased_boolean and has_deceased_datetime:
        errors.append({
            "field": "deceasedBoolean",
            "type": "rule_based",
            "received": f"deceasedBoolean={data['deceasedBoolean']}, deceasedDateTime={data['deceasedDateTime']}",
            "fix": None,
            "message": "Cannot have both deceasedBoolean and deceasedDateTime.",
            "explanation": "FHIR allows only one deceased field: either deceasedBoolean (boolean) or deceasedDateTime (datetime).",
            "suggested_fix": "Remove one of the deceased fields. Use deceasedBoolean for simple yes/no, or deceasedDateTime for exact time of death."
        })

    # Choice field validation: multipleBirthBoolean vs multipleBirthInteger (mutually exclusive)
    has_multiple_birth_boolean = "multipleBirthBoolean" in data and data["multipleBirthBoolean"] is not None
    has_multiple_birth_integer = "multipleBirthInteger" in data and data["multipleBirthInteger"] is not None
    if has_multiple_birth_boolean and has_multiple_birth_integer:
        errors.append({
            "field": "multipleBirthBoolean",
            "type": "rule_based",
            "received": f"multipleBirthBoolean={data['multipleBirthBoolean']}, multipleBirthInteger={data['multipleBirthInteger']}",
            "fix": None,
            "message": "Cannot have both multipleBirthBoolean and multipleBirthInteger.",
            "explanation": "FHIR allows only one multipleBirth field: either multipleBirthBoolean (true/false) or multipleBirthInteger (number).",
            "suggested_fix": "Remove one of the multipleBirth fields. Use multipleBirthBoolean for yes/no, or multipleBirthInteger for the actual birth order number."
        })

    # Reference field validation
    reference_fields = ["generalPractitioner", "managingOrganization"]
    for field in reference_fields:
        if field in data:
            ref = data[field]
            if isinstance(ref, str):
                # Check if reference has resource type prefix
                if not ref.startswith(("Patient/", "Practitioner/", "Organization/", "Location/", "RelatedPerson/")):
                    errors.append({
                        "field": field,
                        "type": "rule_based",
                        "received": ref,
                        "fix": None,
                        "message": f"Invalid reference format '{ref}'.",
                        "explanation": f"FHIR references must include the resource type (e.g., 'Practitioner/prac-001').",
                        "suggested_fix": f"Add the resource type prefix. For {field}, use 'Practitioner/...' or 'Organization/...' as appropriate."
                    })
            elif isinstance(ref, dict):
                if "reference" not in ref:
                    errors.append({
                        "field": field,
                        "type": "rule_based",
                        "received": str(ref),
                        "fix": None,
                        "message": f"Missing 'reference' field in {field}.",
                        "explanation": "When {field} is an object, it must contain a 'reference' field.",
                        "suggested_fix": f"Add a 'reference' field to the {field} object."
                    })
                elif ref["reference"] and not ref["reference"].startswith(("Patient/", "Practitioner/", "Organization/", "Location/", "RelatedPerson/")):
                    errors.append({
                        "field": f"{field}.reference",
                        "type": "rule_based",
                        "received": ref["reference"],
                        "fix": None,
                        "message": f"Invalid reference format '{ref['reference']}'.",
                        "explanation": "FHIR references must include the resource type (e.g., 'Practitioner/prac-001').",
                        "suggested_fix": "Add the resource type prefix to the reference."
                    })

    # Meta field validation
    if "meta" in data and isinstance(data["meta"], dict):
        meta = data["meta"]
        # versionId should be string
        if "versionId" in meta and not isinstance(meta["versionId"], str):
            errors.append({
                "field": "meta.versionId",
                "type": "rule_based",
                "received": str(meta["versionId"]),
                "fix": str(meta["versionId"]),
                "message": "meta.versionId must be a string.",
                "explanation": "FHIR requires versionId to be a string type.",
                "suggested_fix": f"Convert versionId to string: '{meta['versionId']}'"
            })
        # lastUpdated should be valid ISO 8601 datetime with timezone
        if "lastUpdated" in meta:
            last_updated = meta["lastUpdated"]
            if isinstance(last_updated, str):
                # Check if it has timezone (Z or +/-HH:MM)
                if not (last_updated.endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", last_updated)):
                    errors.append({
                        "field": "meta.lastUpdated",
                        "type": "rule_based",
                        "received": last_updated,
                        "fix": None,
                        "message": "meta.lastUpdated must include timezone.",
                        "explanation": "FHIR requires lastUpdated to be an ISO 8601 datetime with timezone (e.g., '2026-06-30T10:30:00Z' or '2026-06-30T10:30:00+05:30').",
                        "suggested_fix": "Add timezone suffix 'Z' for UTC or '+/-HH:MM' for local timezone."
                    })

    # Telecom array validation
    if "telecom" in data and isinstance(data["telecom"], list):
        valid_telecom_systems = ["phone", "email", "fax", "pager", "url", "sms", "other"]
        valid_telecom_uses = ["home", "work", "temp", "old", "mobile"]
        for idx, telecom in enumerate(data["telecom"]):
            if not isinstance(telecom, dict):
                errors.append({
                    "field": f"telecom[{idx}]",
                    "type": "rule_based",
                    "received": str(telecom),
                    "fix": None,
                    "message": f"telecom[{idx}] must be an object.",
                    "explanation": "Each telecom entry must be a ContactPoint object with system, value, and use fields.",
                    "suggested_fix": "Convert telecom entry to an object with proper structure."
                })
                continue

            # Validate system field
            if "system" in telecom and telecom["system"] not in valid_telecom_systems:
                errors.append({
                    "field": f"telecom[{idx}].system",
                    "type": "rule_based",
                    "received": telecom["system"],
                    "fix": None,
                    "message": f"Invalid telecom system '{telecom['system']}'.",
                    "explanation": f"FHIR telecom system must be one of: {', '.join(valid_telecom_systems)}.",
                    "suggested_fix": f"Use a valid system value from: {', '.join(valid_telecom_systems)}."
                })

            # Validate use field
            if "use" in telecom and telecom["use"] not in valid_telecom_uses:
                errors.append({
                    "field": f"telecom[{idx}].use",
                    "type": "rule_based",
                    "received": telecom["use"],
                    "fix": None,
                    "message": f"Invalid telecom use '{telecom['use']}'.",
                    "explanation": f"FHIR telecom use must be one of: {', '.join(valid_telecom_uses)}.",
                    "suggested_fix": f"Use a valid use value from: {', '.join(valid_telecom_uses)}."
                })

            # Validate rank field (must be positive integer)
            if "rank" in telecom:
                rank = telecom["rank"]
                if not isinstance(rank, int) or rank < 1:
                    errors.append({
                        "field": f"telecom[{idx}].rank",
                        "type": "rule_based",
                        "received": str(rank),
                        "fix": None,
                        "message": f"Invalid telecom rank '{rank}'.",
                        "explanation": "FHIR telecom rank must be a positive integer (1 or greater).",
                        "suggested_fix": "Use a positive integer for rank, or omit the field."
                    })

    # Empty/null handling in arrays
    array_fields = ["identifier", "name", "telecom", "address", "contact", "communication", "photo", "extension"]
    for field in array_fields:
        if field in data:
            value = data[field]
            if isinstance(value, list):
                # Check for null elements in array
                for idx, item in enumerate(value):
                    if item is None:
                        errors.append({
                            "field": f"{field}[{idx}]",
                            "type": "rule_based",
                            "received": "null",
                            "fix": None,
                            "message": f"Null element found in {field} array at index {idx}.",
                            "explanation": "FHIR arrays should not contain null elements.",
                            "suggested_fix": f"Remove the null element from {field}[{idx}]."
                        })
                    elif isinstance(item, dict):
                        # Check for empty string values in dict
                        for key, val in item.items():
                            if val == "":
                                errors.append({
                                    "field": f"{field}[{idx}].{key}",
                                    "type": "rule_based",
                                    "received": "",
                                    "fix": None,
                                    "message": f"Empty string value in {field}[{idx}].{key}.",
                                    "explanation": "Empty string values may cause validation issues in FHIR.",
                                    "suggested_fix": f"Remove the {key} field or provide a valid value."
                                })

    # Extension array validation
    if "extension" in data and isinstance(data["extension"], list):
        for idx, ext in enumerate(data["extension"]):
            if not isinstance(ext, dict):
                errors.append({
                    "field": f"extension[{idx}]",
                    "type": "rule_based",
                    "received": str(ext),
                    "fix": None,
                    "message": f"extension[{idx}] must be an object.",
                    "explanation": "Each extension must be an Extension object with url and value fields.",
                    "suggested_fix": "Convert extension entry to an object with proper structure."
                })
                continue

            # Check required url field
            if "url" not in ext:
                errors.append({
                    "field": f"extension[{idx}]",
                    "type": "rule_based",
                    "received": str(ext),
                    "fix": None,
                    "message": f"extension[{idx}] missing required 'url' field.",
                    "explanation": "FHIR extensions must have a 'url' field identifying the extension definition.",
                    "suggested_fix": "Add a 'url' field to the extension object."
                })
            elif not isinstance(ext["url"], str) or not ext["url"].startswith("http"):
                errors.append({
                    "field": f"extension[{idx}].url",
                    "type": "rule_based",
                    "received": str(ext["url"]),
                    "fix": None,
                    "message": f"Invalid extension URL '{ext['url']}'.",
                    "explanation": "FHIR extension URLs must be valid HTTP/HTTPS URLs.",
                    "suggested_fix": "Provide a valid HTTP/HTTPS URL for the extension."
                })

            # Check that at least one value field is present
            value_fields = [k for k in ext.keys() if k.startswith("value") and k != "url"]
            if not value_fields:
                errors.append({
                    "field": f"extension[{idx}]",
                    "type": "rule_based",
                    "received": str(ext),
                    "fix": None,
                    "message": f"extension[{idx}] missing value field.",
                    "explanation": "FHIR extensions must have a value field (e.g., valueString, valueCodeableConcept, valueBoolean).",
                    "suggested_fix": "Add an appropriate value field to the extension."
                })

    # Contact array validation
    if "contact" in data and isinstance(data["contact"], list):
        for idx, contact in enumerate(data["contact"]):
            if not isinstance(contact, dict):
                errors.append({
                    "field": f"contact[{idx}]",
                    "type": "rule_based",
                    "received": str(contact),
                    "fix": None,
                    "message": f"contact[{idx}] must be an object.",
                    "explanation": "Each contact must be a PatientContact object with relationship, name, and telecom fields.",
                    "suggested_fix": "Convert contact entry to an object with proper structure."
                })
                continue

            # Validate gender field (must be valid FHIR gender)
            if "gender" in contact and contact["gender"] not in ["male", "female", "other", "unknown"]:
                errors.append({
                    "field": f"contact[{idx}].gender",
                    "type": "rule_based",
                    "received": contact["gender"],
                    "fix": None,
                    "message": f"Invalid contact gender '{contact['gender']}'.",
                    "explanation": "FHIR gender must be one of: male, female, other, unknown.",
                    "suggested_fix": "Use a valid FHIR gender value."
                })

            # Validate name field (if present, must have family or given)
            if "name" in contact:
                name = contact["name"]
                if isinstance(name, dict):
                    if not name.get("family") and not name.get("given"):
                        errors.append({
                            "field": f"contact[{idx}].name",
                            "type": "rule_based",
                            "received": str(name),
                            "fix": None,
                            "message": f"contact[{idx}].name must have either 'family' or 'given' field.",
                            "explanation": "FHIR HumanName requires at least a family name or given name(s).",
                            "suggested_fix": "Add either 'family' or 'given' field to the contact name."
                        })

    # Photo array validation
    if "photo" in data and isinstance(data["photo"], list):
        valid_content_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        for idx, photo in enumerate(data["photo"]):
            if not isinstance(photo, dict):
                errors.append({
                    "field": f"photo[{idx}]",
                    "type": "rule_based",
                    "received": str(photo),
                    "fix": None,
                    "message": f"photo[{idx}] must be an object.",
                    "explanation": "Each photo must be an Attachment object with contentType and either url or data field.",
                    "suggested_fix": "Convert photo entry to an object with proper structure."
                })
                continue

            # Validate contentType
            if "contentType" in photo and photo["contentType"] not in valid_content_types:
                errors.append({
                    "field": f"photo[{idx}].contentType",
                    "type": "rule_based",
                    "received": photo["contentType"],
                    "fix": None,
                    "message": f"Invalid photo contentType '{photo['contentType']}'.",
                    "explanation": f"FHIR photo contentType must be one of: {', '.join(valid_content_types)}.",
                    "suggested_fix": f"Use a valid content type from: {', '.join(valid_content_types)}."
                })

            # Check that either url or data is present
            has_url = "url" in photo and photo["url"]
            has_data = "data" in photo and photo["data"]
            if not has_url and not has_data:
                errors.append({
                    "field": f"photo[{idx}]",
                    "type": "rule_based",
                    "received": str(photo),
                    "fix": None,
                    "message": f"photo[{idx}] missing required 'url' or 'data' field.",
                    "explanation": "FHIR Attachment must have either a 'url' (external reference) or 'data' (base64-encoded content).",
                    "suggested_fix": "Add either a 'url' or 'data' field to the photo object."
                })

            # Validate data field (if present, should be base64)
            if has_data and isinstance(photo["data"], str):
                data_val = photo["data"]
                # Basic base64 validation (should only contain base64 chars)
                import base64
                try:
                    base64.b64decode(data_val, validate=True)
                except Exception:
                    errors.append({
                        "field": f"photo[{idx}].data",
                        "type": "rule_based",
                        "received": data_val[:50] + "..." if len(data_val) > 50 else data_val,
                        "fix": None,
                        "message": f"Invalid base64 data in photo[{idx}].data.",
                        "explanation": "FHIR photo data must be valid base64-encoded content.",
                        "suggested_fix": "Provide valid base64-encoded image data."
                    })

    try:
        cleaned = apply_known_fixes(data.copy())
        Patient.model_validate(cleaned)
    except ValidationError as e:
        for err in e.errors():
            field = " → ".join(str(x) for x in err["loc"])
            message = err["msg"]
            already_caught = any(
                e["field"] == err["loc"][0] for e in errors
            )
            if not already_caught:
                errors.append({
                    "field": field,
                    "type": "ai_needed",
                    "received": data.get(err["loc"][0], "unknown"),
                    "fix": None,
                    "message": message,
                    "explanation": None,
                    "suggested_fix": None
                })
    except Exception:
        pass

    warnings += business_rule_checks(data)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def business_rule_checks(data: dict) -> list:
    warnings = []
    from datetime import datetime

    birth_date = data.get("birthDate")
    if birth_date:
        try:
            fixed = fix_date(str(birth_date).strip())
            # Only check full dates not partials
            if fixed and len(fixed) == 10:
                dob = datetime.strptime(fixed, "%Y-%m-%d")
                age = (datetime.now() - dob).days // 365

                if age > 120:
                    warnings.append({
                        "field": "birthDate",
                        "message": f"Patient age ({age} years) is unrealistic.",
                        "suggestion": "Please verify the birth date."
                    })
                if dob > datetime.now():
                    warnings.append({
                        "field": "birthDate",
                        "message": "Birth date is in the future.",
                        "suggestion": "Patient cannot be born in the future."
                    })
                if age < 0:
                    warnings.append({
                        "field": "birthDate",
                        "message": "Birth date is in the future.",
                        "suggestion": "Please verify the birth date."
                    })
        except Exception:
            pass

    return warnings


def apply_known_fixes(data: dict) -> dict:
    """Apply rule-based fixes before FHIR validation"""
    # Strip whitespace from all string values
    for key in list(data.keys()):
        if isinstance(data[key], str):
            data[key] = data[key].strip()

    if "gender" in data and data["gender"]:
        data["gender"] = KNOWN_FIXES["gender"].get(
            data["gender"], data["gender"]
        )

    if "birthDate" in data and data["birthDate"]:
        fixed = fix_date(data["birthDate"])
        if fixed:
            data["birthDate"] = fixed

    # Normalize boolean fields
    for key in ["deceasedBoolean", "deceasedDateTime"]:
        if key in data and data[key] is not None:
            data[key] = normalize_boolean(data[key])

    # Remove empty string fields that would fail validation
    for key in list(data.keys()):
        if data[key] == "":
            del data[key]

    return data


def estimate_birth_date_age(date_str: str) -> tuple[int | None, bool]:
    """Estimate age from a birthDate string.

    Returns a tuple of (age, exact_match).
    exact_match is True when the full date could be parsed, otherwise False.
    """
    from datetime import datetime
    import re

    # Try to parse a normalized ISO date first.
    normalized = fix_date(date_str)
    if normalized != date_str:
        try:
            dob = datetime.strptime(normalized, "%Y-%m-%d")
            return (datetime.now() - dob).days // 365, True
        except ValueError:
            pass

    # If the string is already ISO but invalid, let it fall through.
    try:
        dob = datetime.strptime(date_str, "%Y-%m-%d")
        return (datetime.now() - dob).days // 365, True
    except ValueError:
        pass

    # Fallback to year-only estimation when the full date does not parse.
    match = re.search(r"(?P<year>\d{4})", date_str)
    if match:
        year = int(match.group("year"))
        return datetime.now().year - year, False

    return None, False


def business_rule_checks(data: dict) -> list:
    """Basic business rule warnings"""
    warnings = []

    birth_date = data.get("birthDate")
    if birth_date:
        age, exact = estimate_birth_date_age(birth_date)
        if age is not None:
            if age > 120:
                suggestion = "Please verify the birth date."
                if not exact:
                    message = f"Patient age is estimated to be {age} years based on '{birth_date}', which is unrealistic."
                else:
                    message = f"Patient age ({age} years) is unrealistic."
                warnings.append({
                    "field": "birthDate",
                    "message": message,
                    "suggestion": suggestion
                })
            if age < 0:
                warnings.append({
                    "field": "birthDate",
                    "message": "Birth date is in the future.",
                    "suggestion": "Please verify the birth date."
                })

    return warnings


def validate_cross_resource(
    resource: dict,
    patient_store: dict = None,
    patient: dict = None
) -> dict:
    """
    Validate cross-resource relationships for non-Patient resources.
    
    Args:
        resource: The FHIR resource to validate
        patient_store: Dictionary of all patients for reference resolution
        patient: The specific patient resource if already known
    
    Returns:
        Dictionary with valid, errors, and warnings
    """
    if patient_store is None:
        patient_store = {}
    
    validator = CrossResourceValidator(patient_store)
    resource_type = resource.get("resourceType")
    errors = []
    
    if resource_type == "Observation":
        errors = validator.validate_observation_for_patient(resource, patient)
    elif resource_type == "MedicationRequest":
        errors = validator.validate_medication_request_for_patient(resource, patient)
    elif resource_type == "Encounter":
        errors = validator.validate_encounter_for_patient(resource, patient)
    elif resource_type == "Condition":
        errors = validator.validate_condition_for_patient(resource, patient)
    elif resource_type == "Bundle":
        errors = validator.validate_bundle_patient_consistency(resource)
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": []
    }
