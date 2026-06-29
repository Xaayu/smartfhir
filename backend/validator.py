from fhir.resources.patient import Patient
from pydantic import ValidationError
import json
from datetime import datetime
import re

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
