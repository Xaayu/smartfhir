from terminology.snomed_lookup import lookup_snomed
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

VALID_CLINICAL_STATUSES = [
    "active", "recurrence", "relapse",
    "inactive", "remission", "resolved"
]

VALID_VERIFICATION_STATUSES = [
    "unconfirmed", "provisional",
    "differential", "confirmed", "refuted"
]

VALID_SEVERITIES = ["mild", "moderate", "severe"]

CLINICAL_STATUS_FIXES = {
    "current": "active",
    "ongoing": "active",
    "open": "active",
    "new": "active",
    "chronic": "active",
    "recurring": "recurrence",
    "returned": "recurrence",
    "worsened": "relapse",
    "closed": "resolved",
    "healed": "resolved",
    "cured": "resolved",
    "done": "resolved",
    "controlled": "remission",
    "better": "remission",
    "improving": "remission",
    "inactive": "inactive",
}

VERIFICATION_STATUS_FIXES = {
    "yes": "confirmed",
    "true": "confirmed",
    "verified": "confirmed",
    "sure": "confirmed",
    "suspected": "provisional",
    "maybe": "provisional",
    "possible": "differential",
    "no": "refuted",
    "false": "refuted",
    "wrong": "refuted",
}

SEVERITY_FIXES = {
    "light": "mild",
    "minor": "mild",
    "low": "mild",
    "medium": "moderate",
    "average": "moderate",
    "high": "severe",
    "serious": "severe",
    "critical": "severe",
    "extreme": "severe",
}





def load_patients() -> dict:
    if os.path.exists(PATIENTS_STORE):
        with open(PATIENTS_STORE, "r") as f:
            return json.load(f)
    return {}


def validate_condition(data: dict) -> dict:
    errors = []
    warnings = []
    snomed_result = None

    # 1. Subject / Patient reference
    subject = data.get("subject", "")
    if not subject:
        errors.append({
            "field": "subject",
            "type": "rule_based",
            "received": None,
            "fix": None,
            "message": "Missing required field 'subject'.",
            "explanation": "Condition must reference a Patient.",
            "suggested_fix": "Add subject field like 'Patient/P101'."
        })
    else:
        if not subject.startswith("Patient/"):
            subject = f"Patient/{subject}"
        # Note: Patient existence check removed to allow standalone validation
    # ID auto-generation
    if not data.get("id"):
        import uuid
        generated_id = f"condition-{uuid.uuid4().hex[:8]}"
        errors.append({
            "field": "id",
            "type": "rule_based",
            "received": None,
            "fix": generated_id,
            "message": "Missing required field 'id'.",
            "explanation": "Every FHIR Condition resource must have a unique id.",
            "suggested_fix": f"Add a unique identifier like 'id': '{generated_id}'"
        })


    # 2. Code / SNOMED lookup
    code_display = get_nested_value(data, "code.display") or get_nested_value(data, "code")
    if not code_display:
        errors.append({
            "field": "code",
            "type": "rule_based",
            "received": None,
            "fix": None,
            "message": "Missing required field 'code'.",
            "explanation": "Condition must have a code identifying the diagnosis.",
            "suggested_fix": "Add a diagnosis name or SNOMED CT code."
        })
    else:
        snomed_result = lookup_snomed(str(code_display))
        if not snomed_result["found"]:
            warnings.append({
                "field": "code",
                "message": f"Could not find SNOMED code for '{code_display}'.",
                "suggestion": "Verify diagnosis name or provide SNOMED CT code manually."
            })

    # 3. Clinical status check
    clinical_status = data.get("clinicalStatus")
    if not clinical_status:
        errors.append({
            "field": "clinicalStatus",
            "type": "rule_based",
            "received": None,
            "fix": "active",
            "message": "Missing required field 'clinicalStatus'.",
            "explanation": "Condition must have a clinical status.",
            "suggested_fix": "Add clinicalStatus. Most common value is 'active'."
        })
    elif clinical_status.lower() not in VALID_CLINICAL_STATUSES:
        fix = CLINICAL_STATUS_FIXES.get(clinical_status.lower())
        errors.append({
            "field": "clinicalStatus",
            "type": "rule_based",
            "received": clinical_status,
            "fix": fix,
            "message": f"Invalid clinicalStatus '{clinical_status}'.",
            "explanation": f"FHIR accepts: {', '.join(VALID_CLINICAL_STATUSES)}",
            "suggested_fix": f"Change to '{fix}'" if fix else "Use a valid FHIR clinical status."
        })

    # 4. Verification status check
    verification_status = data.get("verificationStatus")
    if verification_status:
        if verification_status.lower() not in VALID_VERIFICATION_STATUSES:
            fix = VERIFICATION_STATUS_FIXES.get(verification_status.lower())
            errors.append({
                "field": "verificationStatus",
                "type": "rule_based",
                "received": verification_status,
                "fix": fix,
                "message": f"Invalid verificationStatus '{verification_status}'.",
                "explanation": f"FHIR accepts: {', '.join(VALID_VERIFICATION_STATUSES)}",
                "suggested_fix": f"Change to '{fix}'" if fix else "Use a valid verification status."
            })

    # 5. Severity check
    severity = data.get("severity")
    if severity:
        if severity.lower() not in VALID_SEVERITIES:
            fix = SEVERITY_FIXES.get(severity.lower())
            errors.append({
                "field": "severity",
                "type": "rule_based",
                "received": severity,
                "fix": fix,
                "message": f"Invalid severity '{severity}'.",
                "explanation": f"FHIR accepts: {', '.join(VALID_SEVERITIES)}",
                "suggested_fix": f"Change to '{fix}'" if fix else "Use mild, moderate, or severe."
            })

    # 6. Date checks
    for date_field in ["onsetDateTime", "recordedDate", "abatementDateTime"]:
        date_val = data.get(date_field)
        if date_val:
            fixed = fix_date(date_val)
            if fixed != date_val:
                errors.append({
                    "field": date_field,
                    "type": "rule_based",
                    "received": date_val,
                    "fix": fixed,
                    "message": f"Invalid date format '{date_val}'.",
                    "explanation": "FHIR requires YYYY-MM-DD format.",
                    "suggested_fix": f"Change to '{fixed}'"
                })

    # 7. Business rules
    warnings += condition_business_rules(data)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "snomed_result": snomed_result
    }


