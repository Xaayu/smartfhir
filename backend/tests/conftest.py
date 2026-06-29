import pytest
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = "http://localhost:8000"

# ── Shared test data ──────────────────────────────────────────

VALID_PATIENT = {
    "PtID": "P101",
    "first_name": "John",
    "last_name": "Doe",
    "Sex": "M",
    "DOB": "15/04/1990",
    "marital": "married",
    "phone": "555-1234",
    "email": "john@example.com"
}

VALID_OBSERVATION = {
    "TestName": "Blood Pressure",
    "Value": "120",
    "Unit": "mmHg",
    "PatientID": "P101",
    "Date": "15/01/2024",
    "Status": "final",
    "Interpretation": "N"
}

VALID_CONDITION = {
    "PatientID": "P101",
    "Diagnosis": "Diabetes Type 2",
    "Status": "active",
    "Severity": "moderate",
    "VerificationStatus": "confirmed",
    "OnsetDate": "2023-06-15"
}

VALID_ENCOUNTER = {
    "PatientID": "P101",
    "Status": "finished",
    "VisitType": "emergency",
    "AdmissionDate": "2024-01-15",
    "DischargeDate": "2024-01-18",
    "Reason": "Chest pain",
    "Doctor": "Dr. Smith"
}

VALID_MEDICATION = {
    "PatientID": "P101",
    "MedicationName": "Metformin",
    "Status": "active",
    "OrderType": "order",
    "Dose": "500",
    "Unit": "mg",
    "Frequency": "twice daily",
    "Route": "oral"
}


@pytest.fixture(scope="session")
def client():
    """Shared HTTP client for all tests"""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def register_test_patient(client):
    """Register P101 before all tests run"""
    client.post("/patient/register", json={
        "resource": {
            "resourceType": "Patient",
            "id": "P101",
            "gender": "male",
            "birthDate": "1990-04-15"
        }
    })