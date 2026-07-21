import json
import os
import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime
from collections import defaultdict
import uuid
from validator import fix_date

BUILT_IN_PATH = "mappings/built_in.json"
USER_MAPPINGS_PATH = "mappings/user_mappings.json"
LEARNING_PATH = "mappings/learned_mappings.json"


def load_mappings(resource_type: str = "Patient") -> tuple:
    """Load both built-in and user-defined mappings for any resource type"""
    
    # Built-in mappings - try resource-specific file first, then general file
    built_in = {}
    resource_specific_files = {
        "Patient": "mappings/built_in.json",
        "Observation": "mappings/observation_built_in.json",
        "MedicationRequest": "mappings/medication_built_in.json",
        "Condition": "mappings/condition_built_in.json",
        "Encounter": "mappings/encounter_built_in.json"
    }
    
    built_in_file = resource_specific_files.get(resource_type, BUILT_IN_PATH)
    if os.path.exists(built_in_file):
        try:
            with open(built_in_file, "r") as f:
                data = json.load(f)
                built_in = data.get(resource_type, {})
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    # User mappings
    user = {}
    if os.path.exists(USER_MAPPINGS_PATH):
        try:
            with open(USER_MAPPINGS_PATH, "r") as f:
                data = json.load(f)
                user = data.get(resource_type, {})
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    # Load learned mappings if available
    learned = {}
    if os.path.exists(LEARNING_PATH):
        try:
            with open(LEARNING_PATH, "r") as f:
                learned_data = json.load(f)
                resource_learned = learned_data.get(resource_type, {})
                # Extract the fhir_field from the learned mapping structure
                for field, mapping_info in resource_learned.items():
                    if isinstance(mapping_info, dict) and "fhir_field" in mapping_info:
                        learned[field] = mapping_info["fhir_field"]
                    else:
                        learned[field] = mapping_info
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    return built_in, user, learned



def normalize_field_name(field: str) -> str:
    """Normalize field name for comparison"""
    return field.lower().replace(" ", "").replace("_", "").replace("-", "")


def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity between two strings using multiple methods"""
    # Normalize both strings
    s1 = normalize_field_name(str1)
    s2 = normalize_field_name(str2)
    
    # Exact match
    if s1 == s2:
        return 1.0
    
    # Sequence matcher (Levenshtein-like)
    seq_ratio = SequenceMatcher(None, s1, s2).ratio()
    
    # Contains check
    contains_score = 0.0
    if s1 in s2 or s2 in s1:
        contains_score = 0.8
    
    # Word overlap
    words1 = set(re.findall(r'[a-z]+', s1))
    words2 = set(re.findall(r'[a-z]+', s2))
    if words1 and words2:
        overlap = len(words1 & words2) / len(words1 | words2)
        word_score = overlap * 0.7
    else:
        word_score = 0.0
    
    # Combined score with weights
    final_score = max(seq_ratio, contains_score, word_score)
    return final_score


def find_best_match(field: str, target_fields: Dict[str, str], threshold: float = 0.6) -> Tuple[Optional[str], float]:
    """Find the best matching field using fuzzy matching"""
    best_match = None
    best_score = 0.0
    
    for target_field, fhir_path in target_fields.items():
        score = calculate_similarity(field, target_field)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = fhir_path
    
    return best_match, best_score


def semantic_field_analysis(field: str, value: Any, resource_type: str) -> Optional[str]:
    """Analyze field semantically to determine FHIR mapping"""
    field_lower = field.lower()
    value_str = str(value).lower() if value is not None else ""
    
    # Date patterns
    date_patterns = [r'\d{4}-\d{2}-\d{2}', r'\d{2}/\d{2}/\d{4}', r'\d{8}']
    if any(re.search(pattern, value_str) for pattern in date_patterns):
        if any(keyword in field_lower for keyword in ['birth', 'dob', 'born']):
            return 'birthDate'
        elif any(keyword in field_lower for keyword in ['death', 'deceased', 'died']):
            return 'deceasedDateTime'
        elif any(keyword in field_lower for keyword in ['start', 'begin', 'onset']):
            return 'onsetDateTime'
        elif any(keyword in field_lower for keyword in ['end', 'expire', 'abatement']):
            return 'abatementDateTime'
    
    # Email patterns
    if '@' in value_str and 'email' not in field_lower:
        return 'telecom.email'
    
    # Phone patterns
    phone_pattern = r'[\d\-\+\(\)\s]{10,}'
    if re.search(phone_pattern, value_str) and 'phone' not in field_lower:
        return 'telecom'
    
    # Boolean patterns
    if value_str in ['true', 'false', 'yes', 'no', '1', '0']:
        if 'active' in field_lower or 'status' in field_lower:
            return 'active'
        elif 'dead' in field_lower or 'deceased' in field_lower:
            return 'deceasedBoolean'
    
    # Numeric patterns with units
    if re.search(r'^\d+\.?\d*\s*[a-zA-Z]+$', value_str):
        if any(keyword in field_lower for keyword in ['result', 'value', 'test']):
            return 'valueQuantity.value'
    
    # ID patterns
    if field_lower.endswith('id') or field_lower.endswith('_id'):
        if 'patient' in field_lower or 'pt' in field_lower:
            return 'subject'
        elif any(keyword in field_lower for keyword in ['doctor', 'provider', 'practitioner']):
            return 'requester'
    
    return None


def convert_flat_to_nested(data: dict) -> dict:
    """Convert flat dot-notation keys to nested dict structure.
    Example: {"code.display": "Blood Pressure"} -> {"code": {"display": "Blood Pressure"}}
    Enhanced to handle array indices and complex nested structures.
    """
    result = {}
    for key, value in data.items():
        if '.' in key:
            parts = key.split('.')
            current = result
            for i, part in enumerate(parts[:-1]):
                # Handle array indices (e.g., "name.0.family")
                if part.isdigit():
                    idx = int(part)
                    if not isinstance(current, list):
                        current = []
                    # Extend list if needed
                    while len(current) <= idx:
                        current.append({})
                    if not isinstance(current[idx], dict):
                        current[idx] = {}
                    current = current[idx]
                else:
                    if part not in current:
                        current[part] = {}
                    elif not isinstance(current[part], (dict, list)):
                        # If intermediate part exists but is not a dict, convert it
                        current[part] = {}
                    current = current[part]
            
            # Handle the last part
            last = parts[-1]
            if last.isdigit():
                idx = int(last)
                if not isinstance(current, list):
                    current = []
                while len(current) <= idx:
                    current.append(None)
                current[idx] = value
            else:
                current[last] = value
        else:
            result[key] = value
    return result


def normalize_input_data(data: Union[dict, list, str]) -> dict:
    """Normalize various input formats to standard dict structure for mapping.
    Handles: flat dicts, nested dicts, CSV-like lists, JSON strings, etc.
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            # Try to parse as key=value pairs
            data = parse_key_value_string(data)
    
    if isinstance(data, list):
        # Convert list of dicts to single dict
        if all(isinstance(item, dict) for item in data):
            merged = {}
            for item in data:
                merged.update(item)
            data = merged
        else:
            raise ValueError("Cannot normalize non-dict list")
    
    if not isinstance(data, dict):
        raise ValueError(f"Unsupported input type: {type(data)}")
    
    # Flatten nested structures for easier mapping
    data = flatten_nested_structure(data)
    
    # Normalize field names
    normalized = {}
    for key, value in data.items():
        # Handle camelCase, snake_case, kebab-case, spaces
        normalized_key = normalize_field_name(key)
        normalized[normalized_key] = value
    
    return normalized


def flatten_nested_structure(data: dict, parent_key: str = "", separator: str = ".") -> dict:
    """Flatten nested dict structure to dot-notation keys.
    Example: {"name": {"family": "Doe"}} -> {"name.family": "Doe"}
    """
    items = []
    for key, value in data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_nested_structure(value, new_key, separator).items())
        elif isinstance(value, list):
            # Handle arrays by including index
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    items.extend(flatten_nested_structure(item, f"{new_key}.{i}", separator).items())
                else:
                    items.append((f"{new_key}.{i}", item))
        else:
            items.append((new_key, value))
    return dict(items)


