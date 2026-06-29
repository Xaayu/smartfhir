import json
from validator import fix_date
from terminology.rxnorm_lookup import lookup_rxnorm
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

VALID_STATUSES = [
    "active", "on-hold", "cancelled",
    "completed", "entered-in-error",
    "stopped", "draft", "unknown"
]

STATUS_FIXES = {
    "complete": "completed",
    "completed": "completed",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "prescribed": "active",
    "hold": "on-hold",
    "onhold": "on-hold",
    "requested": "active",
    "pending": "draft",
    "drafted": "draft"
}

VALID_INTENTS = [
    "proposal", "plan", "order",
    "original-order", "reflex-order",
    "filler-order", "instance-order", "option"
]

INTENT_FIXES = {
    "prescription": "order",
    "request": "order",
    "planned": "plan",
    "proposed": "proposal",
    "option": "option"
}


def normalize_patient_reference(value):
    if not value:
        return None
    if isinstance(value, dict):
        ref = value.get("reference") or value.get("id") or value.get("patient")
    else:
        ref = value

    if not isinstance(ref, str):
        return None

    ref = ref.strip()
    if not ref:
        return None

    if not ref.startswith("Patient/"):
        ref = f"Patient/{ref}"

    return ref


def load_patients() -> dict:
    if os.path.exists(PATIENTS_STORE):
        with open(PATIENTS_STORE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def validate_medication(data: dict) -> dict:
    errors = []
    warnings = []

    medication_name = data.get("medicationCodeableConcept") or data.get("medication")
    if not medication_name:
        errors.append({
            "field": "medicationCodeableConcept",
            "type": "rule_based",
            "received": None,
            "fix": None,
            "message": "Missing medication name.",
            "explanation": "MedicationRequest must identify the medication.",
            "suggested_fix": "Provide medication name in medicationCodeableConcept."
        })
        rxnorm_result = {"found": False, "code": None, "display": None, "system": None, "source": "none"}
    else:
        rxnorm_result = lookup_rxnorm(str(medication_name))
        if not rxnorm_result.get("found"):
            warnings.append({
                "field": "medicationCodeableConcept",
                "message": f"Could not resolve RxNorm code for '{medication_name}'.",
                "suggestion": "Verify medication name or provide a standard RxNorm identifier."
            })

    subject = normalize_patient_reference(data.get("subject"))
    if not subject:
        errors.append({
            "field": "subject",
            "type": "rule_based",
            "received": data.get("subject"),
            "fix": None,
            "message": "Missing or invalid Patient reference.",
            "explanation": "MedicationRequest must reference a Patient resource.",
            "suggested_fix": "Use 'subject': 'Patient/[id]' or a dict containing reference."
        })
    else:
        data["subject"] = subject
        # Note: Patient existence check removed to allow standalone validation
    # ID auto-generation
    if not data.get("id"):
        import uuid
        generated_id = f"medication-{uuid.uuid4().hex[:8]}"
        errors.append({
            "field": "id",
            "type": "rule_based",
            "received": None,
            "fix": generated_id,
            "message": "Missing required field 'id'.",
            "explanation": "Every FHIR MedicationRequest resource must have a unique id.",
            "suggested_fix": f"Add a unique identifier like 'id': '{generated_id}'"
        })


    status = data.get("status")
    if not status:
        errors.append({
            "field": "status",
            "type": "rule_based",
            "received": None,
            "fix": "active",
            "message": "Missing MedicationRequest status.",
            "explanation": "MedicationRequest requires a status value.",
            "suggested_fix": "Add status e.g. 'active', 'on-hold', or 'completed'."
        })
    else:
        normalized_status = status.lower().strip()
        if normalized_status not in VALID_STATUSES:
            fix = STATUS_FIXES.get(normalized_status)
            errors.append({
                "field": "status",
                "type": "rule_based",
                "received": status,
                "fix": fix,
                "message": f"Invalid status '{status}'.",
                "explanation": f"FHIR accepts: {', '.join(VALID_STATUSES)}.",
                "suggested_fix": f"Change to '{fix}'" if fix else "Use a valid MedicationRequest status."
            })

    intent = data.get("intent")
    if not intent:
        errors.append({
            "field": "intent",
            "type": "rule_based",
            "received": None,
            "fix": "order",
            "message": "Missing intent field.",
            "explanation": "MedicationRequest should include an intent (e.g., 'order').",
            "suggested_fix": "Add intent such as 'order' or 'plan'."
        })
    else:
        normalized_intent = intent.lower().strip()
        if normalized_intent not in VALID_INTENTS:
            fix = INTENT_FIXES.get(normalized_intent)
            errors.append({
                "field": "intent",
                "type": "rule_based",
                "received": intent,
                "fix": fix,
                "message": f"Unrecognized intent '{intent}'.",
                "explanation": f"Valid intents: {', '.join(VALID_INTENTS)}.",
                "suggested_fix": f"Change to '{fix}'" if fix else "Use a valid intent value."
            })

    for field in ["dispenseRequest.start", "dispenseRequest.end"]:
        value = data.get(field)
        if value:
            fixed = fix_date(value)
            if fixed != value:
                errors.append({
                    "field": field,
                    "type": "rule_based",
                    "received": value,
                    "fix": fixed,
                    "message": f"Invalid date format '{value}'.",
                    "explanation": "FHIR requires YYYY-MM-DD date format.",
                    "suggested_fix": f"Change to '{fixed}'."
                })

    quantity = get_nested_value(data, "dispenseRequest.quantity")
    if quantity is not None and not isinstance(quantity, (int, float)):
        try:
            float(quantity)
        except Exception:
            warnings.append({
                "field": "dispenseRequest.quantity",
                "message": f"Dispense quantity '{quantity}' is not numeric.",
                "suggestion": "Use a numeric quantity value."
            })

    # Business rules
    warnings += medication_business_rules(data)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "rxnorm_result": rxnorm_result
    }


