from fhir.resources.observation import Observation
from pydantic import ValidationError
from terminology.loinc_lookup import lookup_loinc, get_observation_category
import json
import os

PATIENTS_STORE = "store/patients.json"

VALID_STATUSES = [
    "registered", "preliminary",
    "final", "amended",
    "corrected", "cancelled",
    "entered-in-error", "unknown"
]

STATUS_FIXES = {
    "complete": "final",
    "completed": "final",
    "done": "final",
    "approved": "final",
    "pending": "preliminary",
    "draft": "preliminary",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "error": "entered-in-error"
}

def get_nested_value(data: dict, key: str):
    """Get value from nested dict using dot notation (e.g., 'code.display')"""
    if '.' in key:
        parts = key.split('.')
        value = data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value
    return data.get(key)

INTERPRETATION_MAP = {
    "H": {"code": "H", "display": "High"},
    "L": {"code": "L", "display": "Low"},
    "N": {"code": "N", "display": "Normal"},
    "A": {"code": "A", "display": "Abnormal"},
    "high": {"code": "H", "display": "High"},
    "low": {"code": "L", "display": "Low"},
    "normal": {"code": "N", "display": "Normal"},
    "abnormal": {"code": "A", "display": "Abnormal"},
}


def load_patients() -> dict:
    if os.path.exists(PATIENTS_STORE):
        with open(PATIENTS_STORE, "r") as f:
            return json.load(f)
    return {}


