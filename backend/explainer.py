from google import genai
import os
from dotenv import load_dotenv
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

load_dotenv(os.path.join(PROJECT_DIR, ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

MODEL_NAME = "gemini-2.5-flash"
_client = None


def get_gemini_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")
        _client = genai.Client(api_key=api_key)
    return _client


def explain_errors(errors: list, original_data: dict) -> list:
    """
    Hybrid explainer:
    - Rule-based errors already have explanations
    - AI-needed errors go to Gemini
    """
    explained = []

    for error in errors:
        if error["type"] == "rule_based":
            # Already has explanation, just append
            explained.append(error)

        elif error["type"] == "ai_needed":
            # Send to Gemini for explanation
            ai_explanation = ask_gemini(error, original_data)
            error["explanation"] = ai_explanation.get("explanation")
            error["suggested_fix"] = ai_explanation.get("suggested_fix")
            error["fix"] = ai_explanation.get("fix")
            explained.append(error)

    return explained


def ask_gemini(error: dict, original_data: dict) -> dict:
    """Ask Gemini to explain a FHIR error and suggest a fix"""

    prompt = f"""
You are a FHIR expert assistant helping a developer fix FHIR validation errors.

The developer is working with this FHIR Patient resource:
{json.dumps(original_data, indent=2)}

They got this validation error:
- Field: {error['field']}
- Error Message: {error['message']}
- Received Value: {error['received']}

Please respond ONLY in this JSON format, nothing else:
{{
    "explanation": "Plain English explanation of why this error occurred",
    "suggested_fix": "Clear instruction on how to fix it",
    "fix": "The corrected value or null if you cannot determine it"
}}
"""

    try:
        response = get_gemini_client().models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        text = response.text.strip()

        # Clean markdown if Gemini wraps in ```json
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        return json.loads(text.strip())

    except Exception as e:
        return {
            "explanation": "An AI explanation is unavailable right now due to a service issue. For date fields, please ensure the value is valid and formatted as YYYY-MM-DD.",
            "suggested_fix": "Please review the FHIR documentation for date formatting and use YYYY-MM-DD.",
            "fix": None
        }
