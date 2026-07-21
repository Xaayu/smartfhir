"""
PHI De-identification API endpoints.
HIPAA Safe Harbor compliant.
"""
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from phi_deidentifier import deidentify, deidentify_bundle
from policy_engine.executor import apply_policy_to_resource, build_policy_summary
from policy_engine.loader import list_preset_policies
from policy_engine.preview import create_policy_preview
from policy_engine.risk_score import calculate_risk_score
from policy_engine.validator import validate_policy

router = APIRouter(prefix="/phi", tags=["PHI De-identification"])


class DeidentifyInput(BaseModel):
    resource: dict
    mode: Literal["redact", "mask", "pseudonymize"] = "pseudonymize"
    audit: bool = True
    policy: dict | None = None
    purpose: str | None = None


class BundleDeidentifyInput(BaseModel):
    bundle: dict
    mode: Literal["redact", "mask", "pseudonymize"] = "pseudonymize"
    audit: bool = True
    policy: dict | None = None
    purpose: str | None = None


class PolicyApplyInput(BaseModel):
    resource: dict
    policy: dict
    mode: Literal["redact", "mask", "pseudonymize"] = "pseudonymize"


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
        working_resource = input.resource
        policy_info = None

        if input.policy or input.purpose:
            policy_to_apply = input.policy
            if not policy_to_apply and input.purpose:
                presets = list_preset_policies()
                policy_to_apply = next((p for p in presets if p.get("purpose") == input.purpose), None)
            
            if policy_to_apply:
                policy_to_apply = validate_policy(policy_to_apply)
                working_resource = apply_policy_to_resource(policy_to_apply, working_resource, input.mode)
                policy_info = build_policy_summary(policy_to_apply, working_resource)

        result = deidentify(
            resource=working_resource,
            mode=input.mode,
            include_audit=input.audit
        )

        if policy_info and isinstance(result.get("audit_report"), dict):
            result["audit_report"]["policy_applied"] = policy_info.get("purpose")
            result["audit_report"]["policy_summary"] = policy_info
            result["audit_report"]["policy_actions"] = policy_info.get("actions", [])

        return {
            "original_resource_type": resource_type,
            "mode": input.mode,
            "hipaa_safe_harbor": True,
            "policy_applied": policy_info.get("purpose") if policy_info else None,
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
        working_bundle = input.bundle
        policy_info = None

        if input.policy or input.purpose:
            policy_to_apply = input.policy
            if not policy_to_apply and input.purpose:
                presets = list_preset_policies()
                policy_to_apply = next((p for p in presets if p.get("purpose") == input.purpose), None)

            if policy_to_apply:
                policy_to_apply = validate_policy(policy_to_apply)
                working_bundle = apply_policy_to_resource(policy_to_apply, working_bundle, input.mode)
                policy_info = build_policy_summary(policy_to_apply, working_bundle)

        result = deidentify_bundle(
            bundle=working_bundle,
            mode=input.mode,
            include_audit=input.audit
        )

        if policy_info and isinstance(result.get("audit_report"), dict):
            result["audit_report"]["policy_applied"] = policy_info.get("purpose")
            result["audit_report"]["policy_summary"] = policy_info
            result["audit_report"]["policy_actions"] = policy_info.get("actions", [])

        return {
            "mode": input.mode,
            "hipaa_safe_harbor": True,
            "policy_applied": policy_info.get("purpose") if policy_info else None,
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


@router.get("/policies/presets")
def get_policies_presets():
    """Return the available purpose-based presets for the UI."""
    presets = list_preset_policies()
    return {"presets": presets}


@router.post("/policies/apply")
def apply_policy(payload: PolicyApplyInput):
    """Apply a purpose-based policy to an input resource and return a preview summary."""
    policy = validate_policy(payload.policy)
    processed = apply_policy_to_resource(policy, payload.resource, payload.mode)
    summary = build_policy_summary(policy, processed)
    preview = create_policy_preview(policy, payload.resource, payload.mode)
    preview["summary"] = summary
    preview["risk"] = calculate_risk_score(policy, preview.get("stats", {}))
    return preview