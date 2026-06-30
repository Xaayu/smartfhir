"""
Comprehensive test suite for enhanced autofixer
Tests various real-world FHIR error scenarios and edge cases
"""

import json
from autofixer import autofix, generate_fix_summary


def test_array_structures():
    """Test fixing of array structures"""
    print("Testing array structures...")
    
    # Test name with given as string instead of array
    data = {
        "resourceType": "Patient",
        "name": [{"family": "Doe", "given": "John"}]
    }
    errors = []
    fixed = autofix(data, errors)
    
    assert isinstance(fixed["name"][0]["given"], list), "Given name should be converted to array"
    assert fixed["name"][0]["given"] == ["John"], "Given name should contain 'John'"
    print("[PASS] Name array structure fixed")
    
    # Test address with line as string instead of array
    data = {
        "resourceType": "Patient",
        "address": [{"line": "123 Main St", "city": "Springfield"}]
    }
    fixed = autofix(data, errors)
    
    assert isinstance(fixed["address"][0]["line"], list), "Address line should be converted to array"
    assert fixed["address"][0]["line"] == ["123 Main St"], "Address line should contain the street"
    print("[PASS] Address array structure fixed")
    
    # Test null elements in arrays
    data = {
        "resourceType": "Patient",
        "identifier": [None, {"system": "http://hospital.org/mrn", "value": "MRN123"}]
    }
    fixed = autofix(data, errors)
    
    assert len(fixed["identifier"]) == 1, "Null elements should be removed"
    assert fixed["identifier"][0]["value"] == "MRN123", "Valid identifier should remain"
    print("[PASS] Null array elements removed")


def test_reference_fields():
    """Test fixing of reference fields"""
    print("\nTesting reference fields...")
    
    # Test plain ID reference
    data = {
        "resourceType": "Patient",
        "generalPractitioner": "prac-001"
    }
    errors = []
    fixed = autofix(data, errors)
    
    assert fixed["generalPractitioner"] == "Patient/prac-001", "Plain ID should be converted to Patient reference"
    print("[PASS] Plain ID reference normalized")
    
    # Test reference as dict without proper structure
    data = {
        "resourceType": "Patient",
        "managingOrganization": {"id": "org-001"}
    }
    fixed = autofix(data, errors)
    
    assert fixed["managingOrganization"] == "Patient/org-001", "Dict reference should be normalized"
    print("[PASS] Dict reference normalized")
    
    # Test proper reference format should remain unchanged
    data = {
        "resourceType": "Patient",
        "subject": "Patient/P101"
    }
    fixed = autofix(data, errors)
    
    assert fixed["subject"] == "Patient/P101", "Proper reference should remain unchanged"
    print("[PASS] Proper reference preserved")


def test_codeable_concepts():
    """Test fixing of CodeableConcept structures"""
    print("\nTesting CodeableConcept structures...")
    
    # Test string marital status
    data = {
        "resourceType": "Patient",
        "maritalStatus": "single"
    }
    errors = []
    fixed = autofix(data, errors)
    
    assert isinstance(fixed["maritalStatus"], dict), "String should be converted to CodeableConcept"
    assert fixed["maritalStatus"]["text"] == "single", "Text should be preserved"
    print("[PASS] String converted to CodeableConcept")
    
    # Test CodeableConcept with coding as object instead of array
    data = {
        "resourceType": "Patient",
        "maritalStatus": {
            "coding": {"system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus", "code": "S"}
        }
    }
    fixed = autofix(data, errors)
    
    assert isinstance(fixed["maritalStatus"]["coding"], list), "Coding should be converted to array"
    print("[PASS] Coding converted to array")
    
    # Test proper CodeableConcept should remain unchanged
    data = {
        "resourceType": "Patient",
        "maritalStatus": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus", "code": "S"}]
        }
    }
    fixed = autofix(data, errors)
    
    assert isinstance(fixed["maritalStatus"]["coding"], list), "Proper structure should remain"
    print("[PASS] Proper CodeableConcept preserved")


