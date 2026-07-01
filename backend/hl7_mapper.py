"""
HL7 v2 to FHIR Mapper
Maps HL7 segments to FHIR resources following existing mapper patterns.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal, InvalidOperation
import uuid

from hl7_parser import HL7Message, HL7Segment, HL7Parser


HL7_MAPPINGS_PATH = "mappings/hl7_built_in.json"


def load_hl7_mappings() -> Dict[str, Any]:
    """Load HL7 to FHIR field mappings"""
    if os.path.exists(HL7_MAPPINGS_PATH):
        try:
            with open(HL7_MAPPINGS_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return {}


class HL7Mapper:
    """Maps HL7 segments to FHIR resources"""
    
    def __init__(self):
        self.parser = HL7Parser()
        self.mappings = load_hl7_mappings()
    
    def map_to_fhir(self, hl7_message: str) -> Dict[str, Any]:
        """
        Convert HL7 v2 message to FHIR Bundle.
        
        Args:
            hl7_message: Raw HL7 message string
            
        Returns:
            Dictionary containing FHIR Bundle and any errors
        """
        errors = []
        
        # Parse HL7 message
        parsed = self.parser.parse(hl7_message)
        errors.extend(parsed.errors)
        
        # Create FHIR Bundle
        bundle = {
            "resourceType": "Bundle",
            "type": "message",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "entry": []
        }
        
        # Map based on message type
        message_type = f"{parsed.message_type}^{parsed.trigger_event}" if parsed.trigger_event != "UNKNOWN" else parsed.message_type
        
        if message_type == "ADT^A01":
            # Admit patient
            resources = self._map_adt_a01(parsed)
        elif message_type == "ORU^R01":
            # Observation result
            resources = self._map_oru_r01(parsed)
        elif message_type == "ORM^O01":
            # Order message
            resources = self._map_orm_o01(parsed)
        else:
            # Generic mapping
            resources = self._map_generic(parsed)
        
        # Add resources to bundle
        for resource in resources:
            bundle["entry"].append({
                "resource": resource,
                "fullUrl": f"{resource['resourceType']}/{resource.get('id', uuid.uuid4())}"
            })
        
        return {
            "bundle": bundle,
            "errors": errors,
            "message_type": message_type
        }
    
    def _map_adt_a01(self, parsed: HL7Message) -> List[Dict[str, Any]]:
        """Map ADT^A01 (Admit Patient) message to FHIR resources"""
        resources = []
        
        # Map PID segment to Patient resource
        pid_segments = parsed.segments.get("PID", [])
        if pid_segments:
            patient = self._map_pid_to_patient(pid_segments[0])
            resources.append(patient)
        
        # Map PV1 segment to Encounter resource
        pv1_segments = parsed.segments.get("PV1", [])
        if pv1_segments and pid_segments:
            encounter = self._map_pv1_to_encounter(pv1_segments[0], patient)
            resources.append(encounter)
        
        return resources
    
    def _map_oru_r01(self, parsed: HL7Message) -> List[Dict[str, Any]]:
        """Map ORU^R01 (Observation Result) message to FHIR resources"""
        resources = []
        report_refs = {}
        
        # Map PID segment to Patient resource
        pid_segments = parsed.segments.get("PID", [])
        patient = None
        if pid_segments:
            patient = self._map_pid_to_patient(pid_segments[0])
            resources.append(patient)
        
        # Map PV1 segment to Encounter resource
        pv1_segments = parsed.segments.get("PV1", [])
        encounter = None
        if pv1_segments:
            encounter = self._map_pv1_to_encounter(pv1_segments[0], patient)
            resources.append(encounter)
        
        # Map OBR segments to DiagnosticReport resources so OBX observations can reference their parent report
        obr_segments = parsed.segments.get("OBR", [])
        for i, obr in enumerate(obr_segments):
            diagnostic_report = self._map_obr_to_diagnostic_report(obr, patient, encounter, i)
            resources.append(diagnostic_report)
            report_refs[id(obr)] = diagnostic_report

        # Map OBX segments to Observation resources and preserve OBR parent linkage
        obx_segments = parsed.segments.get("OBX", [])
        for i, obx in enumerate(obx_segments):
            parent_obr = self._find_parent_obr(parsed, obx)
            parent_report = report_refs.get(id(parent_obr)) if parent_obr else None
            observation = self._map_obx_to_observation(obx, patient, encounter, i, parent_report)
            resources.append(observation)
        
        return resources
    
    def _map_orm_o01(self, parsed: HL7Message) -> List[Dict[str, Any]]:
        """Map ORM^O01 (Order) message to FHIR resources"""
        resources = []
        
        # Map PID segment to Patient resource
        pid_segments = parsed.segments.get("PID", [])
        patient = None
        if pid_segments:
            patient = self._map_pid_to_patient(pid_segments[0])
            resources.append(patient)
        
        # Map PV1 segment to Encounter resource
        pv1_segments = parsed.segments.get("PV1", [])
        encounter = None
        if pv1_segments:
            encounter = self._map_pv1_to_encounter(pv1_segments[0], patient)
            resources.append(encounter)
        
        # Map ORC segments to ServiceRequest resources
        orc_segments = parsed.segments.get("ORC", [])
        for i, orc in enumerate(orc_segments):
            service_request = self._map_orc_to_service_request(orc, patient, encounter, i)
            resources.append(service_request)
        
        return resources
    
    def _map_generic(self, parsed: HL7Message) -> List[Dict[str, Any]]:
        """Generic mapping for unsupported message types"""
        resources = []
        
        # Always try to map PID if present
        pid_segments = parsed.segments.get("PID", [])
        if pid_segments:
            patient = self._map_pid_to_patient(pid_segments[0])
            resources.append(patient)
        
        return resources
    
    def _map_pid_to_patient(self, pid: HL7Segment) -> Dict[str, Any]:
        """Map PID segment to FHIR Patient resource"""
        patient = {
            "resourceType": "Patient",
            "id": str(uuid.uuid4()),
            "identifier": []
        }
        
        # Patient ID (PID-3)
        patient_id = self.parser.get_field(pid, 3)
        if patient_id:
            patient_id_value = self.parser.parse_first_component(patient_id)
            patient["identifier"].append({
                "use": "usual",
                "system": "urn:oid:2.16.840.1.113883.4.1",
                "value": patient_id_value or patient_id
            })
        
        # Patient Name (PID-5)
        patient_name = self.parser.get_field(pid, 5)
        if patient_name:
            name_parts = patient_name.split(self.parser.component_separator)
            family_name = name_parts[0] if len(name_parts) > 0 else ""
            given_names = name_parts[1:] if len(name_parts) > 1 else []
            
            patient["name"] = [{
                "family": family_name,
                "given": given_names
            }]
        
        # Date of Birth (PID-7)
        dob = self.parser.get_field(pid, 7)
        if dob:
            iso_dob = self.parser.parse_hl7_date(dob)
            if iso_dob:
                patient["birthDate"] = iso_dob
        
        # Gender (PID-8)
        gender = self.parser.get_field(pid, 8)
        if gender:
            gender_map = {
                "M": "male",
                "F": "female",
                "O": "other",
                "U": "unknown"
            }
            patient["gender"] = gender_map.get(gender, "unknown")
        
        # Address (PID-11)
        address = self.parser.get_field(pid, 11)
        if address:
            address_parts = address.split(self.parser.component_separator)
            if len(address_parts) > 0:
                patient["address"] = [{
                    "line": [address_parts[0]] if address_parts[0] else [],
                    "city": address_parts[2] if len(address_parts) > 2 else "",
                    "state": address_parts[3] if len(address_parts) > 3 else "",
                    "postalCode": address_parts[4] if len(address_parts) > 4 else "",
                    "country": address_parts[5] if len(address_parts) > 5 else ""
                }]
        
        # Phone (PID-13)
        phone = self.parser.get_field(pid, 13)
        if phone:
            phone_parts = phone.split(self.parser.component_separator)
            phone_value = phone_parts[0] if phone_parts else phone
            phone_use_code = phone_parts[1] if len(phone_parts) > 1 else None
            use_map = {
                "PRN": "home",
                "WPN": "work",
                "ORN": "home",
                "NET": "home",
                "CP": "mobile"
            }
            phone_use = use_map.get(phone_use_code, "home")
            patient["telecom"] = patient.get("telecom", [])
            patient["telecom"].append({
                "system": "phone",
                "value": phone_value,
                "use": phone_use
            })
        
        # Email (PID-14)
        email = self.parser.get_field(pid, 14)
        if email:
            patient["telecom"] = patient.get("telecom", [])
            patient["telecom"].append({
                "system": "email",
                "value": email,
                "use": "home"
            })
        
        return patient
    
    def _map_pv1_to_encounter(self, pv1: HL7Segment, patient: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Map PV1 segment to FHIR Encounter resource"""
        encounter = {
            "resourceType": "Encounter",
            "id": str(uuid.uuid4()),
            "status": "in-progress",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "IMP",
                "display": "inpatient encounter"
            }
        }
        
        # Reference to patient
        if patient:
            encounter["subject"] = {
                "reference": f"Patient/{patient['id']}",
                "display": patient.get("name", [{}])[0].get("family", "Unknown") if patient.get("name") else "Unknown"
            }
        
        # Patient Class (PV1-2)
        patient_class = self.parser.get_field(pv1, 2)
        if patient_class:
            class_map = {
                "I": "IMP",
                "O": "AMB",
                "E": "EMER",
                "P": "AMB"
            }
            fhir_class = class_map.get(patient_class, "IMP")
            encounter["class"]["code"] = fhir_class
        
        # Attending Doctor (PV1-7)
        attending_doc = self.parser.get_field(pv1, 7)
        if attending_doc:
            doc_parts = attending_doc.split(self.parser.component_separator)
            if doc_parts:
                encounter["participant"] = [{
                    "type": [{
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                            "code": "ATND",
                            "display": "attender"
                        }]
                    }],
                    "individual": {
                        "identifier": {
                            "system": "urn:oid:2.16.840.1.113883.4.6",
                            "value": doc_parts[0]
                        }
                    }
                }]
        
        # Admission Date (PV1-44)
        admit_date = self.parser.get_field(pv1, 44)
        if admit_date:
            iso_date = self.parser.parse_hl7_datetime(admit_date)
            if iso_date:
                encounter["period"] = {
                    "start": iso_date
                }
        
        return encounter
    
    def _map_obx_to_observation(self, obx: HL7Segment, patient: Optional[Dict[str, Any]], 
                                encounter: Optional[Dict[str, Any]], index: int,
                                parent_report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Map OBX segment to FHIR Observation resource"""
        observation = {
            "resourceType": "Observation",
            "id": str(uuid.uuid4()),
            "status": "final"
        }
        
        if patient:
            observation["subject"] = {"reference": f"Patient/{patient['id']}"}
        if encounter:
            observation["encounter"] = {"reference": f"Encounter/{encounter['id']}"}
        if parent_report:
            observation["derivedFrom"] = [{"reference": f"DiagnosticReport/{parent_report['id']}"}]
        
        # Observation Code (OBX-3)
        obs_code = self.parser.get_field(obx, 3)
        codeable_concept = self.parser.parse_codeable_concept(obs_code, default_system="http://loinc.org")
        if codeable_concept:
            observation["code"] = codeable_concept
        elif obs_code:
            observation["code"] = {"text": obs_code}
        else:
            observation["code"] = {"text": "Unknown observation code"}
        
        # Observation Value Type (OBX-2)
        value_type = self.parser.get_field(obx, 2) or ""
        obs_value = self.parser.get_field(obx, 5)
        units = self.parser.get_field(obx, 6)

        if value_type == "NM":
            numeric_value = self._parse_numeric_value(obs_value)
            if numeric_value is not None:
                observation["valueQuantity"] = {
                    "value": numeric_value,
                    "unit": units or None,
                    "code": units or None,
                    "system": "http://unitsofmeasure.org"
                }
            elif obs_value is not None:
                observation["valueString"] = obs_value
        elif value_type in {"ST", "TX", "FT", "ED"}:
            if obs_value is not None:
                observation["valueString"] = obs_value
        elif value_type in {"CE", "CWE", "CNE"}:
            value_concept = self.parser.parse_codeable_concept(obs_value)
            if value_concept:
                observation["valueCodeableConcept"] = value_concept
            elif obs_value is not None:
                observation["valueString"] = obs_value
        elif value_type == "DT":
            iso_date = self.parser.parse_hl7_date(obs_value)
            observation["valueDateTime"] = iso_date if iso_date else obs_value
        elif value_type == "TS":
            iso_date = self.parser.parse_hl7_datetime(obs_value)
            observation["valueDateTime"] = iso_date if iso_date else obs_value
        else:
            if obs_value is not None:
                observation["valueString"] = obs_value
        
        if units and value_type != "NM":
            # Keep unit metadata separate from interpretation
            pass

        abnormal_flag = self.parser.get_field(obx, 8)
        if abnormal_flag:
            interpretation_display = self._interpretation_display(abnormal_flag)
            observation["interpretation"] = {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": abnormal_flag,
                    "display": interpretation_display
                }],
                "text": interpretation_display
            }

        obs_date = self.parser.get_field(obx, 14)
        if obs_date:
            iso_date = self.parser.parse_hl7_datetime(obs_date)
            if iso_date:
                observation["effectiveDateTime"] = iso_date

        return observation

    def _parse_numeric_value(self, value: Optional[str]) -> Optional[Decimal]:
        if value is None:
            return None
        try:
            cleaned = value.strip()
            if cleaned == "":
                return None
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None

    def _interpretation_display(self, code: str) -> str:
        interpretations = {
            "L": "Low",
            "H": "High",
            "AA": "Very abnormal",
            "N": "Normal",
            "A": "Abnormal",
            "LL": "Critical low",
            "HH": "Critical high"
        }
        return interpretations.get(code, "Interpretation")

    def _find_parent_obr(self, parsed: HL7Message, obx: HL7Segment) -> Optional[HL7Segment]:
        """Find the nearest preceding OBR segment for a given OBX segment."""
        try:
            obx_index = parsed.ordered_segments.index(obx)
        except ValueError:
            return None
        for prior_segment in reversed(parsed.ordered_segments[:obx_index]):
            if prior_segment.segment_id == "OBR":
                return prior_segment
        return None

    def _map_obr_to_diagnostic_report(self, obr: HL7Segment, patient: Optional[Dict[str, Any]],
                                     encounter: Optional[Dict[str, Any]], index: int) -> Dict[str, Any]:
        """Map OBR segment to FHIR DiagnosticReport resource."""
        report = {
            "resourceType": "DiagnosticReport",
            "id": str(uuid.uuid4()),
            "status": "final"
        }
        if patient:
            report["subject"] = {"reference": f"Patient/{patient['id']}"}
        if encounter:
            report["encounter"] = {"reference": f"Encounter/{encounter['id']}"}

        obr_code = self.parser.get_field(obr, 4)
        codeable = self.parser.parse_codeable_concept(obr_code, default_system="http://loinc.org")
        if codeable:
            report["code"] = codeable
        elif obr_code:
            report["code"] = {"text": obr_code}

        report_date = self.parser.get_field(obr, 7)
        if report_date:
            iso_date = self.parser.parse_hl7_datetime(report_date)
            if iso_date:
                report["issued"] = iso_date

        return report
    
    def _map_orc_to_service_request(self, orc: HL7Segment, patient: Optional[Dict[str, Any]],
                                   encounter: Optional[Dict[str, Any]], index: int) -> Dict[str, Any]:
        """Map ORC segment to FHIR ServiceRequest resource"""
        service_request = {
            "resourceType": "ServiceRequest",
            "id": str(uuid.uuid4()),
            "status": "active",
            "intent": "order"
        }
        
        # Reference to patient
        if patient:
            service_request["subject"] = {
                "reference": f"Patient/{patient['id']}"
            }
        
        # Reference to encounter
        if encounter:
            service_request["encounter"] = {
                "reference": f"Encounter/{encounter['id']}"
            }
        
        # Order Control (ORC-1)
        order_control = self.parser.get_field(orc, 1)
        if order_control:
            status_map = {
                "NW": "active",
                "XO": "cancelled",
                "CA": "cancelled",
                "DC": "cancelled"
            }
            service_request["status"] = status_map.get(order_control, "active")
        
        # Placer Order Number (ORC-2)
        placer_order = self.parser.get_field(orc, 2)
        if placer_order:
            service_request["identifier"] = [{
                "system": "urn:oid:2.16.840.1.113883.4.1",
                "value": placer_order
            }]
        
        # Ordering Provider (ORC-12)
        ordering_provider = self.parser.get_field(orc, 12)
        if ordering_provider:
            provider_parts = ordering_provider.split(self.parser.component_separator)
            if provider_parts:
                service_request["requester"] = {
                    "reference": f"Practitioner/{provider_parts[0]}",
                    "display": provider_parts[2] if len(provider_parts) > 2 else ""
                }
        
        return service_request


def map_hl7_to_fhir(hl7_message: str) -> Dict[str, Any]:
    """Convenience function to map HL7 to FHIR"""
    mapper = HL7Mapper()
    return mapper.map_to_fhir(hl7_message)
