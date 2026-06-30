from validator import fix_date, apply_known_fixes, safe_float, normalize_boolean
import json
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


def autofix(data: dict, errors: list) -> dict:
    """
    Apply all fixes from explained errors back to the resource with comprehensive error handling
    """
    fixed = data.copy()

    # Apply rule-based fixes from error messages
    for error in errors:
        field = error.get("field")
        fix = error.get("fix")
        error_type = error.get("type", "rule_based")

        if not field:
            continue

        # Handle nested fields like "name → 0 → family" or "period.start"
        if "→" in field:
            parts = [p.strip() for p in field.split("→")]
            apply_nested_fix(fixed, parts, fix)
        elif "." in field:
            parts = field.split(".")
            apply_nested_fix(fixed, parts, fix)
        else:
            if fix is not None:
                fixed[field] = fix

    # Apply comprehensive structural fixes
    fixed = apply_structural_fixes(fixed)
    
    # Apply known fixes from validator (only if safe to do so)
    try:
        fixed = apply_known_fixes(fixed)
    except (TypeError, KeyError):
        # Skip known fixes if data structure is too complex
        pass

    # Final cleanup and normalization
    fixed = cleanup_resource(fixed)

    return fixed


def apply_nested_fix(data: dict, parts: list, fix):
    """Apply fix to nested field with array and object support"""
    try:
        ref = data
        for i, part in enumerate(parts[:-1]):
            # Handle array indices
            if part.isdigit():
                idx = int(part)
                if idx not in range(len(ref)):
                    # Create array if needed
                    if isinstance(ref, list):
                        ref.extend([{}] * (idx - len(ref) + 1))
                    else:
                        return
                ref = ref[idx]
            else:
                # Handle object keys
                if part not in ref:
                    ref[part] = {}
                ref = ref[part]
        
        last = parts[-1]
        if last.isdigit():
            idx = int(last)
            if isinstance(ref, list):
                if idx < len(ref):
                    ref[idx] = fix
                else:
                    ref.extend([None] * (idx - len(ref) + 1))
                    ref[idx] = fix
        else:
            ref[last] = fix
    except (KeyError, IndexError, TypeError, AttributeError):
        pass


def apply_structural_fixes(data: dict) -> dict:
    """Apply comprehensive structural fixes for complex FHIR scenarios"""
    fixed = data.copy()
    
    # Fix array structures
    fixed = fix_array_structures(fixed)
    
    # Fix reference fields
    fixed = fix_reference_fields(fixed)
    
    # Fix CodeableConcept structures
    fixed = fix_codeable_concepts(fixed)
    
    # Fix choice field conflicts
    fixed = fix_choice_field_conflicts(fixed)
    
    # Fix identifier structures
    fixed = fix_identifiers(fixed)
    
    # Fix period structures
    fixed = fix_periods(fixed)
    
    # Fix telecom structures
    fixed = fix_telecom(fixed)
    
    # Fix extension structures
    fixed = fix_extensions(fixed)
    
    # Fix contact structures
    fixed = fix_contacts(fixed)
    
    # Fix meta fields
    fixed = fix_meta_fields(fixed)
    
    return fixed


def fix_array_structures(data: dict) -> dict:
    """Fix common array structure issues"""
    if not isinstance(data, dict):
        return data
    
    fixed = data.copy()
    
    # Fix name arrays - ensure given is array
    if "name" in fixed and isinstance(fixed["name"], list):
        for name in fixed["name"]:
            if isinstance(name, dict) and "given" in name:
                if isinstance(name["given"], str):
                    name["given"] = [name["given"]]
                elif not isinstance(name["given"], list):
                    name["given"] = []
    
    # Fix address arrays - ensure line is array
    if "address" in fixed and isinstance(fixed["address"], list):
        for addr in fixed["address"]:
            if isinstance(addr, dict) and "line" in addr:
                if isinstance(addr["line"], str):
                    addr["line"] = [addr["line"]]
                elif not isinstance(addr["line"], list):
                    addr["line"] = []
    
    # Fix identifier arrays - ensure proper structure
    if "identifier" in fixed and isinstance(fixed["identifier"], list):
        fixed["identifier"] = [fix_identifier_structure(id_obj) for id_obj in fixed["identifier"] if id_obj]
    
    # Fix telecom arrays
    if "telecom" in fixed and isinstance(fixed["telecom"], list):
        fixed["telecom"] = [fix_telecom_structure(t) for t in fixed["telecom"] if t]
    
    # Clean up null array elements
    for key in fixed:
        if isinstance(fixed[key], list):
            fixed[key] = [item for item in fixed[key] if item is not None]
    
    return fixed


