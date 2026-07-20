import json
import os
from pathlib import Path
from typing import Any, Dict, List

from .validator import validate_policy

BASE_DIR = Path(__file__).resolve().parent.parent
PRESET_DIR = BASE_DIR / "policies"


DEFAULT_PRESETS = {
    "AI Processing": {
        "purpose": "AI Processing",
        "description": "Designed for preparing healthcare data for modern AI systems while removing direct identifiers and limiting re-identification risk.",
        "privacyLevel": "High",
        "objectives": [
            "Remove direct identifiers",
            "Reduce quasi-identifiers",
            "Minimize re-identification risk",
            "Preserve clinical usefulness where possible",
        ],
        "recommendedFor": ["LLM training", "Model evaluation", "Internal analytics", "AI demonstrations"],
        "notRecommendedFor": ["Operational hospital systems", "Patient follow-up", "Identity matching", "Care coordination"],
        "fields": {
            "patient_name": "REMOVE",
            "phone": "REMOVE",
            "email": "REMOVE",
            "address": "GENERALIZE",
            "dob": "YEAR_ONLY",
            "dates": "SHIFT_DATE",
            "patient_id": "HASH",
            "medical_record_number": "HASH",
            "organization": "KEEP",
            "clinical_notes": "KEEP",
            "lab_results": "KEEP",
            "medications": "KEEP",
        },
    },
    "Clinical Research": {
        "purpose": "Clinical Research",
        "description": "Optimized for cohort studies and controlled research access while preserving analytic value and limiting identity disclosure.",
        "privacyLevel": "High",
        "objectives": [
            "Remove direct identifiers",
            "Reduce quasi-identifiers",
            "Support safe cohort analysis",
            "Preserve clinical usefulness where possible",
        ],
        "recommendedFor": ["Clinical studies", "Research cohorts", "Academic analysis", "Trial planning"],
        "notRecommendedFor": ["Public release", "Operational patient outreach", "Identity matching"],
        "fields": {
            "patient_name": "REMOVE",
            "phone": "REMOVE",
            "email": "REMOVE",
            "address": "CITY_ONLY",
            "dob": "YEAR_ONLY",
            "dates": "SHIFT_DATE",
            "patient_id": "HASH",
            "medical_record_number": "HASH",
            "clinical_notes": "KEEP",
            "lab_results": "KEEP",
        },
    },
    "Analytics": {
        "purpose": "Analytics",
        "description": "Balances statistical utility with privacy controls for dashboards, reporting, and internal analysis.",
        "privacyLevel": "Medium",
        "objectives": [
            "Protect identities",
            "Preserve aggregate trends",
            "Reduce re-identification risk",
            "Maintain reporting utility",
        ],
        "recommendedFor": ["Dashboards", "Operational reporting", "Internal analytics", "Performance metrics"],
        "notRecommendedFor": ["Public release", "External sharing", "Patient follow-up"],
        "fields": {
            "patient_name": "REMOVE",
            "phone": "REMOVE",
            "email": "REMOVE",
            "address": "STATE_ONLY",
            "dob": "YEAR_ONLY",
            "dates": "MONTH_YEAR",
            "patient_id": "HASH",
            "clinical_notes": "REMOVE",
        },
    },
    "Internal Testing": {
        "purpose": "Internal Testing",
        "description": "Creates realistic de-identified data for QA, sandbox, and development workflows without exposing patient identity.",
        "privacyLevel": "Medium",
        "objectives": [
            "Protect identities",
            "Generate realistic substitutes",
            "Support safe testing",
            "Preserve data structure",
        ],
        "recommendedFor": ["QA", "Sandbox", "Software testing", "Training environments"],
        "notRecommendedFor": ["Public release", "Patient follow-up", "Production analytics"],
        "fields": {
            "patient_name": "REPLACE_FAKE",
            "phone": "REPLACE_FAKE",
            "email": "REPLACE_FAKE",
            "address": "CITY_ONLY",
            "dob": "YEAR_ONLY",
            "dates": "SHIFT_DATE",
            "patient_id": "HASH",
            "clinical_notes": "KEEP",
        },
    },
    "Software Development": {
        "purpose": "Software Development",
        "description": "Creates safe development datasets for product teams while preserving structural patterns and reducing privacy risk.",
        "privacyLevel": "Medium",
        "objectives": [
            "Protect identities",
            "Support feature development",
            "Preserve schema fidelity",
            "Reduce disclosure risk",
        ],
        "recommendedFor": ["Development", "Staging", "Integration testing", "App demos"],
        "notRecommendedFor": ["Public release", "External sharing", "Operational decisions"],
        "fields": {
            "patient_name": "REPLACE_FAKE",
            "phone": "MASK",
            "email": "REPLACE_FAKE",
            "address": "CITY_ONLY",
            "dob": "YEAR_ONLY",
            "dates": "MONTH_YEAR",
            "patient_id": "HASH",
            "clinical_notes": "KEEP",
        },
    },
    "Vendor Sharing": {
        "purpose": "Vendor Sharing",
        "description": "Prepares data for trusted third parties with stronger controls and reduced likelihood of identity recovery.",
        "privacyLevel": "High",
        "objectives": [
            "Remove direct identifiers",
            "Reduce quasi-identifiers",
            "Limit third-party exposure",
            "Preserve limited utility",
        ],
        "recommendedFor": ["Vendor review", "Partner analytics", "Managed services", "Contracts"],
        "notRecommendedFor": ["Public release", "Broad dissemination", "Patient follow-up"],
        "fields": {
            "patient_name": "REMOVE",
            "phone": "REMOVE",
            "email": "REMOVE",
            "address": "CITY_ONLY",
            "dob": "YEAR_ONLY",
            "dates": "SHIFT_DATE",
            "patient_id": "HASH",
            "clinical_notes": "REMOVE",
        },
    },
    "Public Release": {
        "purpose": "Public Release",
        "description": "Designed for publishing healthcare datasets where patient identity should not be reasonably recoverable while preserving useful clinical information whenever possible.",
        "privacyLevel": "Maximum",
        "objectives": [
            "Remove direct identifiers",
            "Reduce quasi-identifiers",
            "Minimize re-identification risk",
            "Preserve clinical usefulness where possible",
        ],
        "recommendedFor": ["Public datasets", "Academic publications", "Demonstrations", "Open research", "Educational examples"],
        "notRecommendedFor": ["Operational hospital systems", "Patient follow-up", "Identity matching", "Care coordination"],
        "fields": {
            "patient_name": "REMOVE",
            "phone": "REMOVE",
            "email": "REMOVE",
            "address": "STATE_ONLY",
            "dob": "YEAR_ONLY",
            "dates": "YEAR_ONLY",
            "patient_id": "HASH",
            "medical_record_number": "REMOVE",
            "clinical_notes": "REMOVE",
        },
    },
    "Education": {
        "purpose": "Education",
        "description": "Creates safe teaching examples that preserve the structure of healthcare data without exposing real patient identities.",
        "privacyLevel": "Medium",
        "objectives": [
            "Protect identities",
            "Support teaching",
            "Preserve sample structure",
            "Reduce disclosure risk",
        ],
        "recommendedFor": ["Training", "Teaching", "Classroom demos", "Workshops"],
        "notRecommendedFor": ["Operational decisions", "Public release", "Care coordination"],
        "fields": {
            "patient_name": "REPLACE_FAKE",
            "phone": "REMOVE",
            "email": "REPLACE_FAKE",
            "address": "CITY_ONLY",
            "dob": "YEAR_ONLY",
            "dates": "MONTH_YEAR",
            "patient_id": "HASH",
            "clinical_notes": "KEEP",
        },
    },
    "Healthcare Operations": {
        "purpose": "Healthcare Operations",
        "description": "Protects identities while preserving workflows that support care coordination and operational reviews.",
        "privacyLevel": "Medium",
        "objectives": [
            "Protect identifiers",
            "Preserve operational utility",
            "Reduce re-identification risk",
            "Support safe workflow access",
        ],
        "recommendedFor": ["Care teams", "Operations", "Clinical support", "Internal admin"],
        "notRecommendedFor": ["Public release", "Broad sharing", "Research publication"],
        "fields": {
            "patient_name": "REMOVE",
            "phone": "MASK",
            "email": "REMOVE",
            "address": "CITY_ONLY",
            "dob": "YEAR_ONLY",
            "dates": "SHIFT_DATE",
            "patient_id": "HASH",
            "clinical_notes": "KEEP",
        },
    },
    "Legal Review": {
        "purpose": "Legal Review",
        "description": "Prepares records for audits and compliance review while limiting unnecessary identity exposure.",
        "privacyLevel": "High",
        "objectives": [
            "Protect identities",
            "Support legal review",
            "Reduce disclosure risk",
            "Preserve context for review",
        ],
        "recommendedFor": ["Compliance review", "Audit support", "Investigations", "Internal legal work"],
        "notRecommendedFor": ["Public release", "Care coordination", "Operational patient outreach"],
        "fields": {
            "patient_name": "REMOVE",
            "phone": "REMOVE",
            "email": "REMOVE",
            "address": "STATE_ONLY",
            "dob": "YEAR_ONLY",
            "dates": "SHIFT_DATE",
            "patient_id": "HASH",
            "clinical_notes": "KEEP",
        },
    },
    "Security Audit": {
        "purpose": "Security Audit",
        "description": "Protects sensitive information during security assessments while preserving enough context for incident analysis.",
        "privacyLevel": "High",
        "objectives": [
            "Protect identities",
            "Support security review",
            "Preserve investigative context",
            "Reduce disclosure risk",
        ],
        "recommendedFor": ["Security review", "Incident investigations", "Assessments", "Internal audits"],
        "notRecommendedFor": ["Public release", "Broad dissemination", "Patient follow-up"],
        "fields": {
            "patient_name": "REMOVE",
            "phone": "REMOVE",
            "email": "REMOVE",
            "address": "CITY_ONLY",
            "dob": "YEAR_ONLY",
            "dates": "SHIFT_DATE",
            "patient_id": "HASH",
            "clinical_notes": "SCAN_FREE_TEXT",
        },
    },
}


def ensure_policy_dir() -> Path:
    PRESET_DIR.mkdir(parents=True, exist_ok=True)
    return PRESET_DIR


def list_preset_policies() -> List[Dict[str, Any]]:
    ensure_policy_dir()
    policies = []
    for name in DEFAULT_PRESETS:
        policy = load_preset_policy(name)
        if policy:
            policies.append(policy)
    return policies


def load_preset_policy(name: str) -> Dict[str, Any]:
    ensure_policy_dir()
    file_path = PRESET_DIR / f"{name.lower().replace(' ', '_')}.json"
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            return validate_policy(data)

    policy = DEFAULT_PRESETS.get(name)
    if policy is None:
        return None

    # Persist the bundled preset to disk so the UI can inspect it.
    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(policy, handle, indent=2)

    return validate_policy(policy)
