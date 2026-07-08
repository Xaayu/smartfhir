from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from api_key_manager import (
    create_key,
    validate_key,
    record_usage,
    get_usage,
    get_admin_metrics,
    delete_user,
    use_postgres,
    db_connect,
    init_api_database,
    store_dir,
    store_path,
)
from typing import Optional, List
from datetime import datetime, timezone


import json
import os
import time
import uuid

from validator import validate_patient
from explainer import explain_errors
from autofixer import autofix, generate_fix_summary
from mapper import (
    map_to_fhir,
    save_user_mapping,
    get_all_mappings,
    delete_user_mapping
)

from validators.observation_validator import (
    validate_observation,
    build_observation_resource
)

from validators.condition_validator import (
    validate_condition,
    build_condition_resource
)
from validators.encounter_validator import (
    CONDITIONS_STORE,
    validate_encounter,
    build_encounter_resource
)

from validators.medication_validator import (
    validate_medication,
    build_medication_resource
)

from hl7_converter import convert_hl7_to_fhir
from hl7_parser import HL7Parser
from clinical_nlp import analyze_clinical_note
import logging


# 2. Store manager functions (ADD HERE)
PATIENTS_STORE = store_path("patients.json")
OBSERVATIONS_STORE = store_path("observations.json")
API_KEY_REQUESTS_PATH = store_path("api_key_requests.json")
FEEDBACK_STORE = store_path("feedback.json")
API_KEY_REQUEST_WINDOW_SECONDS = 60 * 60
MAX_API_KEY_REQUESTS_PER_EMAIL = 3
MAX_API_KEY_REQUESTS_PER_IP = 10

app = FastAPI(
    title="MedTechTools",
    description="AI-Powered FHIR Validation, Explanation, Auto-Fix & HL7 v2 Conversion",
    version="1.0.0"
)

# Setup logging for startup diagnostics
logger = logging.getLogger("smartfhir")
logging.basicConfig(level=logging.INFO)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup"""
    if use_postgres():
        init_api_database()
        print("Using PostgreSQL storage for API keys and usage.")
    else:
        print(f"Using local file storage for API keys and usage: {store_dir()}")
    # Log resolved CORS origins for debugging deployed environment
    try:
        cors_origins = get_cors_origins()
        logger.info(f"Resolved CORS origins: {cors_origins}")
    except Exception as e:
        logger.exception("Error resolving CORS origins on startup")

# Note: OAuth routes removed for simplified email-only flow


def get_cors_origins() -> list:
    configured_origins = os.getenv("FRONTEND_ORIGINS", "")
    origins = [
        origin.strip().rstrip("/")
        for origin in configured_origins.split(",")
        if origin.strip()
    ]
    return origins or ["http://localhost:3000"]


# Add this RIGHT after app = FastAPI(...)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Key Middleware ─────────────────────────────────────
EXEMPT_PATHS = {
    "/",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/health",
    "/api/feedback",
    "/api/clinical-note/analyze",
    "/get-api-key",
    "/register",
    "/usage",
    "/admin/metrics",
    "/admin/feedback",
    "/admin/delete-user",
    "/api/hl7-to-fhir",
    "/_debug_cors",
    "/validate",
    "/explain-errors",
    "/autofix",
    "/map-validate",
    "/map",
    "/map-and-validate",
    "/observation/map-validate",
    "/condition/map-validate",
    "/encounter/map-validate",
    "/medication/map-validate",
    "/bundle",
    "/unified-bundle",
    # OAuth endpoints removed; simplified email registration used instead
}

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """Check API key on every request except exempt paths"""

    # Browser CORS preflight requests do not include API keys.
    if request.method == "OPTIONS":
        return await call_next(request)

    # Allow exempt paths through
    if request.url.path in EXEMPT_PATHS:
        return await call_next(request)

    # Get key from header
    api_key = request.headers.get("X-API-Key")

    # Validate
    result = validate_key(api_key)

    if not result["valid"]:
        return JSONResponse(
            status_code=401,
            content={
                "error": result["reason"],
                "message": result["message"],
                "get_key": "POST /register with your email"
            }
        )

    # Attach key info to request state
    request.state.api_key   = api_key
    request.state.email     = result["email"]
    request.state.calls_remaining = result["calls_remaining"]

    # Process request
    start = time.perf_counter()
    response = await call_next(request)
    response_time_ms = int((time.perf_counter() - start) * 1000)

    # Log usage after successful response. 4xx calls still count; 5xx does not.
    if response.status_code < 500:
        record_usage(
            api_key,
            request.url.path,
            request.method,
            response.status_code,
            response_time_ms
        )

    # Add usage info to response headers
    response.headers["X-Calls-Remaining"] = str(result["calls_remaining"] - 1)
    response.headers["X-Calls-Limit"]     = str(result["calls_limit"])

    return response



def load_store(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_store(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_list_store(path: str) -> list:
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass
    return []


@app.get("/_debug_cors")
def debug_cors():
    """Simple diagnostic endpoint that returns the resolved CORS origins."""
    return {"allowed_origins": get_cors_origins()}


def save_list_store(path: str, data: list):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def ensure_feedback_table():
    if not use_postgres():
        return

    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("create extension if not exists pgcrypto")
            cur.execute(
                """
                create table if not exists feedback_submissions (
                  id uuid primary key default gen_random_uuid(),
                  feedback text not null default '',
                  next_features jsonb not null default '[]'::jsonb,
                  email text,
                  page text,
                  ip text,
                  user_agent text,
                  submitted_at timestamptz not null default now(),
                  created_at timestamptz not null default now()
                )
                """
            )
            cur.execute(
                """
                create index if not exists idx_feedback_submissions_submitted_at
                on feedback_submissions (submitted_at desc)
                """
            )
            cur.execute(
                """
                create index if not exists idx_feedback_submissions_email
                on feedback_submissions (email)
                """
            )


def save_feedback_entry(entry: dict) -> dict:
    if use_postgres():
        ensure_feedback_table()
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into feedback_submissions (
                      feedback,
                      next_features,
                      email,
                      page,
                      ip,
                      user_agent,
                      submitted_at
                    )
                    values (%s, %s::jsonb, %s, %s, %s, %s, %s)
                    returning id, submitted_at
                    """,
                    (
                        entry["feedback"],
                        json.dumps(entry["next_features"]),
                        entry["email"],
                        entry["page"],
                        entry["ip"],
                        entry["user_agent"],
                        entry["submitted_at"],
                    ),
                )
                row = cur.fetchone()
                entry["id"] = str(row["id"])
                entry["submitted_at"] = row["submitted_at"].isoformat()
                return entry

    feedback_entries = load_list_store(FEEDBACK_STORE)
    feedback_entries.append(entry)
    save_list_store(FEEDBACK_STORE, feedback_entries)
    return entry