def parse_key_value_string(input_str: str) -> dict:
    """Parse key=value string format to dict.
    Example: "name=John&age=30&city=NYC" -> {"name": "John", "age": "30", "city": "NYC"}
    """
    result = {}
    if not input_str:
        return result
    
    # Try different separators
    separators = ["&", ";", ",", "|"]
    pairs = []
    
    for sep in separators:
        if sep in input_str:
            pairs = input_str.split(sep)
            break
    
    if not pairs:
        # Try space separator
        pairs = input_str.split()
    
    for pair in pairs:
        if "=" in pair:
            key, value = pair.split("=", 1)
            result[key.strip()] = value.strip()
    
    return result


def advanced_semantic_analysis(field: str, value: Any, resource_type: str, context: dict = None) -> Optional[Dict[str, Any]]:
    """Enhanced semantic analysis with context awareness and pattern recognition."""
    field_lower = field.lower()
    value_str = str(value).lower() if value is not None else ""
    context = context or {}
    
    # Enhanced date patterns with more formats
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',  # ISO format
        r'\d{2}/\d{2}/\d{4}',  # US format
        r'\d{2}-\d{2}-\d{4}',  # European format
        r'\d{8}',              # Compact format
        r'\d{1,2}\s+[a-zA-Z]+\s+\d{4}',  # "15 January 2020"
        r'[a-zA-Z]+\s+\d{1,2},?\s+\d{4}'  # "January 15, 2020"
    ]
    
    if any(re.search(pattern, value_str) for pattern in date_patterns):
        if any(keyword in field_lower for keyword in ['birth', 'dob', 'born', 'dateofbirth']):
            return {"fhir_field": "birthDate", "confidence": 0.9, "reason": "Date pattern with birth keyword"}
        elif any(keyword in field_lower for keyword in ['death', 'deceased', 'died', 'dateofdeath']):
            return {"fhir_field": "deceasedDateTime", "confidence": 0.9, "reason": "Date pattern with death keyword"}
        elif any(keyword in field_lower for keyword in ['start', 'begin', 'onset', 'admission']):
            return {"fhir_field": "onsetDateTime", "confidence": 0.85, "reason": "Date pattern with start keyword"}
        elif any(keyword in field_lower for keyword in ['end', 'expire', 'abatement', 'discharge']):
            return {"fhir_field": "abatementDateTime", "confidence": 0.85, "reason": "Date pattern with end keyword"}
        elif any(keyword in field_lower for keyword in ['effective', 'performed', 'observed']):
            return {"fhir_field": "effectiveDateTime", "confidence": 0.8, "reason": "Date pattern with effective keyword"}
    
    # Enhanced email patterns
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    if re.search(email_pattern, value_str):
        if 'email' not in field_lower:
            return {"fhir_field": "telecom", "confidence": 0.95, "reason": "Email pattern detected", "subfield": "email"}
    
    # Enhanced phone patterns (international formats)
    phone_patterns = [
        r'\+?[\d\s\-\(\)]{10,}',  # International format
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
        r'\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'  # European format
    ]
    
    if any(re.search(pattern, value_str) for pattern in phone_patterns):
        if 'phone' not in field_lower and 'mobile' not in field_lower and 'tel' not in field_lower:
            return {"fhir_field": "telecom", "confidence": 0.9, "reason": "Phone pattern detected", "subfield": "phone"}
    
    # Enhanced boolean patterns
    boolean_true = ['true', 'yes', 'y', '1', 'on', 'active', 'enabled', 'positive']
    boolean_false = ['false', 'no', 'n', '0', 'off', 'inactive', 'disabled', 'negative']
    
    if value_str.lower() in boolean_true + boolean_false:
        if any(keyword in field_lower for keyword in ['active', 'status', 'current']):
            return {"fhir_field": "active", "confidence": 0.85, "reason": "Boolean pattern with status keyword"}
        elif any(keyword in field_lower for keyword in ['dead', 'deceased', 'died', 'death']):
            return {"fhir_field": "deceasedBoolean", "confidence": 0.9, "reason": "Boolean pattern with death keyword"}
        elif any(keyword in field_lower for keyword in ['multiple', 'twin', 'birth']):
            return {"fhir_field": "multipleBirthBoolean", "confidence": 0.8, "reason": "Boolean pattern with birth keyword"}
    
    # Enhanced numeric patterns with units
    numeric_with_unit = r'^\d+\.?\d*\s*[a-zA-Z%°]+$'
    if re.search(numeric_with_unit, value_str):
        if any(keyword in field_lower for keyword in ['result', 'value', 'test', 'measurement', 'reading']):
            return {"fhir_field": "valueQuantity.value", "confidence": 0.85, "reason": "Numeric with unit pattern"}
        elif any(keyword in field_lower for keyword in ['dose', 'amount', 'quantity']):
            return {"fhir_field": "dosage", "confidence": 0.8, "reason": "Numeric with unit pattern for dosage"}
    
    # ID patterns with context
    if field_lower.endswith('id') or field_lower.endswith('_id') or field_lower.endswith('id'):
        if any(keyword in field_lower for keyword in ['patient', 'pt', 'subject']):
            return {"fhir_field": "subject", "confidence": 0.9, "reason": "ID pattern with patient keyword"}
        elif any(keyword in field_lower for keyword in ['doctor', 'provider', 'practitioner', 'physician']):
            return {"fhir_field": "requester", "confidence": 0.85, "reason": "ID pattern with provider keyword"}
        elif any(keyword in field_lower for keyword in ['encounter', 'visit', 'admission']):
            return {"fhir_field": "encounter", "confidence": 0.85, "reason": "ID pattern with encounter keyword"}
        elif any(keyword in field_lower for keyword in ['organization', 'facility', 'hospital']):
            return {"fhir_field": "organization", "confidence": 0.85, "reason": "ID pattern with organization keyword"}
    
    # Name patterns
    name_keywords = ['name', 'firstname', 'lastname', 'family', 'given', 'surname']
    if any(keyword in field_lower for keyword in name_keywords):
        if 'first' in field_lower or 'given' in field_lower:
            return {"fhir_field": "name.0.given", "confidence": 0.85, "reason": "First name pattern"}
        elif 'last' in field_lower or 'family' in field_lower or 'sur' in field_lower:
            return {"fhir_field": "name.0.family", "confidence": 0.85, "reason": "Last name pattern"}
        else:
            return {"fhir_field": "name", "confidence": 0.8, "reason": "Name pattern"}
    
    # Address patterns
    address_keywords = ['address', 'street', 'city', 'state', 'zip', 'postal', 'country']
    if any(keyword in field_lower for keyword in address_keywords):
        if 'street' in field_lower or 'line' in field_lower:
            return {"fhir_field": "address.0.line", "confidence": 0.85, "reason": "Street address pattern"}
        elif 'city' in field_lower:
            return {"fhir_field": "address.0.city", "confidence": 0.85, "reason": "City pattern"}
        elif 'state' in field_lower or 'region' in field_lower:
            return {"fhir_field": "address.0.state", "confidence": 0.85, "reason": "State pattern"}
        elif 'zip' in field_lower or 'postal' in field_lower:
            return {"fhir_field": "address.0.postalCode", "confidence": 0.85, "reason": "Postal code pattern"}
        else:
            return {"fhir_field": "address", "confidence": 0.8, "reason": "Address pattern"}
    
    # Gender patterns
    gender_values = ['male', 'female', 'other', 'unknown', 'm', 'f']
    if value_str.lower() in gender_values:
        return {"fhir_field": "gender", "confidence": 0.95, "reason": "Gender value pattern"}
    
    # Medical code patterns (LOINC, SNOMED, RxNorm)
    code_patterns = [
        r'^\d{3,5}-\d+$',  # LOINC format
        r'^\d{6,8}$',      # SNOMED CT format
        r'^\d{6,8}$'       # RxNorm format
    ]
    
    if any(re.search(pattern, value_str) for pattern in code_patterns):
        if resource_type == "Observation":
            return {"fhir_field": "code", "confidence": 0.9, "reason": "Medical code pattern for observation"}
        elif resource_type == "Condition":
            return {"fhir_field": "code", "confidence": 0.9, "reason": "Medical code pattern for condition"}
        elif resource_type == "MedicationRequest":
            return {"fhir_field": "medicationCodeableConcept", "confidence": 0.9, "reason": "Medical code pattern for medication"}
    
    return None


