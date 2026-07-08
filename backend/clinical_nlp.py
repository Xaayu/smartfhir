"""
Clinical NLP helpers powered by medSpaCy.

The public entry point is analyze_clinical_note(text: str) -> dict.
It intentionally keeps the returned shape small and stable for API use while
doing the heavier section/context work internally.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Optional


HEADER_RE = re.compile(
    r"""
    ^\s*
    (?P<header>[A-Z][A-Za-z0-9 /&(),.'-]{1,80})
    \s*:?\s*$
    """,
    re.VERBOSE,
)

INLINE_HEADER_RE = re.compile(
    r"""
    (?im)
    ^\s*
    (?P<header>[A-Z][A-Za-z0-9 /&(),.'-]{1,80})
    \s*:\s*
    (?P<body>.+?)\s*$
    """,
    re.VERBOSE,
)

VITAL_SECTION_HINTS = {
    "vitals",
    "vital signs",
    "physical exam",
    "physical examination",
    "exam",
    "pe",
}

MEDICATION_SECTION_HINTS = {
    "medications",
    "current medications",
    "home medications",
    "meds",
    "current meds",
}

IGNORED_SECTION_HINTS = {
    "family history",
    "social history",
    "past surgical history",
}

PROBLEM_LABEL_HINTS = {
    "condition",
    "problem",
    "diagnosis",
    "disease",
    "disorder",
    "symptom",
    "finding",
    "sign",
}

MEDICATION_LABEL_HINTS = {
    "med",
    "medication",
    "drug",
    "treatment",
    "rx",
}

DOSE_RE = re.compile(
    r"""
    (?P<dose>
      \b\d+(?:\.\d+)?\s*
      (?:mg|mcg|g|gram|grams|ml|mL|units?|iu|meq|%)
      (?:\s*(?:po|iv|sc|subq|bid|tid|qid|qhs|q\d+h|daily|nightly|weekly|prn|twice\s+daily|once\s+daily))*\b
      |
      \b(?:bid|tid|qid|qhs|prn|daily|nightly|weekly|twice\s+daily|once\s+daily)\b
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

VITAL_PATTERNS = {
    "blood_pressure": re.compile(
        r"\b(?:bp|blood pressure)\b\s*(?:is|:|=)?\s*(?P<value>\d{2,3}\s*/\s*\d{2,3})\b",
        re.IGNORECASE,
    ),
    "heart_rate": re.compile(
        r"\b(?:hr|heart rate|pulse)\b\s*(?:is|:|=)?\s*(?P<value>\d{2,3})\b",
        re.IGNORECASE,
    ),
    "respiratory_rate": re.compile(
        r"\b(?:rr|respiratory rate|resp rate)\b\s*(?:is|:|=)?\s*(?P<value>\d{1,3})\b",
        re.IGNORECASE,
    ),
    "spo2": re.compile(
        r"\b(?:spo2|o2 sat|oxygen saturation)\b\s*(?:is|:|=)?\s*(?P<value>\d{2,3}\s*%?)\b",
        re.IGNORECASE,
    ),
    "temperature": re.compile(
        r"\b(?:temp|temperature|t)\b\s*(?:is|:|=)?\s*(?P<value>\d{2,3}(?:\.\d+)?)\b",
        re.IGNORECASE,
    ),
}


@dataclass(frozen=True)
class Section:
    title: str
    normalized_title: str
    text: str
    start: int
    end: int


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _is_header_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 90:
        return False
    if stripped.endswith("."):
        return False
    match = HEADER_RE.match(stripped)
    if not match:
        return False
    words = stripped.replace(":", "").split()
    return len(words) <= 8


def _segment_sections(text: str) -> list[Section]:
    """
    Deterministically segment messy clinical notes by header-like lines.

    This avoids relying on exact section names, but it still normalizes common
    section titles so downstream rules can bind vitals to exam/vitals only.
    """
    if not text.strip():
        return []

    sections: list[Section] = []
    lines = text.splitlines(keepends=True)
    cursor = 0
    current_title = "Unsectioned"
    current_start = 0
    current_body_start = 0

    for line in lines:
        line_start = cursor
        line_end = cursor + len(line)
        inline = INLINE_HEADER_RE.match(line.strip())
        is_header = _is_header_line(line)

        if is_header or inline:
            if current_body_start < line_start:
                body = text[current_body_start:line_start].strip()
                if body:
                    sections.append(
                        Section(
                            title=current_title,
                            normalized_title=_normalize_header(current_title),
                            text=body,
                            start=current_body_start,
                            end=line_start,
                        )
                    )

            if inline:
                current_title = inline.group("header").strip()
                current_body_start = line_start + line.find(inline.group("body"))
            else:
                current_title = line.strip().rstrip(":")
                current_body_start = line_end
            current_start = line_start

        cursor = line_end

    if current_body_start < len(text):
        body = text[current_body_start:].strip()
        if body:
            sections.append(
                Section(
                    title=current_title,
                    normalized_title=_normalize_header(current_title),
                    text=body,
                    start=current_body_start,
                    end=len(text),
                )
            )

    if not sections:
        return [
            Section(
                title="Unsectioned",
                normalized_title="unsectioned",
                text=text.strip(),
                start=0,
                end=len(text),
            )
        ]

    return sections


def _section_has_hint(section: Section, hints: set[str]) -> bool:
    title = section.normalized_title
    return any(hint in title for hint in hints)


def _section_for_span(sections: list[Section], start: int, end: int) -> Optional[Section]:
    for section in sections:
        if section.start <= start and end <= section.end:
            return section
    return None


@lru_cache(maxsize=1)
def _get_nlp():
    try:
        import medspacy
    except ImportError as exc:
        raise RuntimeError(
            "medspacy is required for analyze_clinical_note. "
            "Install it with `pip install medspacy`."
        ) from exc

    nlp = medspacy.load()
    return nlp


def _safe_extension_value(ent, name: str, default=False):
    try:
        return getattr(ent._, name)
    except Exception:
        return default


def _entity_category(ent, section: Optional[Section]) -> str:
    label = str(getattr(ent, "label_", "") or "").lower()
    if any(hint in label for hint in MEDICATION_LABEL_HINTS):
        return "MEDICATION"
    if section and _section_has_hint(section, MEDICATION_SECTION_HINTS):
        return "MEDICATION"
    if any(hint in label for hint in PROBLEM_LABEL_HINTS):
        if "symptom" in label:
            return "SYMPTOM"
        return "CONDITION"
    return "CONDITION"


def _extract_dose_info(entity_text: str, section_text: str) -> str:
    """
    Bind dose-like text from the entity's line, not from the full document.
    """
    if not section_text:
        return ""

    for raw_line in section_text.splitlines():
        if entity_text.lower() not in raw_line.lower():
            continue
        match = DOSE_RE.search(raw_line)
        if match:
            return re.sub(r"\s+", " ", match.group("dose")).strip()

    return ""


def _dedupe_dicts(items: Iterable[dict], key: str = "text") -> list[dict]:
    seen = set()
    deduped = []
    for item in items:
        value = str(item.get(key, "")).lower().strip()
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(item)
    return deduped


def _dedupe_strings(items: Iterable[str]) -> list[str]:
    seen = set()
    deduped = []
    for item in items:
        value = re.sub(r"\s+", " ", str(item)).strip()
        key = value.lower()
        if not value or key in seen:
            continue
        seen.add(key)
        deduped.append(value)
    return deduped


def _extract_vitals(sections: list[Section]) -> dict:
    """
    Pull vitals only from exam/vitals sections to prevent historical leakage.
    """
    vitals = {}
    for section in sections:
        if not _section_has_hint(section, VITAL_SECTION_HINTS):
            continue
        for name, pattern in VITAL_PATTERNS.items():
            if name in vitals:
                continue
            match = pattern.search(section.text)
            if match:
                vitals[name] = re.sub(r"\s+", "", match.group("value"))
    return vitals


def _extract_medications_from_sections(sections: list[Section]) -> list[dict]:
    """
    Generic section-based medication fallback.

    This does not hardcode medication names. It only considers medication-like
    sections and extracts the text before a dose/frequency pattern on each line.
    """
    medications = []
    for section in sections:
        if not _section_has_hint(section, MEDICATION_SECTION_HINTS):
            continue
        for raw_line in re.split(r"[\n;]+", section.text):
            line = raw_line.strip(" -\t")
            if not line:
                continue
            dose_match = DOSE_RE.search(line)
            if not dose_match:
                continue
            name = line[: dose_match.start()].strip(" -,:")
            name = re.sub(r"^(?:continue|start|resume|hold)\s+", "", name, flags=re.IGNORECASE)
            if not name or len(name.split()) > 5:
                continue
            medications.append(
                {
                    "text": name,
                    "dose_info": re.sub(r"\s+", " ", dose_match.group("dose")).strip(),
                }
            )
    return medications


def analyze_clinical_note(text: str) -> dict:
    """
    Analyze a raw clinical note into active problems, active medications,
    vitals, and ignored context-filtered concepts.

    The returned dictionary intentionally matches the requested public contract:

    {
        "active_problems": [{"text": "HFrEF", "category": "CONDITION"}],
        "active_medications": [{"text": "Carvedilol", "dose_info": "12.5 mg BID"}],
        "vitals": {"blood_pressure": "142/88", "heart_rate": "92"},
        "negated_or_ignored": ["chest pain", "palpitations"]
    }

    Notes:
    - medSpaCy supplies clinical context such as negation/historical status.
    - This function does not hardcode clinical concept strings. It consumes
      entities produced by the configured medSpaCy/spaCy pipeline.
    - Historical concepts are included in negated_or_ignored to preserve the
      exact requested output schema.
    """
    if not isinstance(text, str):
        raise TypeError("analyze_clinical_note expects text to be a string.")

    cleaned_text = text.strip()
    if not cleaned_text:
        return {
            "active_problems": [],
            "active_medications": [],
            "vitals": {},
            "negated_or_ignored": [],
        }

    sections = _segment_sections(cleaned_text)
    nlp = _get_nlp()
    doc = nlp(cleaned_text)

    active_problems = []
    active_medications = []
    negated_or_ignored = []

    for ent in doc.ents:
        ent_text = re.sub(r"\s+", " ", ent.text).strip()
        if not ent_text:
            continue

        section = _section_for_span(sections, ent.start_char, ent.end_char)
        is_negated = bool(_safe_extension_value(ent, "is_negated", False))
        is_historical = bool(_safe_extension_value(ent, "is_historical", False))
        is_family = bool(_safe_extension_value(ent, "is_family", False))
        in_ignored_section = bool(section and _section_has_hint(section, IGNORED_SECTION_HINTS))

        if is_negated or is_historical or is_family or in_ignored_section:
            negated_or_ignored.append(ent_text)
            continue

        category = _entity_category(ent, section)
        if category == "MEDICATION":
            dose_info = _extract_dose_info(ent_text, section.text if section else cleaned_text)
            active_medications.append({"text": ent_text, "dose_info": dose_info})
        else:
            active_problems.append({"text": ent_text, "category": category})

    active_medications.extend(_extract_medications_from_sections(sections))

    return {
        "active_problems": _dedupe_dicts(active_problems),
        "active_medications": _dedupe_dicts(active_medications),
        "vitals": _extract_vitals(sections),
        "negated_or_ignored": _dedupe_strings(negated_or_ignored),
    }