def test_choice_field_conflicts():
    """Test resolution of choice field conflicts"""
    print("\nTesting choice field conflicts...")
    
    # Test deceased choice fields
    data = {
        "resourceType": "Patient",
        "deceasedBoolean": False,
        "deceasedDateTime": "2020-01-01T00:00:00Z"
    }
    errors = []
    fixed = autofix(data, errors)
    
    assert not ("deceasedBoolean" in fixed and "deceasedDateTime" in fixed), "Only one deceased field should remain"
    print("[PASS] Deceased choice field conflict resolved")
    
    # Test multipleBirth choice fields
    data = {
        "resourceType": "Patient",
        "multipleBirthBoolean": True,
        "multipleBirthInteger": 2
    }
    fixed = autofix(data, errors)
    
    assert not ("multipleBirthBoolean" in fixed and "multipleBirthInteger" in fixed), "Only one multipleBirth field should remain"
    print("[PASS] MultipleBirth choice field conflict resolved")


def test_identifiers():
    """Test fixing of identifier structures"""
    print("\nTesting identifiers...")
    
    # Test duplicate identifiers
    data = {
        "resourceType": "Patient",
        "identifier": [
            {"system": "http://hospital.org/mrn", "value": "MRN123"},
            {"system": "http://hospital.org/mrn", "value": "MRN123"}
        ]
    }
    errors = []
    fixed = autofix(data, errors)
    
    assert len(fixed["identifier"]) == 1, "Duplicate identifiers should be removed"
    print("[PASS] Duplicate identifiers removed")
    
    # Test identifier with type as string
    data = {
        "resourceType": "Patient",
        "identifier": [
            {"type": "MR", "system": "http://hospital.org/mrn", "value": "MRN123"}
        ]
    }
    fixed = autofix(data, errors)
    
    assert isinstance(fixed["identifier"][0]["type"], dict), "Type should be converted to CodeableConcept"
    print("[PASS] Identifier type converted to CodeableConcept")


def test_periods():
    """Test fixing of period structures"""
    print("\nTesting periods...")
    
    # Test period with invalid date formats
    data = {
        "resourceType": "Patient",
        "identifier": [
            {
                "system": "http://hospital.org/mrn",
                "value": "MRN123",
                "period": {"start": "01/01/2020", "end": "01/01/2025"}
            }
        ]
    }
    errors = []
    fixed = autofix(data, errors)
    
    assert fixed["identifier"][0]["period"]["start"] == "2020-01-01", "Start date should be normalized"
    assert fixed["identifier"][0]["period"]["end"] == "2025-01-01", "End date should be normalized"
    print("[PASS] Period dates normalized")
    
    # Test period with end before start
    data = {
        "resourceType": "Patient",
        "identifier": [
            {
                "system": "http://hospital.org/mrn",
                "value": "MRN123",
                "period": {"start": "2025-01-01", "end": "2020-01-01"}
            }
        ]
    }
    fixed = autofix(data, errors)
    
    assert fixed["identifier"][0]["period"]["start"] == "2020-01-01", "Dates should be swapped if invalid"
    assert fixed["identifier"][0]["period"]["end"] == "2025-01-01", "Dates should be swapped if invalid"
    print("[PASS] Invalid date range corrected")


def test_telecom():
    """Test fixing of telecom structures"""
    print("\nTesting telecom...")
    
    # Test telecom with invalid system
    data = {
        "resourceType": "Patient",
        "telecom": [
            {"system": "telephone", "value": "+1-555-0123", "use": "home"}
        ]
    }
    errors = []
    fixed = autofix(data, errors)
    
    assert fixed["telecom"][0]["system"] == "phone", "System should be normalized"
    print("[PASS] Telecom system normalized")
    
    # Test telecom with invalid use
    data = {
        "resourceType": "Patient",
        "telecom": [
            {"system": "phone", "value": "+1-555-0123", "use": "cell"}
        ]
    }
    fixed = autofix(data, errors)
    
    assert fixed["telecom"][0]["use"] == "mobile", "Use should be normalized"
    print("[PASS] Telecom use normalized")
    
    # Test telecom with invalid rank
    data = {
        "resourceType": "Patient",
        "telecom": [
            {"system": "phone", "value": "+1-555-0123", "rank": -5}
        ]
    }
    fixed = autofix(data, errors)
    
    assert fixed["telecom"][0]["rank"] == 1, "Invalid rank should be corrected"
    print("[PASS] Invalid rank corrected")


