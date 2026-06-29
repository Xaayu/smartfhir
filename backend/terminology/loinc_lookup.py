import httpx
import json
import os

LOINC_API = "https://clinicaltables.nlm.nih.gov/api/loinc_items/v3/search"
CACHE_PATH = "store/loinc_cache.json"
LOOKUP_TIMEOUT_SECONDS = float(os.getenv("TERMINOLOGY_LOOKUP_TIMEOUT_SECONDS", "2.0"))

COMMON_LOINC = {
    "blood pressure": {"code": "55284-4", "display": "Blood pressure systolic and diastolic", "class": "VITALS"},
    "systolic blood pressure": {"code": "8480-6", "display": "Systolic blood pressure", "class": "VITALS"},
    "diastolic blood pressure": {"code": "8462-4", "display": "Diastolic blood pressure", "class": "VITALS"},
    "heart rate": {"code": "8867-4", "display": "Heart rate", "class": "VITALS"},
    "pulse": {"code": "8867-4", "display": "Heart rate", "class": "VITALS"},
    "temperature": {"code": "8310-5", "display": "Body temperature", "class": "VITALS"},
    "body temperature": {"code": "8310-5", "display": "Body temperature", "class": "VITALS"},
    "glucose": {"code": "2339-0", "display": "Glucose [Mass/volume] in Blood", "class": "CHEM"},
    "hemoglobin": {"code": "718-7", "display": "Hemoglobin [Mass/volume] in Blood", "class": "HEM/BC"},
    "oxygen saturation": {"code": "2708-6", "display": "Oxygen saturation in Arterial blood", "class": "VITALS"},
    "spo2": {"code": "2708-6", "display": "Oxygen saturation in Arterial blood", "class": "VITALS"},
    "respiratory rate": {"code": "9279-1", "display": "Respiratory rate", "class": "VITALS"},
    "weight": {"code": "29463-7", "display": "Body weight", "class": "VITALS"},
    "height": {"code": "8302-2", "display": "Body height", "class": "VITALS"},
    "bmi": {"code": "39156-5", "display": "Body mass index (BMI)", "class": "VITALS"},
    "cholesterol": {"code": "2093-3", "display": "Cholesterol [Mass/volume] in Serum or Plasma", "class": "CHEM"},
    "creatinine": {"code": "2160-0", "display": "Creatinine [Mass/volume] in Serum or Plasma", "class": "CHEM"},
    "sodium": {"code": "2951-2", "display": "Sodium [Moles/volume] in Serum or Plasma", "class": "CHEM"},
    "potassium": {"code": "2823-3", "display": "Potassium [Moles/volume] in Serum or Plasma", "class": "CHEM"},
}

def lookup_loinc(test_name: str) -> dict:
    # This short definition was intentionally removed in favor of the
    # full implementation below which includes API lookup and caching.
    # Keep this stub only for historical context.
    raise RuntimeError("fallback lookup removed; use main lookup_loinc implementation")


def load_cache() -> dict:
    """Load local LOINC cache to avoid repeated API calls"""
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    """Save LOINC lookup results locally"""
    # Ensure cache directory exists
    dir_path = os.path.dirname(CACHE_PATH)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def lookup_loinc(test_name: str) -> dict:
    """
    Look up LOINC code for a test name.
    Returns code, display name, and category.
    Uses local cache first to avoid repeated API calls.
    """
    cache = load_cache()

    # Normalize key
    cache_key = test_name.lower().strip()

    # 1) Hardcoded common terms have priority as a fallback for vitals/questions
    if cache_key in COMMON_LOINC:
        match = COMMON_LOINC[cache_key]
        result = {
            "found": True,
            "code": match["code"],
            "display": match["display"],
            "class": match.get("class"),
            "system": "http://loinc.org",
            "source": "built_in"
        }
        return result

    # 2) Check cache
    if cache_key in cache:
        cached = cache[cache_key]
        # mark source if missing
        if "source" not in cached:
            cached["source"] = "cache"
        return cached

    try:
        response = httpx.get(
            LOINC_API,
            params={
                "type": "question",
                "terms": test_name,
                "df": "LOINC_NUM,LONG_COMMON_NAME,CLASS",
                "maxList": 1
            },
            timeout=LOOKUP_TIMEOUT_SECONDS
        )

        data = response.json()

        # Response format: [total, [codes], null, [[code, name, class]]]
        if data and data[0] > 0 and data[3]:
            best_match = data[3][0]
            result = {
                "found": True,
                "code": best_match[0],
                "display": best_match[1],
                "class": best_match[2] if len(best_match) > 2 else None,
                "system": "http://loinc.org"
            }
        else:
            result = {
                "found": False,
                "code": None,
                "display": test_name,
                "class": None,
                "system": "http://loinc.org"
            }

        # Save to cache
        cache[cache_key] = result
        save_cache(cache)

        return result

    except Exception as e:
        return {
            "found": False,
            "code": None,
            "display": test_name,
            "class": None,
            "system": "http://loinc.org",
            "error": str(e)
        }


def get_observation_category(loinc_class: str) -> dict:
    """Map LOINC class to FHIR observation category"""
    category_map = {
        "CHEM": "laboratory",
        "HEM/BC": "laboratory",
        "MICRO": "laboratory",
        "UA": "laboratory",
        "COAG": "laboratory",
        "DRUG/TOX": "laboratory",
        "VITALS": "vital-signs",
        "CARDIO": "vital-signs",
        "PULM": "vital-signs",
    }

    fhir_category = category_map.get(
        loinc_class, "laboratory"
    ) if loinc_class else "laboratory"

    return {
        "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
            "code": fhir_category,
            "display": fhir_category.replace("-", " ").title()
        }]
    }