def load_feedback_entries() -> list:
    if use_postgres():
        ensure_feedback_table()
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                      id,
                      feedback,
                      next_features,
                      email,
                      page,
                      ip,
                      user_agent,
                      submitted_at
                    from feedback_submissions
                    order by submitted_at desc
                    limit 500
                    """
                )
                return [
                    {
                        "id": str(row["id"]),
                        "feedback": row["feedback"] or "",
                        "next_features": row["next_features"] or [],
                        "email": row["email"],
                        "page": row["page"],
                        "ip": row["ip"],
                        "user_agent": row["user_agent"],
                        "submitted_at": row["submitted_at"].isoformat() if row["submitted_at"] else None,
                    }
                    for row in cur.fetchall()
                ]

    feedback_entries = load_list_store(FEEDBACK_STORE)
    feedback_entries.sort(key=lambda entry: entry.get("submitted_at") or "", reverse=True)
    return feedback_entries


def load_request_store() -> dict:
    if os.path.exists(API_KEY_REQUESTS_PATH):
        with open(API_KEY_REQUESTS_PATH, "r") as f:
            try:
                store = json.load(f)
                if isinstance(store, dict):
                    return store
            except json.JSONDecodeError:
                pass
    return {"emails": {}, "ips": {}}


def save_request_store(store: dict):
    os.makedirs(os.path.dirname(API_KEY_REQUESTS_PATH), exist_ok=True)
    with open(API_KEY_REQUESTS_PATH, "w") as f:
        json.dump(store, f, indent=2)


def cleanup_request_store(store: dict):
    cutoff = time.time() - API_KEY_REQUEST_WINDOW_SECONDS
    for bucket in ("emails", "ips"):
        for key in list(store.get(bucket, {}).keys()):
            attempts = store[bucket].get(key, [])
            recent_attempts = [ts for ts in attempts if ts >= cutoff]
            if recent_attempts:
                store[bucket][key] = recent_attempts
            else:
                store[bucket].pop(key, None)




def make_resource_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def normalize_patient_reference(reference):
    if isinstance(reference, dict):
        return reference.get("reference") or reference.get("id") or reference.get("patient")
    return reference


def ensure_resource_id(resource: dict, prefix: str):
    if not resource.get("id") or str(resource.get("id")).strip() == "":
        resource["id"] = make_resource_id(prefix)


def ensure_patient_reference(resource: dict, patient_id: str, field: str = "subject"):
    current = normalize_patient_reference(resource.get(field))
    if current and isinstance(current, str) and current.strip():
        normalized = current.strip()
        if not normalized.startswith("Patient/"):
            normalized = f"Patient/{normalized}"
        resource[field] = normalized
    else:
        resource[field] = f"Patient/{patient_id}"


def process_bundle_resource(raw_resource: dict, resource_type: str, patient_id: str) -> dict:
    resource = raw_resource.copy()
    ensure_resource_id(resource, resource_type.lower())

    if resource_type != "Patient":
        ensure_patient_reference(resource, patient_id)

    if resource_type == "Patient":
        validation = validate_patient(resource)
        explained = explain_errors(validation["errors"], resource)
        fixed = autofix(resource, explained)
        ensure_resource_id(fixed, "patient")
        output = fixed
    elif resource_type == "Observation":
        validation = validate_observation(resource)
        explained = explain_errors(validation["errors"], resource)
        fixed = autofix(resource, explained)
        output = build_observation_resource(fixed, validation.get("loinc_result", {}))
    elif resource_type == "Condition":
        validation = validate_condition(resource)
        explained = explain_errors(validation["errors"], resource)
        fixed = autofix(resource, explained)
        output = build_condition_resource(fixed, validation.get("snomed_result", {}))
    elif resource_type == "Encounter":
        validation = validate_encounter(resource)
        explained = explain_errors(validation["errors"], resource)
        fixed = autofix(resource, explained)
        output = build_encounter_resource(fixed)
    elif resource_type == "MedicationRequest":
        validation = validate_medication(resource)
        explained = explain_errors(validation["errors"], resource)
        fixed = autofix(resource, explained)
        output = build_medication_resource(fixed, validation.get("rxnorm_result", {}))
    else:
        raise ValueError(f"Unsupported bundle resource type: {resource_type}")

    return {
        "resource": output,
        "validation": validation,
        "errors": explained,
        "fixed": output
    }


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def enforce_api_key_request_limit(request: Request, email: str):
    store = load_request_store()
    cleanup_request_store(store)

    normalized_email = email.lower().strip()
    client_ip = get_client_ip(request)

    email_attempts = len(store.get("emails", {}).get(normalized_email, []))
    ip_attempts = len(store.get("ips", {}).get(client_ip, []))

    if email_attempts >= MAX_API_KEY_REQUESTS_PER_EMAIL:
        raise HTTPException(
            status_code=429,
            detail=(
                "Too many API key requests for this email. "
                "Please wait one hour before requesting another key."
            )
        )

    if ip_attempts >= MAX_API_KEY_REQUESTS_PER_IP:
        raise HTTPException(
            status_code=429,
            detail=(
                "Too many API key requests from this IP address. "
                "Please try again later."
            )
        )

    store.setdefault("emails", {}).setdefault(normalized_email, []).append(time.time())
    store.setdefault("ips", {}).setdefault(client_ip, []).append(time.time())
    save_request_store(store)


def patient_exists(patient_id: str) -> bool:
    store = load_store(PATIENTS_STORE)
    return patient_id in store

def register_patient(patient_id: str, resource: dict):
    store = load_store(PATIENTS_STORE)
    store[patient_id] = resource
    save_store(PATIENTS_STORE, store)


class FHIRInput(BaseModel):
    resource: dict


class BundleInput(BaseModel):
    patient: dict
    observations: Optional[List[dict]] = []
    conditions: Optional[List[dict]] = []
    encounters: Optional[List[dict]] = []
    medications: Optional[List[dict]] = []


class UnifiedBundleInput(BaseModel):
    Patient: Optional[dict] = None
    Observation: Optional[List[dict]] = []
    Condition: Optional[List[dict]] = []
    Encounter: Optional[dict] = None
    MedicationRequest: Optional[List[dict]] = []
    bundle_type: str = "collection"


def _build_hl7_message_from_fhir(resource: dict) -> dict:
    """Create a simple HL7 v2 message from a FHIR resource for MVP interoperability."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    resource_type = resource.get("resourceType", "Unknown")

    if resource_type == "Patient":
        name = resource.get("name", [{}])[0] if resource.get("name") else {}
        family = name.get("family", "")
        given = " ".join(name.get("given", []))
        full_name = " ".join([part for part in [given, family] if part]).strip() or "UNKNOWN"
        gender = resource.get("gender", "")
        birth_date = resource.get("birthDate", "")
        message = (
            f"MSH|^~\\&|MEDTECHTOOLS|SMARTFHIR|RECEIVER|FACILITY|{timestamp}||ADT^A01|MSG00001|P|2.5\r"
            f"PID|1||{resource.get('id', 'UNKNOWN')}||{full_name}|||{gender}||{birth_date}"
        )
        return {"success": True, "hl7_message": message, "resource_type": resource_type}

    if resource_type == "Observation":
        code = resource.get("code", {}).get("coding", [{}])[0].get("code", "OBS") if resource.get("code") else {}
        value = resource.get("valueString") or resource.get("valueQuantity", {}).get("value") or ""
        unit = resource.get("valueQuantity", {}).get("unit", "")
        subject_id = resource.get("subject", {}).get("reference", "UNKNOWN").split("/")[-1]
        message = (
            f"MSH|^~\\&|MEDTECHTOOLS|SMARTFHIR|RECEIVER|FACILITY|{timestamp}||ORU^R01|MSG00001|P|2.5\r"
            f"OBX|1|TX|{code}||{value} {unit}".strip()
        )
        return {"success": True, "hl7_message": message, "resource_type": resource_type, "subject_id": subject_id}

    if resource_type == "Condition":
        code = resource.get("code", {}).get("coding", [{}])[0].get("code", "COND") if resource.get("code") else {}
        message = (
            f"MSH|^~\\&|MEDTECHTOOLS|SMARTFHIR|RECEIVER|FACILITY|{timestamp}||ADT^A01|MSG00001|P|2.5\r"
            f"DG1|1||{code}||{resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', 'active')}"
        )
        return {"success": True, "hl7_message": message, "resource_type": resource_type}

    if resource_type == "Encounter":
        subject_id = resource.get("subject", {}).get("reference", "UNKNOWN").split("/")[-1]
        message = (
            f"MSH|^~\\&|MEDTECHTOOLS|SMARTFHIR|RECEIVER|FACILITY|{timestamp}||ADT^A01|MSG00001|P|2.5\r"
            f"PV1|1|O|{resource.get('class', {}).get('code', 'OUTPATIENT')}||||{subject_id}"
        )
        return {"success": True, "hl7_message": message, "resource_type": resource_type}

    return {"success": False, "error": f"Unsupported FHIR resource type: {resource_type}"}


