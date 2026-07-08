import re
from typing import Any

from terminology.loinc_lookup import lookup_loinc
from terminology.snomed_lookup import lookup_snomed
from terminology.rxnorm_lookup import lookup_rxnorm
from terminology.icd10_lookup import lookup_icd10

SYSTEM_LOOKUP = {
    "http://loinc.org": lookup_loinc,
    "http://snomed.info/sct": lookup_snomed,
    "http://www.nlm.nih.gov/research/umls/rxnorm": lookup_rxnorm,
    "http://hl7.org/fhir/sid/icd-10": lookup_icd10,
}


def extract_lookup_text(value: Any) -> str | None:
    """Extract a lookup key from strings, CodeableConcepts, or simple objects."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        # Prefer explicit text before code or display extraction
        text = value.get("text")
        if text:
            return str(text).strip()

        # If a CodeableConcept is present, prefer code over display
        coding = value.get("coding")
        if isinstance(coding, list) and coding:
            first = coding[0]
            if isinstance(first, dict):
                return (first.get("code") or first.get("display") or first.get("text") or "").strip() or None

        return (value.get("code") or value.get("display") or "").strip() or None
    return None


def extract_primary_coding(value: Any) -> dict | None:
    """Return the first coding object from a CodeableConcept if present."""
    if not isinstance(value, dict):
        return None
    coding = value.get("coding")
    if isinstance(coding, list) and coding:
        first = coding[0]
        if isinstance(first, dict):
            return first
    return None


def lookup_by_system(system: str, code: str) -> dict | None:
    """Validate a code by system if supported."""
    if not system or not code:
        return None
    finder = SYSTEM_LOOKUP.get(system)
    if not finder:
        return None
    return finder(str(code))


def normalize_code_input(value: Any) -> str | None:
    """Normalize a code value for lookup.

    Handles string values, CodeableConcept objects, and nested properties.
    """
    if value is None:
        return None
    if isinstance(value, dict):
        # Prefer explicit code text from CodeableConcept-like objects.
        primary = extract_primary_coding(value)
        if primary:
            return (primary.get("code") or primary.get("display") or primary.get("text") or "").strip() or None
        return extract_lookup_text(value)
    return extract_lookup_text(value)


def is_code_string(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    return False


def is_coding_object(value: Any) -> bool:
    return isinstance(value, dict) and isinstance(value.get("coding"), list) and bool(value["coding"])