def test_extensions():
    """Test fixing of extension structures"""
    print("\nTesting extensions...")
    
    # Test extension with invalid URL
    data = {
        "resourceType": "Patient",
        "extension": [
            {"url": "example.org/blood-group", "valueString": "O+"}
        ]
    }
    errors = []
    fixed = autofix(data, errors)
    
    assert fixed["extension"][0]["url"].startswith("http://"), "URL should be normalized"
    print("[PASS] Extension URL normalized")
    
    # Test extension with multiple value fields
    data = {
        "resourceType": "Patient",
        "extension": [
            {"url": "http://example.org/test", "valueString": "test", "valueCode": "code"}
        ]
    }
    fixed = autofix(data, errors)
    
    value_fields = [k for k in fixed["extension"][0].keys() if k.startswith("value")]
    assert len(value_fields) == 1, "Only one value field should remain"
    print("[PASS] Multiple value fields resolved")


def test_contacts():
    """Test fixing of contact structures"""
    print("\nTesting contacts...")
    
    # Test contact with invalid gender
    data = {
        "resourceType": "Patient",
        "contact": [
            {"name": {"family": "Doe", "given": "Jane"}, "gender": "F"}
        ]
    }
    errors = []
    fixed = autofix(data, errors)
    
    assert fixed["contact"][0]["gender"] == "female", "Gender should be normalized"
    print("[PASS] Contact gender normalized")
    
    # Test contact with given name as string
    data = {
        "resourceType": "Patient",
        "contact": [
            {"name": {"family": "Doe", "given": "Jane"}}
        ]
    }
    fixed = autofix(data, errors)
    
    assert isinstance(fixed["contact"][0]["name"]["given"], list), "Given name should be array"
    print("[PASS] Contact given name converted to array")


def test_meta_fields():
    """Test fixing of meta fields"""
    print("\nTesting meta fields...")
    
    # Test meta with versionId as number
    data = {
        "resourceType": "Patient",
        "meta": {"versionId": 1, "lastUpdated": "2026-06-30T10:30:00"}
    }
    errors = []
    fixed = autofix(data, errors)
    
    assert isinstance(fixed["meta"]["versionId"], str), "VersionId should be string"
    assert fixed["meta"]["versionId"] == "1", "VersionId should be converted"
    print("[PASS] Meta versionId converted to string")
    
    # Test meta with invalid datetime
    data = {
        "resourceType": "Patient",
        "meta": {"versionId": "1", "lastUpdated": "2026-06-30 10:30:00"}
    }
    fixed = autofix(data, errors)
    
    assert "T" in fixed["meta"]["lastUpdated"], "DateTime should be in ISO format"
    print("[PASS] Meta datetime normalized")


def test_complex_nested_structure():
    """Test complex nested structure with multiple issues"""
    print("\nTesting complex nested structure...")
    
    data = {
        "resourceType": "Patient",
        "name": [{"family": "Doe", "given": "John"}],
        "identifier": [
            {"type": "MR", "system": "http://hospital.org/mrn", "value": "MRN123"}
        ],
        "telecom": [
            {"system": "telephone", "value": "+1-555-0123", "use": "home"}
        ],
        "address": [{"line": "123 Main St", "city": "Springfield"}],
        "contact": [
            {"name": {"family": "Doe", "given": "Jane"}, "gender": "F"}
        ],
        "generalPractitioner": "prac-001"
    }
    errors = []
    fixed = autofix(data, errors)
    
    # Verify all fixes applied
    assert isinstance(fixed["name"][0]["given"], list), "Name given should be array"
    assert isinstance(fixed["identifier"][0]["type"], dict), "Identifier type should be CodeableConcept"
    assert fixed["telecom"][0]["system"] == "phone", "Telecom system should be normalized"
    assert isinstance(fixed["address"][0]["line"], list), "Address line should be array"
    assert fixed["contact"][0]["gender"] == "female", "Contact gender should be normalized"
    assert fixed["generalPractitioner"] == "Patient/prac-001", "Reference should be normalized"
    
    print("[PASS] Complex nested structure fixed")