def _parse_hl7_message(message: str) -> dict:
    parser = HL7Parser()
    parsed = parser.parse(message)
    return {
        "message_type": f"{parsed.message_type}^{parsed.trigger_event}" if parsed.message_type != "UNKNOWN" else "UNKNOWN",
        "message_structure": parsed.message_structure,
        "segments": {
            segment_id: [
                {
                    "segment_id": segment.segment_id,
                    "fields": segment.fields,
                    "raw": segment.raw,
                }
                for segment in segments
            ]
            for segment_id, segments in parsed.segments.items()
        },
        "ordered_segments": [
            {
                "segment_id": segment.segment_id,
                "fields": segment.fields,
                "raw": segment.raw,
            }
            for segment in parsed.ordered_segments
        ],
        "errors": parsed.errors,
    }


def _validate_hl7_message(message: str) -> dict:
    parsed = _parse_hl7_message(message)
    errors = []
    warnings = []

    if not message or not message.strip():
        errors.append({"field": "MESSAGE", "message": "HL7 message is empty"})
        return {"valid": False, "errors": errors, "warnings": warnings, "summary": parsed}

    if not any(segment.get("segment_id") == "MSH" for segment in parsed["ordered_segments"]):
        errors.append({"field": "MSH", "message": "Message must contain an MSH segment"})

    if not parsed["ordered_segments"]:
        errors.append({"field": "MESSAGE", "message": "Message contains no segments"})

    if not parsed["errors"] and not errors:
        warnings.append({"field": "MESSAGE", "message": "Basic HL7 structure looks valid"})

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": parsed,
    }