def handle_complex_mappings(data: dict, resource_type: str) -> dict:
    """Handle complex mapping scenarios that require special processing."""
    processed = data.copy()
    
    # Handle compound fields (e.g., "full_name" -> first_name + last_name)
    compound_fields = {
        'fullname': ['given', 'family'],
        'full_name': ['given', 'family'],
        'name': ['given', 'family'],
        'completeaddress': ['line', 'city', 'state', 'postalCode'],
        'fulladdress': ['line', 'city', 'state', 'postalCode']
    }
    
    for compound, components in compound_fields.items():
        if compound in processed:
            value = processed[compound]
            del processed[compound]
            
            # Try to split compound value
            if isinstance(value, str):
                if compound in ['fullname', 'full_name', 'name']:
                    parts = value.split(maxsplit=1)
                    if len(parts) >= 1:
                        processed['name.0.given'] = parts[0]
                    if len(parts) >= 2:
                        processed['name.0.family'] = parts[1]
                elif compound in ['completeaddress', 'fulladdress']:
                    # Simple address splitting
                    parts = value.split(',')
                    for i, part in enumerate(parts):
                        if i == 0:
                            processed['address.0.line'] = part.strip()
                        elif i == 1:
                            processed['address.0.city'] = part.strip()
                        elif i == 2:
                            processed['address.0.state'] = part.strip()
                        elif i == 3:
                            processed['address.0.postalCode'] = part.strip()
    
    # Handle date-time compound fields
    datetime_fields = ['datetime', 'timestamp', 'created', 'updated', 'modified']
    for field in datetime_fields:
        if field in processed:
            value = processed[field]
            # Determine the most appropriate FHIR date field based on context
            if resource_type == "Observation":
                processed['effectiveDateTime'] = value
            elif resource_type == "Condition":
                processed['onsetDateTime'] = value
            elif resource_type == "Encounter":
                processed['period.start'] = value
            del processed[field]
    
    # Handle phone/email compound fields
    contact_fields = {
        'contact': 'telecom',
        'phone': 'telecom',
        'email': 'telecom',
        'mobile': 'telecom'
    }
    
    for field, target in contact_fields.items():
        if field in processed:
            value = processed[field]
            processed[f'{target}.0.system'] = 'phone' if field in ['phone', 'mobile'] else 'email'
            processed[f'{target}.0.value'] = value
            processed[f'{target}.0.use'] = 'mobile' if field == 'mobile' else 'home'
            del processed[field]
    
    return processed


def validate_and_enrich_mapping(mapped_data: dict, resource_type: str) -> dict:
    """Validate and enrich mapped data with required FHIR fields."""
    enriched = mapped_data.copy()
    
    # Auto-generate ID if missing
    if 'id' not in enriched:
        enriched['id'] = f"{resource_type.lower()}-{uuid.uuid4().hex[:8]}"
    
    # Add resource type if missing
    if 'resourceType' not in enriched:
        enriched['resourceType'] = resource_type
    
    # Resource-specific enrichment
    if resource_type == "Patient":
        # Ensure gender is normalized
        if 'gender' in enriched:
            gender_map = {'m': 'male', 'f': 'female', 'male': 'male', 'female': 'female'}
            enriched['gender'] = gender_map.get(str(enriched['gender']).lower(), enriched['gender'])
        
        # Ensure birthDate is in correct format
        if 'birthDate' in enriched:
            enriched['birthDate'] = fix_date(enriched['birthDate'])
    
    elif resource_type == "Observation":
        # Ensure status is present
        if 'status' not in enriched:
            enriched['status'] = 'final'
        
        # Ensure subject reference is normalized (handle both dict and string)
        if 'subject' in enriched:
            subject = enriched['subject']
            if isinstance(subject, dict):
                # Already a reference dict, ensure it has proper format
                if 'reference' in subject:
                    ref = subject['reference']
                    if not str(ref).startswith('Patient/'):
                        subject['reference'] = f"Patient/{ref}"
                else:
                    # Dict without reference field, convert to string and format
                    enriched['subject'] = f"Patient/{subject.get('id', subject)}"
            elif isinstance(subject, str):
                # String reference, ensure proper format
                if not subject.startswith('Patient/'):
                    enriched['subject'] = f"Patient/{subject}"
    
    elif resource_type == "MedicationRequest":
        # Ensure status is present
        if 'status' not in enriched:
            enriched['status'] = 'active'
        
        # Ensure intent is present
        if 'intent' not in enriched:
            enriched['intent'] = 'order'
    
    elif resource_type == "Condition":
        # Ensure clinicalStatus is present
        if 'clinicalStatus' not in enriched:
            enriched['clinicalStatus'] = 'active'
    
    elif resource_type == "Encounter":
        # Ensure status is present
        if 'status' not in enriched:
            enriched['status'] = 'finished'
        
        # Ensure class is present
        if 'class' not in enriched:
            enriched['class'] = 'AMB'
    
    return enriched


def enhanced_map_to_fhir(input_data: Union[dict, list, str], resource_type: str = "Patient", 
                        enable_fuzzy: bool = True, enable_semantic: bool = True,
                        enable_advanced: bool = True) -> dict:
    """Enhanced mapping function with comprehensive error handling and advanced features."""
    
    try:
        # Normalize input data
        normalized_data = normalize_input_data(input_data)
        
        # Handle complex mappings
        if enable_advanced:
            normalized_data = handle_complex_mappings(normalized_data, resource_type)
        
        # Load mappings
        built_in, user_mappings, learned_mappings = load_mappings(resource_type)
        
        raw_mapped = {}
        unmapped = []
        applied_rules = []
        confidence_scores = []
        
        # Combine all mapping sources with priority
        all_mappings = {**built_in, **user_mappings, **learned_mappings}
        
        for field, value in normalized_data.items():
            if field == "resourcetype":
                continue
            
            # Skip structured telecom fields - they'll be handled by build_telecoms
            if field.startswith("telecom."):
                raw_mapped[field] = value
                applied_rules.append({
                    "original_field": field,
                    "mapped_to": field,
                    "rule_type": "structured",
                    "confidence": 1.0
                })
                confidence_scores.append(1.0)
                continue
            
            normalized = normalize_field_name(field)
            fhir_field = None
            rule_type = None
            confidence = 1.0
            
            # Priority 1: Exact user-defined mapping
            if field in user_mappings or normalized in user_mappings:
                fhir_field = user_mappings.get(field) or user_mappings.get(normalized)
                rule_type = "user_defined"
                confidence = 1.0
            
            # Priority 2: Exact learned mapping
            elif field in learned_mappings or normalized in learned_mappings:
                fhir_field = learned_mappings.get(field) or learned_mappings.get(normalized)
                rule_type = "learned"
                confidence = 0.95
            
            # Priority 3: Exact built-in mapping
            elif field in built_in or normalized in built_in:
                fhir_field = built_in.get(field) or built_in.get(normalized)
                rule_type = "built_in"
                confidence = 0.9
            
            # Priority 4: Fuzzy matching (if enabled)
            elif enable_fuzzy:
                best_match, score = find_best_match(field, all_mappings, threshold=0.7)
                if best_match and score >= 0.7:
                    fhir_field = best_match
                    rule_type = "fuzzy_match"
                    confidence = score
                    save_learned_mapping(field, fhir_field, resource_type, confidence)
            
            # Priority 5: Advanced semantic analysis (if enabled)
            elif enable_advanced and enable_semantic:
                semantic_result = advanced_semantic_analysis(field, value, resource_type, normalized_data)
                if semantic_result:
                    fhir_field = semantic_result["fhir_field"]
                    rule_type = "advanced_semantic"
                    confidence = semantic_result["confidence"]
                    save_learned_mapping(field, fhir_field, resource_type, confidence)
            
            # Priority 6: Basic semantic analysis (fallback)
            elif enable_semantic:
                semantic_match = semantic_field_analysis(field, value, resource_type)
                if semantic_match:
                    fhir_field = semantic_match
                    rule_type = "semantic_analysis"
                    confidence = 0.6
                    save_learned_mapping(field, fhir_field, resource_type, confidence)
            
            # Apply mapping if found
            if fhir_field:
                raw_mapped[fhir_field] = value
                applied_rules.append({
                    "original_field": field,
                    "mapped_to": fhir_field,
                    "rule_type": rule_type,
                    "confidence": confidence
                })
                confidence_scores.append(confidence)
            else:
                unmapped.append({
                    "field": field,
                    "value": value,
                    "status": "unmapped",
                    "message": f"No mapping rule found for '{field}'.",
                    "action_required": "Please provide a manual mapping.",
                    "suggestions": generate_mapping_suggestions(field, value, all_mappings)
                })
        
        # Convert flat mapped fields to proper FHIR structure
        fhir_resource = build_fhir_structure(raw_mapped, resource_type)
        
        # Validate and enrich the mapped resource
        fhir_resource = validate_and_enrich_mapping(fhir_resource, resource_type)
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "mapped_resource": fhir_resource,
            "unmapped_fields": unmapped,
            "applied_rules": applied_rules,
            "mapping_complete": len(unmapped) == 0,
            "overall_confidence": overall_confidence,
            "resource_type": resource_type,
            "input_fields_processed": len(normalized_data),
            "fields_mapped": len(raw_mapped),
            "processing_status": "success"
        }
    
    except Exception as e:
        return {
            "mapped_resource": None,
            "unmapped_fields": [],
            "applied_rules": [],
            "mapping_complete": False,
            "overall_confidence": 0.0,
            "resource_type": resource_type,
            "processing_status": "error",
            "error_message": str(e),
            "error_type": type(e).__name__
        }


