import httpx
import json
import os

SNOMED_API = "https://clinicaltables.nlm.nih.gov/api/snomed/v3/search"
CACHE_PATH = "store/snomed_cache.json"
LOOKUP_TIMEOUT_SECONDS = float(os.getenv("TERMINOLOGY_LOOKUP_TIMEOUT_SECONDS", "2.0"))

# Hardcoded common diagnoses → SNOMED CT codes
COMMON_SNOMED = {
    # Metabolic
    "diabetes type 2": {"code": "44054006", "display": "Diabetes mellitus type 2"},
    "diabetes type 1": {"code": "46635009", "display": "Diabetes mellitus type 1"},
    "diabetes": {"code": "73211009", "display": "Diabetes mellitus"},
    "obesity": {"code": "414916001", "display": "Obesity"},
    "hypothyroidism": {"code": "40930008", "display": "Hypothyroidism"},
    "hyperthyroidism": {"code": "34010009", "display": "Hyperthyroidism"},

    # Cardiovascular
    "hypertension": {"code": "38341003", "display": "Hypertension"},
    "high blood pressure": {"code": "38341003", "display": "Hypertension"},
    "heart failure": {"code": "84114007", "display": "Heart failure"},
    "coronary artery disease": {"code": "53741008", "display": "Coronary artery disease"},
    "atrial fibrillation": {"code": "49436004", "display": "Atrial fibrillation"},
    "stroke": {"code": "230690007", "display": "Stroke"},
    "myocardial infarction": {"code": "22298006", "display": "Myocardial infarction"},
    "heart attack": {"code": "22298006", "display": "Myocardial infarction"},

    # Respiratory
    "asthma": {"code": "195967001", "display": "Asthma"},
    "copd": {"code": "13645005", "display": "Chronic obstructive pulmonary disease"},
    "pneumonia": {"code": "233604007", "display": "Pneumonia"},
    "covid-19": {"code": "840539006", "display": "COVID-19"},
    "covid19": {"code": "840539006", "display": "COVID-19"},
    "tuberculosis": {"code": "56717001", "display": "Tuberculosis"},

    # Mental Health
    "depression": {"code": "35489007", "display": "Depressive disorder"},
    "anxiety": {"code": "48694002", "display": "Anxiety disorder"},
    "schizophrenia": {"code": "58214004", "display": "Schizophrenia"},
    "bipolar disorder": {"code": "13746004", "display": "Bipolar disorder"},

    # Neurological
    "epilepsy": {"code": "84757009", "display": "Epilepsy"},
    "migraine": {"code": "37796009", "display": "Migraine"},
    "alzheimer": {"code": "26929004", "display": "Alzheimer disease"},
    "parkinson": {"code": "49049000", "display": "Parkinson disease"},

    # Musculoskeletal
    "arthritis": {"code": "3723001", "display": "Arthritis"},
    "rheumatoid arthritis": {"code": "69896004", "display": "Rheumatoid arthritis"},
    "osteoporosis": {"code": "64859006", "display": "Osteoporosis"},
    "fracture": {"code": "125605004", "display": "Fracture"},
    "back pain": {"code": "161891005", "display": "Back pain"},

    # Gastrointestinal
    "appendicitis": {"code": "74400008", "display": "Appendicitis"},
    "gastritis": {"code": "4556007", "display": "Gastritis"},
    "ulcer": {"code": "13200003", "display": "Peptic ulcer"},
    "crohn disease": {"code": "34000006", "display": "Crohn disease"},

    # Kidney
    "chronic kidney disease": {"code": "709044004", "display": "Chronic kidney disease"},
    "kidney failure": {"code": "42399005", "display": "Renal failure"},
    "kidney stone": {"code": "95570007", "display": "Kidney stone"},

    # Cancer
    "lung cancer": {"code": "363358000", "display": "Malignant neoplasm of lung"},
    "breast cancer": {"code": "254837009", "display": "Breast cancer"},
    "diabetes insipidus": {"code": "15771004", "display": "Diabetes insipidus"},

    # Infections
    "hiv": {"code": "86406008", "display": "HIV infection"},
    "hepatitis b": {"code": "66071002", "display": "Hepatitis B"},
    "hepatitis c": {"code": "50711007", "display": "Hepatitis C"},
    "malaria": {"code": "61462000", "display": "Malaria"},
    "dengue": {"code": "38362002", "display": "Dengue fever"},
}


def load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def lookup_snomed(condition_name: str) -> dict:
    """
    Look up SNOMED CT code for a condition name.
    Priority: built-in → cache → NLM API
    """
    cache_key = condition_name.lower().strip()

    # 1. Check built-in first
    if cache_key in COMMON_SNOMED:
        match = COMMON_SNOMED[cache_key]
        return {
            "found": True,
            "code": match["code"],
            "display": match["display"],
            "system": "http://snomed.info/sct",
            "source": "built_in"
        }

    # 2. Check cache
    cache = load_cache()
    if cache_key in cache:
        return cache[cache_key]

    # 3. Call NLM SNOMED API
    try:
        response = httpx.get(
            SNOMED_API,
            params={
                "terms": condition_name,
                "df": "code,display",
                "maxList": 1
            },
            timeout=LOOKUP_TIMEOUT_SECONDS
        )

        data = response.json()

        if data and data[0] > 0 and data[3]:
            best_match = data[3][0]
            result = {
                "found": True,
                "code": best_match[0],
                "display": best_match[1],
                "system": "http://snomed.info/sct",
                "source": "api"
            }
        else:
            result = {
                "found": False,
                "code": None,
                "display": condition_name,
                "system": "http://snomed.info/sct",
                "source": "none"
            }

        # Save to cache
        cache[cache_key] = result
        save_cache(cache)
        return result

    except Exception as e:
        return {
            "found": False,
            "code": None,
            "display": condition_name,
            "system": "http://snomed.info/sct",
            "source": "error",
            "error": str(e)
        }