def fix_identifier_structure(id_obj: dict) -> dict:
    """Fix individual identifier structure"""
    if not isinstance(id_obj, dict):
        return {}
    
    fixed = id_obj.copy()
    
    # Ensure type is CodeableConcept if present
    if "type" in fixed and isinstance(fixed["type"], str):
        fixed["type"] = {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                "code": fixed["type"]
            }]
        }
    
    # Normalize system URLs
    if "system" in fixed and isinstance(fixed["system"], str):
        fixed["system"] = normalize_url(fixed["system"])
    
    # Ensure value is string
    if "value" in fixed and not isinstance(fixed["value"], str):
        fixed["value"] = str(fixed["value"]) if fixed["value"] is not None else ""
    
    return fixed


def fix_reference_fields(data: dict) -> dict:
    """Fix and normalize reference fields across all resource types"""
    if not isinstance(data, dict):
        return data
    
    fixed = data.copy()
    
    # Common reference fields in FHIR resources
    reference_fields = [
        "subject", "patient", "practitioner", "organization", 
        "generalPractitioner", "managingOrganization", "basedOn",
        "encounter", "location", "serviceProvider", "author",
        "attender", "recorder", "reporter"
    ]
    
    for field in reference_fields:
        if field in fixed:
            fixed[field] = normalize_reference(fixed[field])
    
    # Handle nested references in arrays
    if "contact" in fixed and isinstance(fixed["contact"], list):
        for contact in fixed["contact"]:
            if isinstance(contact, dict):
                for ref_field in ["organization", "practitioner"]:
                    if ref_field in contact:
                        contact[ref_field] = normalize_reference(contact[ref_field])
    
    return fixed


def normalize_reference(ref: Any) -> Any:
    """Normalize reference to proper FHIR format"""
    if ref is None:
        return None
    
    # If already a dict with reference, keep it
    if isinstance(ref, dict):
        if "reference" in ref:
            ref["reference"] = normalize_reference_string(ref["reference"])
            return ref
        # If dict without reference, try to extract from common keys
        for key in ["reference", "id", "patient", "practitioner", "organization"]:
            if key in ref:
                return normalize_reference(ref[key])
        return None
    
    # If string, normalize format
    if isinstance(ref, str):
        return normalize_reference_string(ref)
    
    return None


def normalize_reference_string(ref: str) -> str:
    """Normalize reference string to proper FHIR format"""
    if not isinstance(ref, str):
        return ref
    
    ref = ref.strip()
    
    # If already has resource type, return as-is
    if "/" in ref and ref.split("/")[0] in [
        "Patient", "Practitioner", "Organization", "Location", 
        "Encounter", "Condition", "Observation", "MedicationRequest"
    ]:
        return ref
    
    # Try to infer resource type from context or use Patient as default
    # This is a heuristic - in real scenarios, you'd need more context
    if not ref.startswith("Patient/") and not ref.startswith("Practitioner/") and not ref.startswith("Organization/"):
        # Default to Patient for common use cases
        return f"Patient/{ref}"
    
    return ref


def fix_codeable_concepts(data: dict) -> dict:
    """Fix CodeableConcept structures across the resource"""
    if not isinstance(data, dict):
        return data
    
    fixed = data.copy()
    
    # Fields that typically contain CodeableConcept (but not simple enums like gender)
    codeable_fields = [
        "maritalStatus", "birthSex", "clinicalStatus", 
        "verificationStatus", "severity", "code", "medicationCodeableConcept",
        "reasonCode", "category"
    ]
    
    for field in codeable_fields:
        if field in fixed:
            fixed[field] = normalize_codeable_concept(fixed[field])
    
    # Handle nested CodeableConcepts in arrays
    if "communication" in fixed and isinstance(fixed["communication"], list):
        for comm in fixed["communication"]:
            if isinstance(comm, dict) and "language" in comm:
                comm["language"] = normalize_codeable_concept(comm["language"])
    
    return fixed