def map_to_fhir(input_data: Union[dict, list, str], resource_type: str = "Patient", enable_fuzzy: bool = True, enable_semantic: bool = True, enable_advanced: bool = True) -> dict:
    """Main mapping function - routes to enhanced mapper if advanced features enabled."""
    if enable_advanced:
        return enhanced_map_to_fhir(input_data, resource_type, enable_fuzzy, enable_semantic, enable_advanced)
    
    # Original implementation for backward compatibility
    built_in, user_mappings, learned_mappings = load_mappings(resource_type)

    raw_mapped = {}
    unmapped = []
    applied_rules = []
    confidence_scores = []

    # Combine all mapping sources with priority
    all_mappings = {**built_in, **user_mappings, **learned_mappings}

    for field, value in input_data.items():
        if field == "resourceType":
            continue

        normalized = normalize_field_name(field)
        fhir_field = None
        rule_type = None
        confidence = 1.0

        # Priority 1: Exact user-defined mapping
        if field in user_mappings or normalized in user_mappings:
            fhir_field = user_mappings.get(field) or user_mappings.get(normalized)
            rule_type = "user_defined"
            confidence = 1.0

        # Priority 2: Exact learned mapping
        elif field in learned_mappings or normalized in learned_mappings:
            fhir_field = learned_mappings.get(field) or learned_mappings.get(normalized)
            rule_type = "learned"
            confidence = 0.95

        # Priority 3: Exact built-in mapping
        elif field in built_in or normalized in built_in:
            fhir_field = built_in.get(field) or built_in.get(normalized)
            rule_type = "built_in"
            confidence = 0.9

        # Priority 4: Fuzzy matching (if enabled)
        elif enable_fuzzy:
            best_match, score = find_best_match(field, all_mappings, threshold=0.7)
            if best_match and score >= 0.7:
                fhir_field = best_match
                rule_type = "fuzzy_match"
                confidence = score
                # Learn this mapping for future
                save_learned_mapping(field, fhir_field, resource_type, confidence)

        # Priority 5: Semantic analysis (if enabled)
        elif enable_semantic:
            semantic_match = semantic_field_analysis(field, value, resource_type)
            if semantic_match:
                fhir_field = semantic_match
                rule_type = "semantic_analysis"
                confidence = 0.6
                # Learn this mapping for future
                save_learned_mapping(field, fhir_field, resource_type, confidence)

        # Apply mapping if found
        if fhir_field:
            raw_mapped[fhir_field] = value
            applied_rules.append({
                "original_field": field,
                "mapped_to": fhir_field,
                "rule_type": rule_type,
                "confidence": confidence
            })
            confidence_scores.append(confidence)
        else:
            unmapped.append({
                "field": field,
                "value": value,
                "status": "unmapped",
                "message": f"No mapping rule found for '{field}'.",
                "action_required": "Please provide a manual mapping.",
                "suggestions": generate_mapping_suggestions(field, value, all_mappings)
            })

    # Convert flat mapped fields to proper FHIR structure
    fhir_resource = build_fhir_structure(raw_mapped, resource_type)

    # Calculate overall confidence
    overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

    return {
        "mapped_resource": fhir_resource,
        "unmapped_fields": unmapped,
        "applied_rules": applied_rules,
        "mapping_complete": len(unmapped) == 0,
        "overall_confidence": overall_confidence,
        "resource_type": resource_type,
        "input_fields_processed": len(input_data),
        "fields_mapped": len(raw_mapped),
        "processing_status": "success"
    }


def generate_mapping_suggestions(field: str, value: Any, mappings: Dict[str, str]) -> List[Dict[str, Any]]:
    """Generate mapping suggestions for unmapped fields"""
    suggestions = []
    
    # Get top 3 fuzzy matches
    matches = []
    for target_field, fhir_path in mappings.items():
        score = calculate_similarity(field, target_field)
        if score >= 0.4:  # Lower threshold for suggestions
            matches.append((fhir_path, score))
    
    # Sort by score and take top 3
    matches.sort(key=lambda x: x[1], reverse=True)
    for fhir_path, score in matches[:3]:
        suggestions.append({
            "fhir_field": fhir_path,
            "confidence": score,
            "reason": "Fuzzy match"
        })
    
    # Add semantic suggestion if available
    semantic_match = semantic_field_analysis(field, value, "Patient")
    if semantic_match and semantic_match not in [s["fhir_field"] for s in suggestions]:
        suggestions.append({
            "fhir_field": semantic_match,
            "confidence": 0.5,
            "reason": "Semantic analysis"
        })
    
    return suggestions


def save_learned_mapping(field: str, fhir_field: str, resource_type: str, confidence: float):
    """Save a learned mapping to the learned mappings file"""
    try:
        path = os.path.join(os.path.dirname(__file__), LEARNING_PATH)
        
        # Load existing learned mappings
        if os.path.exists(path):
            with open(path, "r") as f:
                learned_data = json.load(f)
        else:
            learned_data = {}
        
        # Initialize resource type if not exists
        if resource_type not in learned_data:
            learned_data[resource_type] = {}
        
        # Only save if confidence is high enough or improves existing
        existing_confidence = learned_data[resource_type].get(field, {}).get("confidence", 0)
        if confidence > existing_confidence:
            learned_data[resource_type][field] = {
                "fhir_field": fhir_field,
                "confidence": confidence,
                "learned_at": datetime.now().isoformat(),
                "usage_count": learned_data[resource_type].get(field, {}).get("usage_count", 0) + 1
            }
            
            # Save back to file
            with open(path, "w") as f:
                json.dump(learned_data, f, indent=2)
    
    except Exception as e:
        # Don't fail if learning fails
        pass


def build_fhir_structure(raw: dict, resource_type: str) -> dict:
    """
    Convert flat dot-notation mapped fields
    into proper nested FHIR resource structure for all resource types
    Preserves already-formatted FHIR structures (arrays, CodeableConcepts, etc.)
    """
    resource = {"resourceType": resource_type}

    # Route to resource-specific builder
    if resource_type == "Patient":
        return build_patient_structure(raw)
    elif resource_type == "Observation":
        return build_observation_structure(raw)
    elif resource_type == "MedicationRequest":
        return build_medication_request_structure(raw)
    elif resource_type == "Condition":
        return build_condition_structure(raw)
    elif resource_type == "Encounter":
        return build_encounter_structure(raw)
    else:
        # Generic builder for other resource types
        return build_generic_structure(raw, resource_type)


