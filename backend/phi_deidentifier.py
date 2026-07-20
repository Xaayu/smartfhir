"""
PHI De-identifier — HIPAA Safe Harbor compliant.
Supports three modes: redact, mask, pseudonymize.
Works on individual FHIR resources and full Bundles.
"""

import copy
import re
from datetime import datetime
from typing import Literal

from fake_data_genrator import (
    fake_first_name, fake_last_name, fake_email,
    fake_phone, fake_city, fake_state, fake_zip,
    fake_date, fake_id, fake_url, fake_ip,
    fake_organization, mask_value, redact_value,
    fake_address
)

# De-identification mode type
DeidentifyMode = Literal["redact", "mask", "pseudonymize"]

# ── HIPAA Safe Harbor 18 identifiers ──────────────────────

PHI_PATTERNS = {
    "email": re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    ),
    "phone": re.compile(
        r'(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
    ),
    "ssn": re.compile(
        r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
    ),
    "ip": re.compile(
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ),
    "url": re.compile(
        r'https?://[^\s<>"{}|\\^`\[\]]+'
    ),
    "date_full": re.compile(
        r'\b\d{4}-\d{2}-\d{2}\b'
    ),
    "mrn": re.compile(
        r'\b(MRN|mrn|medical.?record.?number?)[\s:#-]*([A-Z0-9-]+)\b',
        re.IGNORECASE
    ),
}