def _explore_hl7_segments(message: str, segment_id: Optional[str] = None, field_index: Optional[int] = None, component_index: Optional[int] = None) -> dict:
    parsed = _parse_hl7_message(message)
    if segment_id:
        selected = parsed["segments"].get(segment_id.upper(), [])
    else:
        selected = parsed["ordered_segments"]

    if field_index is not None:
        details = []
        for segment in selected:
            fields = segment.get("fields", [])
            if field_index < 1 or field_index > len(fields):
                continue
            value = fields[field_index - 1]
            if component_index is not None:
                components = value.split("^") if value else []
                value = components[component_index] if 0 <= component_index < len(components) else None
            details.append({"segment_id": segment.get("segment_id"), "field_index": field_index, "value": value})
        return {"segment_id": segment_id, "field_index": field_index, "component_index": component_index, "matches": details}

    return {"segment_id": segment_id, "field_index": field_index, "component_index": component_index, "segments": selected}


@app.get("/")
def root():
    return {
        "message": "MedTechTools MVP is running",
        "endpoints": [
            "POST /validate",
            "POST /explain-errors",
            "POST /autofix",
            "POST /map-validate",
            "POST /bundle",
            "POST /unified-bundle",
            "POST /api/hl7-to-fhir",
            "POST /api/fhir-to-hl7",
            "POST /api/hl7/parse",
            "POST /api/hl7/validate",
            "POST /api/hl7/segment-explorer"
        ]
    }


@app.post("/validate")
def validate(input: FHIRInput):
    """Validate a FHIR Patient resource"""
    result = validate_patient(input.resource)
    return result


@app.post("/explain-errors")
def explain(input: FHIRInput):
    """Validate + explain all errors in plain English"""
    # Step 1: Validate
    validation = validate_patient(input.resource)

    if validation["valid"] and not validation["warnings"]:
        return {
            "valid": True,
            "message": "Resource is valid. No errors found.",
            "warnings": []
        }

    # Step 2: Explain errors
    explained = explain_errors(validation["errors"], input.resource)

    return {
        "valid": validation["valid"],
        "errors": explained,
        "warnings": validation["warnings"]
    }


@app.post("/autofix")
def fix(input: FHIRInput):
    """Validate, explain and auto-fix a FHIR Patient resource"""
    # Step 1: Validate
    validation = validate_patient(input.resource)

    if validation["valid"]:
        return {
            "valid": True,
            "message": "Resource is already valid. No fixes needed.",
            "fixed_resource": input.resource
        }

    # Step 2: Explain
    explained = explain_errors(validation["errors"], input.resource)

    # Step 3: Fix
    fixed = autofix(input.resource, explained)

    # Step 4: Summary
    summary = generate_fix_summary(input.resource, fixed, explained)

    return {
        "original_valid": False,
        "warnings": validation["warnings"],
        "fix_summary": summary
    }


@app.post("/map-validate")
def map_validate(input: FHIRInput):
    """Full pipeline: Validate + Explain + Fix + Quality Score"""
    # Step 1: Validate
    validation = validate_patient(input.resource)

    # Step 2: Explain
    explained = explain_errors(validation["errors"], input.resource)

    # Step 3: Fix
    fixed = autofix(input.resource, explained)

    # Step 4: Re-validate fixed resource
    revalidation = validate_patient(fixed)

    # Step 5: Quality Score
    quality = generate_quality_score(validation, revalidation)

    # Step 6: Fix summary
    summary = generate_fix_summary(input.resource, fixed, explained)

    return {
        "original_valid": validation["valid"],
        "final_valid": revalidation["valid"],
        "quality": quality,
        "errors": explained,
        "warnings": validation["warnings"],
        "fix_summary": summary
    }


def generate_quality_score(original: dict, fixed: dict) -> dict:
    """Simple quality scoring based on errors"""
    total_errors = len(original["errors"])
    remaining_errors = len(fixed["errors"])
    warnings = len(original["warnings"])

    if total_errors == 0 and warnings == 0:
        grade = "A+"
        score = 100
    elif total_errors == 0 and warnings > 0:
        grade = "A"
        score = 90
    elif remaining_errors == 0:
        grade = "A"
        score = 85
    elif remaining_errors <= 2:
        grade = "C"
        score = 60
    else:
        grade = "D"
        score = 40

    return {
        "grade": grade,
        "score": score,
        "total_errors_found": total_errors,
        "errors_auto_fixed": total_errors - remaining_errors,
        "remaining_errors": remaining_errors,
        "warnings": warnings
    }
    
from mapper import (
    map_to_fhir,
    save_user_mapping,
    get_all_mappings,
    delete_user_mapping
)

class RawInput(BaseModel):
    data: dict
    resource_type: str = "Patient"