def build_patient_structure(raw: dict) -> dict:
    """Build Patient resource with all complex FHIR structures"""
    resource = {"resourceType": "Patient"}

    # --- Simple flat fields ---
    simple_fields = [
        "id", "gender", "birthDate",
        "deceasedBoolean", "deceasedDateTime",
        "active", "multipleBirthBoolean", "multipleBirthInteger"
    ]
    for field in simple_fields:
        if field in raw:
            resource[field] = normalize_field_value(raw[field], field)

    # --- Preserve complex FHIR structures (arrays, objects) ---
    complex_fields = [
        "identifier", "name", "telecom", "address",
        "contact", "communication", "photo", "extension",
        "generalPractitioner", "managingOrganization",
        "link", "maritalStatus", "meta"
    ]
    for field in complex_fields:
        if field in raw:
            value = raw[field]
            if isinstance(value, (list, dict)):
                resource[field] = value

    # --- Identifiers - complex handling ---
    if "identifier" not in resource:
        resource["identifier"] = build_identifiers(raw)

    # --- Name (HumanName) - advanced handling ---
    if "name" not in resource:
        resource["name"] = build_human_names(raw)

    # --- Telecom - advanced handling ---
    if "telecom" not in resource:
        resource["telecom"] = build_telecoms(raw)

    # --- Address - advanced handling ---
    if "address" not in resource:
        resource["address"] = build_addresses(raw)

    # --- MaritalStatus (CodeableConcept) ---
    if "maritalStatus" in raw:
        resource["maritalStatus"] = build_codeable_concept(
            raw["maritalStatus"],
            "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
            MARITAL_STATUS_CODES
        )

    # --- Communication / Language ---
    if "communication.language" in raw or "language" in raw:
        resource["communication"] = build_communications(raw)

    # --- Contact Points ---
    if "contact" not in resource:
        resource["contact"] = build_contacts(raw)

    # --- Deceased handling (choice type) ---
    if "deceasedBoolean" in raw or "deceasedDateTime" in raw:
        resource = handle_deceased_field(resource, raw)

    # --- Birth Sex extension ---
    if "birthSex" in raw:
        resource = add_birth_sex_extension(resource, raw["birthSex"])

    return resource


def build_observation_structure(raw: dict) -> dict:
    """Build Observation resource with all complex FHIR structures"""
    resource = {"resourceType": "Observation"}

    # --- Simple fields ---
    simple_fields = ["id", "status", "effectiveDateTime", "effectivePeriod", 
                     "issued", "focus", "hasMember", "derivedFrom"]
    for field in simple_fields:
        if field in raw:
            resource[field] = normalize_field_value(raw[field], field)

    # --- Subject (reference) ---
    if "subject" in raw:
        resource["subject"] = build_reference(raw["subject"], "Patient")

    # --- Encounter (reference) ---
    if "encounter" in raw:
        resource["encounter"] = build_reference(raw["encounter"], "Encounter")

    # --- Code (CodeableConcept) - required field ---
    if "code" in raw:
        if isinstance(raw["code"], dict):
            resource["code"] = raw["code"]
        else:
            resource["code"] = build_codeable_concept(
                raw["code"],
                "http://loinc.org",
                LOINC_COMMON_CODES
            )
    elif "code.display" in raw or "testname" in raw:
        code_display = raw.get("code.display") or raw.get("testname")
        resource["code"] = {
            "coding": [{
                "system": "http://loinc.org",
                "code": "unknown",
                "display": code_display
            }],
            "text": code_display
        }

    # --- Value[x] - choice type handling ---
    resource = handle_observation_value(resource, raw)

    # --- DataAbsentReason ---
    if "dataAbsentReason" in raw:
        resource["dataAbsentReason"] = build_codeable_concept(
            raw["dataAbsentReason"],
            "http://terminology.hl7.org/CodeSystem/data-absent-reason"
        )

    # --- Interpretation ---
    if "interpretation" in raw:
        resource["interpretation"] = [build_codeable_concept(
            raw["interpretation"],
            "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
            INTERPRETATION_CODES
        )]

    # --- Reference Range ---
    if "referenceRange" in raw or "referenceRange.low" in raw or "referenceRange.high" in raw:
        resource["referenceRange"] = [build_reference_range(raw)]

    # --- Category ---
    if "category" in raw:
        if isinstance(raw["category"], list):
            resource["category"] = raw["category"]
        else:
            resource["category"] = [build_codeable_concept(
                raw["category"],
                "http://terminology.hl7.org/CodeSystem/observation-category",
                OBSERVATION_CATEGORY_CODES
            )]

    # --- Body Site ---
    if "bodySite" in raw:
        resource["bodySite"] = build_codeable_concept(
            raw["bodySite"],
            "http://snomed.info/sct"
        )

    # --- Method ---
    if "method" in raw:
        resource["method"] = build_codeable_concept(
            raw["method"],
            "http://snomed.info/sct"
        )

    # --- Specimen ---
    if "specimen" in raw:
        resource["specimen"] = build_reference(raw["specimen"], "Specimen")

    # --- Device ---
    if "device" in raw:
        resource["device"] = build_reference(raw["device"], "Device")

    # --- Performer ---
    if "performer" in raw:
        if isinstance(raw["performer"], list):
            resource["performer"] = [build_reference(p, "Practitioner") for p in raw["performer"]]
        else:
            resource["performer"] = [build_reference(raw["performer"], "Practitioner")]

    return resource


def build_medication_request_structure(raw: dict) -> dict:
    """Build MedicationRequest resource with all complex FHIR structures"""
    resource = {"resourceType": "MedicationRequest"}

    # --- Simple fields ---
    simple_fields = ["id", "status", "intent", "priority", "authoredOn", 
                     "doNotPerform", "reported", "reasonCode"]
    for field in simple_fields:
        if field in raw:
            resource[field] = normalize_field_value(raw[field], field)

    # --- Subject (reference) ---
    if "subject" in raw:
        resource["subject"] = build_reference(raw["subject"], "Patient")

    # --- Encounter (reference) ---
    if "encounter" in raw:
        resource["encounter"] = build_reference(raw["encounter"], "Encounter")

    # --- Medication (choice type) ---
    if "medicationCodeableConcept" in raw:
        if isinstance(raw["medicationCodeableConcept"], dict):
            resource["medicationCodeableConcept"] = raw["medicationCodeableConcept"]
        else:
            resource["medicationCodeableConcept"] = build_codeable_concept(
                raw["medicationCodeableConcept"],
                "http://www.nlm.nih.gov/research/umls/rxnorm",
                RXNORM_COMMON_CODES
            )
    elif "medicationReference" in raw:
        resource["medicationReference"] = build_reference(raw["medicationReference"], "Medication")

    # --- Dosage Instruction ---
    if "dosageInstruction" in raw or any(k.startswith("dosageInstruction") for k in raw):
        resource["dosageInstruction"] = [build_dosage_instruction(raw)]

    # --- Dispense Request ---
    if "dispenseRequest" in raw or any(k.startswith("dispenseRequest") for k in raw):
        resource["dispenseRequest"] = build_dispense_request(raw)

    # --- Substitution ---
    if "substitution" in raw:
        resource["substitution"] = build_substitution(raw)

    # --- Requester (reference) ---
    if "requester" in raw:
        resource["requester"] = build_reference(raw["requester"], "Practitioner")

    # --- Reason Reference ---
    if "reasonReference" in raw:
        resource["reasonReference"] = build_reference(raw["reasonReference"], "Condition")

    # --- Note ---
    if "note" in raw:
        if isinstance(raw["note"], list):
            resource["note"] = raw["note"]
        else:
            resource["note"] = [{"text": str(raw["note"])}]

    return resource


