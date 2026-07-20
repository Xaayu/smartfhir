from typing import Any, Dict

from .validator import validate_policy

SEMANTIC_CATEGORIES = [
    "patient_name",
    "patient_identifier",
    "government_identifier",
    "insurance_identifier",
    "employee_identifier",
    "contact_name",
    "contact_information",
    "organization",
    "facility",
    "location",
    "practitioner",
    "related_person",
    "address",
    "birth_date",
    "date_time",
    "financial_information",
    "clinical_notes",
    "clinical_content",
    "medications",
    "laboratory",
    "free_text",
    "narrative",
    "metadata",
    "references",
    "device_identifier",
    "audit_information",
    "communication",
    "coverage_information",
    "claim_information",
]

SEMANTIC_ALIASES = {
    "patient_name": ["patient_name", "name"],
    "patient_identifier": ["patient_id", "patient_identifier", "medical_record_number"],
    "government_identifier": ["government_identifier", "ssn", "passport", "driver_license", "national_identifier"],
    "insurance_identifier": ["insurance_identifier", "insurance"],
    "employee_identifier": ["employee_identifier", "employee_id"],
    "contact_name": ["contact_name"],
    "contact_information": ["contact_information", "phone", "email", "telecom"],
    "organization": ["organization", "organization_name"],
    "facility": ["facility"],
    "location": ["location"],
    "practitioner": ["practitioner"],
    "related_person": ["related_person", "contact"],
    "address": ["address"],
    "birth_date": ["birth_date", "dob"],
    "date_time": ["dates", "date_time"],
    "financial_information": ["financial_information"],
    "clinical_notes": ["clinical_notes", "note", "description"],
    "clinical_content": ["clinical_content"],
    "medications": ["medications", "medication"],
    "laboratory": ["lab_results", "laboratory"],
    "free_text": ["free_text", "text"],
    "narrative": ["narrative"],
    "metadata": ["metadata"],
    "references": ["references"],
    "device_identifier": ["device_identifier"],
    "audit_information": ["audit_information"],
    "communication": ["communication"],
    "coverage_information": ["coverage_information"],
    "claim_information": ["claim_information"],
}

FHIR_TARGETS = {
    "patient_name": ["Patient.name", "RelatedPerson.name", "Contact.name", "Practitioner.name"],
    "patient_identifier": ["Patient.identifier.value", "Patient.identifier"],
    "government_identifier": ["identifier.value", "identifier.type", "identifier.system"],
    "insurance_identifier": ["Coverage.identifier", "Claim.identifier", "InsurancePlan.identifier"],
    "employee_identifier": ["Employee.identifier", "Practitioner.identifier"],
    "contact_name": ["Contact.name", "RelatedPerson.name"],
    "contact_information": ["telecom", "contact.telecom", "Organization.contact.telecom"],
    "organization": ["Organization", "managingOrganization", "serviceProvider"],
    "facility": ["Encounter.serviceProvider", "Encounter.hospitalization", "Location"],
    "location": ["Encounter.location", "Location"],
    "practitioner": ["Practitioner", "participant.individual", "performer", "requester", "recorder", "asserter"],
    "related_person": ["RelatedPerson", "contact"],
    "address": ["address.line", "address.city", "address.state", "address.postalCode", "address.country"],
    "birth_date": ["birthDate", "deceasedDateTime", "effectiveDateTime", "onsetDateTime", "recordedDate", "Period.start", "Period.end", "Timing"],
    "date_time": ["dateTime", "instant", "Period", "Timing", "effectiveDateTime"],
    "financial_information": ["Coverage", "Claim", "Contract"],
    "clinical_notes": ["note.text", "Annotation.text", "DocumentReference.description", "Observation.note", "Encounter.note"],
    "clinical_content": ["Observation.valueString", "Condition.note", "DiagnosticReport.presentedForm"],
    "medications": ["MedicationRequest.medicationCodeableConcept", "MedicationRequest.medicationReference"],
    "laboratory": ["Observation", "DiagnosticReport", "Specimen"],
    "free_text": ["text.div", "note.text", "Annotation.text", "DocumentReference.description", "Observation.note", "Encounter.reason"],
    "narrative": ["text.div", "Narrative"],
    "metadata": ["meta", "lastUpdated", "created", "authoredOn"],
    "references": ["reference", "display", "identifier"],
    "device_identifier": ["Device.identifier", "Device.udiCarrier"],
    "audit_information": ["meta.security", "meta.tag"],
    "communication": ["Communication", "CommunicationRequest"],
    "coverage_information": ["Coverage"],
    "claim_information": ["Claim"],
}


def compile_policy(policy: Dict[str, Any]) -> Dict[str, Any]:
    validated = validate_policy(policy)
    fields = validated.get("fields", {})

    compiled: Dict[str, str] = {}
    for category in SEMANTIC_CATEGORIES:
        action = "KEEP"
        for alias in SEMANTIC_ALIASES.get(category, [category]):
            if alias in fields:
                action = str(fields[alias]).upper()
                break
        compiled[category] = action

    for key, value in fields.items():
        if key not in compiled:
            compiled[str(key)] = str(value).upper()

    return {
        "purpose": validated.get("purpose") or "Custom Policy",
        "policy": validated,
        "actions": compiled,
        "semantic_categories": SEMANTIC_CATEGORIES,
        "fhir_targets": FHIR_TARGETS,
        **compiled,
    }
