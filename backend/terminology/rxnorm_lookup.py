import httpx
import json
import os

RXNORM_API = "https://rxnav.nlm.nih.gov/REST/drugs.json"
RXNORM_SEARCH_API = "https://rxnav.nlm.nih.gov/REST/approximateTerm.json"
CACHE_PATH = "store/rxnorm_cache.json"
LOOKUP_TIMEOUT_SECONDS = float(os.getenv("TERMINOLOGY_LOOKUP_TIMEOUT_SECONDS", "2.0"))

COMMON_RXNORM = {
    # Diabetes
    "metformin": {"code": "860975", "display": "Metformin 500 MG Oral Tablet"},
    "insulin": {"code": "253182", "display": "Insulin"},
    "glipizide": {"code": "310488", "display": "Glipizide 5 MG Oral Tablet"},

    # Cardiovascular
    "aspirin": {"code": "1191", "display": "Aspirin"},
    "atorvastatin": {"code": "83367", "display": "Atorvastatin"},
    "lisinopril": {"code": "29046", "display": "Lisinopril"},
    "amlodipine": {"code": "17767", "display": "Amlodipine"},
    "warfarin": {"code": "11289", "display": "Warfarin"},
    "clopidogrel": {"code": "174742", "display": "Clopidogrel"},
    "metoprolol": {"code": "6918", "display": "Metoprolol"},
    "losartan": {"code": "203160", "display": "Losartan"},
    "furosemide": {"code": "4603", "display": "Furosemide"},

    # Antibiotics
    "amoxicillin": {"code": "723", "display": "Amoxicillin"},
    "azithromycin": {"code": "18631", "display": "Azithromycin"},
    "ciprofloxacin": {"code": "2551", "display": "Ciprofloxacin"},
    "doxycycline": {"code": "3310", "display": "Doxycycline"},
    "penicillin": {"code": "7980", "display": "Penicillin"},

    # Pain/Inflammation
    "ibuprofen": {"code": "5640", "display": "Ibuprofen"},
    "paracetamol": {"code": "161", "display": "Acetaminophen"},
    "acetaminophen": {"code": "161", "display": "Acetaminophen"},
    "naproxen": {"code": "7258", "display": "Naproxen"},
    "diclofenac": {"code": "3355", "display": "Diclofenac"},
    "tramadol": {"code": "41493", "display": "Tramadol"},
    "morphine": {"code": "7052", "display": "Morphine"},

    # Respiratory
    "salbutamol": {"code": "435", "display": "Albuterol"},
    "albuterol": {"code": "435", "display": "Albuterol"},
    "prednisolone": {"code": "8638", "display": "Prednisolone"},
    "montelukast": {"code": "203323", "display": "Montelukast"},

    # Mental Health
    "sertraline": {"code": "36437", "display": "Sertraline"},
    "fluoxetine": {"code": "4493", "display": "Fluoxetine"},
    "amitriptyline": {"code": "704", "display": "Amitriptyline"},
    "diazepam": {"code": "3322", "display": "Diazepam"},

    # Gastro
    "omeprazole": {"code": "7646", "display": "Omeprazole"},
    "pantoprazole": {"code": "40790", "display": "Pantoprazole"},
    "metoclopramide": {"code": "6845", "display": "Metoclopramide"},

    # Hormones
    "levothyroxine": {"code": "10582", "display": "Levothyroxine"},

    # Vitamins/Supplements
    "vitamin d": {"code": "11253", "display": "Vitamin D"},
    "folic acid": {"code": "4511", "display": "Folic Acid"},
    "iron": {"code": "27311", "display": "Ferrous Sulfate"},
    "hydroxychloroquine": {"code": "1049707", "display": "Hydroxychloroquine 200 MG Oral Tablet"},
}


def load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def lookup_rxnorm(medication_name: str) -> dict:
    """
    Look up RxNorm code for a medication.
    Priority: built-in → cache → RxNorm API
    """
    cache_key = medication_name.lower().strip()

    # 1. Check built-in first
    if cache_key in COMMON_RXNORM:
        match = COMMON_RXNORM[cache_key]
        return {
            "found": True,
            "code": match["code"],
            "display": match["display"],
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "source": "built_in"
        }

    # 2. Check cache
    cache = load_cache()
    if cache_key in cache:
        return cache[cache_key]

    # 3. Call RxNorm API
    try:
        response = httpx.get(
            RXNORM_SEARCH_API,
            params={
                "term": medication_name,
                "maxEntries": 1
            },
            timeout=LOOKUP_TIMEOUT_SECONDS
        )

        if response.status_code != 200:
            raise RuntimeError(f"RxNorm API returned {response.status_code}")

        try:
            data = response.json()
        except ValueError:
            raise RuntimeError("RxNorm API returned invalid JSON")

        candidates = data.get(
            "approximateGroup", {}
        ).get("candidate", [])

        if candidates:
            best = candidates[0]
            result = {
                "found": True,
                "code": best.get("rxcui"),
                "display": best.get("name", medication_name),
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "source": "api"
            }
        else:
            result = {
                "found": False,
                "code": None,
                "display": medication_name,
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "source": "none"
            }

        cache[cache_key] = result
        save_cache(cache)
        return result

    except Exception as e:
        return {
            "found": False,
            "code": None,
            "display": medication_name,
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "source": "error",
            "error": str(e)
        }
