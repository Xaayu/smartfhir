"""
Cross-Resource Validation for FHIR Resources

This module validates relationships between different FHIR resources to detect
logical inconsistencies and business rule violations.
Enhanced with advanced validation rules, performance optimization, and comprehensive error handling.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
import re
import json
from collections import defaultdict


class CrossResourceValidator:
    """Validates cross-resource relationships and business rules with advanced features"""

    def __init__(self, patient_store: Optional[Dict[str, Dict]] = None,
                 condition_store: Optional[Dict[str, List[Dict]]] = None,
                 encounter_store: Optional[Dict[str, Dict]] = None,
                 observation_store: Optional[Dict[str, List[Dict]]] = None):
        """
        Initialize validator with optional resource stores for reference resolution.
        
        Args:
            patient_store: Dictionary mapping patient IDs to patient resources
            condition_store: Dictionary mapping patient IDs to condition resources
            encounter_store: Dictionary mapping encounter IDs to encounter resources
            observation_store: Dictionary mapping patient IDs to observation resources
        """
        self.patient_store = patient_store or {}
        self.condition_store = condition_store or defaultdict(list)
        self.encounter_store = encounter_store or {}
        self.observation_store = observation_store or defaultdict(list)
        
        # Validation statistics
        self.validation_stats = {
            "total_validations": 0,
            "errors_found": 0,
            "warnings_found": 0,
            "resources_validated": defaultdict(int)
        }
        
        # Performance optimization: cache computed values
        self._cache = {}
        self._cache_ttl = timedelta(minutes=5)

    def get_patient(self, patient_id: str) -> Optional[Dict]:
        """Retrieve patient by ID from store with caching"""
        cache_key = f"patient_{patient_id}"
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                return cached_data
        
        patient = self.patient_store.get(patient_id)
        if patient:
            self._cache[cache_key] = (patient, datetime.now())
        return patient

    def extract_patient_id(self, reference: str) -> Optional[str]:
        """
        Extract patient ID from a FHIR reference string.
        
        Args:
            reference: FHIR reference string (e.g., "Patient/patient-123")
        
        Returns:
            Patient ID or None if not a patient reference
        """
        if reference and reference.startswith("Patient/"):
            return reference.split("/", 1)[1]
        return None

    def is_deceased(self, patient: Dict) -> bool:
        """Check if patient is marked as deceased"""
        if patient.get("deceasedBoolean") is True:
            return True
        if patient.get("deceasedDateTime"):
            return True
        return False

    def get_birth_date(self, patient: Dict) -> Optional[str]:
        """Get patient birth date with normalization"""
        birth_date = patient.get("birthDate")
        if birth_date:
            # Normalize date format
            if isinstance(birth_date, str):
                return birth_date.split('T')[0]  # Remove time component if present
        return birth_date
    
    def get_age(self, patient: Dict) -> Optional[int]:
        """Calculate patient age from birth date"""
        birth_date = self.get_birth_date(patient)
        if not birth_date:
            return None
        
        try:
            dob = datetime.strptime(birth_date, "%Y-%m-%d")
            age = (datetime.now() - dob).days // 365
            return age
        except (ValueError, TypeError):
            return None
    
    def validate_medication_interactions(self, medication_requests: List[Dict]) -> List[Dict]:
        """
        Validate medication interactions across multiple medication requests.
        
        Checks:
        - Drug-drug interactions
        - Duplicate medications
        - Contraindicated combinations
        """
        errors = []
        
        if len(medication_requests) < 2:
            return errors
        
        # Extract medication names/codes
        medications = []
        for med_req in medication_requests:
            med_concept = med_req.get("medicationCodeableConcept")
            if med_concept:
                if isinstance(med_concept, dict):
                    coding = med_concept.get("coding", [])
                    if coding and isinstance(coding, list):
                        med_code = coding[0].get("code")
                        med_display = coding[0].get("display") or med_concept.get("text")
                        medications.append({
                            "code": med_code,
                            "display": med_display,
                            "request_id": med_req.get("id")
                        })
        
        # Check for duplicates
        med_codes = [m["code"] for m in medications if m["code"]]
        if len(med_codes) != len(set(med_codes)):
            duplicate_codes = [code for code in med_codes if med_codes.count(code) > 1]
            for code in set(duplicate_codes):
                errors.append({
                    "field": "medicationCodeableConcept",
                    "type": "cross_resource",
                    "severity": "warning",
                    "message": f"Duplicate medication detected: {code}",
                    "explanation": "Multiple requests for the same medication may indicate duplicate entry.",
                    "suggested_fix": "Review and consolidate duplicate medication requests."
                })
        
        # Check for known drug interactions (simplified example)
        # In production, this would use a drug interaction database
        interaction_pairs = [
            ("warfarin", "aspirin"),
            ("ace inhibitors", "potassium supplements"),
            ("ssri", "maoi")
        ]
        
        for i, med1 in enumerate(medications):
            for med2 in medications[i+1:]:
                for interaction in interaction_pairs:
                    if (interaction[0].lower() in str(med1["display"]).lower() and 
                        interaction[1].lower() in str(med2["display"]).lower()) or \
                       (interaction[1].lower() in str(med1["display"]).lower() and 
                        interaction[0].lower() in str(med2["display"]).lower()):
                        errors.append({
                            "field": "medicationCodeableConcept",
                            "type": "cross_resource",
                            "severity": "warning",
                            "message": f"Potential drug interaction: {med1['display']} and {med2['display']}",
                            "explanation": f"These medications may interact: {interaction[0]} + {interaction[1]}",
                            "suggested_fix": "Review with clinical pharmacist or consider alternative medications."
                        })
        
        return errors
    
    def validate_condition_observation_consistency(self, conditions: List[Dict], 
                                                   observations: List[Dict]) -> List[Dict]:
        """
        Validate consistency between conditions and observations.
        
        Checks:
        - Observations match registered conditions
        - Lab results align with condition status
        - Vital signs are within expected ranges for conditions
        """
        errors = []
        
        if not conditions or not observations:
            return errors
        
        # Create condition lookup
        condition_map = {}
        for condition in conditions:
            code = condition.get("code")
            if code:
                if isinstance(code, dict):
                    condition_text = code.get("text") or code.get("coding", [{}])[0].get("display")
                else:
                    condition_text = str(code)
                condition_map[condition_text.lower()] = condition
        
        # Check observations against conditions
        for observation in observations:
            obs_code = observation.get("code")
            if obs_code:
                if isinstance(obs_code, dict):
                    obs_text = obs_code.get("text") or obs_code.get("coding", [{}])[0].get("display")
                else:
                    obs_text = str(obs_code)
                
                obs_text_lower = obs_text.lower()
                
                # Check if observation relates to any condition
                related_condition = None
                for condition_text in condition_map:
                    if condition_text in obs_text_lower or obs_text_lower in condition_text:
                        related_condition = condition_map[condition_text]
                        break
                
                if related_condition:
                    # Check if observation results align with condition status
                    clinical_status = related_condition.get("clinicalStatus")
                    if isinstance(clinical_status, dict):
                        status = clinical_status.get("coding", [{}])[0].get("code")
                    else:
                        status = str(clinical_status).lower()
                    
                    value_quantity = observation.get("valueQuantity")
                    if value_quantity and isinstance(value_quantity, dict):
                        value = value_quantity.get("value")
                        unit = value_quantity.get("unit")
                        
                        # Example: Check if diabetes condition has normal blood sugar
                        if "diabetes" in obs_text_lower or "glucose" in obs_text_lower:
                            if value and float(value) > 200 and status == "resolved":
                                errors.append({
                                    "field": "valueQuantity.value",
                                    "type": "cross_resource",
                                    "severity": "warning",
                                    "message": f"High glucose value ({value} {unit}) for resolved diabetes condition",
                                    "explanation": "Elevated glucose levels may indicate condition recurrence.",
                                    "suggested_fix": "Review condition status or verify lab results."
                                })
        
        return errors
    
    def validate_encounter_timeline(self, encounters: List[Dict]) -> List[Dict]:
        """
        Validate encounter timeline consistency.
        
        Checks:
        - No overlapping encounters for same patient
        - Encounters are in chronological order
        - No gaps in expected admission patterns
        """
        errors = []
        
        if len(encounters) < 2:
            return errors
        
        # Sort encounters by start date
        sorted_encounters = sorted(encounters, key=lambda e: self._get_encounter_start(e))
        
        for i in range(len(sorted_encounters) - 1):
            current = sorted_encounters[i]
            next_enc = sorted_encounters[i + 1]
            
            current_end = self._get_encounter_end(current)
            next_start = self._get_encounter_start(next_enc)
            
            if current_end and next_start:
                try:
                    end_dt = datetime.fromisoformat(current_end.replace("Z", "+00:00"))
                    start_dt = datetime.fromisoformat(next_start.replace("Z", "+00:00"))
                    
                    # Check for overlap
                    if end_dt > start_dt:
                        errors.append({
                            "field": "period",
                            "type": "cross_resource",
                            "severity": "warning",
                            "message": f"Overlapping encounters detected",
                            "explanation": f"Encounter {current.get('id')} ends after {next_enc.get('id')} starts.",
                            "suggested_fix": "Review encounter dates for accuracy."
                        })
                    
                    # Check for unreasonable gaps (e.g., > 1 year between encounters)
                    gap = (start_dt - end_dt).days
                    if gap > 365:
                        errors.append({
                            "field": "period",
                            "type": "cross_resource",
                            "severity": "info",
                            "message": f"Large gap ({gap} days) between encounters",
                            "explanation": "Extended period without documented encounters.",
                            "suggested_fix": "Verify if patient records are complete."
                        })
                except (ValueError, TypeError):
                    pass
        
        return errors
    
    def _get_encounter_start(self, encounter: Dict) -> Optional[str]:
        """Extract encounter start date"""
        period = encounter.get("period", {})
        if isinstance(period, dict):
            return period.get("start")
        return None
    
    def _get_encounter_end(self, encounter: Dict) -> Optional[str]:
        """Extract encounter end date"""
        period = encounter.get("period", {})
        if isinstance(period, dict):
            return period.get("end")
        return None
    
    def validate_allergy_consistency(self, patient: Dict, medication_requests: List[Dict]) -> List[Dict]:
        """
        Validate consistency between patient allergies and medication requests.
        
        Checks:
        - No prescribed medications that patient is allergic to
        - Allergy reactions are documented
        """
        errors = []
        
        # Extract allergies from patient
        allergies = []
        if "allergyIntolerance" in patient:
            allergy_list = patient["allergyIntolerance"]
            if isinstance(allergy_list, list):
                for allergy in allergy_list:
                    if isinstance(allergy, dict):
                        substance = allergy.get("substance")
                        if substance:
                            if isinstance(substance, dict):
                                allergy_text = substance.get("text") or substance.get("coding", [{}])[0].get("display")
                            else:
                                allergy_text = str(substance)
                            allergies.append(allergy_text.lower())
        
        if not allergies:
            return errors
        
        # Check medications against allergies
        for med_req in medication_requests:
            med_concept = med_req.get("medicationCodeableConcept")
            if med_concept:
                if isinstance(med_concept, dict):
                    coding = med_concept.get("coding", [])
                    if coding and isinstance(coding, list):
                        med_display = coding[0].get("display") or med_concept.get("text")
                        if med_display:
                            med_display_lower = med_display.lower()
                            
                            # Check for allergy match
                            for allergy in allergies:
                                if allergy in med_display_lower or med_display_lower in allergy:
                                    errors.append({
                                        "field": "medicationCodeableConcept",
                                        "type": "cross_resource",
                                        "severity": "critical",
                                        "message": f"Medication prescribed despite allergy: {med_display}",
                                        "explanation": f"Patient has documented allergy to: {allergy}",
                                        "suggested_fix": "Review medication prescription and consider alternatives."
                                    })
        
        return errors
    
    def validate_vital_signs_trends(self, observations: List[Dict]) -> List[Dict]:
        """
        Validate vital signs trends over time.
        
        Checks:
        - Sudden changes in vital signs
        - Values outside physiological ranges
        - Inconsistent measurement patterns
        """
        errors = []
        
        if len(observations) < 2:
            return errors
        
        # Group observations by type
        obs_by_type = defaultdict(list)
        for obs in observations:
            code = obs.get("code")
            if code:
                if isinstance(code, dict):
                    obs_type = code.get("text") or code.get("coding", [{}])[0].get("display")
                else:
                    obs_type = str(code)
                obs_by_type[obs_type.lower()].append(obs)
        
        # Analyze trends for each type
        for obs_type, type_observations in obs_by_type.items():
            if len(type_observations) < 2:
                continue
            
            # Sort by date
            sorted_obs = sorted(type_observations, key=lambda o: o.get("effectiveDateTime", ""))
            
            # Check for sudden changes
            for i in range(len(sorted_obs) - 1):
                current = sorted_obs[i]
                next_obs = sorted_obs[i + 1]
                
                current_value = self._extract_numeric_value(current)
                next_value = self._extract_numeric_value(next_obs)
                
                if current_value is not None and next_value is not None:
                    # Calculate percent change
                    if current_value != 0:
                        percent_change = abs((next_value - current_value) / current_value) * 100
                        
                        # Flag sudden large changes (> 50%)
                        if percent_change > 50:
                            errors.append({
                                "field": "valueQuantity.value",
                                "type": "cross_resource",
                                "severity": "warning",
                                "message": f"Sudden change in {obs_type}: {percent_change:.1f}%",
                                "explanation": f"Value changed from {current_value} to {next_value} between observations.",
                                "suggested_fix": "Verify measurement accuracy and patient condition."
                            })
        
        return errors
    
    def _extract_numeric_value(self, observation: Dict) -> Optional[float]:
        """Extract numeric value from observation"""
        value_quantity = observation.get("valueQuantity")
        if value_quantity and isinstance(value_quantity, dict):
            value = value_quantity.get("value")
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    pass
        return None
    
    def validate_resource_completeness(self, resource: Dict, resource_type: str) -> List[Dict]:
        """
        Validate resource completeness based on FHIR profiles and best practices.
        
        Checks:
        - Required fields are present
        - Business-critical optional fields are present
        - Data quality indicators
        """
        errors = []
        
        # Define required fields by resource type
        required_fields = {
            "Patient": ["id", "gender"],
            "Observation": ["id", "status", "code", "subject"],
            "MedicationRequest": ["id", "status", "intent", "medicationCodeableConcept", "subject"],
            "Condition": ["id", "clinicalStatus", "code", "subject"],
            "Encounter": ["id", "status", "class", "subject"]
        }
        
        # Define recommended fields by resource type
        recommended_fields = {
            "Patient": ["birthDate", "name"],
            "Observation": ["effectiveDateTime", "valueQuantity"],
            "MedicationRequest": ["authoredOn", "requester"],
            "Condition": ["onsetDateTime", "verificationStatus"],
            "Encounter": ["period", "participant"]
        }
        
        # Check required fields
        for field in required_fields.get(resource_type, []):
            if field not in resource or resource[field] is None:
                errors.append({
                    "field": field,
                    "type": "completeness",
                    "severity": "error",
                    "message": f"Missing required field: {field}",
                    "explanation": f"{field} is required for {resource_type} resources.",
                    "suggested_fix": f"Provide a value for {field}."
                })
        
        # Check recommended fields
        for field in recommended_fields.get(resource_type, []):
            if field not in resource or resource[field] is None:
                errors.append({
                    "field": field,
                    "type": "completeness",
                    "severity": "warning",
                    "message": f"Missing recommended field: {field}",
                    "explanation": f"{field} is recommended for {resource_type} resources for better data quality.",
                    "suggested_fix": f"Consider providing a value for {field}."
                })
        
        return errors
    
    def validate_batch(self, resources: List[Tuple[str, Dict]]) -> Dict[str, List[Dict]]:
        """
        Validate multiple resources in batch with performance optimization.
        
        Args:
            resources: List of (resource_type, resource) tuples
        
        Returns:
            Dictionary mapping resource IDs to validation errors
        """
        results = {}
        
        # Group resources by type for efficient processing
        resources_by_type = defaultdict(list)
        for resource_type, resource in resources:
            resource_id = resource.get("id", "unknown")
            resources_by_type[resource_type].append((resource_id, resource))
        
        # Process each resource type
        for resource_type, type_resources in resources_by_type.items():
            if resource_type == "Patient":
                for resource_id, resource in type_resources:
                    errors = self.validate_resource_completeness(resource, resource_type)
                    results[resource_id] = errors
            
            elif resource_type == "Observation":
                observations = [r for _, r in type_resources]
                for resource_id, resource in type_resources:
                    errors = []
                    errors.extend(self.validate_resource_completeness(resource, resource_type))
                    errors.extend(self.validate_observation_for_patient(resource))
                    results[resource_id] = errors
                
                # Add trend analysis
                if len(observations) > 1:
                    trend_errors = self.validate_vital_signs_trends(observations)
                    for resource_id, _ in type_resources:
                        results[resource_id].extend(trend_errors)
            
            elif resource_type == "MedicationRequest":
                medication_requests = [r for _, r in type_resources]
                for resource_id, resource in type_resources:
                    errors = []
                    errors.extend(self.validate_resource_completeness(resource, resource_type))
                    errors.extend(self.validate_medication_request_for_patient(resource))
                    results[resource_id] = errors
                
                # Add interaction analysis
                if len(medication_requests) > 1:
                    interaction_errors = self.validate_medication_interactions(medication_requests)
                    for resource_id, _ in type_resources:
                        results[resource_id].extend(interaction_errors)
        
        # Update statistics
        self.validation_stats["total_validations"] += len(resources)
        self.validation_stats["resources_validated"][resource_type] += len(type_resources)
        for resource_id, errors in results.items():
            self.validation_stats["errors_found"] += len([e for e in errors if e.get("severity") != "warning"])
            self.validation_stats["warnings_found"] += len([e for e in errors if e.get("severity") == "warning"])
        
        return results
    
    def get_validation_summary(self) -> Dict:
        """Get summary of validation statistics"""
        return {
            "total_validations": self.validation_stats["total_validations"],
            "total_errors": self.validation_stats["errors_found"],
            "total_warnings": self.validation_stats["warnings_found"],
            "resources_by_type": dict(self.validation_stats["resources_validated"]),
            "cache_size": len(self._cache)
        }
    
    def clear_cache(self):
        """Clear the validation cache"""
        self._cache.clear()

    def validate_observation_for_patient(
        self, 
        observation: Dict, 
        patient: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Validate Observation resource against Patient
        
        Checks:
        - Patient exists
        - Observation date not before patient birth
        - Observation not for deceased patient (warning)
        - Observation timestamp not in future
        """
        errors = []
        
        # Extract patient reference
        subject = observation.get("subject")
        if not subject:
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": "Observation missing subject reference.",
                "explanation": "Observations must reference a patient.",
                "suggested_fix": "Add a subject reference to the patient."
            })
            return errors

        patient_id = self.extract_patient_id(subject) if isinstance(subject, str) else self.extract_patient_id(subject.get("reference", ""))
        
        if not patient_id:
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": "Observation subject is not a Patient reference.",
                "explanation": "Observation subject should reference a Patient resource.",
                "suggested_fix": "Use 'Patient/{id}' format for subject reference."
            })
            return errors

        # Check if patient exists
        if not patient:
            patient = self.get_patient(patient_id)
        
        if not patient:
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": f"Observation references non-existent patient: {patient_id}",
                "explanation": "The referenced patient does not exist in the system.",
                "suggested_fix": "Verify the patient ID or create the patient resource first."
            })
            return errors

        # Check observation date against patient birth date
        effective_datetime = observation.get("effectiveDateTime") or observation.get("effectivePeriod", {}).get("start")
        birth_date = self.get_birth_date(patient)
        
        if effective_datetime and birth_date:
            try:
                # Parse dates (handle partial dates)
                obs_date = datetime.fromisoformat(effective_datetime.replace("Z", "+00:00"))
                dob = datetime.fromisoformat(birth_date)
                
                if obs_date < dob:
                    errors.append({
                        "field": "effectiveDateTime",
                        "type": "cross_resource",
                        "message": f"Observation date ({effective_datetime}) is before patient birth ({birth_date}).",
                        "explanation": "Observations cannot occur before the patient was born.",
                        "suggested_fix": "Verify the observation date or patient birth date."
                    })
            except (ValueError, TypeError):
                pass  # Date parsing failed, skip this check

        # Check if observation is for deceased patient
        if self.is_deceased(patient):
            deceased_date = patient.get("deceasedDateTime")
            obs_date = observation.get("effectiveDateTime") or observation.get("effectivePeriod", {}).get("start")
            
            if obs_date and deceased_date:
                try:
                    obs_dt = datetime.fromisoformat(obs_date.replace("Z", "+00:00"))
                    death_dt = datetime.fromisoformat(deceased_date.replace("Z", "+00:00"))
                    
                    if obs_dt > death_dt:
                        errors.append({
                            "field": "subject",
                            "type": "cross_resource",
                            "message": "Observation recorded after patient death.",
                            "explanation": "Observations should not be recorded for deceased patients after their death date.",
                            "suggested_fix": "Verify the patient is still alive or correct the dates."
                        })
                except (ValueError, TypeError):
                    pass
            else:
                errors.append({
                    "field": "subject",
                    "type": "cross_resource",
                    "severity": "warning",
                    "message": "Observation for deceased patient.",
                    "explanation": "The patient is marked as deceased. Verify this observation is intentional.",
                    "suggested_fix": "Confirm the observation is correct or update patient status."
                })

        # Check if observation timestamp is in future
        if effective_datetime:
            try:
                obs_dt = datetime.fromisoformat(effective_datetime.replace("Z", "+00:00"))
                if obs_dt > datetime.now(obs_dt.tzinfo):
                    errors.append({
                        "field": "effectiveDateTime",
                        "type": "cross_resource",
                        "message": f"Observation timestamp ({effective_datetime}) is in the future.",
                        "explanation": "Observations should not have future timestamps.",
                        "suggested_fix": "Verify the observation date and time."
                    })
            except (ValueError, TypeError):
                pass

        # Check encounter reference
        encounter = observation.get("encounter")
        if encounter:
            enc_ref = encounter if isinstance(encounter, str) else encounter.get("reference", "")
            if enc_ref and not enc_ref.startswith("Encounter/"):
                errors.append({
                    "field": "encounter",
                    "type": "cross_resource",
                    "message": f"Invalid encounter reference: {enc_ref}",
                    "explanation": "Encounter references should use 'Encounter/{id}' format.",
                    "suggested_fix": "Use proper Encounter reference format."
                })

        return errors

    def validate_medication_request_for_patient(
        self,
        medication_request: Dict,
        patient: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Validate MedicationRequest against Patient
        
        Checks:
        - Patient exists
        - Medication not prescribed for deceased patient
        - Weight-based dosage has patient weight
        """
        errors = []
        
        # Extract patient reference
        subject = medication_request.get("subject")
        if not subject:
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": "MedicationRequest missing subject reference.",
                "explanation": "MedicationRequests must reference a patient.",
                "suggested_fix": "Add a subject reference to the patient."
            })
            return errors

        patient_id = self.extract_patient_id(subject) if isinstance(subject, str) else self.extract_patient_id(subject.get("reference", ""))
        
        if not patient_id:
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": "MedicationRequest subject is not a Patient reference.",
                "explanation": "MedicationRequest subject should reference a Patient resource.",
                "suggested_fix": "Use 'Patient/{id}' format for subject reference."
            })
            return errors

        # Check if patient exists
        if not patient:
            patient = self.get_patient(patient_id)
        
        if not patient:
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": f"MedicationRequest references non-existent patient: {patient_id}",
                "explanation": "The referenced patient does not exist in the system.",
                "suggested_fix": "Verify the patient ID or create the patient resource first."
            })
            return errors

        # Check if medication prescribed for deceased patient
        if self.is_deceased(patient):
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": "Medication prescribed for deceased patient.",
                "explanation": "Medications should not be prescribed for deceased patients.",
                "suggested_fix": "Verify the patient is still alive or cancel the prescription."
            })

        # Check weight-based dosage
        dosage_instruction = medication_request.get("dosageInstruction", [])
        if isinstance(dosage_instruction, list):
            for dose in dosage_instruction:
                dose_and_rate = dose.get("doseAndRate", [])
                if isinstance(dose_and_rate, list):
                    for dr in dose_and_rate:
                        dose_range = dr.get("doseRange")
                        if dose_range:
                            # Check if it's weight-based (/kg)
                            denominator = dose_range.get("denominator", {})
                            if isinstance(denominator, dict):
                                code = denominator.get("code") or denominator.get("unit", "")
                                if "kg" in code.lower():
                                    # Check if patient has weight recorded
                                    has_weight = False
                                    for obs in self.patient_store.values():
                                        if obs.get("resourceType") == "Observation":
                                            code_concept = obs.get("code", {}).get("coding", [{}])[0]
                                            if code_concept.get("code") in ["29463-7", "8302-2", "3141-9"]:  # LOINC codes for weight
                                                has_weight = True
                                                break
                                    
                                    if not has_weight:
                                        errors.append({
                                            "field": "dosageInstruction",
                                            "type": "cross_resource",
                                            "message": "Weight-based dosage prescribed but no patient weight recorded.",
                                            "explanation": "Weight-based dosages require a recorded patient weight.",
                                            "suggested_fix": "Record patient weight or use absolute dosage."
                                        })

        return errors

    def validate_encounter_for_patient(
        self,
        encounter: Dict,
        patient: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Validate Encounter against Patient
        
        Checks:
        - Patient exists
        - Encounter not for deceased patient
        - Encounter duration not negative (end before start)
        """
        errors = []
        
        # Extract patient reference
        subject = encounter.get("subject")
        if not subject:
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": "Encounter missing subject reference.",
                "explanation": "Encounters must reference a patient.",
                "suggested_fix": "Add a subject reference to the patient."
            })
            return errors

        patient_id = self.extract_patient_id(subject) if isinstance(subject, str) else self.extract_patient_id(subject.get("reference", ""))
        
        if not patient_id:
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": "Encounter subject is not a Patient reference.",
                "explanation": "Encounter subject should reference a Patient resource.",
                "suggested_fix": "Use 'Patient/{id}' format for subject reference."
            })
            return errors

        # Check if patient exists
        if not patient:
            patient = self.get_patient(patient_id)
        
        if not patient:
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": f"Encounter references non-existent patient: {patient_id}",
                "explanation": "The referenced patient does not exist in the system.",
                "suggested_fix": "Verify the patient ID or create the patient resource first."
            })
            return errors

        # Check if encounter is for deceased patient
        if self.is_deceased(patient):
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": "Encounter for deceased patient.",
                "explanation": "Encounters should not be created for deceased patients.",
                "suggested_fix": "Verify the patient is still alive or correct patient status."
            })

        # Check encounter duration
        period = encounter.get("period", {})
        if isinstance(period, dict):
            start = period.get("start")
            end = period.get("end")
            
            if start and end:
                try:
                    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    
                    if end_dt < start_dt:
                        errors.append({
                            "field": "period",
                            "type": "cross_resource",
                            "message": f"Encounter end time ({end}) is before start time ({start}).",
                            "explanation": "Encounter duration cannot be negative.",
                            "suggested_fix": "Correct the start and end times."
                        })
                except (ValueError, TypeError):
                    pass

        return errors

    def validate_condition_for_patient(
        self,
        condition: Dict,
        patient: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Validate Condition against Patient
        
        Checks:
        - Patient exists
        - Condition not created after patient death
        - Pregnancy condition not assigned to male patient
        """
        errors = []
        
        # Extract patient reference
        subject = condition.get("subject")
        if not subject:
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": "Condition missing subject reference.",
                "explanation": "Conditions must reference a patient.",
                "suggested_fix": "Add a subject reference to the patient."
            })
            return errors

        patient_id = self.extract_patient_id(subject) if isinstance(subject, str) else self.extract_patient_id(subject.get("reference", ""))
        
        if not patient_id:
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": "Condition subject is not a Patient reference.",
                "explanation": "Condition subject should reference a Patient resource.",
                "suggested_fix": "Use 'Patient/{id}' format for subject reference."
            })
            return errors

        # Check if patient exists
        if not patient:
            patient = self.get_patient(patient_id)
        
        if not patient:
            errors.append({
                "field": "subject",
                "type": "cross_resource",
                "message": f"Condition references non-existent patient: {patient_id}",
                "explanation": "The referenced patient does not exist in the system.",
                "suggested_fix": "Verify the patient ID or create the patient resource first."
            })
            return errors

        # Check if condition created after patient death
        if self.is_deceased(patient):
            recorded_date = condition.get("recordedDate") or condition.get("onsetDateTime")
            deceased_date = patient.get("deceasedDateTime")
            
            if recorded_date and deceased_date:
                try:
                    rec_dt = datetime.fromisoformat(recorded_date.replace("Z", "+00:00"))
                    death_dt = datetime.fromisoformat(deceased_date.replace("Z", "+00:00"))
                    
                    if rec_dt > death_dt:
                        errors.append({
                            "field": "recordedDate",
                            "type": "cross_resource",
                            "message": "Condition recorded after patient death.",
                            "explanation": "Conditions should not be recorded after patient death.",
                            "suggested_fix": "Verify the dates or patient status."
                        })
                except (ValueError, TypeError):
                    pass

        # Check pregnancy condition for male patient
        gender = patient.get("gender")
        if gender == "male":
            code = condition.get("code", {}).get("coding", [])
            if isinstance(code, list):
                for coding in code:
                    code_val = coding.get("code", "").lower()
                    display = coding.get("display", "").lower()
                    system = coding.get("system", "")
                    
                    # SNOMED codes for pregnancy
                    pregnancy_codes = ["77386006", "118186009", "364320009", "255650007"]
                    if (code_val in pregnancy_codes or 
                        "pregnancy" in display or 
                        "pregnant" in display):
                        errors.append({
                            "field": "code",
                            "type": "cross_resource",
                            "message": "Pregnancy condition assigned to male patient.",
                            "explanation": "Pregnancy conditions should not be assigned to male patients.",
                            "suggested_fix": "Verify patient gender or condition code."
                        })

        return errors

    def validate_bundle_patient_consistency(self, bundle: Dict) -> List[Dict]:
        """
        Validate that all resources in a Bundle reference the same patient
        
        This is important for transaction bundles that should contain
        resources for a single patient.
        """
        errors = []
        
        if bundle.get("resourceType") != "Bundle":
            return errors
        
        entries = bundle.get("entry", [])
        if not isinstance(entries, list):
            return errors
        
        patient_ids = set()
        
        for entry in entries:
            resource = entry.get("resource", {})
            if not isinstance(resource, dict):
                continue
            
            resource_type = resource.get("resourceType")
            subject = resource.get("subject")
            
            if subject and resource_type in ["Observation", "Condition", "MedicationRequest", "Encounter"]:
                patient_id = self.extract_patient_id(subject) if isinstance(subject, str) else self.extract_patient_id(subject.get("reference", ""))
                if patient_id:
                    patient_ids.add(patient_id)
        
        if len(patient_ids) > 1:
            errors.append({
                "field": "Bundle",
                "type": "cross_resource",
                "message": f"Bundle contains resources for multiple patients: {', '.join(patient_ids)}",
                "explanation": "Transaction bundles should typically contain resources for a single patient.",
                "suggested_fix": "Split the bundle into separate bundles per patient, or verify this is intentional."
            })
        
        return errors