def build_condition_resource(data: dict, snomed_result: dict) -> dict:
    """Build proper nested FHIR Condition resource"""

    resource = {"resourceType": "Condition"}

    # ID
    if data.get("id"):
        resource["id"] = data["id"]

    # Clinical Status (CodeableConcept)
    clinical_status = data.get("clinicalStatus", "active")
    clinical_status = CLINICAL_STATUS_FIXES.get(
        clinical_status.lower(), clinical_status.lower()
    ) if clinical_status.lower() not in VALID_CLINICAL_STATUSES else clinical_status.lower()

    resource["clinicalStatus"] = {
        "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
            "code": clinical_status,
            "display": clinical_status.title()
        }]
    }

    # Verification Status (CodeableConcept)
    verification = data.get("verificationStatus", "confirmed")
    verification = VERIFICATION_STATUS_FIXES.get(
        verification.lower(), verification.lower()
    ) if verification.lower() not in VALID_VERIFICATION_STATUSES else verification.lower()

    resource["verificationStatus"] = {
        "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
            "code": verification,
            "display": verification.title()
        }]
    }

    # Category
    category = data.get("category", "encounter-diagnosis")
    resource["category"] = [{
        "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
            "code": category,
            "display": category.replace("-", " ").title()
        }]
    }]

    # Severity
    severity = data.get("severity")
    if severity:
        severity = SEVERITY_FIXES.get(
            severity.lower(), severity.lower()
        ) if severity.lower() not in VALID_SEVERITIES else severity.lower()

        SEVERITY_CODES = {
            "mild": "255604002",
            "moderate": "6736007",
            "severe": "24484000"
        }
        resource["severity"] = {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": SEVERITY_CODES.get(severity, "6736007"),
                "display": severity.title()
            }]
        }

    # Code with SNOMED
    code_display = get_nested_value(data, "code.display") or data.get("code", "Unknown")
    if snomed_result and snomed_result["found"]:
        resource["code"] = {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": snomed_result["code"],
                "display": snomed_result["display"]
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

    # Dates
    if data.get("onsetDateTime"):
        resource["onsetDateTime"] = fix_date(data["onsetDateTime"])
    if data.get("recordedDate"):
        resource["recordedDate"] = fix_date(data["recordedDate"])
    if data.get("abatementDateTime"):
        resource["abatementDateTime"] = fix_date(data["abatementDateTime"])

    # Note
    if data.get("note"):
        resource["note"] = [{"text": str(data["note"])}]

    return resource


def condition_business_rules(data: dict) -> list:
    warnings = []

    clinical_status = (data.get("clinicalStatus") or "").lower()
    abatement = data.get("abatementDateTime")
    onset = data.get("onsetDateTime")
    code = str(
        get_nested_value(data, "code.display") or data.get("code", "")
    ).lower()

    if clinical_status in ["resolved", "remission"] and not abatement:
        warnings.append({
            "field": "abatementDateTime",
            "message": f"Condition marked '{clinical_status}' but no abatement date.",
            "suggestion": "Add abatementDateTime to indicate when condition ended."
        })

    if onset and abatement:
        try:
            fixed_onset = fix_date(str(onset).strip())
            fixed_abatement = fix_date(str(abatement).strip())
            if (fixed_onset and fixed_abatement and
                    len(fixed_onset) == 10 and
                    len(fixed_abatement) == 10):
                if fixed_onset > fixed_abatement:
                    warnings.append({
                        "field": "onsetDateTime",
                        "message": "Onset date is after abatement date.",
                        "suggestion": "Onset must be before abatement date."
                    })
        except Exception:
            pass

    pregnancy_terms = ["pregnancy", "pregnant", "maternity", "prenatal"]
    if any(term in code for term in pregnancy_terms):
        warnings.append({
            "field": "code",
            "message": "Pregnancy-related condition detected.",
            "suggestion": "Verify patient gender is appropriate."
        })

    return warnings