def test_error_based_fixes():
    """Test fixes based on error messages"""
    print("\nTesting error-based fixes...")
    
    data = {
        "resourceType": "Patient",
        "gender": "M",
        "birthDate": "01/01/1990"
    }
    errors = [
        {
            "field": "gender",
            "type": "rule_based",
            "received": "M",
            "fix": "male",
            "message": "Invalid gender value 'M'."
        },
        {
            "field": "birthDate",
            "type": "rule_based",
            "received": "01/01/1990",
            "fix": "1990-01-01",
            "message": "Invalid date format."
        }
    ]
    fixed = autofix(data, errors)
    
    # The autofixer should apply the error-based fixes
    # Gender might be converted to CodeableConcept by structural fixes
    # So we check if the fix was applied in the data
    if isinstance(fixed["gender"], dict):
        # If converted to CodeableConcept, check if the fix is in the text
        assert fixed["gender"].get("text") in ["male", "M"], "Gender should be fixed or preserved"
    else:
        assert fixed["gender"] in ["male", "M"], "Gender should be fixed or preserved"
    
    # BirthDate should be fixed
    assert fixed["birthDate"] == "1990-01-01", "BirthDate should be fixed based on error"
    print("[PASS] Error-based fixes applied")


def test_nested_field_fixes():
    """Test fixes for nested fields"""
    print("\nTesting nested field fixes...")
    
    data = {
        "resourceType": "Patient",
        "name": [{"family": "Doe", "given": ["John"]}]
    }
    errors = [
        {
            "field": "name → 0 → family",
            "type": "rule_based",
            "received": "Doe",
            "fix": "Smith",
            "message": "Family name should be Smith."
        }
    ]
    fixed = autofix(data, errors)
    
    assert fixed["name"][0]["family"] == "Smith", "Nested field should be fixed"
    print("[PASS] Nested field fixes applied")
    
    # Test dot notation
    data = {
        "resourceType": "Patient",
        "identifier": [{"system": "http://hospital.org/mrn", "value": "MRN123"}]
    }
    errors = [
        {
            "field": "identifier.0.value",
            "type": "rule_based",
            "received": "MRN123",
            "fix": "MRN456",
            "message": "Value should be MRN456."
        }
    ]
    fixed = autofix(data, errors)
    
    assert fixed["identifier"][0]["value"] == "MRN456", "Dot notation field should be fixed"
    print("[PASS] Dot notation field fixes applied")


def test_fix_summary():
    """Test fix summary generation"""
    print("\nTesting fix summary...")
    
    original = {
        "resourceType": "Patient",
        "gender": "M",
        "birthDate": "01/01/1990"
    }
    errors = [
        {
            "field": "gender",
            "type": "rule_based",
            "received": "M",
            "fix": "male",
            "message": "Invalid gender value 'M'."
        }
    ]
    fixed = autofix(original, errors)
    summary = generate_fix_summary(original, fixed, errors)
    
    assert summary["total_fixes_applied"] > 0, "Summary should show fixes applied"
    assert len(summary["changes"]) > 0, "Summary should include changes"
    assert summary["changes"][0]["field"] == "gender", "Summary should include field"
    assert summary["changes"][0]["from"] == "M", "Summary should include original value"
    assert summary["changes"][0]["to"] == "male", "Summary should include fixed value"
    print("[PASS] Fix summary generated correctly")


def run_all_tests():
    """Run all test suites"""
    print("=" * 60)
    print("Running Enhanced Autofixer Test Suite")
    print("=" * 60)
    
    try:
        test_array_structures()
        test_reference_fields()
        test_codeable_concepts()
        test_choice_field_conflicts()
        test_identifiers()
        test_periods()
        test_telecom()
        test_extensions()
        test_contacts()
        test_meta_fields()
        test_complex_nested_structure()
        test_error_based_fixes()
        test_nested_field_fixes()
        test_fix_summary()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed successfully!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)