def medication_business_rules(data: dict) -> list:
    """Business rule checks specific to MedicationRequest."""
    warnings = []
    from datetime import datetime

    start = get_nested_value(data, "dispenseRequest.start")
    end = get_nested_value(data, "dispenseRequest.end")

    if start and end:
        try:
            fixed_start = fix_date(str(start).strip())
            fixed_end = fix_date(str(end).strip())
            if fixed_start and fixed_end and len(fixed_start) == 10 and len(fixed_end) == 10:
                start_date = datetime.strptime(fixed_start, "%Y-%m-%d")
                end_date = datetime.strptime(fixed_end, "%Y-%m-%d")
                if end_date < start_date:
                    warnings.append({
                        "field": "dispenseRequest.end",
                        "message": "Medication end date is before the start date.",
                        "suggestion": "Verify the medication validity period."
                    })
        except Exception:
            pass

    dose = get_nested_value(data, "dosageInstruction.dose")
    if dose is not None:
        try:
            dose_value = float(str(dose).strip())
            if dose_value <= 0:
                warnings.append({
                    "field": "dosageInstruction.dose",
                    "message": "Medication dose should be greater than zero.",
                    "suggestion": "Verify the prescribed dose."
                })
            elif dose_value > 10000:
                warnings.append({
                    "field": "dosageInstruction.dose",
                    "message": f"Medication dose {dose_value:g} appears unusually high.",
                    "suggestion": "Verify the dose and unit."
                })
        except (ValueError, TypeError):
            pass

    return warnings


def build_medication_resource(data: dict, rxnorm_result: dict | None = None) -> dict:
    resource = {"resourceType": "MedicationRequest"}

    if data.get("id"):
        resource["id"] = data["id"]

    status = data.get("status") or "active"
    normalized_status = status.lower().strip()
    resource["status"] = STATUS_FIXES.get(normalized_status, normalized_status if normalized_status in VALID_STATUSES else "active")

    intent = data.get("intent") or "order"
    normalized_intent = intent.lower().strip()
    resource["intent"] = normalized_intent if normalized_intent in VALID_INTENTS else INTENT_FIXES.get(normalized_intent, "order")

    subject = normalize_patient_reference(data.get("subject"))
    if subject:
        resource["subject"] = {"reference": subject}

    medication_name = data.get("medicationCodeableConcept") or data.get("medication")
    if medication_name:
        if rxnorm_result and rxnorm_result.get("found"):
            resource["medicationCodeableConcept"] = {
                "coding": [{
                    "system": rxnorm_result.get("system"),
                    "code": rxnorm_result.get("code"),
                    "display": rxnorm_result.get("display")
                }],
                "text": str(medication_name)
            }
        else:
            resource["medicationCodeableConcept"] = {
                "text": str(medication_name)
            }

    dosage = {}
    dose_and_rate = {}
    if get_nested_value(data, "dosageInstruction.dose") is not None:
        dose_value = get_nested_value(data, "dosageInstruction.dose")
        # Convert string numbers to float/int
        try:
            dose_value = float(dose_value) if isinstance(dose_value, str) else dose_value
        except (ValueError, TypeError):
            pass
        dose_and_rate["doseQuantity"] = {"value": dose_value}
    if get_nested_value(data, "dosageInstruction.unit"):
        dose_and_rate.setdefault("doseQuantity", {})["unit"] = get_nested_value(data, "dosageInstruction.unit")
    if dose_and_rate:
        dosage["doseAndRate"] = [dose_and_rate]
    if get_nested_value(data, "dosageInstruction.route"):
        dosage["route"] = {"text": get_nested_value(data, "dosageInstruction.route")}
    if get_nested_value(data, "dosageInstruction.frequency"):
        dosage["text"] = get_nested_value(data, "dosageInstruction.frequency")
    if dosage:
        resource["dosageInstruction"] = [dosage]

    dispense = {}
    if get_nested_value(data, "dispenseRequest.quantity") is not None:
        quantity_value = get_nested_value(data, "dispenseRequest.quantity")
        dispense["quantity"] = {"value": quantity_value}
        if get_nested_value(data, "dosageInstruction.unit"):
            dispense["quantity"]["unit"] = get_nested_value(data, "dosageInstruction.unit")
    if get_nested_value(data, "dispenseRequest.start"):
        dispense["validityPeriod"] = dispense.get("validityPeriod", {})
        dispense["validityPeriod"]["start"] = fix_date(get_nested_value(data, "dispenseRequest.start"))
    if get_nested_value(data, "dispenseRequest.end"):
        dispense["validityPeriod"] = dispense.get("validityPeriod", {})
        dispense["validityPeriod"]["end"] = fix_date(get_nested_value(data, "dispenseRequest.end"))
    if get_nested_value(data, "dispenseRequest.numberOfRepeatsAllowed") is not None:
        dispense["numberOfRepeatsAllowed"] = get_nested_value(data, "dispenseRequest.numberOfRepeatsAllowed")
    if dispense:
        resource["dispenseRequest"] = dispense

    if data.get("note"):
        resource["note"] = [{"text": data.get("note")}]

    requester = data.get("requester")
    if requester:
        if isinstance(requester, str):
            resource["requester"] = {"display": requester}
        elif isinstance(requester, dict):
            resource["requester"] = requester

    return resource