def normalize_codeable_concept(value: Any) -> Any:
    """Normalize value to proper CodeableConcept format"""
    if value is None:
        return None
    
    # If already a proper CodeableConcept dict, validate it
    if isinstance(value, dict):
        if "coding" in value or "text" in value:
            # Ensure coding is array
            if "coding" in value and not isinstance(value["coding"], list):
                value["coding"] = [value["coding"]]
            # Fix individual coding objects
            if "coding" in value and isinstance(value["coding"], list):
                value["coding"] = [fix_coding_structure(c) for c in value["coding"] if c]
            return value
        # If dict but not CodeableConcept, convert
        return {
            "text": str(value.get("text", value.get("display", ""))) or str(value),
            "coding": []
        }
    
    # If string, convert to CodeableConcept
    if isinstance(value, str):
        return {
            "text": value,
            "coding": []
        }
    
    return value


def fix_coding_structure(coding: Any) -> dict:
    """Fix individual coding structure"""
    if not isinstance(coding, dict):
        return {}
    
    fixed = coding.copy()
    
    # Normalize system URL
    if "system" in fixed:
        fixed["system"] = normalize_url(fixed["system"])
    
    # Ensure code is string
    if "code" in fixed and not isinstance(fixed["code"], str):
        fixed["code"] = str(fixed["code"]) if fixed["code"] is not None else ""
    
    return fixed


def fix_choice_field_conflicts(data: dict) -> dict:
    """Resolve mutually exclusive choice field conflicts"""
    if not isinstance(data, dict):
        return data
    
    fixed = data.copy()
    
    # Deceased choice fields
    if "deceasedBoolean" in fixed and "deceasedDateTime" in fixed:
        # Keep the more specific one (datetime) and remove boolean
        if fixed["deceasedDateTime"]:
            del fixed["deceasedBoolean"]
        else:
            del fixed["deceasedDateTime"]
    
    # MultipleBirth choice fields
    if "multipleBirthBoolean" in fixed and "multipleBirthInteger" in fixed:
        # Keep integer if present and non-zero, otherwise boolean
        if fixed["multipleBirthInteger"] and fixed["multipleBirthInteger"] > 1:
            del fixed["multipleBirthBoolean"]
        else:
            del fixed["multipleBirthInteger"]
    
    return fixed


def fix_identifiers(data: dict) -> dict:
    """Fix identifier structures and remove duplicates"""
    if not isinstance(data, dict):
        return data
    
    fixed = data.copy()
    
    if "identifier" not in fixed or not isinstance(fixed["identifier"], list):
        return fixed
    
    # Remove duplicate identifiers (same system and value)
    seen = set()
    unique_identifiers = []
    
    for ident in fixed["identifier"]:
        if isinstance(ident, dict):
            key = (ident.get("system"), ident.get("value"))
            if key not in seen:
                seen.add(key)
                unique_identifiers.append(ident)
    
    fixed["identifier"] = unique_identifiers
    
    return fixed


def fix_periods(data: dict) -> dict:
    """Fix period structures and validate date ranges"""
    if not isinstance(data, dict):
        return data
    
    fixed = data.copy()
    
    # Fix period in identifier
    if "identifier" in fixed and isinstance(fixed["identifier"], list):
        for ident in fixed["identifier"]:
            if isinstance(ident, dict) and "period" in ident:
                ident["period"] = fix_period_structure(ident["period"])
    
    # Fix period in other fields
    period_fields = ["period", "effectivePeriod", "dispenseRequest.validityPeriod"]
    for field in period_fields:
        if "." in field:
            parts = field.split(".")
            if parts[0] in fixed and isinstance(fixed[parts[0]], dict):
                if parts[1] in fixed[parts[0]]:
                    fixed[parts[0]][parts[1]] = fix_period_structure(fixed[parts[0]][parts[1]])
        elif field in fixed:
            fixed[field] = fix_period_structure(fixed[field])
    
    return fixed


