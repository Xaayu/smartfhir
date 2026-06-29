# test_validator.py
from validator import validate_patient

test_data = {
    "resourceType": "Patient",
    "id": "P101",
    "gender": "M",
    "birthDate": "15/04/1990"
}

result = validate_patient(test_data)
print(result)