def validate_observation(data: dict) -> dict:
    errors = []
    warnings = []
    loinc_result = None

    # --- Rule-based checks ---

    # 1. Status check
    status = data.get("status")
    if not status:
        errors.append({
            "field": "status",
            "type": "rule_based",
            "received": None,
            "fix": "final",
            "message": "Missing required field 'status'.",
            "explanation": "Every Observation must have a status.",
            "suggested_fix": "Add status field. Most common value is 'final'."
        })
    elif status not in VALID_STATUSES:
        fix = STATUS_FIXES.get(status.lower())
        errors.append({
            "field": "status",
            "type": "rule_based",
            "received": status,
            "fix": fix,
            "message": f"Invalid status value '{status}'.",
            "explanation": f"FHIR accepts: {', '.join(VALID_STATUSES)}",
            "suggested_fix": f"Change '{status}' to '{fix}'" if fix else "Use a valid FHIR status value."
        })

    # 2. Subject / Patient reference check
    subject = data.get("subject")
    if not subject:
        errors.append({
            "field": "subject",
            "type": "rule_based",
            "received": None,
            "fix": None,
            "message": "Missing required field 'subject'.",
            "explanation": "Observation must reference a Patient.",
            "suggested_fix": "Add subject field like 'Patient/P101'."
        })
    else:
        # Support either a reference string or a nested dict with 'reference'
        ref = None
        if isinstance(subject, dict):
            # Accept common keys that may contain a patient ref
            ref = subject.get("reference") or subject.get("id") or subject.get("patient")
        else:
            ref = subject

        if not ref:
            errors.append({
                "field": "subject",
                "type": "rule_based",
                "received": subject,
                "fix": None,
                "message": "Invalid subject structure.",
                "explanation": "Subject must be a string like 'Patient/[id]' or a dict with 'reference'.",
                "suggested_fix": "Use 'subject': {'reference': 'Patient/P101'} or 'subject': 'Patient/P101'"
            })
        else:
            # Normalize to a string reference
            if isinstance(ref, str):
                normalized = ref
                # Normalize plain IDs to Patient/[id] without treating it as an error.
                if not normalized.startswith("Patient/"):
                    normalized = f"Patient/{normalized}"

                # Note: Patient existence check removed to allow standalone observation validation
            else:
                errors.append({
                    "field": "subject",
                    "type": "rule_based",
                    "received": subject,
                    "fix": None,
                    "message": "Unsupported subject type.",
                    "explanation": "Subject should be a string reference or a dict with 'reference'.",
                    "suggested_fix": "Use a proper Patient reference."
                })
    # ID auto-generation
    if not data.get("id"):
        import uuid
        generated_id = f"observation-{uuid.uuid4().hex[:8]}"
        errors.append({
            "field": "id",
            "type": "rule_based",
            "received": None,
            "fix": generated_id,
            "message": "Missing required field 'id'.",
            "explanation": "Every FHIR Observation resource must have a unique id.",
            "suggested_fix": f"Add a unique identifier like 'id': '{generated_id}'"
        })


    # 3. Code / LOINC lookup
    code_display = get_nested_value(data, "code.display") or get_nested_value(data, "code")
    if not code_display:
        errors.append({
            "field": "code",
            "type": "rule_based",
            "received": None,
            "fix": None,
            "message": "Missing required field 'code'.",
            "explanation": "Observation must have a code identifying what was observed.",
            "suggested_fix": "Add a test name or LOINC code."
        })
    else:
        # Look up LOINC code
        loinc_result = lookup_loinc(str(code_display))
        if not loinc_result["found"]:
            warnings.append({
                "field": "code",
                "message": f"Could not find LOINC code for '{code_display}'.",
                "suggestion": "Verify the test name or provide a LOINC code manually."
            })

    # 4. Value check
    value = get_nested_value(data, "valueQuantity.value") or data.get("value")
    unit = get_nested_value(data, "valueQuantity.unit") or data.get("unit")

    if value is None:
        warnings.append({
            "field": "valueQuantity",
            "message": "No value provided for observation.",
            "suggestion": "Add valueQuantity.value for numeric results."
        })

    if value is not None and unit is None:
        warnings.append({
            "field": "valueQuantity.unit",
            "message": "Value provided but unit is missing.",
            "suggestion": "Add a unit like 'mmHg', 'mg/dL', '%' etc."
        })

    # 5. Date check
    from validator import fix_date
    date = data.get("effectiveDateTime")
    if date:
        fixed = fix_date(date)
        if fixed != date:
            errors.append({
                "field": "effectiveDateTime",
                "type": "rule_based",
                "received": date,
                "fix": fixed,
                "message": f"Invalid date format '{date}'.",
                "explanation": "FHIR requires YYYY-MM-DD format.",
                "suggested_fix": f"Change to '{fixed}'"
            })

    # 6. Interpretation check
    interp = data.get("interpretation")
    interp_code = None
    if interp:
        # Interpretations may be a list of dicts or a single string/code
        if isinstance(interp, list):
            first = interp[0]
            if isinstance(first, dict):
                coding = first.get("coding")
                if isinstance(coding, list) and coding:
                    interp_code = coding[0].get("code")
                else:
                    interp_code = first.get("code")
            else:
                interp_code = first
        elif isinstance(interp, dict):
            coding = interp.get("coding")
            if isinstance(coding, list) and coding:
                interp_code = coding[0].get("code")
            else:
                interp_code = interp.get("code")
        else:
            interp_code = interp

        if interp_code and interp_code not in INTERPRETATION_MAP:
            warnings.append({
                "field": "interpretation",
                "message": f"Unrecognized interpretation value '{interp_code}'.",
                "suggestion": "Use: H (High), L (Low), N (Normal), A (Abnormal)"
            })

    # 7. Business rules
    warnings += observation_business_rules(data)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "loinc_result": loinc_result
    }