class UserMappingInput(BaseModel):
    field: str
    fhir_field: str
    resource_type: str = "Patient"

class DeleteMappingInput(BaseModel):
    field: str
    resource_type: str = "Patient"


@app.post("/map")
def map_resource(input: RawInput):
    """Map raw input fields to FHIR resource"""
    result = map_to_fhir(input.data, input.resource_type)
    return result


@app.post("/map-and-validate")
def map_and_validate(input: RawInput):
    """Map raw input + validate + explain + autofix — full pipeline"""

    # Step 1: Map
    mapping_result = map_to_fhir(input.data, input.resource_type)
    mapped = mapping_result["mapped_resource"]

    # Step 2: Validate
    validation = validate_patient(mapped)

    # Step 3: Explain
    explained = explain_errors(validation["errors"], mapped)

    # Step 4: Fix
    fixed = autofix(mapped, explained)

    # Step 5: Quality Score
    revalidation = validate_patient(fixed)
    quality = generate_quality_score(validation, revalidation)

    return {
        "mapping": {
            "applied_rules": mapping_result["applied_rules"],
            "unmapped_fields": mapping_result["unmapped_fields"],
            "mapping_complete": mapping_result["mapping_complete"]
        },
        "mapped_resource": mapped,
        "validation": {
            "original_valid": validation["valid"],
            "final_valid": revalidation["valid"],
            "errors": explained,
            "warnings": validation["warnings"]
        },
        "quality": quality,
        "fixed_resource": fixed
    }


@app.post("/mappings/save")
def save_mapping(input: UserMappingInput):
    """Save a user-defined field mapping"""
    result = save_user_mapping(
        input.field,
        input.fhir_field,
        input.resource_type
    )
    return result


@app.get("/mappings/{resource_type}")
def view_mappings(resource_type: str = "Patient"):
    """View all mappings for a resource type"""
    return get_all_mappings(resource_type)


@app.delete("/mappings/delete")
def remove_mapping(input: DeleteMappingInput):
    """Delete a user-defined mapping"""
    return delete_user_mapping(input.field, input.resource_type)

from validators.observation_validator import (
    validate_observation,
    build_observation_resource
)

from validators.condition_validator import validate_condition, build_condition_resource

class ObservationInput(BaseModel):
    data: dict
    resource_type: str = "Observation"


@app.post("/observation/map-validate")
def observation_map_validate(input: ObservationInput):
    """Full pipeline for Observation resources"""
    import json
    from mapper import map_to_fhir, convert_flat_to_nested

    # Load observation mappings
    with open("mappings/observation_built_in.json") as f:
        obs_mappings = json.load(f)

    # Step 1: Map fields
    raw = {}
    for field, value in input.data.items():
        normalized = field.lower().replace(" ", "").replace("_", "")
        obs_map = obs_mappings.get("Observation", {})
        if field in obs_map:
            raw[obs_map[field]] = value
        elif normalized in obs_map:
            raw[obs_map[normalized]] = value
        else:
            raw[field] = value

    # Step 2: Convert flat dot notation to nested structure
    raw = convert_flat_to_nested(raw)
    
    # Step 3: Validate
    validation = validate_observation(raw)

    # Step 4: Build proper FHIR structure
    fhir_resource = build_observation_resource(
        raw, validation.get("loinc_result")
    )

    # Step 5: Explain ai_needed errors
    from explainer import explain_errors
    explained = explain_errors(validation["errors"], raw)

    # Step 6: Quality score
    quality = generate_quality_score(
        {"errors": validation["errors"], "warnings": validation["warnings"]},
        {"errors": [e for e in explained if not e.get("fix")], "warnings": []}
    )

    return {
        "loinc_lookup": validation.get("loinc_result"),
        "fhir_resource": fhir_resource,
        "validation": {
            "valid": validation["valid"],
            "errors": explained,
            "warnings": validation["warnings"]
        },
        "quality": quality
    }


class ConditionInput(BaseModel):
    data: dict
    resource_type: str = "Condition"


@app.post("/condition/map-validate")
def condition_map_validate(input: ConditionInput):
    """Full pipeline for Condition resources"""
    import json
    from mapper import convert_flat_to_nested

    # Step 1: Map fields
    with open("mappings/condition_built_in.json") as f:
        cond_mappings = json.load(f).get("Condition", {})

    raw = {}
    for field, value in input.data.items():
        normalized = field.lower().replace(" ", "").replace("_", "")
        if field in cond_mappings:
            raw[cond_mappings[field]] = value
        elif normalized in cond_mappings:
            raw[cond_mappings[normalized]] = value
        else:
            raw[field] = value

    # Step 2: Convert flat dot notation to nested structure
    raw = convert_flat_to_nested(raw)
    
    # Step 3: Validate
    validation = validate_condition(raw)

    # Step 4: Build FHIR structure
    fhir_resource = build_condition_resource(
        raw,
        validation.get("snomed_result"),
        validation.get("icd10_result")
    )

    # Step 5: Explain ai_needed errors
    from explainer import explain_errors
    explained = explain_errors(validation["errors"], raw)

    # Step 6: Quality score
    quality = generate_quality_score(
        {"errors": validation["errors"], "warnings": validation["warnings"]},
        {"errors": [e for e in explained if not e.get("fix")], "warnings": []}
    )

    return {
        "snomed_lookup": validation.get("snomed_result"),
        "icd10_lookup": validation.get("icd10_result"),
        "fhir_resource": fhir_resource,
        "validation": {
            "valid": validation["valid"],
            "errors": explained,
            "warnings": validation["warnings"]
        },
        "quality": quality
    }


