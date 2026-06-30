"""
HL7 v2 to FHIR Mapper
Maps HL7 segments to FHIR resources following existing mapper patterns.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
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
        
        # Map OBX segments to Observation resources
        obx_segments = parsed.segments.get("OBX", [])
        for i, obx in enumerate(obx_segments):
            observation = self._map_obx_to_observation(obx, patient, encounter, i)
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
            patient["identifier"].append({
                "use": "usual",
                "system": "urn:oid:2.16.840.1.113883.4.1",
                "value": patient_id
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
            patient["telecom"] = patient.get("telecom", [])
            patient["telecom"].append({
                "system": "phone",
                "value": phone,
                "use": "home"
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
                                encounter: Optional[Dict[str, Any]], index: int) -> Dict[str, Any]:
        """Map OBX segment to FHIR Observation resource"""
        observation = {
            "resourceType": "Observation",
            "id": str(uuid.uuid4()),
            "status": "final",
            "code": {
                "coding": [],
                "text": ""
            }
        }
        
        # Reference to patient
        if patient:
            observation["subject"] = {
                "reference": f"Patient/{patient['id']}"
            }
        
        # Reference to encounter
        if encounter:
            observation["encounter"] = {
                "reference": f"Encounter/{encounter['id']}"
            }
        
        # Observation Identifier (OBX-3)
        obs_id = self.parser.get_field(obx, 3)
        if obs_id:
            id_parts = obs_id.split(self.parser.component_separator)
            if len(id_parts) > 0:
                observation["code"]["coding"].append({
                    "system": "http://loinc.org",
                    "code": id_parts[0],
                    "display": id_parts[1] if len(id_parts) > 1 else ""
                })
            if len(id_parts) > 2:
                observation["code"]["text"] = id_parts[2]
        
        # Observation Value (OBX-5)
        obs_value = self.parser.get_field(obx, 5)
        if obs_value:
            observation["valueString"] = obs_value
        
        # Units (OBX-6)
        units = self.parser.get_field(obx, 6)
        if units:
            observation["valueQuantity"] = {
                "value": float(obs_value) if obs_value and obs_value.replace('.', '').isdigit() else 0,
                "unit": units,
                "system": "http://unitsofmeasure.org"
            }
        
        # Observation Date (OBX-14)
        obs_date = self.parser.get_field(obx, 14)
        if obs_date:
            iso_date = self.parser.parse_hl7_datetime(obs_date)
            if iso_date:
                observation["effectiveDateTime"] = iso_date
        
        return observation
    
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
