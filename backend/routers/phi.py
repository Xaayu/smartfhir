"""
PHI De-identification API endpoints.
HIPAA Safe Harbor compliant.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
from phi_deidentifier import deidentify, deidentify_bundle

router = APIRouter(prefix="/phi", tags=["PHI De-identification"])


class DeidentifyInput(BaseModel):
    resource: dict
    mode: Literal["redact", "mask", "pseudonymize"] = "pseudonymize"
    audit: bool = True


class BundleDeidentifyInput(BaseModel):
    bundle: dict
    mode: Literal["redact", "mask", "pseudonymize"] = "pseudonymize"
    audit: bool = True


@router.post("/deidentify")
def deidentify_resource(input: DeidentifyInput):
    """
    De-identify a single FHIR resource.

    Modes:
    - redact:        replace PHI with [REDACTED]
    - mask:          partially hide (J*** D**)
    - pseudonymize:  replace with realistic fake data (HIPAA Safe Harbor)

    Supports: Patient, Observation, Condition, Encounter, MedicationRequest
    """
    if not input.resource:
        raise HTTPException(status_code=400, detail="Resource cannot be empty.")

    resource_type = input.resource.get("resourceType")
    if not resource_type:
        raise HTTPException(
            status_code=400,
            detail="Missing resourceType field."
        )

    supported = [
        "Patient", "Observation", "Condition",
        "Encounter", "MedicationRequest"
    ]

    try:
        result = deidentify(
            resource=input.resource,
            mode=input.mode,
            include_audit=input.audit
        )

        return {
            "original_resource_type": resource_type,
            "mode": input.mode,
            "hipaa_safe_harbor": True,
            **result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"De-identification failed: {str(e)}"
        )


@router.post("/deidentify-bundle")
def deidentify_fhir_bundle(input: BundleDeidentifyInput):
    """
    De-identify an entire FHIR Bundle.
    All resources inside the bundle are processed.

    Perfect for sharing patient records with vendors
    for testing without exposing real PHI.
    """
    if not input.bundle:
        raise HTTPException(status_code=400, detail="Bundle cannot be empty.")

    if input.bundle.get("resourceType") != "Bundle":
        raise HTTPException(
            status_code=400,
            detail="Input must be a FHIR Bundle (resourceType: Bundle)."
        )

    entries = input.bundle.get("entry", [])
    if not entries:
        raise HTTPException(
            status_code=400,
            detail="Bundle has no entries to de-identify."
        )

    try:
        result = deidentify_bundle(
            bundle=input.bundle,
            mode=input.mode,
            include_audit=input.audit
        )

        return {
            "mode": input.mode,
            "hipaa_safe_harbor": True,
            "total_resources_processed": result["total_resources"],
            **result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Bundle de-identification failed: {str(e)}"
        )


@router.get("/modes")
def get_modes():
    """Get available de-identification modes and their descriptions"""
    return {
        "modes": [
            {
                "name": "redact",
                "description": "Replace all PHI with [REDACTED]",
                "example": "John Doe → [REDACTED]",
                "use_case": "Maximum privacy, data is not usable for testing"
            },
            {
                "name": "mask",
                "description": "Partially hide PHI, keep format",
                "example": "John Doe → J*** D**",
                "use_case": "Audit logs, debugging while protecting identity"
            },
            {
                "name": "pseudonymize",
                "description": "Replace with realistic fake data (recommended)",
                "example": "John Doe → James Wilson",
                "use_case": "Testing, development, vendor sharing — HIPAA Safe Harbor",
                "note": "Deterministic — same input always produces same fake output"
            }
        ],
        "standard": "HIPAA Safe Harbor (45 CFR §164.514(b))",
        "phi_categories_covered": [
            "Names", "Geographic data", "Dates (year kept)",
            "Phone/Fax numbers", "Email addresses",
            "SSN/National IDs", "Medical record numbers",
            "Account numbers", "URLs", "IP addresses",
            "Biometric identifiers (photos removed)"
        ]
    }


@router.post("/scan-text")
def scan_free_text(payload: dict):
    """
    Scan a free text string for PHI patterns.
    Useful for checking notes, comments, or any text field.

    Body: { "text": "...", "mode": "redact|mask|pseudonymize" }
    """
    text = payload.get("text", "")
    mode = payload.get("mode", "pseudonymize")

    if not text:
        raise HTTPException(status_code=400, detail="text field is required.")

    if mode not in ["redact", "mask", "pseudonymize"]:
        raise HTTPException(status_code=400, detail="Invalid mode.")

    from phi_deidentifier import PHIDeidentifier
    engine = PHIDeidentifier(mode=mode)
    cleaned = engine._scan_text_for_phi(text, "free_text")
    audit = engine.get_audit_report()

    return {
        "original_text": text,
        "cleaned_text": cleaned,
        "phi_found": audit["phi_items_found"],
        "phi_types": audit["phi_by_type"],
        "mode": mode
    }