def build_condition_structure(raw: dict) -> dict:
    """Build Condition resource with all complex FHIR structures"""
    resource = {"resourceType": "Condition"}

    # --- Simple fields ---
    simple_fields = ["id", "recordedDate", "verificationStatus"]
    for field in simple_fields:
        if field in raw:
            resource[field] = normalize_field_value(raw[field], field)

    # --- Subject (reference) ---
    if "subject" in raw:
        resource["subject"] = build_reference(raw["subject"], "Patient")

    # --- Encounter (reference) ---
    if "encounter" in raw:
        resource["encounter"] = build_reference(raw["encounter"], "Encounter")

    # --- Code (CodeableConcept) - required field ---
    if "code" in raw:
        if isinstance(raw["code"], dict):
            resource["code"] = raw["code"]
        else:
            resource["code"] = build_codeable_concept(
                raw["code"],
                "http://snomed.info/sct",
                SNOMED_CONDITION_CODES
            )
    elif "code.display" in raw or "diagnosis" in raw:
        code_display = raw.get("code.display") or raw.get("diagnosis")
        resource["code"] = {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "unknown",
                "display": code_display
            }],
            "text": code_display
        }

    # --- Clinical Status ---
    if "clinicalStatus" in raw:
        resource["clinicalStatus"] = build_codeable_concept(
            raw["clinicalStatus"],
            "http://terminology.hl7.org/CodeSystem/condition-clinical",
            CONDITION_CLINICAL_STATUS_CODES
        )

    # --- Severity ---
    if "severity" in raw:
        resource["severity"] = build_codeable_concept(
            raw["severity"],
            "http://snomed.info/sct",
            SEVERITY_CODES
        )

    # --- Onset (choice type) ---
    if "onsetDateTime" in raw:
        resource["onsetDateTime"] = normalize_date(raw["onsetDateTime"])
    elif "onsetAge" in raw:
        resource["onsetAge"] = build_quantity(raw["onsetAge"])
    elif "onsetPeriod" in raw:
        resource["onsetPeriod"] = build_period(raw["onsetPeriod"])

    # --- Abatement (choice type) ---
    if "abatementDateTime" in raw:
        resource["abatementDateTime"] = normalize_date(raw["abatementDateTime"])
    elif "abatementAge" in raw:
        resource["abatementAge"] = build_quantity(raw["abatementAge"])

    # --- Body Site ---
    if "bodySite" in raw:
        resource["bodySite"] = build_codeable_concept(
            raw["bodySite"],
            "http://snomed.info/sct"
        )

    # --- Category ---
    if "category" in raw:
        if isinstance(raw["category"], list):
            resource["category"] = raw["category"]
        else:
            resource["category"] = [build_codeable_concept(
                raw["category"],
                "http://terminology.hl7.org/CodeSystem/condition-category"
            )]

    # --- Note ---
    if "note" in raw:
        if isinstance(raw["note"], list):
            resource["note"] = raw["note"]
        else:
            resource["note"] = [{"text": str(raw["note"])}]

    return resource


def build_encounter_structure(raw: dict) -> dict:
    """Build Encounter resource with all complex FHIR structures"""
    resource = {"resourceType": "Encounter"}

    # --- Simple fields ---
    simple_fields = ["id", "status", "period", "reasonCode"]
    for field in simple_fields:
        if field in raw:
            resource[field] = normalize_field_value(raw[field], field)

    # --- Subject (reference) ---
    if "subject" in raw:
        resource["subject"] = build_reference(raw["subject"], "Patient")

    # --- Class ---
    if "class" in raw:
        if isinstance(raw["class"], dict):
            resource["class"] = raw["class"]
        else:
            resource["class"] = {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory",
                "userSelected": False
            }

    # --- Priority ---
    if "priority" in raw:
        resource["priority"] = build_codeable_concept(
            raw["priority"],
            "http://terminology.hl7.org/CodeSystem/v3-ActPriority"
        )

    # --- Participant ---
    if "participant" in raw:
        if isinstance(raw["participant"], list):
            resource["participant"] = raw["participant"]
        else:
            resource["participant"] = [{
                "individual": build_reference(raw["participant"], "Practitioner")
            }]

    # --- Type ---
    if "type" in raw:
        if isinstance(raw["type"], list):
            resource["type"] = raw["type"]
        else:
            resource["type"] = [build_codeable_concept(
                raw["type"],
                "http://snomed.info/sct"
            )]

    # --- Service Type ---
    if "serviceType" in raw:
        resource["serviceType"] = build_codeable_concept(
            raw["serviceType"],
            "http://snomed.info/sct"
        )

    # --- Location ---
    if "location" in raw:
        if isinstance(raw["location"], list):
            resource["location"] = raw["location"]
        else:
            resource["location"] = [{
                "location": build_reference(raw["location"], "Location")
            }]

    # --- Reason Reference ---
    if "reasonReference" in raw:
        if isinstance(raw["reasonReference"], list):
            resource["reasonReference"] = raw["reasonReference"]
        else:
            resource["reasonReference"] = [build_reference(raw["reasonReference"], "Condition")]

    # --- Hospitalization ---
    if "hospitalization" in raw or any(k.startswith("hospitalization") for k in raw):
        resource["hospitalization"] = build_hospitalization(raw)

    return resource


def build_generic_structure(raw: dict, resource_type: str) -> dict:
    """Generic builder for other resource types"""
    resource = {"resourceType": resource_type}

    # Handle basic field types
    for field, value in raw.items():
        if '.' in field:
            # Handle nested fields
            parts = field.split('.')
            current = resource
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = normalize_field_value(value, parts[-1])
        else:
            resource[field] = normalize_field_value(value, field)

    return resource


# ============================================================================
# HELPER FUNCTIONS FOR COMPLEX FHIR STRUCTURES
# ============================================================================

# Code system mappings
MARITAL_STATUS_CODES = {
    "married": "M", "single": "S", "divorced": "D", 
    "widowed": "W", "separated": "L", "unknown": "U"
}

CONDITION_CLINICAL_STATUS_CODES = {
    "active": "active", "recurrence": "recurrence", "relapse": "relapse",
    "inactive": "inactive", "remission": "remission", "resolved": "resolved"
}

INTERPRETATION_CODES = {
    "high": "H", "low": "L", "normal": "N", "abnormal": "A",
    "critical": "AA", "off": "OFF"
}

OBSERVATION_CATEGORY_CODES = {
    "vital-signs": "vital-signs", "laboratory": "laboratory",
    "social-history": "social-history", "imaging": "imaging",
    "procedure": "procedure", "survey": "survey"
}

SEVERITY_CODES = {
    "mild": "255604002", "moderate": "6736007", 
    "severe": "24484000", "fatal": "399166001"
}

LOINC_COMMON_CODES = {
    "blood pressure": "85354-9",
    "heart rate": "8867-4",
    "body temperature": "8310-5",
    "respiratory rate": "9279-1",
    "oxygen saturation": "2708-6"
}

RXNORM_COMMON_CODES = {
    "aspirin": "1191",
    "ibuprofen": "4907",
    "acetaminophen": "161",
    "amoxicillin": "733"
}

SNOMED_CONDITION_CODES = {
    "hypertension": "38341003",
    "diabetes": "73211009",
    "asthma": "195967001",
    "depression": "35489007"
}


def normalize_field_value(value: Any, field_name: str) -> Any:
    """Normalize field value based on field type"""
    if value is None:
        return None
    
    # Boolean normalization
    if field_name.endswith("Boolean") or field_name in ["active", "deceased"]:
        return normalize_boolean(value)
    
    # Date normalization
    if any(keyword in field_name.lower() for keyword in ["date", "datetime", "birth", "death", "onset", "abatement"]):
        return normalize_date(value)
    
    # Numeric normalization
    if any(keyword in field_name.lower() for keyword in ["value", "quantity", "age", "count"]):
        return safe_float(value)
    
    return value