@app.post("/patient/register")
def register_patient_endpoint(input: FHIRInput):
    """
    Validate Patient and register in store
    so Observations can reference them
    """
    result = validate_patient(input.resource)

    if result["valid"]:
        patient_id = input.resource.get("id")
        if patient_id:
            register_patient(patient_id, input.resource)
            return {
                "registered": True,
                "patient_id": patient_id,
                "message": f"Patient '{patient_id}' registered successfully."
            }

    return {
        "registered": False,
        "errors": result["errors"],
        "message": "Fix errors before registering patient."
    }
    
class EncounterInput(BaseModel):
    data: dict
    resource_type: str = "Encounter"

class MedicationInput(BaseModel):
    data: dict
    resource_type: str = "MedicationRequest"


@app.post("/encounter/map-validate")
def encounter_map_validate(input: EncounterInput):
    """Full pipeline for Encounter resources"""
    import json
    from mapper import convert_flat_to_nested

    with open("mappings/encounter_built_in.json") as f:
        enc_mappings = json.load(f).get("Encounter", {})

    raw = {}
    for field, value in input.data.items():
        normalized = field.lower().replace(" ", "").replace("_", "")
        if field in enc_mappings:
            raw[enc_mappings[field]] = value
        elif normalized in enc_mappings:
            raw[enc_mappings[normalized]] = value
        else:
            raw[field] = value

    raw = convert_flat_to_nested(raw)
    validation = validate_encounter(raw)
    fhir_resource = build_encounter_resource(raw)
    from explainer import explain_errors
    explained = explain_errors(validation["errors"], raw)
    quality = generate_quality_score(
        {"errors": validation["errors"], "warnings": validation["warnings"]},
        {"errors": [e for e in explained if not e.get("fix")], "warnings": []}
    )

    return {
        "fhir_resource": fhir_resource,
        "validation": {
            "valid": validation["valid"],
            "errors": explained,
            "warnings": validation["warnings"]
        },
        "quality": quality
    }


@app.post("/medication/map-validate")
def medication_map_validate(input: MedicationInput):
    """Full pipeline for MedicationRequest resources"""
    import json
    from mapper import convert_flat_to_nested

    with open("mappings/medication_built_in.json") as f:
        med_mappings = json.load(f).get("MedicationRequest", {})

    raw = {}
    for field, value in input.data.items():
        normalized = field.lower().replace(" ", "").replace("_", "")
        if field in med_mappings:
            raw[med_mappings[field]] = value
        elif normalized in med_mappings:
            raw[med_mappings[normalized]] = value
        else:
            raw[field] = value

    raw = convert_flat_to_nested(raw)
    validation = validate_medication(raw)
    fhir_resource = build_medication_resource(
        raw, validation.get("rxnorm_result")
    )
    from explainer import explain_errors
    explained = explain_errors(validation["errors"], raw)
    quality = generate_quality_score(
        {"errors": validation["errors"], "warnings": validation["warnings"]},
        {"errors": [e for e in explained if not e.get("fix")], "warnings": []}
    )

    return {
        "rxnorm_lookup": validation.get("rxnorm_result"),
        "fhir_resource": fhir_resource,
        "validation": {
            "valid": validation["valid"],
            "errors": explained,
            "warnings": validation["warnings"]
        },
        "quality": quality
    }


@app.post("/encounter/register")
def register_encounter(input: FHIRInput):
    """Register encounter and its reason against patient"""
    store = load_store(CONDITIONS_STORE)
    encounter = input.resource
    patient_ref = encounter.get("subject", {}).get("reference", "")
    patient_id = patient_ref.replace("Patient/", "")
    reason = encounter.get("reasonCode", [{}])[0].get("text", "")

    if patient_id and reason:
        if patient_id not in store:
            store[patient_id] = []
        if reason not in store[patient_id]:
            store[patient_id].append(reason)
        save_store(CONDITIONS_STORE, store)

    return {"registered": True, "patient_id": patient_id, "reason": reason}


@app.post("/bundle")
def create_bundle(input: BundleInput):
    """Validate, fix, link, and pack resources into a FHIR Bundle."""
    patient_raw = input.patient.copy()
    ensure_resource_id(patient_raw, "patient")
    patient_id = str(patient_raw["id"])

    # Process patient first so related resources can reference it
    patient_result = process_bundle_resource(patient_raw, "Patient", patient_id)
    register_patient(patient_id, patient_result["resource"])

    entries = [{"resource": patient_result["resource"]}]
    summary = {
        "patient": patient_result["validation"],
        "observations": [],
        "conditions": [],
        "encounters": [],
        "medications": []
    }

    resource_sets = [
        (input.observations or [], "Observation"),
        (input.conditions or [], "Condition"),
        (input.encounters or [], "Encounter"),
        (input.medications or [], "MedicationRequest")
    ]

    for items, resource_type in resource_sets:
        for raw in items:
            result = process_bundle_resource(raw.copy(), resource_type, patient_id)
            entries.append({"resource": result["resource"]})

            summary_key = {
                "Observation": "observations",
                "Condition": "conditions",
                "Encounter": "encounters",
                "MedicationRequest": "medications",
            }.get(resource_type, resource_type.lower() + "s")

            if summary_key not in summary:
                summary[summary_key] = []
            summary[summary_key].append(result["validation"])

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": entries,
        "summary": summary
    }


