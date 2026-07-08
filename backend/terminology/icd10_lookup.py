
import httpx
import json
import os
import re
from api_key_manager import store_path

ICD10_API = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
CACHE_PATH = store_path("icd10_cache.json")
LOOKUP_TIMEOUT_SECONDS = float(os.getenv("TERMINOLOGY_LOOKUP_TIMEOUT_SECONDS", "2.0"))

COMMON_ICD10 = {
    "e11.9": {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications"},
    "diabetes type 2": {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications"},
    "type 2 diabetes": {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications"},
    "diabetes": {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications"},
    "hypertension": {"code": "I10", "display": "Essential (primary) hypertension"},
    "high blood pressure": {"code": "I10", "display": "Essential (primary) hypertension"},
    "asthma": {"code": "J45.909", "display": "Other specified asthma, uncomplicated"},
    "copd": {"code": "J44.9", "display": "Chronic obstructive pulmonary disease, unspecified"},
    "pneumonia": {"code": "J18.9", "display": "Pneumonia, unspecified organism"},
    "depression": {"code": "F32.9", "display": "Major depressive disorder, single episode, unspecified"},
    "anxiety": {"code": "F41.9", "display": "Anxiety disorder, unspecified"},
    "migraine": {"code": "G43.909", "display": "Migraine, unspecified, not intractable, without status migrainosus"},
    "urinary tract infection": {"code": "N39.0", "display": "Urinary tract infection, site not specified"},
    "uti": {"code": "N39.0", "display": "Urinary tract infection, site not specified"},
    "acute bronchitis": {"code": "J20.9", "display": "Acute bronchitis, unspecified"},
    "bronchitis": {"code": "J20.9", "display": "Acute bronchitis, unspecified"},
    "otitis media": {"code": "H66.90", "display": "Otitis media, unspecified, unspecified ear"},
    "flu": {"code": "J11.1", "display": "Influenza due to unidentified influenza virus with other respiratory manifestations"},
    "influenza": {"code": "J11.1", "display": "Influenza due to unidentified influenza virus with other respiratory manifestations"},
    "congestive heart failure": {"code": "I50.9", "display": "Heart failure, unspecified"},
    "heart failure": {"code": "I50.9", "display": "Heart failure, unspecified"},
    "chronic kidney disease": {"code": "N18.9", "display": "Chronic kidney disease, unspecified"},
    "arthritis": {"code": "M13.9", "display": "Arthritis, unspecified"},
    "back pain": {"code": "M54.9", "display": "Dorsalgia, unspecified"},
    "anemia": {"code": "D64.9", "display": "Anemia, unspecified"},
    "fever": {"code": "R50.9", "display": "Fever, unspecified"},
    "cough": {"code": "R05", "display": "Cough"},
    "headache": {"code": "R51", "display": "Headache"},
    "low back pain": {"code": "M54.5", "display": "Low back pain"},
    "fatigue": {"code": "R53.83", "display": "Other fatigue"},
    "common cold": {"code": "J00", "display": "Acute nasopharyngitis [common cold]"},
    "paralysis agitans": {"code": "G20", "display": "Parkinson disease"},
    "parkinson disease": {"code": "G20", "display": "Parkinson disease"},
    "parkinson's disease": {"code": "G20", "display": "Parkinson disease"},
    "parkinsons disease": {"code": "G20", "display": "Parkinson disease"},
    "acute appendicitis with generalized peritonitis": {"code": "K35.20", "display": "Acute appendicitis with generalized peritonitis, without abscess"},
    "copd exacerbation": {"code": "J44.1", "display": "Chronic obstructive pulmonary disease with (acute) exacerbation"},
    "atypical chest pain": {"code": "R07.89", "display": "Other chest pain"},
    "essential hypertenstion": {"code": "I10", "display": "Essential (primary) hypertension"},
    "essential hypertension": {"code": "I10", "display": "Essential (primary) hypertension"},
}


def load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def _normalize_lookup_term(term: str) -> str:
    normalized = term.strip().lower()
    normalized = normalized.replace("’", "'").replace("-", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def lookup_icd10(term: str) -> dict:
    """Look up ICD-10-CM code for a diagnosis or code-like string."""
    if not term:
        return {"found": False, "code": None, "display": None, "system": "http://hl7.org/fhir/sid/icd-10", "source": "none"}

    cache_key = _normalize_lookup_term(term)

    if cache_key in COMMON_ICD10:
        match = COMMON_ICD10[cache_key]
        return {
            "found": True,
            "code": match["code"],
            "display": match["display"],
            "system": "http://hl7.org/fhir/sid/icd-10",
            "source": "built_in"
        }

    cache = load_cache()
    if cache_key in cache:
        return cache[cache_key]

    if cache_key in COMMON_ICD10:
        match = COMMON_ICD10[cache_key]
        return {
            "found": True,
            "code": match["code"],
            "display": match["display"],
            "system": "http://hl7.org/fhir/sid/icd-10",
            "source": "built_in"
        }

    typo_aliases = {
        "essential hypertenstion": "essential hypertension",
        "copd exacerviation": "copd exacerbation",
        "copd exacerbation": "copd exacerbation",
    }
    if cache_key in typo_aliases:
        canonical = typo_aliases[cache_key]
        match = COMMON_ICD10[canonical]
        result = {
            "found": True,
            "code": match["code"],
            "display": match["display"],
            "system": "http://hl7.org/fhir/sid/icd-10",
            "source": "built_in"
        }
        cache[cache_key] = result
        save_cache(cache)
        return result

    if term.upper().startswith(("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z")) and ("." in term or len(term) >= 3):
        result = {
            "found": True,
            "code": term.upper(),
            "display": term.upper(),
            "system": "http://hl7.org/fhir/sid/icd-10",
            "source": "direct"
        }
        cache[cache_key] = result
        save_cache(cache)
        return result

    try:
        response = httpx.get(
            ICD10_API,
            params={"terms": term, "df": "code,display", "maxList": 1},
            timeout=LOOKUP_TIMEOUT_SECONDS,
        )
        data = response.json()

        if data and data[0] > 0 and data[3]:
            best_match = data[3][0]
            result = {
                "found": True,
                "code": best_match[0],
                "display": best_match[1],
                "system": "http://hl7.org/fhir/sid/icd-10",
                "source": "api"
            }
        else:
            result = {
                "found": False,
                "code": None,
                "display": term,
                "system": "http://hl7.org/fhir/sid/icd-10",
                "source": "none"
            }

        cache[cache_key] = result
        save_cache(cache)
        return result
    except Exception as e:
        return {
            "found": False,
            "code": None,
            "display": term,
            "system": "http://hl7.org/fhir/sid/icd-10",
            "source": "error",
            "error": str(e)
        }