def build_observation_resource(data: dict, loinc_result: dict) -> dict:
    """Build proper nested FHIR Observation resource"""
    from validator import fix_date

    resource = {"resourceType": "Observation"}

    # ID
    if data.get("id"):
        resource["id"] = data["id"]

    # Status
    status = data.get("status", "final")
    resource["status"] = STATUS_FIXES.get(
        status.lower(), status
    ) if status not in ["final", "preliminary",
                         "registered", "amended"] else status

    # Category from LOINC class
    if loinc_result:
        resource["category"] = [
            get_observation_category(loinc_result.get("class"))
        ]

    # Code with LOINC
    code_display = get_nested_value(data, "code.display") or data.get("code", "Unknown")
    if loinc_result and loinc_result["found"]:
        resource["code"] = {
            "coding": [{
                "system": "http://loinc.org",
                "code": loinc_result["code"],
                "display": loinc_result["display"]
            }],
            "text": str(code_display)
        }
    else:
        resource["code"] = {"text": str(code_display)}

    # Subject
    subject = data.get("subject", "")
    if subject and not subject.startswith("Patient/"):
        subject = f"Patient/{subject}"
    if subject:
        resource["subject"] = {"reference": subject}

    # Effective date
    date = data.get("effectiveDateTime")
    if date:
        resource["effectiveDateTime"] = fix_date(date)

    # Value Quantity
    value = get_nested_value(data, "valueQuantity.value") or data.get("value")
    unit = get_nested_value(data, "valueQuantity.unit") or data.get("unit")
    if value is not None:
        resource["valueQuantity"] = {
            "value": float(value) if str(value).replace(".", "").isdigit() else value,
            "unit": unit or "",
            "system": "http://unitsofmeasure.org",
            "code": unit or ""
        }

    # Interpretation
    interp = data.get("interpretation")
    if interp and interp in INTERPRETATION_MAP:
        interp_data = INTERPRETATION_MAP[interp]
        resource["interpretation"] = [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": interp_data["code"],
                "display": interp_data["display"]
            }]
        }]

    # Reference Range
    ref_low = get_nested_value(data, "referenceRange.low")
    ref_high = get_nested_value(data, "referenceRange.high")
    if ref_low or ref_high:
        ref_range = {}
        if ref_low:
            ref_range["low"] = {"value": float(ref_low), "unit": unit or ""}
        if ref_high:
            ref_range["high"] = {"value": float(ref_high), "unit": unit or ""}
        resource["referenceRange"] = [ref_range]

    # Notes
    note = data.get("note")
    if note:
        resource["note"] = [{"text": str(note)}]

    return resource


def observation_business_rules(data: dict) -> list:
    """Business rule checks specific to observations"""
    warnings = []
    from datetime import datetime
    from validator import fix_date

    date = data.get("effectiveDateTime")
    if date:
        try:
            fixed = fix_date(str(date).strip())
            if fixed and len(fixed) == 10:
                obs_date = datetime.strptime(fixed, "%Y-%m-%d")
                if obs_date > datetime.now():
                    warnings.append({
                        "field": "effectiveDateTime",
                        "message": "Observation date is in the future.",
                        "suggestion": "Verify the observation date is correct."
                    })
        except Exception:
            pass

    value = get_nested_value(data, "valueQuantity.value") or data.get("value")
    unit = get_nested_value(data, "valueQuantity.unit") or data.get("unit")
    code = str(
        get_nested_value(data, "code.display") or data.get("code", "")
    ).lower()

    if value is not None:
        try:
            v = float(str(value).split("/")[0])

            # Blood pressure
            if "blood pressure" in code or "bp" in code:
                if v > 250 or v < 40:
                    warnings.append({
                        "field": "valueQuantity.value",
                        "message": f"Blood pressure value {v} seems unrealistic.",
                        "suggestion": "Normal range: 60-200 mmHg"
                    })

            # Heart rate
            if "heart rate" in code or "pulse" in code:
                if v > 300 or v < 20:
                    warnings.append({
                        "field": "valueQuantity.value",
                        "message": f"Heart rate {v} bpm seems unrealistic.",
                        "suggestion": "Normal range: 40-200 bpm"
                    })

            # Temperature
            if "temperature" in code or "temp" in code:
                if unit and "c" in unit.lower():
                    if v > 45 or v < 30:
                        warnings.append({
                            "field": "valueQuantity.value",
                            "message": f"Temperature {v}°C seems unrealistic.",
                            "suggestion": "Normal range: 35-42°C"
                        })

            # Glucose
            if "glucose" in code:
                if v > 1000 or v < 0:
                    warnings.append({
                        "field": "valueQuantity.value",
                        "message": f"Glucose value {v} seems unrealistic.",
                        "suggestion": "Typical range: 50-500 mg/dL"
                    })

        except (ValueError, TypeError):
            pass

    return warnings