@app.post("/unified-bundle")
def create_unified_bundle(input: UnifiedBundleInput):
    """Create FHIR Bundle from unified input format with all resource types."""
    import json
    from mapper import convert_flat_to_nested

    entries = []
    summary = {
        "patient": None,
        "observations": [],
        "conditions": [],
        "encounters": [],
        "medications": []
    }
    patient_id = None

    # Process Patient
    if input.Patient:
        # Map patient fields
        with open("mappings/built_in.json") as f:
            patient_mappings = json.load(f).get("Patient", {})

        patient_raw = {}
        for field, value in input.Patient.items():
            normalized = field.lower().replace(" ", "").replace("_", "")
            if field in patient_mappings:
                patient_raw[patient_mappings[field]] = value
            elif normalized in patient_mappings:
                patient_raw[patient_mappings[normalized]] = value
            else:
                patient_raw[field] = value

        # Convert flat to nested
        patient_raw = convert_flat_to_nested(patient_raw)
        ensure_resource_id(patient_raw, "patient")
        patient_id = str(patient_raw["id"])

        # Validate and build
        patient_result = process_bundle_resource(patient_raw, "Patient", patient_id)
        register_patient(patient_id, patient_result["resource"])
        entries.append({"resource": patient_result["resource"]})
        summary["patient"] = patient_result["validation"]

    # Process Observations
    if input.Observation:
        with open("mappings/observation_built_in.json") as f:
            obs_mappings = json.load(f).get("Observation", {})

        for obs_data in input.Observation:
            obs_raw = {}
            for field, value in obs_data.items():
                normalized = field.lower().replace(" ", "").replace("_", "")
                if field in obs_mappings:
                    obs_raw[obs_mappings[field]] = value
                elif normalized in obs_mappings:
                    obs_raw[obs_mappings[normalized]] = value
                else:
                    obs_raw[field] = value

            obs_raw = convert_flat_to_nested(obs_raw)
            if patient_id:
                obs_raw["subject"] = f"Patient/{patient_id}"

            obs_result = process_bundle_resource(obs_raw, "Observation", patient_id or "unknown")
            entries.append({"resource": obs_result["resource"]})
            summary["observations"].append(obs_result["validation"])

    # Process Conditions
    if input.Condition:
        with open("mappings/condition_built_in.json") as f:
            cond_mappings = json.load(f).get("Condition", {})

        for cond_data in input.Condition:
            cond_raw = {}
            for field, value in cond_data.items():
                normalized = field.lower().replace(" ", "").replace("_", "")
                if field in cond_mappings:
                    cond_raw[cond_mappings[field]] = value
                elif normalized in cond_mappings:
                    cond_raw[cond_mappings[normalized]] = value
                else:
                    cond_raw[field] = value

            cond_raw = convert_flat_to_nested(cond_raw)
            if patient_id:
                cond_raw["subject"] = f"Patient/{patient_id}"

            cond_result = process_bundle_resource(cond_raw, "Condition", patient_id or "unknown")
            entries.append({"resource": cond_result["resource"]})
            summary["conditions"].append(cond_result["validation"])

    # Process Encounter (single object or list)
    encounters = input.Encounter if isinstance(input.Encounter, list) else ([input.Encounter] if input.Encounter else [])
    if encounters:
        with open("mappings/encounter_built_in.json") as f:
            enc_mappings = json.load(f).get("Encounter", {})

        for enc_data in encounters:
            enc_raw = {}
            for field, value in enc_data.items():
                normalized = field.lower().replace(" ", "").replace("_", "")
                if field in enc_mappings:
                    enc_raw[enc_mappings[field]] = value
                elif normalized in enc_mappings:
                    enc_raw[enc_mappings[normalized]] = value
                else:
                    enc_raw[field] = value

            enc_raw = convert_flat_to_nested(enc_raw)
            if patient_id:
                enc_raw["subject"] = f"Patient/{patient_id}"

            enc_result = process_bundle_resource(enc_raw, "Encounter", patient_id or "unknown")
            entries.append({"resource": enc_result["resource"]})
            summary["encounters"].append(enc_result["validation"])

    # Process MedicationRequests
    if input.MedicationRequest:
        with open("mappings/medication_built_in.json") as f:
            med_mappings = json.load(f).get("MedicationRequest", {})

        for med_data in input.MedicationRequest:
            med_raw = {}
            for field, value in med_data.items():
                normalized = field.lower().replace(" ", "").replace("_", "")
                if field in med_mappings:
                    med_raw[med_mappings[field]] = value
                elif normalized in med_mappings:
                    med_raw[med_mappings[normalized]] = value
                else:
                    med_raw[field] = value

            med_raw = convert_flat_to_nested(med_raw)
            if patient_id:
                med_raw["subject"] = f"Patient/{patient_id}"

            med_result = process_bundle_resource(med_raw, "MedicationRequest", patient_id or "unknown")
            entries.append({"resource": med_result["resource"]})
            summary["medications"].append(med_result["validation"])

    return {
        "resourceType": "Bundle",
        "type": input.bundle_type,
        "entry": entries,
        "summary": summary
    }


# ── HL7 v2 to FHIR Conversion Endpoint ─────────────────────────────

class HL7Input(BaseModel):
    hl7_message: str
    explain_errors: bool = True


class FHIRToHL7Input(BaseModel):
    resource: dict


class HL7ParseInput(BaseModel):
    hl7_message: str


class HL7ValidateInput(BaseModel):
    hl7_message: str


class HL7ExplorerInput(BaseModel):
    hl7_message: str
    segment_id: Optional[str] = None
    field_index: Optional[int] = None
    component_index: Optional[int] = None