def normalize_boolean(value: Any) -> bool:
    """Convert various boolean representations to Python bool"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ["true", "yes", "1", "y"]
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def normalize_date(value: Any) -> str:
    """Normalize various date formats to FHIR date format"""
    if value is None:
        return None
    
    if isinstance(value, str):
        # Try to parse and reformat
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d"]:
            try:
                dt = datetime.strptime(value, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        # If already in ISO format, return as-is
        if re.match(r"\d{4}-\d{2}-\d{2}", value):
            return value
    elif isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    
    return str(value)


def safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def build_reference(ref: Any, resource_type: str) -> dict:
    """Build FHIR reference structure"""
    if isinstance(ref, dict) and "reference" in ref:
        return ref
    
    if isinstance(ref, str):
        # If already in proper format
        if "/" in ref:
            return {"reference": ref}
        # Add resource type if missing
        return {"reference": f"{resource_type}/{ref}"}
    
    if isinstance(ref, dict) and "id" in ref:
        return {"reference": f"{resource_type}/{ref['id']}"}
    
    return {"reference": f"{resource_type}/{ref}"}


def build_codeable_concept(value: Any, system: str, code_map: dict = None) -> dict:
    """Build FHIR CodeableConcept structure"""
    if isinstance(value, dict) and "coding" in value:
        return value
    
    value_str = str(value).lower() if value is not None else ""
    
    # Try to find code in mapping
    code = None
    display = value_str.title() if value_str else "Unknown"
    
    if code_map:
        for key, mapped_code in code_map.items():
            if key in value_str:
                code = mapped_code
                display = key.title()
                break
    
    if not code:
        code = value_str.upper()[:10] if value_str else "UNKNOWN"
    
    return {
        "coding": [{
            "system": system,
            "code": code,
            "display": display
        }],
        "text": str(value) if value else None
    }


def build_quantity(value: Any, unit: str = None, system: str = "http://unitsofmeasure.org") -> dict:
    """Build FHIR Quantity structure"""
    numeric_value = safe_float(value)
    if numeric_value is None:
        return None
    
    quantity = {"value": numeric_value}
    
    if unit:
        quantity["unit"] = unit
        quantity["system"] = system
        quantity["code"] = unit
    
    return quantity


def build_period(value: Any) -> dict:
    """Build FHIR Period structure"""
    if isinstance(value, dict):
        return value
    
    if isinstance(value, str):
        # Try to parse as date range
        if " to " in value or "-" in value:
            parts = re.split(r"\s*(?:to|-)\s*", value)
            if len(parts) == 2:
                return {
                    "start": normalize_date(parts[0]),
                    "end": normalize_date(parts[1])
                }
    
    return {"start": normalize_date(value)}


def build_identifiers(raw: dict) -> list:
    """Build identifier list from raw data"""
    identifiers = []
    
    # Common identifier patterns
    identifier_patterns = [
        ("mrn", "medical record number", "MR"),
        ("ssn", "social security number", "SS"),
        ("account", "account number", "AN"),
        ("passport", "passport number", "PPN"),
        ("driver", "driver's license", "DL"),
        ("insurance", "insurance number", "IN")
    ]
    
    for field, value in raw.items():
        if value is None:
            continue
        
        for pattern, display, code in identifier_patterns:
            if pattern in field.lower():
                identifiers.append({
                    "use": "official",
                    "type": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": code,
                            "display": display
                        }]
                    },
                    "system": f"urn:oid:2.16.840.1.113883.4.1.{code}",
                    "value": str(value)
                })
    
    # Generic identifier for id fields
    if "id" in raw and not identifiers:
        identifiers.append({
            "use": "usual",
            "type": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                    "code": "PI",
                    "display": "Patient internal identifier"
                }]
            },
            "value": str(raw["id"])
        })
    
    return identifiers


def build_human_names(raw: dict) -> list:
    """Build human name list from raw data"""
    names = []
    name_entry = {}
    
    # Given name(s)
    given_names = []
    for field in ["name.given", "firstname", "first_name", "fname", "givenname"]:
        if field in raw:
            value = raw[field]
            if isinstance(value, list):
                given_names.extend(value)
            else:
                given_names.append(str(value))
    
    if given_names:
        name_entry["given"] = given_names
    
    # Family name
    for field in ["name.family", "lastname", "last_name", "lname", "familyname", "surname"]:
        if field in raw:
            name_entry["family"] = str(raw[field])
            break
    
    # Full name text
    for field in ["name", "fullname", "full_name", "patientname", "patient_name"]:
        if field in raw:
            name_entry["text"] = str(raw[field])
            break
    
    # Name use and period
    if "name.use" in raw:
        name_entry["use"] = raw["name.use"]
    if "name.period" in raw:
        name_entry["period"] = build_period(raw["name.period"])
    
    # Prefixes and suffixes
    if "name.prefix" in raw:
        name_entry["prefix"] = [str(raw["name.prefix"])]
    if "name.suffix" in raw:
        name_entry["suffix"] = [str(raw["name.suffix"])]
    
    if name_entry:
        names.append(name_entry)
    
    return names


def build_telecoms(raw: dict) -> list:
    """Build telecom list from raw data"""
    telecoms = []
    
    # Check if telecom is already structured (from complex mappings)
    if "telecom.0.system" in raw or "telecom.0.value" in raw:
        # Build from structured telecom data
        for i in range(10):  # Check up to 10 telecom entries
            system = raw.get(f"telecom.{i}.system")
            value = raw.get(f"telecom.{i}.value")
            use = raw.get(f"telecom.{i}.use", "home")
            
            if system and value:
                telecoms.append({
                    "system": system,
                    "value": value,
                    "use": use
                })
            elif not system and not value and i == 0:
                break  # No more entries if first entry is empty
        
        if telecoms:
            return telecoms
    
    # Phone numbers - expanded field list
    phone_fields = ["phone", "phonenumber", "phone_number", "mobile", "contact", "tel", 
                    "telephone", "homephone", "home_phone", "workphone", "work_phone",
                    "cellphone", "cell_phone", "mobilenumber", "mobile_number"]
    for field in phone_fields:
        if field in raw and raw[field]:
            phone_value = str(raw[field])
            # More lenient phone pattern check
            if re.search(r'[\d\-\+\(\)\s]{5,}', phone_value):
                use = "mobile" if "mobile" in field.lower() or "cell" in field.lower() else "home"
                if "work" in field.lower():
                    use = "work"
                telecoms.append({
                    "system": "phone",
                    "value": phone_value,
                    "use": use
                })
    
    # Email addresses - expanded field list
    email_fields = ["email", "emailaddress", "email_address", "mail", "emailaddress",
                    "e_mail", "emailaddress", "contactemail", "contact_email"]
    for field in email_fields:
        if field in raw and raw[field]:
            email_value = str(raw[field])
            if "@" in email_value:
                telecoms.append({
                    "system": "email",
                    "value": email_value,
                    "use": "home"
                })
    
    # FAX
    if "fax" in raw and raw["fax"]:
        telecoms.append({
            "system": "fax",
            "value": str(raw["fax"]),
            "use": "work"
        })
    
    return telecoms


def build_addresses(raw: dict) -> list:
    """Build address list from raw data"""
    addresses = []
    address_entry = {}
    
    # Address components - both prefixed and non-prefixed versions
    field_mappings = {
        # Text/full address
        "address": "text",
        "fulladdress": "text",
        "full_address": "text",
        "streetaddress": "text",
        "street_address": "text",
        
        # Line/street
        "address.line": "line",
        "address.street": "line",
        "street": "line",
        "street_line": "line",
        "addressline": "line",
        "address_line": "line",
        
        # City
        "address.city": "city",
        "city": "city",
        "cityname": "city",
        "city_name": "city",
        
        # State/province
        "address.state": "state",
        "address.province": "state",
        "state": "state",
        "statecode": "state",
        "state_code": "state",
        "province": "state",
        "region": "state",
        
        # Postal code/zip
        "address.postalcode": "postalCode",
        "address.zip": "postalCode",
        "zip": "postalCode",
        "zipcode": "postalCode",
        "zip_code": "postalCode",
        "postalcode": "postalCode",
        "postal_code": "postalCode",
        "postcode": "postalCode",
        "post_code": "postalCode",
        
        # Country
        "address.country": "country",
        "country": "country",
        "countrycode": "country",
        "country_code": "country",
        
        # Use and type
        "address.use": "use",
        "address.type": "type"
    }
    
    for raw_field, fhir_field in field_mappings.items():
        if raw_field in raw and raw[raw_field]:
            value = raw[raw_field]
            if fhir_field == "line":
                address_entry[fhir_field] = [str(value)] if not isinstance(value, list) else value
            else:
                address_entry[fhir_field] = value
    
    # Also check for direct postalCode field (from built-in mappings)
    if "postalCode" in raw and raw["postalCode"]:
        address_entry["postalCode"] = raw["postalCode"]
    
    # District/county
    district_fields = ["address.district", "address.county", "district", "county"]
    for field in district_fields:
        if field in raw and raw[field]:
            address_entry["district"] = raw[field]
            break
    
    # Period
    if "address.period" in raw:
        address_entry["period"] = build_period(raw["address.period"])
    
    if address_entry:
        addresses.append(address_entry)
    
    return addresses


def build_communications(raw: dict) -> list:
    """Build communication list from raw data"""
    communications = []
    
    language = raw.get("communication.language") or raw.get("language")
    if language:
        communications.append({
            "language": {
                "coding": [{
                    "system": "urn:ietf:bcp:47",
                    "code": str(language).lower()[:2],
                    "display": str(language)
                }]
            },
            "preferred": True
        })
    
    return communications


def build_contacts(raw: dict) -> list:
    """Build contact list from raw data"""
    contacts = []
    
    # This would need more complex logic for multiple contacts
    # For now, just handle single emergency contact
    if "emergency.contact" in raw or "emergencycontact" in raw:
        contact_entry = {}
        
        emergency_field = "emergency.contact" if "emergency.contact" in raw else "emergencycontact"
        contact_value = raw[emergency_field]
        
        contact_entry["relationship"] = [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v2-0131",
                "code": "C",
                "display": "Emergency Contact"
            }]
        }]
        
        if isinstance(contact_value, str):
            contact_entry["name"] = {"text": contact_value}
        elif isinstance(contact_value, dict):
            contact_entry.update(contact_value)
        
        contacts.append(contact_entry)
    
    return contacts


def handle_deceased_field(resource: dict, raw: dict) -> dict:
    """Handle deceased choice field (Boolean or DateTime)"""
    if "deceasedBoolean" in raw:
        value = normalize_boolean(raw["deceasedBoolean"])
        resource["deceasedBoolean"] = value
    elif "deceasedDateTime" in raw:
        resource["deceasedDateTime"] = normalize_date(raw["deceasedDateTime"])
    
    return resource


def add_birth_sex_extension(resource: dict, sex: str) -> dict:
    """Add birth sex extension to patient resource"""
    if "extension" not in resource:
        resource["extension"] = []
    
    sex_code = str(sex).upper()
    if sex_code in ["M", "F"]:
        resource["extension"].append({
            "url": "http://hl7.org/fhir/StructureDefinition/individual-birthSex",
            "valueCode": sex_code
        })
    
    return resource


def handle_observation_value(resource: dict, raw: dict) -> dict:
    """Handle observation value[x] choice type"""
    # Priority: Quantity > CodeableConcept > String > Boolean > Integer > Range > Ratio > SampledData > Time > DateTime > Period
    
    if "valueQuantity" in raw:
        if isinstance(raw["valueQuantity"], dict):
            resource["valueQuantity"] = raw["valueQuantity"]
        else:
            resource["valueQuantity"] = build_quantity(raw["valueQuantity"])
    
    elif "valueQuantity.value" in raw:
        value = safe_float(raw["valueQuantity.value"])
        unit = raw.get("valueQuantity.unit") or raw.get("unit")
        resource["valueQuantity"] = build_quantity(value, unit)
    
    elif "valueCodeableConcept" in raw:
        resource["valueCodeableConcept"] = build_codeable_concept(
            raw["valueCodeableConcept"],
            "http://loinc.org"
        )
    
    elif "valueString" in raw or "value" in raw:
        value = raw.get("valueString") or raw.get("value")
        # Try to convert to quantity if numeric
        numeric = safe_float(value)
        if numeric is not None:
            unit = raw.get("unit")
            resource["valueQuantity"] = build_quantity(numeric, unit)
        else:
            resource["valueString"] = str(value)
    
    elif "valueBoolean" in raw:
        resource["valueBoolean"] = normalize_boolean(raw["valueBoolean"])
    
    elif "valueInteger" in raw:
        resource["valueInteger"] = int(raw["valueInteger"])
    
    elif "valueDateTime" in raw:
        resource["valueDateTime"] = normalize_date(raw["valueDateTime"])
    
    return resource


def build_reference_range(raw: dict) -> dict:
    """Build reference range structure"""
    ref_range = {}
    
    if "referenceRange.low" in raw or "referencelow" in raw or "low" in raw:
        low_value = raw.get("referenceRange.low") or raw.get("referencelow") or raw.get("low")
        ref_range["low"] = build_quantity(low_value)
    
    if "referenceRange.high" in raw or "referencehigh" in raw or "high" in raw:
        high_value = raw.get("referenceRange.high") or raw.get("referencehigh") or raw.get("high")
        ref_range["high"] = build_quantity(high_value)
    
    if "referenceRange.type" in raw:
        ref_range["type"] = build_codeable_concept(
            raw["referenceRange.type"],
            "http://terminology.hl7.org/CodeSystem/referencerange-meaning"
        )
    
    return ref_range


def build_dosage_instruction(raw: dict) -> dict:
    """Build dosage instruction structure"""
    dosage = {}
    
    # Dose quantity
    if "dosageInstruction.dose" in raw or "dose" in raw:
        dose_value = raw.get("dosageInstruction.dose") or raw.get("dose")
        dose_unit = raw.get("dosageInstruction.unit") or raw.get("unit")
        dosage["doseAndRate"] = [{
            "doseQuantity": build_quantity(dose_value, dose_unit)
        }]
    
    # Timing/frequency
    if "dosageInstruction.frequency" in raw or "frequency" in raw:
        freq = raw.get("dosageInstruction.frequency") or raw.get("frequency")
        dosage["timing"] = {
            "code": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/timing-abbr",
                    "code": str(freq).upper(),
                    "display": str(freq)
                }]
            }
        }
    
    # Route
    if "dosageInstruction.route" in raw or "route" in raw:
        route = raw.get("dosageInstruction.route") or raw.get("route")
        dosage["route"] = build_codeable_concept(
            route,
            "http://snomed.info/sct"
        )
    
    # Text instructions
    if "dosageInstruction.text" in raw or "instructions" in raw or "sig" in raw:
        text = raw.get("dosageInstruction.text") or raw.get("instructions") or raw.get("sig")
        dosage["text"] = str(text)
    
    return dosage


def build_dispense_request(raw: dict) -> dict:
    """Build dispense request structure"""
    dispense = {}
    
    if "dispenseRequest.quantity" in raw or "quantity" in raw:
        qty = raw.get("dispenseRequest.quantity") or raw.get("quantity")
        dispense["quantity"] = build_quantity(qty)
    
    if "dispenseRequest.start" in raw or "startdate" in raw:
        start = raw.get("dispenseRequest.start") or raw.get("startdate")
        dispense["validityPeriod"] = {
            "start": normalize_date(start)
        }
    
    if "dispenseRequest.end" in raw or "enddate" in raw:
        end = raw.get("dispenseRequest.end") or raw.get("enddate")
        if "validityPeriod" in dispense:
            dispense["validityPeriod"]["end"] = normalize_date(end)
        else:
            dispense["validityPeriod"] = {
                "end": normalize_date(end)
            }
    
    if "dispenseRequest.numberOfRepeatsAllowed" in raw or "refills" in raw:
        refills = raw.get("dispenseRequest.numberOfRepeatsAllowed") or raw.get("refills")
        dispense["numberOfRepeatsAllowed"] = int(refills) if refills else 0
    
    return dispense


def build_substitution(raw: dict) -> dict:
    """Build substitution structure"""
    return {
        "allowed": True,
        "type": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-substanceAdminSubstitution",
                "code": "E",
                "display": "equivalent"
            }]
        }
    }


def build_hospitalization(raw: dict) -> dict:
    """Build hospitalization structure"""
    hospitalization = {}
    
    if "hospitalization.admitSource" in raw:
        hospitalization["admitSource"] = build_codeable_concept(
            raw["hospitalization.admitSource"],
            "http://terminology.hl7.org/CodeSystem/admit-source"
        )
    
    if "hospitalization.dischargeDisposition" in raw:
        hospitalization["dischargeDisposition"] = build_codeable_concept(
            raw["hospitalization.dischargeDisposition"],
            "http://terminology.hl7.org/CodeSystem/discharge-disposition"
        )
    
    if "hospitalization.period" in raw:
        hospitalization["period"] = build_period(raw["hospitalization.period"])
    
    return hospitalization


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

    built_in, _, learned = load_mappings(resource_type)

    if not os.path.exists(path):
        return {
            "resource_type": resource_type,
            "built_in_mappings": built_in,
            "user_defined_mappings": {},
            "learned_mappings": learned,
            "total_built_in": len(built_in),
            "total_user_defined": 0,
            "total_learned": len(learned)
        }

    with open(path, "r", encoding="utf-8") as f:
        mappings = json.load(f)

    user_defined = mappings.get(resource_type, {}) if isinstance(mappings, dict) else {}
    
    # Process learned mappings to extract just the field mappings
    learned_simple = {}
    for field, mapping_info in learned.items():
        if isinstance(mapping_info, dict) and "fhir_field" in mapping_info:
            learned_simple[field] = mapping_info["fhir_field"]
        else:
            learned_simple[field] = mapping_info
    
    return {
        "resource_type": resource_type,
        "built_in_mappings": built_in,
        "user_defined_mappings": user_defined,
        "learned_mappings": learned_simple,
        "total_built_in": len(built_in),
        "total_user_defined": len(user_defined),
        "total_learned": len(learned_simple)
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