def fix_period_structure(period: Any) -> dict:
    """Fix individual period structure"""
    if not isinstance(period, dict):
        return {}
    
    fixed = period.copy()
    
    # Fix dates
    if "start" in fixed:
        fixed["start"] = fix_date(fixed["start"])
    if "end" in fixed:
        fixed["end"] = fix_date(fixed["end"])
    
    # Validate that end is after start
    if fixed.get("start") and fixed.get("end"):
        try:
            start = datetime.strptime(fixed["start"], "%Y-%m-%d")
            end = datetime.strptime(fixed["end"], "%Y-%m-%d")
            if end < start:
                # Swap if dates are reversed
                fixed["start"], fixed["end"] = fixed["end"], fixed["start"]
        except (ValueError, TypeError):
            pass
    
    return fixed


def fix_telecom(data: dict) -> dict:
    """Fix telecom structures"""
    if not isinstance(data, dict):
        return data
    
    fixed = data.copy()
    
    if "telecom" not in fixed or not isinstance(fixed["telecom"], list):
        return fixed
    
    fixed["telecom"] = [fix_telecom_structure(t) for t in fixed["telecom"] if t]
    
    return fixed


def fix_telecom_structure(telecom: Any) -> dict:
    """Fix individual telecom structure"""
    if not isinstance(telecom, dict):
        return {}
    
    fixed = telecom.copy()
    
    # Normalize system
    if "system" in fixed:
        system_map = {
            "phone": "phone", "telephone": "phone", "tel": "phone",
            "email": "email", "mail": "email", "electronic": "email",
            "fax": "fax", "facsimile": "fax",
            "url": "url", "link": "url", "website": "url",
            "pager": "pager", "sms": "sms", "other": "other"
        }
        fixed["system"] = system_map.get(fixed["system"].lower(), fixed["system"])
    
    # Normalize use
    if "use" in fixed:
        use_map = {
            "home": "home", "work": "work", "mobile": "mobile", "cell": "mobile",
            "temp": "temp", "temporary": "temp", "old": "old", "expired": "old"
        }
        fixed["use"] = use_map.get(fixed["use"].lower(), fixed["use"])
    
    # Normalize rank to positive integer
    if "rank" in fixed:
        try:
            rank = int(fixed["rank"])
            fixed["rank"] = max(1, rank) if rank > 0 else 1
        except (ValueError, TypeError):
            del fixed["rank"]
    
    return fixed


def fix_extensions(data: dict) -> dict:
    """Fix extension structures"""
    if not isinstance(data, dict):
        return data
    
    fixed = data.copy()
    
    if "extension" not in fixed or not isinstance(fixed["extension"], list):
        return fixed
    
    fixed["extension"] = [fix_extension_structure(ext) for ext in fixed["extension"] if ext]
    
    return fixed


def fix_extension_structure(extension: Any) -> dict:
    """Fix individual extension structure"""
    if not isinstance(extension, dict):
        return {}
    
    fixed = extension.copy()
    
    # Normalize URL
    if "url" in fixed:
        fixed["url"] = normalize_url(fixed["url"])
    
    # Ensure exactly one value field is present
    value_fields = [k for k in fixed.keys() if k.startswith("value") and k != "url"]
    if len(value_fields) > 1:
        # Keep the first one and remove others
        keep_field = value_fields[0]
        for field in value_fields[1:]:
            del fixed[field]
    
    return fixed


def fix_contacts(data: dict) -> dict:
    """Fix contact structures"""
    if not isinstance(data, dict):
        return data
    
    fixed = data.copy()
    
    if "contact" not in fixed or not isinstance(fixed["contact"], list):
        return fixed
    
    fixed["contact"] = [fix_contact_structure(contact) for contact in fixed["contact"] if contact]
    
    return fixed