@app.post("/api/hl7-to-fhir")
def convert_hl7_endpoint(input: HL7Input):
    """Convert HL7 v2 message to FHIR Bundle with error handling and explanations"""
    result = convert_hl7_to_fhir(input.hl7_message, input.explain_errors)
    return result


@app.post("/api/fhir-to-hl7")
def convert_fhir_to_hl7_endpoint(input: FHIRToHL7Input):
    """Convert a simple FHIR resource into an HL7 v2 message for interoperability workflows."""
    return _build_hl7_message_from_fhir(input.resource)


@app.post("/api/hl7/parse")
def parse_hl7_endpoint(input: HL7ParseInput):
    """Parse an HL7 message into structured segments and fields."""
    return _parse_hl7_message(input.hl7_message)


@app.post("/api/hl7/validate")
def validate_hl7_endpoint(input: HL7ValidateInput):
    """Validate basic HL7 structure and return issues."""
    return _validate_hl7_message(input.hl7_message)


@app.post("/api/hl7/segment-explorer")
def segment_explorer_endpoint(input: HL7ExplorerInput):
    """Inspect HL7 segments, fields, and components in a structured way."""
    return _explore_hl7_segments(
        input.hl7_message,
        segment_id=input.segment_id,
        field_index=input.field_index,
        component_index=input.component_index,
    )


# ── API Key endpoints ──────────────────────────────────────

class EmailInput(BaseModel):
    email: str


class FeedbackInput(BaseModel):
    feedback: str = ""
    next_features: List[str] = Field(default_factory=list)
    email: Optional[str] = None
    submitted_at: Optional[str] = None
    page: Optional[str] = None


class ClinicalNoteInput(BaseModel):
    text: str


@app.post("/api/clinical-note/analyze")
def analyze_clinical_note_endpoint(input: ClinicalNoteInput):
    note_text = input.text.strip()
    if not note_text:
        raise HTTPException(
            status_code=400,
            detail="Clinical note text is required."
        )

    try:
        return analyze_clinical_note(note_text)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/feedback")
def receive_feedback(input: FeedbackInput, request: Request):
    feedback = input.feedback.strip()
    next_features = [feature.strip() for feature in input.next_features if feature.strip()]
    email = input.email.strip().lower() if input.email else None

    if not feedback and not next_features:
        raise HTTPException(
            status_code=400,
            detail="Please include feedback text or at least one roadmap choice."
        )

    entry = {
        "id": str(uuid.uuid4()),
        "feedback": feedback,
        "next_features": next_features,
        "email": email,
        "submitted_at": input.submitted_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "page": input.page,
        "ip": get_client_ip(request),
        "user_agent": request.headers.get("user-agent"),
    }

    entry = save_feedback_entry(entry)

    return {"received": True, "id": entry["id"]}


@app.post("/get-api-key")
def get_api_key_request(input: EmailInput, request: Request):
    """
    Create or return an API key for the provided email.
    """
    email = input.email.strip().lower()

    # Basic email validation
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid email address."
        )

    enforce_api_key_request_limit(request, email)

    result = create_key(email)
    result["message"] = "API key created successfully."
    result["dashboard_url"] = "/dashboard"
    return result


@app.post("/register")
def register_email_simple(input: EmailInput, request: Request):
    """
    Simplified flow: immediately create and return an API key for the provided email.
    This replaces the previous OAuth/OTP flows for a minimal user experience.
    """
    email = input.email.strip().lower()

    # Basic email validation
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid email address."
        )

    # lightweight abuse protection (rate limiting)
    try:
        enforce_api_key_request_limit(request, email)
    except HTTPException:
        raise

    result = create_key(email)
    result["message"] = "API key created successfully."
    result["dashboard_url"] = "/dashboard"
    return result


@app.get("/usage")
def check_usage(x_api_key: Optional[str] = Header(None)):
    """Check your API key usage and remaining calls"""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Add X-API-Key header to check usage."
        )

    validation = validate_key(x_api_key)
    if not validation["valid"] and validation["reason"] != "limit_exceeded":
        raise HTTPException(status_code=401, detail=validation["message"])

    return get_usage(x_api_key)


@app.get("/admin/metrics")
def admin_metrics(x_admin_token: Optional[str] = Header(None)):
    """
    Founder-only V1 analytics.
    Set ADMIN_TOKEN in production to require X-Admin-Token.
    """
    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token and x_admin_token != admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token.")

    return get_admin_metrics()


@app.get("/admin/feedback")
def admin_feedback(x_admin_token: Optional[str] = Header(None)):
    """
    Founder-only feedback inbox.
    Set ADMIN_TOKEN in production to require X-Admin-Token.
    """
    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token and x_admin_token != admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token.")

    feedback_entries = load_feedback_entries()

    feature_counts = {}
    for entry in feedback_entries:
        for feature in entry.get("next_features", []):
            feature_counts[feature] = feature_counts.get(feature, 0) + 1

    return {
        "total": len(feedback_entries),
        "with_email": sum(1 for entry in feedback_entries if entry.get("email")),
        "feature_counts": [
            {"feature": feature, "count": count}
            for feature, count in sorted(feature_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        "items": feedback_entries,
        "storage": "supabase.feedback_submissions" if use_postgres() else FEEDBACK_STORE,
    }


class DeleteUserInput(BaseModel):
    email: str


@app.delete("/admin/delete-user")
def delete_user_endpoint(input: DeleteUserInput, x_admin_token: Optional[str] = Header(None)):
    """
    Delete a user and their API key.
    Requires admin token if ADMIN_TOKEN is set.
    """
    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token and x_admin_token != admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token.")

    result = delete_user(input.email)
    return result
