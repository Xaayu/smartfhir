from validator import fix_date
import json
import os
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



PATIENTS_STORE = "store/patients.json"
CONDITIONS_STORE = "store/conditions.json"

VALID_STATUSES = [
    "planned", "arrived", "triaged",
    "in-progress", "onleave", "finished",
    "cancelled", "entered-in-error", "unknown"
]

STATUS_FIXES = {
    "complete": "finished",
    "completed": "finished",
    "done": "finished",
    "discharged": "finished",
    "active": "in-progress",
    "ongoing": "in-progress",
    "current": "in-progress",
    "admitted": "in-progress",
    "scheduled": "planned",
    "upcoming": "planned",
    "pending": "planned",
    "waiting": "arrived",
    "checkedin": "arrived",
    "checked-in": "arrived",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "noshow": "cancelled",
    "no-show": "cancelled",
}

CLASS_CODES = {
    "ambulatory": {"code": "AMB", "display": "Ambulatory"},
    "outpatient": {"code": "AMB", "display": "Ambulatory"},
    "amb": {"code": "AMB", "display": "Ambulatory"},
    "inpatient": {"code": "IMP", "display": "Inpatient"},
    "admitted": {"code": "IMP", "display": "Inpatient"},
    "imp": {"code": "IMP", "display": "Inpatient"},
    "emergency": {"code": "EMER", "display": "Emergency"},
    "emer": {"code": "EMER", "display": "Emergency"},
    "er": {"code": "EMER", "display": "Emergency"},
    "urgent": {"code": "EMER", "display": "Emergency"},
    "virtual": {"code": "VR", "display": "Virtual"},
    "telehealth": {"code": "VR", "display": "Virtual"},
    "online": {"code": "VR", "display": "Virtual"},
    "home": {"code": "HH", "display": "Home Health"},
    "homehealth": {"code": "HH", "display": "Home Health"},
}