def fix_contact_structure(contact: Any) -> dict:
    """Fix individual contact structure"""
    if not isinstance(contact, dict):
        return {}
    
    fixed = contact.copy()
    
    # Fix gender
    if "gender" in fixed:
        gender_map = {"m": "male", "f": "female", "male": "male", "female": "female"}
        fixed["gender"] = gender_map.get(str(fixed["gender"]).lower(), fixed["gender"])
    
    # Fix name structure
    if "name" in fixed and isinstance(fixed["name"], dict):
        if "given" in fixed["name"] and isinstance(fixed["name"]["given"], str):
            fixed["name"]["given"] = [fixed["name"]["given"]]
    
    # Fix telecom in contact
    if "telecom" in fixed and isinstance(fixed["telecom"], list):
        fixed["telecom"] = [fix_telecom_structure(t) for t in fixed["telecom"] if t]
    
    return fixed


def fix_meta_fields(data: dict) -> dict:
    """Fix meta fields"""
    if not isinstance(data, dict):
        return data
    
    fixed = data.copy()
    
    if "meta" not in fixed or not isinstance(fixed["meta"], dict):
        return fixed
    
    meta = fixed["meta"]
    
    # Fix versionId to string
    if "versionId" in meta:
        meta["versionId"] = str(meta["versionId"])
    
    # Fix lastUpdated datetime
    if "lastUpdated" in meta:
        meta["lastUpdated"] = fix_datetime(meta["lastUpdated"])
    
    fixed["meta"] = meta
    
    return fixed


def fix_datetime(dt_str: str) -> str:
    """Fix datetime format to FHIR standard"""
    if not dt_str:
        return dt_str
    
    # Try to parse and reformat
    try:
        # Handle various datetime formats
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(dt_str, fmt)
                # Format to FHIR standard with timezone
                if dt.tzinfo:
                    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")
                else:
                    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue
    except (ValueError, TypeError):
        pass
    
    return dt_str


def normalize_url(url: str) -> str:
    """Normalize URL to proper format"""
    if not isinstance(url, str):
        return url
    
    url = url.strip()
    
    # Add http:// if missing
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    
    return url


def cleanup_resource(data: dict) -> dict:
    """Final cleanup of the resource"""
    if not isinstance(data, dict):
        return data
    
    fixed = data.copy()
    
    # Remove null values
    fixed = {k: v for k, v in fixed.items() if v is not None}
    
    # Remove empty strings
    fixed = {k: v for k, v in fixed.items() if v != "" or k in ["id", "text"]}
    
    # Convert numeric strings to numbers where appropriate
    for key, value in fixed.items():
        if isinstance(value, str):
            # Try to convert to number
            num = safe_float(value)
            if num is not None and num != value:
                fixed[key] = num
    
    return fixed


def generate_fix_summary(original: dict, fixed: dict, errors: list) -> dict:
    """Generate a human readable summary of what was fixed"""
    changes = []

    for error in errors:
        field = error.get("field")
        fix = error.get("fix")
        received = error.get("received")

        if fix and received and fix != received:
            changes.append({
                "field": field,
                "from": received,
                "to": fix,
                "explanation": error.get("explanation", "")
            })

    # Add structural fixes
    structural_changes = detect_structural_changes(original, fixed)
    changes.extend(structural_changes)

    return {
        "total_fixes_applied": len(changes),
        "changes": changes,
        "fixed_resource": fixed
    }


def detect_structural_changes(original: dict, fixed: dict) -> list:
    """Detect structural changes made during fixing"""
    changes = []
    
    # Compare structures
    for key in set(list(original.keys()) + list(fixed.keys())):
        orig_val = original.get(key)
        fixed_val = fixed.get(key)
        
        if orig_val != fixed_val:
            change_type = "modified"
            if orig_val is None and fixed_val is not None:
                change_type = "added"
            elif orig_val is not None and fixed_val is None:
                change_type = "removed"
            
            changes.append({
                "field": key,
                "from": str(orig_val)[:100] if orig_val is not None else None,
                "to": str(fixed_val)[:100] if fixed_val is not None else None,
                "explanation": f"Structural {change_type} during cleanup"
            })
    
    return changes