class PHIDeidentifier:
    """
    HIPAA Safe Harbor PHI De-identifier.

    Safe Harbor method: remove all 18 PHI identifier categories.
    Three output modes:
      - redact:       replace with [REDACTED]
      - mask:         partially hide (J*** D**)
      - pseudonymize: replace with realistic fake data
    """

    def __init__(self, mode: DeidentifyMode = "pseudonymize"):
        self.mode = mode
        self.audit_log = []  # track what was changed
        self.entity_map = {}  # deterministic entity mapping for text replacement
        self.patient_gender = None  # store patient gender for consistent name generation
        self.is_90_plus = False  # track if patient is 90+ years old

    def _log(self, field: str, original: str, replacement: str, phi_type: str):
        """Log a PHI replacement for the audit report"""
        self.audit_log.append({
            "field": field,
            "phi_type": phi_type,
            "original_length": len(str(original)),
            "replaced_with": replacement if self.mode != "pseudonymize"
            else f"[FAKE_{phi_type.upper()}]",
            "action": self.mode
        })

    def _is_protected_schema_url(self, key: str, value: str) -> bool:
        """
        Check if a field is a protected schema URL that should not be modified.
        Protects HL7 FHIR StructureDefinition URLs and XML/HTML namespaces.
        """
        if key.endswith(".url") or key == "url":
            if isinstance(value, str):
                # Protect HL7 FHIR StructureDefinition URLs
                if "hl7.org/fhir/StructureDefinition" in value:
                    return True
                # Protect other standard FHIR schema URLs
                if "hl7.org/fhir" in value:
                    return True
        # Protect XML/HTML namespace attributes
        if key.startswith("xmlns") or key.endswith("xmlns"):
            return True
        return False

    def _is_custom_identifier_extension(self, extension: dict) -> bool:
        """
        Identify custom non-standard extensions that may contain PHI.
        Includes patient-employer, school tracking, and other organization-specific identifiers.
        """
        if not isinstance(extension, dict):
            return False
        
        url = extension.get("url", "")
        if not isinstance(url, str):
            return False
        
        # Skip protected standard HL7 extensions
        if self._is_protected_schema_url("url", url):
            return False
        
        # Identify custom extensions that may contain organization identifiers
        custom_patterns = [
            "employer",
            "school",
            "organization",
            "company",
            "workplace",
            "facility",
            "institution",
            "tracking",
            "patient-id",
            "external-id"
        ]
        
        url_lower = url.lower()
        for pattern in custom_patterns:
            if pattern in url_lower:
                return True
        
        return False

    def _apply(self, field: str, value: str, phi_type: str,
               pseudo_fn=None) -> str:
        """Apply de-identification based on mode"""
        if not value or str(value).strip() == "":
            return value

        original = str(value)

        if self.mode == "redact":
            result = redact_value(field)
        elif self.mode == "mask":
            result = mask_value(original)
        elif self.mode == "pseudonymize":
            result = pseudo_fn(original) if pseudo_fn else redact_value()
        else:
            result = redact_value()

        self._log(field, original, result, phi_type)
        return result

    # ── FHIR field handlers ──────────────────────────────

    def _deidentify_name(self, name_list: list, resource_id: str = "") -> list:
        """Handle FHIR HumanName array with deterministic entity mapping and gender consistency"""
        if not name_list:
            return name_list

        result = []
        for name_entry in name_list:
            new_entry = copy.deepcopy(name_entry)

            # Store original name parts for translation map
            original_family = new_entry.get("family", "")
            original_given = new_entry.get("given", [])

            if "family" in new_entry:
                fake_family = self._apply(
                    "name.family",
                    new_entry["family"],
                    "name",
                    lambda v: fake_last_name(v + resource_id)
                )
                new_entry["family"] = fake_family
                
                # Build translation map for family name
                if original_family:
                    entity_key = f"{resource_id}_name_{original_family.lower()}"
                    self.entity_map[entity_key] = fake_family

            if "given" in new_entry:
                fake_given_list = []
                for i, g in enumerate(new_entry["given"]):
                    # Use gender-aware name generation if patient gender is known
                    if self.patient_gender:
                        fake_given = self._apply(
                            "name.given",
                            g,
                            "name",
                            lambda v: fake_first_name(v + resource_id + self.patient_gender)
                        )
                    else:
                        fake_given = self._apply(
                            "name.given",
                            g,
                            "name",
                            lambda v: fake_first_name(v + resource_id)
                        )
                    fake_given_list.append(fake_given)
                    
                    # Build translation map for given name
                    entity_key = f"{resource_id}_name_{g.lower()}"
                    self.entity_map[entity_key] = fake_given
                
                new_entry["given"] = fake_given_list

            if "text" in new_entry:
                # Use gender-aware name generation for text field
                if self.patient_gender:
                    new_entry["text"] = self._apply(
                        "name.text",
                        new_entry["text"],
                        "name",
                        lambda v: fake_first_name(v + self.patient_gender) + " " + fake_last_name(v)
                    )
                else:
                    new_entry["text"] = self._apply(
                        "name.text",
                        new_entry["text"],
                        "name",
                        lambda v: fake_first_name(v) + " " + fake_last_name(v)
                    )

            result.append(new_entry)
        return result

    def _deidentify_telecom(self, telecom_list: list) -> list:
        """Handle FHIR ContactPoint array"""
        if not telecom_list:
            return telecom_list

        result = []
        for entry in telecom_list:
            new_entry = copy.deepcopy(entry)
            system = new_entry.get("system", "")
            value  = new_entry.get("value", "")

            if system == "email":
                new_entry["value"] = self._apply(
                    "telecom.email", value, "email", fake_email
                )
            elif system == "phone":
                new_entry["value"] = self._apply(
                    "telecom.phone", value, "phone", fake_phone
                )
            elif system == "fax":
                new_entry["value"] = self._apply(
                    "telecom.fax", value, "fax", fake_phone
                )
            elif value:
                new_entry["value"] = self._apply(
                    f"telecom.{system}", value, "contact", mask_value
                )

            result.append(new_entry)
        return result

    def _deidentify_address(self, address_list: list) -> list:
        """Handle FHIR Address array"""
        if not address_list:
            return address_list

        result = []
        for addr in address_list:
            new_addr = copy.deepcopy(addr)

            if "line" in new_addr:
                new_addr["line"] = [
                    self._apply(
                        "address.line", line, "address", fake_address
                    )
                    for line in new_addr["line"]
                ]

            if "text" in new_addr:
                new_addr["text"] = self._apply(
                    "address.text", new_addr["text"], "address", fake_address
                )

            if "city" in new_addr:
                new_addr["city"] = self._apply(
                    "address.city", new_addr["city"], "geographic", fake_city
                )

            if "state" in new_addr:
                new_addr["state"] = self._apply(
                    "address.state", new_addr["state"],
                    "geographic", fake_state
                )

            if "postalCode" in new_addr:
                # Safe Harbor: only first 3 digits
                new_addr["postalCode"] = self._apply(
                    "address.postalCode",
                    new_addr["postalCode"],
                    "geographic",
                    fake_zip
                )

            # Country is generally safe to keep
            # but redact if mode is redact
            if "country" in new_addr and self.mode == "redact":
                new_addr["country"] = redact_value()

            result.append(new_addr)
        return result

    def _calculate_age(self, birth_date: str) -> int:
        """Calculate patient age from birth date"""
        if not birth_date:
            return 0
        try:
            from datetime import datetime, date
            # Parse the date
            for fmt in ["%Y-%m-%d", "%Y-%m", "%Y"]:
                try:
                    parsed = datetime.strptime(str(birth_date)[:10], fmt)
                    age = (date.today() - parsed.date()).days // 365
                    return age
                except ValueError:
                    continue
        except Exception:
            pass
        return 0

    def _aggressive_date_redaction_90_plus(self, date_val: str, field: str) -> str:
        """
        Aggressively redact dates for patients 90+ years old.
        Removes day, month, and year from all timestamps to protect identity.
        """
        if not date_val:
            return date_val
        
        # For 90+ patients, completely redact all date components
        if self.mode == "redact":
            self._log(field, date_val, "null", "date_90_plus")
            return None
        elif self.mode == "mask":
            self._log(field, date_val, "[REDACTED_DATE]", "date_90_plus")
            return "[REDACTED_DATE]"
        else:  # pseudonymize
            self._log(field, date_val, ">89_AGGREGATED", "date_90_plus")
            return ">89"

    def _deidentify_date(self, date_val: str, field: str, birth_date: str = None) -> str:
        """
        HIPAA Safe Harbor date: keep year only.
        For patients 90+ years old, aggressively suppress all date components.
        """
        if not date_val:
            return date_val

        # If patient is 90+, apply aggressive date redaction for ALL dates
        if self.is_90_plus:
            return self._aggressive_date_redaction_90_plus(date_val, field)

        # Check if this is a birth date and patient is >89
        if field == "birthDate" and birth_date:
            age = self._calculate_age(birth_date)
            if age >= 90:
                # HIPAA: aggressively suppress year for ages 90+
                # Use null or explicit >89 category based on mode
                if self.mode == "redact":
                    self._log(field, date_val, "null", "date")
                    return None
                elif self.mode == "mask":
                    self._log(field, date_val, ">89", "date")
                    return ">89"
                else:  # pseudonymize
                    self._log(field, date_val, ">89_AGGREGATED", "date")
                    return ">89"

        return self._apply(field, date_val, "date", fake_date)

    def _deidentify_id(self, id_val: str, field: str) -> str:
        """De-identify patient/record IDs"""
        if not id_val:
            return id_val
        return self._apply(field, id_val, "identifier", fake_id)

    def _classify_identifier(self, identifier: dict) -> str:
        """Classify an identifier by semantic type using FHIR metadata."""
        if not isinstance(identifier, dict):
            return "unknown"

        candidates = []
        identifier_type = identifier.get("type") or {}
        if isinstance(identifier_type, dict):
            type_text = identifier_type.get("text")
            if isinstance(type_text, str) and type_text.strip():
                candidates.append(type_text.strip().lower())
            coding = identifier_type.get("coding") or []
            if isinstance(coding, list):
                for item in coding:
                    if isinstance(item, dict):
                        code = item.get("code")
                        if isinstance(code, str) and code.strip():
                            candidates.append(code.strip().lower())
                        display = item.get("display")
                        if isinstance(display, str) and display.strip():
                            candidates.append(display.strip().lower())

        system = identifier.get("system")
        if isinstance(system, str) and system.strip():
            candidates.append(system.strip().lower())

        for candidate in candidates:
            if any(token in candidate for token in ["ssn", "social security", "passport", "driver", "national", "employee", "insurance", "mrn", "medical record", "record number"]):
                if "ssn" in candidate or "social security" in candidate:
                    return "social_security"
                if "passport" in candidate:
                    return "passport"
                if "driver" in candidate:
                    return "driver_license"
                if "national" in candidate:
                    return "national_identifier"
                if "employee" in candidate:
                    return "employee_id"
                if "insurance" in candidate:
                    return "insurance_number"
                if "mrn" in candidate or "medical record" in candidate or "record number" in candidate:
                    return "medical_record_number"

        return "unknown"

    def _transform_identifier_value(self, identifier: dict) -> dict:
        """Transform only identifier.value based on its semantic category."""
        if not isinstance(identifier, dict):
            return identifier

        updated = copy.deepcopy(identifier)
        value = updated.get("value")
        if not value:
            return updated

        category = self._classify_identifier(updated)
        if category == "social_security":
            updated["value"] = None
        elif category in {"passport", "driver_license", "national_identifier"}:
            updated["value"] = None
        elif category in {"medical_record_number", "insurance_number", "employee_id"}:
            updated["value"] = self._apply(
                "identifier.value",
                str(value),
                "identifier",
                fake_id,
            )
        else:
            updated["value"] = self._apply(
                "identifier.value",
                str(value),
                "identifier",
                fake_id,
            )

        return updated

    def _scan_text_for_phi(self, text: str, field: str) -> str:
        """
        Scan free text fields (notes, comments) for PHI patterns.
        Removes emails, phones, SSNs, URLs, IPs found in text.
        """
        if not text:
            return text

        result = str(text)

        # Emails in text
        for match in PHI_PATTERNS["email"].findall(result):
            replacement = self._apply(
                field + "[text:email]", match, "email", fake_email
            )
            result = result.replace(match, replacement)

        # Phones in text
        for match in PHI_PATTERNS["phone"].findall(result):
            phone_str = "".join(match) if isinstance(match, tuple) else match
            replacement = self._apply(
                field + "[text:phone]", phone_str, "phone", fake_phone
            )
            result = result.replace(phone_str, replacement)

        # SSNs in text
        for match in PHI_PATTERNS["ssn"].findall(result):
            replacement = self._apply(
                field + "[text:ssn]", match, "ssn",
                lambda v: "[REDACTED-SSN]"
            )
            result = result.replace(match, replacement)

        # URLs in text
        for match in PHI_PATTERNS["url"].findall(result):
            replacement = self._apply(
                field + "[text:url]", match, "url", fake_url
            )
            result = result.replace(match, replacement)

        # IPs in text
        for match in PHI_PATTERNS["ip"].findall(result):
            replacement = self._apply(
                field + "[text:ip]", match, "ip", fake_ip
            )
            result = result.replace(match, replacement)

        return result

    def _apply_entity_translation_map(self, text: str, resource_id: str = "") -> str:
        """
        Apply the deterministic entity translation map to free text.
        This ensures that names found in structured fields are consistently
        replaced in unstructured text fields.
        """
        if not text or not self.entity_map:
            return text
        
        result = str(text)
        
        # Sort entities by length (longest first) to avoid partial replacements
        sorted_entities = sorted(
            [(key, value) for key, value in self.entity_map.items()],
            key=lambda x: len(x[0].split('_')[-1]),
            reverse=True
        )
        
        for entity_key, replacement in sorted_entities:
            # Extract the original name from the key
            parts = entity_key.split('_')
            if len(parts) >= 3 and parts[1] == "name":
                original_name = parts[-1]
                # Replace whole words only, case-insensitive
                pattern = r'\b' + re.escape(original_name) + r'\b'
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result
    
    def _remove_birth_years_from_text(self, text: str, original_birth_date: str = None) -> str:
        """
        Remove birth years from text when patient is >89 years old.
        This prevents age disclosure through narrative text.
        """
        if not text or not original_birth_date:
            return text
        
        # Check if patient is >89
        age = self._calculate_age(original_birth_date)
        if age <= 89:
            return text
        
        result = str(text)
        
        # Extract birth year from original date
        try:
            birth_year = original_birth_date[:4]
            if birth_year.isdigit():
                # Remove the specific birth year from text
                pattern = r'\b' + re.escape(birth_year) + r'\b'
                result = re.sub(pattern, ">89 years", result, flags=re.IGNORECASE)
                self._log(
                    "text.birth_year",
                    birth_year,
                    ">89 years",
                    "date"
                )
        except Exception:
            pass
        
        return result

    def _anonymize_clinicians(self, text: str, field: str) -> str:
        """
        Anonymize clinician references in text.
        Handles patterns like "Dr. [Name]", "Doctor [Name]", and authorString fields.
        """
        if not text:
            return text
        
        result = str(text)
        
        # Standard clinician patterns
        clinician_patterns = [
            # Dr. [First] [Last] or Doctor [First] [Last]
            r'(?:Dr\.?|Doctor)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)',
            # Dr. [Last] only
            r'(?:Dr\.?|Doctor)\s+([A-Z][a-z]+)',
            # [Name], MD
            r'([A-Z][a-z]+)\s+([A-Z][a-z]+),\s*(?:MD|DO|PhD)',
            # Physician/Provider references
            r'(?:physician|provider|practitioner|clinician|attending)\s+([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?',
        ]
        
        for pattern in clinician_patterns:
            for match in re.finditer(pattern, result, re.IGNORECASE):
                groups = match.groups()
                
                if self.mode == "redact":
                    replacement = "[PROVIDER]"
                elif self.mode == "mask":
                    replacement = "Dr. [REDACTED]"
                else:  # pseudonymize
                    # Generate consistent fake clinician name
                    if len(groups) >= 2:
                        fake_first = fake_first_name("clinician_" + groups[0])
                        fake_last = fake_last_name("clinician_" + groups[1])
                        replacement = f"Dr. {fake_first} {fake_last}"
                    else:
                        fake_last = fake_last_name("clinician_" + groups[0])
                        replacement = f"Dr. {fake_last}"
                
                result = result.replace(match.group(0), replacement)
                self._log(
                    f"{field}[clinician]",
                    match.group(0),
                    replacement,
                    "clinician"
                )
        
        return result

    def _enhanced_nlp_scan(self, text: str, field: str, resource_id: str = "", original_birth_date: str = None) -> str:
        """
        Enhanced NLP scanning for unstructured text fields with healthcare-trained NER patterns.
        Aggressively flags and pseudonymizes human names, relationships, employers, and neighborhoods.
        Now includes deterministic entity syncing from structured fields and gender consistency.
        """
        if not text:
            return text

        result = str(text)
        
        # Step 1: Anonymize clinician references first
        result = self._anonymize_clinicians(result, field)
        
        # Step 2: Remove birth years for elderly patients
        result = self._remove_birth_years_from_text(result, original_birth_date)
        
        word_count = len(result.split())

        # Apply enhanced scanning for narrative fields (notes, comments, etc.)
        if word_count > 3 or "note" in field.lower() or "text" in field.lower():
            # Healthcare-trained NER patterns for human names
            # These patterns are designed to catch names in clinical contexts
            
            # Pattern 1: Full names (First Last) with title prefixes
            # Skip Dr. patterns as they're handled by _anonymize_clinicians
            full_name_patterns = [
                r'(?:Mr\.?|Mrs\.?|Ms\.?|Miss|Prof\.?|Professor)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)',
                r'(?:Mr\.?|Mrs\.?|Ms\.?|Miss|Prof\.?|Professor)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)',  # Middle name
            ]
            
            for pattern in full_name_patterns:
                for match in re.finditer(pattern, result, re.IGNORECASE):
                    groups = match.groups()
                    if len(groups) >= 2:
                        first_name = groups[0]
                        last_name = groups[-1]
                        fake_first = self._get_gender_aware_replacement(first_name, "name", resource_id)
                        fake_last = self._get_deterministic_replacement(last_name, "name", resource_id)
                        replacement = f"{fake_first} {fake_last}"
                        result = result.replace(match.group(0), replacement)
                        self._log(
                            f"{field}[nlp:full_name]",
                            match.group(0),
                            replacement,
                            "name"
                        )
            
            # Pattern 2: Aggressive employer/organization detection
            employer_patterns = [
                r'(?:works at|employed by|employee of|works for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'(?:employer|company|organization|workplace)\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'(?:from|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|Corp|LLC|Ltd|Company|Corporation)',
            ]
            
            for pattern in employer_patterns:
                for match in re.finditer(pattern, result, re.IGNORECASE):
                    org_name = match.group(1)
                    fake_org = self._apply(
                        f"{field}[nlp:employer]",
                        org_name,
                        "organization",
                        fake_organization
                    )
                    result = result.replace(match.group(0), match.group(0).replace(org_name, fake_org))
            
            # Pattern 3: Neighborhood/borough/location detection
            neighborhood_patterns = [
                r'(?:lives in|resides in|located in|from)\s+([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?',
                r'(?:neighborhood|borough|area|district)\s*(?:of|in)?\s*[:\-]?\s*([A-Z][a-z]+)',
                # Specific known neighborhoods/boroughs
                r'\b(?:Manhattan|Brooklyn|Queens|Bronx|Staten Island|Brookline|Cambridge|Somerville|Brighton|Allston|Back Bay|South End|North End|Beacon Hill|Fenway|Jamaica Plain|Dorchester|Roxbury|West Roxbury|Hyde Park|Charlestown|East Boston)\b',
            ]
            
            for pattern in neighborhood_patterns:
                for match in re.finditer(pattern, result, re.IGNORECASE):
                    location = match.group(1) if match.groups() else match.group(0)
                    fake_location = self._apply(
                        f"{field}[nlp:neighborhood]",
                        location,
                        "geographic",
                        fake_city
                    )
                    result = result.replace(match.group(0), match.group(0).replace(location, fake_location))
            
            # Pattern 4: Contextual relationship patterns (husband, wife, etc.)
            # Skip name replacement - let translation map handle it consistently
            # These patterns are kept for context detection but don't replace names
            relationship_patterns = [
                r'(?:husband|wife|spouse|partner|father|mother|son|daughter|brother|sister|grandfather|grandmother|uncle|aunt|cousin|nephew|niece|grandchild|grandson|granddaughter)\s+([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?',
                r'(?:his|her|their)\s+(?:husband|wife|spouse|partner|father|mother|son|daughter|brother|sister)\s+([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?',
            ]
            
            # Pattern 5: Action-based name references (called, spoke with, etc.)
            # Skip name replacement - let translation map handle it consistently
            action_patterns = [
                r'(?:called|spoke with|contacted|reached|phoned|emailed|messaged|texted)\s+(?:to\s+)?([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?',
                r'(?:referred by|seen by|treated by|examined by)\s+([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?',
                r'(?:patient|subject|client)\s+([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?',
            ]
            
            # Pattern 6: Aggressive proper name detection with context awareness
            # Skip name replacement - let translation map handle it consistently
            # This pattern is kept for context detection but doesn't replace names

            # Enhanced patterns for contextual relationships
            # Only handle phone patterns, skip name patterns (translation map handles those)
            contextual_patterns = {
                # "at [Phone]" patterns
                r'(?:at|call|phone|dial)\s+(\+?1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})': lambda m: self._apply(field + "[nlp:phone]", m.group(1), "phone", fake_phone),
            }

            # Apply contextual pattern replacements
            for pattern, replacement_fn in contextual_patterns.items():
                for match in re.finditer(pattern, result, re.IGNORECASE):
                    try:
                        replacement = replacement_fn(match)
                        result = result.replace(match.group(0), replacement)
                    except Exception:
                        pass

            # Enhanced regex patterns for hidden identifiers
            enhanced_patterns = {
                # Hidden phone numbers in various formats (more aggressive)
                r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b': lambda m: self._apply(field + "[nlp:hidden_phone]", m.group(0), "phone", fake_phone),
                # Phone numbers without area code
                r'\b\d{3}[-.\s]?\d{4}\b': lambda m: self._apply(field + "[nlp:phone_short]", m.group(0), "phone", fake_phone),
                # Medical record numbers in text
                r'\b(?:MRN|medical record|patient ID|ID):\s*([A-Z0-9-]+)': lambda m: self._apply(field + "[nlp:mrn]", m.group(1), "identifier", fake_id),
                # Social Security numbers
                r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b': lambda m: "[REDACTED-SSN]",
                # URLs and domains
                r'\b(?:https?:\/\/|www\.)[^\s<>"{}|\\^`\[\]]+\.[a-zA-Z]{2,}\b': lambda m: self._apply(field + "[nlp:url]", m.group(0), "url", fake_url),
                # Email addresses (more aggressive pattern)
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': lambda m: self._apply(field + "[nlp:email]", m.group(0), "email", fake_email),
            }

            # Apply enhanced pattern replacements
            for pattern, replacement_fn in enhanced_patterns.items():
                for match in re.finditer(pattern, result):
                    try:
                        replacement = replacement_fn(match)
                        result = result.replace(match.group(0), replacement)
                    except Exception:
                        pass

        # Fall back to basic PHI pattern scanning
        result = self._scan_text_for_phi(result, field)
        
        # Step 3: Apply deterministic entity translation map LAST
        # This ensures names from structured fields replace any NLP-detected names
        result = self._apply_entity_translation_map(result, resource_id)

        return result

    def _get_gender_aware_replacement(self, original: str, phi_type: str, resource_id: str = "") -> str:
        """
        Get deterministic replacement for an entity with gender awareness.
        Ensures consistent gender-appropriate names across the resource.
        """
        # Create a deterministic key for this entity
        entity_key = f"{resource_id}_{phi_type}_{original.lower()}"
        
        # Check if we already have a mapping for this entity
        if entity_key in self.entity_map:
            return self.entity_map[entity_key]
        
        # Generate new deterministic replacement
        if phi_type == "name":
            # Use gender-aware name generation if patient gender is known
            if self.patient_gender:
                replacement = fake_first_name(original + resource_id + self.patient_gender)
            else:
                replacement = fake_first_name(original + resource_id)
        else:
            # For other types, use the existing apply logic
            replacement = self._apply(f"entity_map.{phi_type}", original, phi_type, None)
        
        # Store the mapping for future use
        self.entity_map[entity_key] = replacement
        
        return replacement

    def _get_deterministic_replacement(self, original: str, phi_type: str, resource_id: str = "") -> str:
        """
        Get deterministic replacement for an entity to ensure consistency
        across structured data and unstructured text.
        """
        # Create a deterministic key for this entity
        entity_key = f"{resource_id}_{phi_type}_{original.lower()}"
        
        # Check if we already have a mapping for this entity
        if entity_key in self.entity_map:
            return self.entity_map[entity_key]
        
        # Generate new deterministic replacement
        if phi_type == "name":
            # Split name into parts and replace deterministically
            parts = original.split()
            if len(parts) >= 2:
                fake_parts = [
                    fake_first_name(parts[0] + resource_id),
                    fake_last_name(parts[-1] + resource_id)
                ]
                replacement = " ".join(fake_parts)
            else:
                replacement = fake_first_name(original + resource_id)
        else:
            # For other types, use the existing apply logic
            replacement = self._apply(f"entity_map.{phi_type}", original, phi_type, None)
        
        # Store the mapping for future use
        self.entity_map[entity_key] = replacement
        
        return replacement

    def _handle_extensions(self, obj: dict, resource_id: str = "", original_birth_date: str = None):
        """
        Handle primitive extensions (_* keys) and complex extensions recursively.
        Primitive extensions mirror the de-identification of their parent field.
        Complex extensions are parsed for nested PHI.
        Custom identifier extensions are aggressively pseudonymized.
        """
        if not isinstance(obj, dict):
            return

        # Track primitive extensions to mirror transformations
        primitive_extensions = {}
        complex_extensions = []

        for key, value in obj.items():
            # Detect primitive extensions (underscore-prefixed keys)
            if key.startswith("_") and len(key) > 1:
                parent_key = key[1:]  # Remove underscore
                primitive_extensions[key] = (parent_key, value)
            # Detect complex extension arrays
            elif key == "extension" and isinstance(value, list):
                complex_extensions.extend(value)

        # Apply mirroring for primitive extensions with key-mirroring heuristic
        for ext_key, (parent_key, ext_value) in primitive_extensions.items():
            if parent_key in obj:
                parent_value = obj[parent_key]
                
                # Handle primitive extension with nested extension array
                if isinstance(ext_value, dict) and "extension" in ext_value:
                    # Recursively process nested extensions in primitive extension
                    for nested_ext in ext_value["extension"]:
                        if isinstance(nested_ext, dict):
                            # Handle nested timestamp values (valueDateTime, valueInstant, etc.)
                            for value_key in ["valueDateTime", "valueInstant", "valueDate", "valueTime"]:
                                if value_key in nested_ext:
                                    # Apply the same date transformation as parent field
                                    if parent_key == "birthDate":
                                        # Check if parent birthDate was set to >89
                                        if parent_value == ">89":
                                            # Apply same >89 logic to extension timestamp
                                            if self.mode == "redact":
                                                nested_ext[value_key] = None
                                            elif self.mode == "mask":
                                                nested_ext[value_key] = ">89"
                                            else:  # pseudonymize
                                                nested_ext[value_key] = ">89"
                                            self._log(
                                                f"_{parent_key}.extension.{value_key}",
                                                str(nested_ext.get(value_key, "")),
                                                str(nested_ext[value_key]),
                                                "date"
                                            )
                                        else:
                                            nested_ext[value_key] = self._deidentify_date(
                                                nested_ext[value_key],
                                                f"_{parent_key}.extension.{value_key}",
                                                original_birth_date
                                            )
                                    else:
                                        nested_ext[value_key] = self._deidentify_date(
                                            nested_ext[value_key],
                                            f"_{parent_key}.extension.{value_key}"
                                        )
                                    self._log(
                                        f"primitive_extension.{ext_key}.{value_key}",
                                        str(nested_ext.get(value_key, "")),
                                        str(nested_ext[value_key]),
                                        "primitive_extension_timestamp"
                                    )
                            # Handle other value types
                            for value_key in ["valueString", "valueUri", "valueUrl"]:
                                if value_key in nested_ext:
                                    nested_ext[value_key] = self._scan_text_for_phi(
                                        nested_ext[value_key],
                                        f"_{parent_key}.extension.{value_key}"
                                    )
                
                # Handle primitive extension with direct value field
                elif isinstance(ext_value, dict) and "value" in ext_value:
                    # Mirror the transformation applied to parent field
                    obj[ext_key]["value"] = parent_value
                    self._log(
                        f"extension.{ext_key}",
                        str(ext_value.get("value", "")),
                        str(parent_value),
                        "primitive_extension"
                    )
                elif isinstance(ext_value, str):
                    # Direct string primitive extension
                    obj[ext_key] = parent_value
                    self._log(
                        f"extension.{ext_key}",
                        ext_value,
                        parent_value,
                        "primitive_extension"
                    )

        # Process complex extensions recursively
        for ext in complex_extensions:
            if isinstance(ext, dict):
                # Check if this is a custom identifier extension that needs aggressive pseudonymization
                if self._is_custom_identifier_extension(ext):
                    # Aggressively pseudonymize valueString and valueReference fields
                    if "valueString" in ext:
                        original_value = ext["valueString"]
                        ext["valueString"] = self._apply(
                            "extension.custom_identifier.valueString",
                            original_value,
                            "organization",
                            fake_organization
                        )
                    if "valueReference" in ext and isinstance(ext["valueReference"], dict):
                        ref_data = ext["valueReference"]
                        if "display" in ref_data:
                            original_display = ref_data["display"]
                            ref_data["display"] = self._apply(
                                "extension.custom_identifier.valueReference.display",
                                original_display,
                                "organization",
                                fake_organization
                            )
                        if "reference" in ref_data:
                            # Pseudonymize the reference ID
                            original_ref = ref_data["reference"]
                            ref_data["reference"] = self._apply(
                                "extension.custom_identifier.valueReference.reference",
                                original_ref,
                                "identifier",
                                fake_id
                            )
                
                # Handle valueAddress (e.g., patient-birthPlace)
                if "valueAddress" in ext:
                    address_data = ext["valueAddress"]
                    if isinstance(address_data, dict):
                        # De-identify address fields
                        if "city" in address_data:
                            address_data["city"] = self._apply(
                                "extension.valueAddress.city",
                                address_data["city"],
                                "geographic",
                                fake_city
                            )
                        if "state" in address_data:
                            address_data["state"] = self._apply(
                                "extension.valueAddress.state",
                                address_data["state"],
                                "geographic",
                                fake_state
                            )
                        if "postalCode" in address_data:
                            address_data["postalCode"] = self._apply(
                                "extension.valueAddress.postalCode",
                                address_data["postalCode"],
                                "geographic",
                                fake_zip
                            )
                        if "country" in address_data and self.mode == "redact":
                            address_data["country"] = redact_value()

                # Handle valueString (may contain names or other PHI)
                if "valueString" in ext:
                    ext["valueString"] = self._scan_text_for_phi(
                        ext["valueString"],
                        "extension.valueString"
                    )

                # Handle valueContact (contact information in extensions)
                if "valueContact" in ext and isinstance(ext["valueContact"], dict):
                    contact_data = ext["valueContact"]
                    if "name" in contact_data:
                        contact_data["name"] = self._deidentify_name(
                            [contact_data["name"]], resource_id
                        )[0]
                    if "telecom" in contact_data:
                        contact_data["telecom"] = self._deidentify_telecom(
                            contact_data["telecom"]
                        )
                    if "address" in contact_data:
                        contact_data["address"] = self._deidentify_address(
                            [contact_data["address"]]
                        )[0]

                # Recursively process nested extensions
                if "extension" in ext:
                    self._handle_extensions(ext, resource_id, original_birth_date)

    def _sanitize_value_by_context(self, value: str, field_path: str, resource_id: str = "") -> str:
        """Apply context-aware sanitization for deeply nested string values."""
        if not isinstance(value, str):
            return value

        normalized_path = field_path.lower()

        # Preserve schema and structural values.
        if field_path.split(".")[-1] in {"resourceType", "status", "gender", "use", "system", "code"}:
            return value

        if "identifier" in normalized_path and normalized_path.endswith(".value"):
            return self._deidentify_id(value, field_path)

        if "text" in normalized_path or "note" in normalized_path or normalized_path.endswith(".div"):
            return self._enhanced_nlp_scan(value, field_path, resource_id, None)

        return self._scan_text_for_phi(value, field_path)

    def _recursive_crawl(self, obj: dict, path: str = "", resource_id: str = ""):
        """
        Recursively crawl through FHIR structure to find PHI at any depth.
        Handles nested arrays, objects, and applies appropriate de-identification.
        Protects schema URLs and XML/HTML namespaces from modification.
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key

                # Skip already processed top-level fields
                if path == "" and key in ["id", "name", "birthDate", "telecom", "address",
                                           "deceasedDateTime", "photo", "identifier", "contact", "extension"]:
                    continue

                # Skip protected schema URLs and namespaces
                if self._is_protected_schema_url(key, value):
                    continue

                if isinstance(value, str):
                    obj[key] = self._sanitize_value_by_context(value, current_path, resource_id)
                elif isinstance(value, dict):
                    # Recursively process nested objects
                    self._recursive_crawl(value, current_path, resource_id)
                elif isinstance(value, list):
                    # Process each item in array
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            # Handle nested HumanName objects
                            if key == "name" or (key.endswith("name") and "family" in item):
                                item = self._deidentify_name([item], resource_id)[0]
                                value[i] = item
                            # Handle nested Address objects
                            elif key == "address" or (key.endswith("address") and "city" in item):
                                item = self._deidentify_address([item])[0]
                                value[i] = item
                            # Handle nested ContactPoint objects
                            elif key == "telecom" or (key.endswith("telecom") and "system" in item):
                                item = self._deidentify_telecom([item])[0]
                                value[i] = item
                            elif key == "identifier":
                                if item.get("value"):
                                    item["value"] = self._sanitize_value_by_context(
                                        item["value"], f"{current_path}[{i}].value", resource_id
                                    )
                                if item.get("system"):
                                    item["system"] = self._sanitize_value_by_context(
                                        item["system"], f"{current_path}[{i}].system", resource_id
                                    )
                                self._recursive_crawl(item, f"{current_path}[{i}]", resource_id)
                                value[i] = item
                            else:
                                self._recursive_crawl(item, f"{current_path}[{i}]", resource_id)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, dict):
                    self._recursive_crawl(item, f"{path}[{i}]", resource_id)

    # ── Resource-level de-identifiers ───────────────────

    def deidentify_patient(self, resource: dict) -> dict:
        """De-identify a FHIR Patient resource"""
        r = copy.deepcopy(resource)
        
        # Store original birth date for age calculation
        original_birth_date = r.get("birthDate")
        
        # Store patient gender for consistent name generation
        self.patient_gender = r.get("gender", "")
        
        # Check if patient is 90+ years old for aggressive date redaction
        if original_birth_date:
            age = self._calculate_age(original_birth_date)
            if age >= 90:
                self.is_90_plus = True

        # ID
        if r.get("id"):
            r["id"] = self._deidentify_id(r["id"], "id")

        # Name
        if r.get("name"):
            r["name"] = self._deidentify_name(r["name"], r.get("id", ""))

        # Birth date — keep year only (Safe Harbor), with >89 aggregation
        if r.get("birthDate"):
            r["birthDate"] = self._deidentify_date(r["birthDate"], "birthDate", original_birth_date)

        # Telecom (phone, email, fax)
        if r.get("telecom"):
            r["telecom"] = self._deidentify_telecom(r["telecom"])

        # Address
        if r.get("address"):
            r["address"] = self._deidentify_address(r["address"])

        # Deceased date
        if r.get("deceasedDateTime"):
            r["deceasedDateTime"] = self._deidentify_date(
                r["deceasedDateTime"], "deceasedDateTime", original_birth_date
            )

        # Photo — always remove
        if "photo" in r:
            del r["photo"]
            self._log("photo", "[binary]", "[REMOVED]", "biometric")

        # Identifiers (MRN, SSN, etc)
        if r.get("identifier"):
            for idx, ident in enumerate(r["identifier"]):
                if isinstance(ident, dict):
                    r["identifier"][idx] = self._transform_identifier_value(ident)

        # Secondary contacts (emergency contacts, family members)
        if r.get("contact"):
            for contact in r["contact"]:
                # De-identify contact names
                if contact.get("name"):
                    contact["name"] = self._deidentify_name([contact["name"]], r.get("id", ""))[0]
                # De-identify contact telecom
                if contact.get("telecom"):
                    contact["telecom"] = self._deidentify_telecom(contact["telecom"])
                # De-identify contact address
                if contact.get("address"):
                    contact["address"] = self._deidentify_address([contact["address"]])[0]
                # De-identify organization
                if contact.get("organization", {}).get("display"):
                    contact["organization"]["display"] = self._apply(
                        "contact.organization",
                        contact["organization"]["display"],
                        "organization",
                        fake_organization
                    )
                # De-identify contact identifiers
                if contact.get("identifier"):
                    for ident in contact["identifier"]:
                        if ident.get("value"):
                            ident["value"] = self._apply(
                                "contact.identifier.value",
                                ident["value"],
                                "identifier",
                                fake_id
                            )

        # Handle Patient.link array (links to other patient resources)
        if r.get("link"):
            for link in r["link"]:
                # De-identify other patient references
                if link.get("other", {}).get("reference"):
                    original_ref = link["other"]["reference"]
                    if original_ref.startswith("Patient/"):
                        patient_id = original_ref.replace("Patient/", "")
                        new_id = fake_id(patient_id)
                        link["other"]["reference"] = f"Patient/{new_id}"
                        self._log(
                            "link.other.reference",
                            original_ref,
                            link["other"]["reference"],
                            "identifier"
                        )

        # Handle general practitioner references
        if r.get("generalPractitioner"):
            for gp in r["generalPractitioner"]:
                if gp.get("display"):
                    gp["display"] = self._apply(
                        "generalPractitioner.display",
                        gp["display"],
                        "name",
                        fake_id
                    )
                if gp.get("reference"):
                    original_ref = gp["reference"]
                    if original_ref.startswith("Practitioner/"):
                        new_id = fake_id(original_ref)
                        gp["reference"] = f"Practitioner/{new_id}"
                        self._log(
                            "generalPractitioner.reference",
                            original_ref,
                            gp["reference"],
                            "identifier"
                        )

        # Handle managing organization
        if r.get("managingOrganization", {}).get("display"):
            r["managingOrganization"]["display"] = self._apply(
                "managingOrganization.display",
                r["managingOrganization"]["display"],
                "organization",
                fake_organization
            )

        # Handle meta timestamps (aggressive redaction for 90+ patients)
        if r.get("meta"):
            if r["meta"].get("lastUpdated"):
                r["meta"]["lastUpdated"] = self._deidentify_date(
                    r["meta"]["lastUpdated"],
                    "meta.lastUpdated",
                    original_birth_date
                )

        # Handle primitive extensions and complex extensions recursively
        self._handle_extensions(r, r.get("id", ""), original_birth_date)

        # Recursive crawl for deeply nested PHI
        self._recursive_crawl(r, "", r.get("id", ""))

        # Scan notes/text with NLP-enhanced PHI detection
        if r.get("text", {}).get("div"):
            r["text"]["div"] = self._enhanced_nlp_scan(
                r["text"]["div"], "text.div", r.get("id", ""), original_birth_date
            )

        return r

    def deidentify_observation(self, resource: dict) -> dict:
        """De-identify a FHIR Observation resource"""
        r = copy.deepcopy(resource)
        resource_id = r.get("id", "")

        # Remove direct patient reference ID
        if r.get("subject", {}).get("reference"):
            original_ref = r["subject"]["reference"]
            patient_id = original_ref.replace("Patient/", "")
            new_id = fake_id(patient_id)
            r["subject"]["reference"] = f"Patient/{new_id}"
            self._log(
                "subject.reference", original_ref,
                r["subject"]["reference"], "identifier"
            )

        # Effective date — keep year only
        if r.get("effectiveDateTime"):
            r["effectiveDateTime"] = self._deidentify_date(
                r["effectiveDateTime"], "effectiveDateTime"
            )

        # Performer names and related entities
        if r.get("performer"):
            for perf in r["performer"]:
                if perf.get("display"):
                    perf["display"] = self._apply(
                        "performer.display",
                        perf["display"],
                        "name",
                        fake_id
                    )
                # Handle nested practitioner references
                if perf.get("reference", "").startswith("Practitioner/"):
                    perf["reference"] = f"Practitioner/{fake_id(perf['reference'])}"

        # Handle extensions recursively
        self._handle_extensions(r, resource_id)

        # Recursive crawl for deeply nested PHI
        self._recursive_crawl(r, "", resource_id)

        # Scan notes with enhanced NLP
        if r.get("note"):
            for note in r["note"]:
                if note.get("text"):
                    note["text"] = self._enhanced_nlp_scan(
                        note["text"], "note.text", resource_id, None
                    )

        return r

    def deidentify_condition(self, resource: dict) -> dict:
        """De-identify a FHIR Condition resource"""
        r = copy.deepcopy(resource)
        resource_id = r.get("id", "")

        # Patient reference
        if r.get("subject", {}).get("reference"):
            original_ref = r["subject"]["reference"]
            patient_id = original_ref.replace("Patient/", "")
            new_id = fake_id(patient_id)
            r["subject"]["reference"] = f"Patient/{new_id}"
            self._log(
                "subject.reference", original_ref,
                r["subject"]["reference"], "identifier"
            )

        # Dates
        for date_field in ["onsetDateTime", "recordedDate", "abatementDateTime"]:
            if r.get(date_field):
                r[date_field] = self._deidentify_date(r[date_field], date_field)

        # Recorder / asserter names and related entities
        for name_field in ["recorder", "asserter"]:
            if r.get(name_field, {}).get("display"):
                r[name_field]["display"] = self._apply(
                    f"{name_field}.display",
                    r[name_field]["display"],
                    "name",
                    fake_id
                )
            # Handle practitioner references
            if r.get(name_field, {}).get("reference", "").startswith("Practitioner/"):
                r[name_field]["reference"] = f"Practitioner/{fake_id(r[name_field]['reference'])}"

        # Handle extensions recursively
        self._handle_extensions(r, resource_id)

        # Recursive crawl for deeply nested PHI
        self._recursive_crawl(r, "", resource_id)

        # Scan notes with enhanced NLP
        if r.get("note"):
            for note in r["note"]:
                if note.get("text"):
                    note["text"] = self._enhanced_nlp_scan(
                        note["text"], "note.text", resource_id, None
                    )

        return r

    def deidentify_encounter(self, resource: dict) -> dict:
        """De-identify a FHIR Encounter resource"""
        r = copy.deepcopy(resource)
        resource_id = r.get("id", "")

        # Patient reference
        if r.get("subject", {}).get("reference"):
            original_ref = r["subject"]["reference"]
            patient_id = original_ref.replace("Patient/", "")
            new_id = fake_id(patient_id)
            r["subject"]["reference"] = f"Patient/{new_id}"
            self._log(
                "subject.reference", original_ref,
                r["subject"]["reference"], "identifier"
            )

        # Period dates — keep year only
        if r.get("period"):
            if r["period"].get("start"):
                r["period"]["start"] = self._deidentify_date(
                    r["period"]["start"], "period.start"
                )
            if r["period"].get("end"):
                r["period"]["end"] = self._deidentify_date(
                    r["period"]["end"], "period.end"
                )

        # Participant names (doctors) and related entities
        if r.get("participant"):
            for part in r["participant"]:
                if part.get("individual", {}).get("display"):
                    part["individual"]["display"] = self._apply(
                        "participant.individual",
                        part["individual"]["display"],
                        "name",
                        fake_id
                    )
                # Handle practitioner references
                if part.get("individual", {}).get("reference", "").startswith("Practitioner/"):
                    part["individual"]["reference"] = f"Practitioner/{fake_id(part['individual']['reference'])}"
                # Handle related person references
                if part.get("individual", {}).get("reference", "").startswith("RelatedPerson/"):
                    part["individual"]["reference"] = f"RelatedPerson/{fake_id(part['individual']['reference'])}"

        # Location names and geographic data
        if r.get("location"):
            for loc in r["location"]:
                if loc.get("location", {}).get("display"):
                    loc["location"]["display"] = self._apply(
                        "location.display",
                        loc["location"]["display"],
                        "location",
                        lambda v: f"Ward-{fake_id(v)[-4:]}"
                    )
                # Handle location address
                if loc.get("location", {}).get("address"):
                    loc["location"]["address"] = self._deidentify_address([loc["location"]["address"]])[0]

        # Handle extensions recursively
        self._handle_extensions(r, resource_id)

        # Recursive crawl for deeply nested PHI
        self._recursive_crawl(r, "", resource_id)

        # Scan notes with enhanced NLP
        if r.get("note"):
            for note in r["note"]:
                if note.get("text"):
                    note["text"] = self._enhanced_nlp_scan(
                        note["text"], "note.text", resource_id, None
                    )

        return r

    def deidentify_medication_request(self, resource: dict) -> dict:
        """De-identify a FHIR MedicationRequest resource"""
        r = copy.deepcopy(resource)
        resource_id = r.get("id", "")

        # Patient reference
        if r.get("subject", {}).get("reference"):
            original_ref = r["subject"]["reference"]
            patient_id = original_ref.replace("Patient/", "")
            new_id = fake_id(patient_id)
            r["subject"]["reference"] = f"Patient/{new_id}"
            self._log(
                "subject.reference", original_ref,
                r["subject"]["reference"], "identifier"
            )

        # Requester (prescriber) and related entities
        if r.get("requester", {}).get("display"):
            r["requester"]["display"] = self._apply(
                "requester.display",
                r["requester"]["display"],
                "name",
                fake_id
            )
        # Handle practitioner references
        if r.get("requester", {}).get("reference", "").startswith("Practitioner/"):
            r["requester"]["reference"] = f"Practitioner/{fake_id(r['requester']['reference'])}"

        # Dispense validity period
        if r.get("dispenseRequest", {}).get("validityPeriod"):
            vp = r["dispenseRequest"]["validityPeriod"]
            if vp.get("start"):
                vp["start"] = self._deidentify_date(vp["start"], "dispense.start")
            if vp.get("end"):
                vp["end"] = self._deidentify_date(vp["end"], "dispense.end")

        # Handle extensions recursively
        self._handle_extensions(r, resource_id)

        # Recursive crawl for deeply nested PHI
        self._recursive_crawl(r, "", resource_id)

        # Scan notes with enhanced NLP
        if r.get("note"):
            for note in r["note"]:
                if note.get("text"):
                    note["text"] = self._enhanced_nlp_scan(
                        note["text"], "note.text", resource_id, None
                    )

        return r

    # ── Main public methods ──────────────────────────────

    def deidentify_resource(self, resource: dict) -> dict:
        """Route to correct de-identifier based on resourceType"""
        resource_type = resource.get("resourceType", "")

        handlers = {
            "Patient":           self.deidentify_patient,
            "Observation":       self.deidentify_observation,
            "Condition":         self.deidentify_condition,
            "Encounter":         self.deidentify_encounter,
            "MedicationRequest": self.deidentify_medication_request,
        }

        handler = handlers.get(resource_type)
        if handler:
            return handler(resource)

        # Unknown resource — scan all string values for PHI patterns
        return self._scan_unknown_resource(resource)

    def _scan_unknown_resource(self, resource: dict) -> dict:
        """
        For unknown resource types — scan all string
        values for PHI patterns as a safety net.
        """
        r = copy.deepcopy(resource)
        self._deep_scan(r, "")
        return r

    def _deep_scan(self, obj, path: str):
        """Recursively scan all string values for PHI"""
        if isinstance(obj, dict):
            for key, val in obj.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(val, str):
                    scanned = self._scan_text_for_phi(val, current_path)
                    obj[key] = scanned
                elif isinstance(val, (dict, list)):
                    self._deep_scan(val, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self._deep_scan(item, f"{path}[{i}]")

    def deidentify_bundle(self, bundle: dict) -> dict:
        """De-identify an entire FHIR Bundle"""
        b = copy.deepcopy(bundle)

        if b.get("resourceType") != "Bundle":
            raise ValueError("Input must be a FHIR Bundle")

        entries = b.get("entry", [])
        new_entries = []

        for entry in entries:
            resource = entry.get("resource", {})
            if resource:
                entry["resource"] = self.deidentify_resource(resource)
                # Also update fullUrl if it contains patient ID
                if entry.get("fullUrl"):
                    entry["fullUrl"] = self._apply(
                        "entry.fullUrl",
                        entry["fullUrl"],
                        "identifier",
                        fake_url
                    )
            new_entries.append(entry)

        b["entry"] = new_entries
        return b

    def get_audit_report(self) -> dict:
        """Generate audit report of all PHI found and replaced"""
        phi_types = {}
        for log in self.audit_log:
            t = log["phi_type"]
            phi_types[t] = phi_types.get(t, 0) + 1

        fields_cleaned = list(set(log["field"] for log in self.audit_log))

        return {
            "phi_items_found": len(self.audit_log),
            "phi_by_type": phi_types,
            "fields_cleaned": sorted(fields_cleaned),
            "mode": self.mode,
            "hipaa_safe_harbor_compliant": True,
            "standard": "HIPAA Safe Harbor (45 CFR §164.514(b))",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "details": self.audit_log
        }


def deidentify(
    resource: dict,
    mode: DeidentifyMode = "pseudonymize",
    include_audit: bool = True,
    policy: dict | None = None,
) -> dict:
    """
    Main entry point for single resource de-identification.

    Args:
        resource:      FHIR resource dict
        mode:          redact | mask | pseudonymize
        include_audit: include audit report in response

    Returns:
        deidentified resource + optional audit report
    """
    engine = PHIDeidentifier(mode=mode)
    result = engine.deidentify_resource(resource)

    if policy is not None:
        from policy_engine.compiler import compile_policy
        from policy_engine.semantic_engine import apply_semantic_policy

        compiled = compile_policy(policy)
        if any(compiled["actions"].get(category, "KEEP") != "KEEP" for category in ["patient_name", "government_identifier", "address", "birth_date", "free_text"]):
            result = apply_semantic_policy(policy, resource, mode=mode)

    response = {"deidentified_resource": result}

    if include_audit:
        response["audit_report"] = engine.get_audit_report()

    return response


def deidentify_bundle(
    bundle: dict,
    mode: DeidentifyMode = "pseudonymize",
    include_audit: bool = True,
    policy: dict | None = None,
) -> dict:
    """
    Main entry point for Bundle de-identification.
    """
    engine = PHIDeidentifier(mode=mode)
    result = engine.deidentify_bundle(bundle)
    if policy is not None:
        from policy_engine.compiler import compile_policy
        from policy_engine.semantic_engine import apply_semantic_policy

        compiled = compile_policy(policy)
        if any(compiled["actions"].get(category, "KEEP") != "KEEP" for category in ["patient_name", "government_identifier", "address", "birth_date", "free_text"]):
            if isinstance(result.get("entry"), list):
                for entry in result["entry"]:
                    resource = entry.get("resource")
                    if isinstance(resource, dict):
                        entry["resource"] = apply_semantic_policy(policy, resource, mode=mode)

    response = {
        "deidentified_bundle": result,
        "total_resources": len(bundle.get("entry", []))
    }

    if include_audit:
        response["audit_report"] = engine.get_audit_report()

    return response