def load_store(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def validate_encounter(data: dict) -> dict:
    errors = []
    warnings = []

    # 1. Patient reference
    subject = data.get("subject", "")
    if not subject:
        errors.append({
            "field": "subject",
            "type": "rule_based",
            "received": None,
            "fix": None,
            "message": "Missing required field 'subject'.",
            "explanation": "Encounter must reference a Patient.",
            "suggested_fix": "Add subject like 'Patient/P101'."
        })
    else:
        if not subject.startswith("Patient/"):
            subject = f"Patient/{subject}"
        # Note: Patient existence check removed to allow standalone validation
    # ID auto-generation
    if not data.get("id"):
        import uuid
        generated_id = f"encounter-{uuid.uuid4().hex[:8]}"
        errors.append({
            "field": "id",
            "type": "rule_based",
            "received": None,
            "fix": generated_id,
            "message": "Missing required field 'id'.",
            "explanation": "Every FHIR Encounter resource must have a unique id.",
            "suggested_fix": f"Add a unique identifier like 'id': '{generated_id}'"
        })


    # 2. Status check
    status = data.get("status")
    if not status:
        errors.append({
            "field": "status",
            "type": "rule_based",
            "received": None,
            "fix": "finished",
            "message": "Missing required field 'status'.",
            "explanation": "Encounter must have a status.",
            "suggested_fix": "Add status. Common values: planned, in-progress, finished."
        })
    elif status.lower() not in VALID_STATUSES:
        fix = STATUS_FIXES.get(status.lower())
        errors.append({
            "field": "status",
            "type": "rule_based",
            "received": status,
            "fix": fix,
            "message": f"Invalid status '{status}'.",
            "explanation": f"FHIR accepts: {', '.join(VALID_STATUSES)}",
            "suggested_fix": f"Change to '{fix}'" if fix else "Use a valid status."
        })

    # 3. Class check
    encounter_class = data.get("class")
    if not encounter_class:
        errors.append({
            "field": "class",
            "type": "rule_based",
            "received": None,
            "fix": "AMB",
            "message": "Missing required field 'class'.",
            "explanation": "Encounter must have a class.",
            "suggested_fix": "Add class: AMB, IMP, or EMER."
        })
    elif encounter_class.lower() not in CLASS_CODES:
        errors.append({
            "field": "class",
            "type": "ai_needed",
            "received": encounter_class,
            "fix": None,
            "message": f"Unrecognized class '{encounter_class}'.",
            "explanation": None,
            "suggested_fix": None
        })

    # 4. Period dates
    start = get_nested_value(data, "period.start")
    end = get_nested_value(data, "period.end")

    for field, val in [("period.start", start), ("period.end", end)]:
        if val:
            fixed = fix_date(val)
            if fixed != val:
                errors.append({
                    "field": field,
                    "type": "rule_based",
                    "received": val,
                    "fix": fixed,
                    "message": f"Invalid date format '{val}'.",
                    "explanation": "FHIR requires YYYY-MM-DD format.",
                    "suggested_fix": f"Change to '{fixed}'"
                })

    # 5. Business rules
    warnings += encounter_business_rules(data)

    # 6. Reason code vs conditions check
    reason = data.get("reasonCode")
    if reason:
        patient_id = subject.replace("Patient/", "") if subject else ""
        warnings += validate_reason_against_conditions(reason, patient_id)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_reason_against_conditions(
    reason: str, patient_id: str
) -> list:
    """Check if encounter reason matches a registered condition"""
    warnings = []
    if not patient_id:
        return warnings

    conditions = load_store(CONDITIONS_STORE)
    patient_conditions = conditions.get(patient_id, [])

    if not patient_conditions:
        warnings.append({
            "field": "reasonCode",
            "message": f"No registered conditions found for Patient '{patient_id}'.",
            "suggestion": "Consider registering the Condition resource first."
        })
    else:
        reason_lower = reason.lower()
        matched = any(
            reason_lower in str(c).lower()
            for c in patient_conditions
        )
        if not matched:
            warnings.append({
                "field": "reasonCode",
                "message": f"Reason '{reason}' doesn't match any registered condition.",
                "suggestion": f"Registered conditions: {', '.join(str(c) for c in patient_conditions)}"
            })

    return warnings


def encounter_business_rules(data: dict) -> list:
    warnings = []
    from datetime import datetime

    start = get_nested_value(data, "period.start")
    end = get_nested_value(data, "period.end")

    if start and end:
        fixed_start = fix_date(str(start).strip())
        fixed_end = fix_date(str(end).strip())

        # Only warn if start is STRICTLY after end
        # Same date is valid (day visit)
        if fixed_start > fixed_end:
            warnings.append({
                "field": "period",
                "message": "Admission date is after discharge date.",
                "suggestion": "Start date must be before or equal to end date."
            })

    status = (data.get("status") or "").lower()
    if status == "finished" and not end:
        warnings.append({
            "field": "period.end",
            "message": "Encounter marked 'finished' but no end date.",
            "suggestion": "Add period.end for finished encounters."
        })

    if status == "planned" and start:
        try:
            fixed_start = fix_date(str(start).strip())
            if fixed_start and len(fixed_start) == 10:
                if fixed_start < datetime.now().strftime("%Y-%m-%d"):
                    warnings.append({
                        "field": "period.start",
                        "message": "Encounter marked 'planned' but start is past.",
                        "suggestion": "Update status to 'finished' or 'in-progress'."
                    })
        except Exception:
            pass

    return warnings


def build_encounter_resource(data: dict) -> dict:
    resource = {"resourceType": "Encounter"}

    if data.get("id"):
        resource["id"] = data["id"]

    # Status
    status = data.get("status", "finished")
    resource["status"] = STATUS_FIXES.get(
        status.lower(), status.lower()
    ) if status.lower() not in VALID_STATUSES else status.lower()

    # Class
    encounter_class = data.get("class", "AMB")
    class_info = CLASS_CODES.get(
        encounter_class.lower(),
        {"code": encounter_class.upper(), "display": encounter_class.title()}
    )
    resource["class"] = {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": class_info["code"],
        "display": class_info["display"]
    }

    # Type
    encounter_type = data.get("type")
    if encounter_type:
        resource["type"] = [{
            "coding": [{
                "display": str(encounter_type)
            }],
            "text": str(encounter_type)
        }]

    # Subject
    subject = data.get("subject", "")
    if subject and not subject.startswith("Patient/"):
        subject = f"Patient/{subject}"
    if subject:
        resource["subject"] = {"reference": subject}

    # Period
    period = {}
    if get_nested_value(data, "period.start"):
        period["start"] = fix_date(data["period.start"])
    if get_nested_value(data, "period.end"):
        period["end"] = fix_date(data["period.end"])
    if period:
        resource["period"] = period

    # Reason
    reason = data.get("reasonCode")
    if reason:
        resource["reasonCode"] = [{
            "coding": [{"display": str(reason)}],
            "text": str(reason)
        }]

    # Priority
    priority = data.get("priority")
    if priority:
        resource["priority"] = {
            "coding": [{"display": str(priority)}],
            "text": str(priority)
        }

    # Location
    location = data.get("location")
    if location:
        resource["location"] = [{
            "location": {"display": str(location)}
        }]

    # Participant (doctor)
    participant = data.get("participant")
    if participant:
        resource["participant"] = [{
            "individual": {"display": str(participant)}
        }]

    # Note
    if data.get("note"):
        resource["note"] = [{"text": str(data["note"])}]

    return resource