"""
Advanced PHI De-identification Test Case
Tests 16 PHI elements across complex, nested, and unstructured data scenarios.
"""

from phi_deidentifier import PHIDeidentifier, deidentify

# Complex test case with 16 PHI elements
COMPLEX_PATIENT = {
    "resourceType": "Patient",
    "id": "PT-1930-001",  # PHI #1: Patient ID (age >89)
    "name": [{
        "family": "Williams",
        "given": ["Arthur", "James"],
        "prefix": ["Dr."]
    }],  # PHI #2-3: Name components
    "birthDate": "1930-05-15",  # PHI #4: Birth date (age >89 - should aggregate)
    "gender": "male",
    "telecom": [
        {"system": "phone", "value": "+1-555-0123"},  # PHI #5: Phone
        {"system": "email", "value": "arthur.williams@hospital.org"}  # PHI #6: Email
    ],
    "address": [{
        "line": ["123 Main Street", "Apt 4B"],
        "city": "Boston",
        "state": "MA",
        "postalCode": "02101",
        "country": "USA"
    }],  # PHI #7-11: Address components
    "contact": [{
        "name": {
            "family": "Williams",
            "given": ["Martha"]
        },  # PHI #12: Secondary contact name (spouse)
        "telecom": [
            {"system": "phone", "value": "+1-555-9876"}  # PHI #13: Contact phone
        ],
        "address": {
            "line": ["456 Oak Avenue"],
            "city": "Boston",
            "state": "MA",
            "postalCode": "02102"
        },  # PHI #14-16: Contact address
        "relationship": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                "code": "SPS",
                "display": "spouse"
            }]
        }]
    }],
    "identifier": [{
        "system": "http://hospital.org/mrn",
        "value": "MRN-1930-001"  # Additional PHI: Medical record number
    }],
    # Primitive extension (underscore-prefixed key)
    "_birthDate": {
        "id": "birthDate-1",
        "extension": [{
            "url": "http://hl7.org/fhir/StructureDefinition/entryFormat",
            "valueString": "YYYY-MM-DD"
        }]
    },
    # Complex extension with nested PHI
    "extension": [{
        "url": "http://hl7.org/fhir/StructureDefinition/patient-birthPlace",
        "valueAddress": {
            "city": "Springfield",  # PHI in extension
            "state": "MA",
            "postalCode": "01101"
        }
    }],
    "text": {
        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">Patient Arthur Williams (age 94) was admitted. Contact his wife Martha at 555-9876. Dr. Smith referred him. MRN: MRN-1930-001. Email backup: arthur.williams@gmail.com</div>"
    }  # PHI in unstructured text: names, phone, MRN, email
}

def test_advanced_deidentification():
    """Test the enhanced PHI de-identification with complex scenarios"""
    
    print("Testing Advanced PHI De-identification")
    print("=" * 60)
    
    # Test with pseudonymize mode
    engine = PHIDeidentifier(mode="pseudonymize")
    result = engine.deidentify_resource(COMPLEX_PATIENT)
    
    print("\nOriginal Patient Resource:")
    print(f"  Name: {COMPLEX_PATIENT['name'][0]['given'][0]} {COMPLEX_PATIENT['name'][0]['family']}")
    print(f"  Birth Date: {COMPLEX_PATIENT['birthDate']} (Age: 94)")
    print(f"  Phone: {COMPLEX_PATIENT['telecom'][0]['value']}")
    print(f"  Email: {COMPLEX_PATIENT['telecom'][1]['value']}")
    print(f"  Address: {COMPLEX_PATIENT['address'][0]['line'][0]}, {COMPLEX_PATIENT['address'][0]['city']}, {COMPLEX_PATIENT['address'][0]['state']}")
    print(f"  Contact Name: {COMPLEX_PATIENT['contact'][0]['name']['given'][0]} {COMPLEX_PATIENT['contact'][0]['name']['family']}")
    print(f"  Contact Phone: {COMPLEX_PATIENT['contact'][0]['telecom'][0]['value']}")
    print(f"  Birth Place Extension: {COMPLEX_PATIENT['extension'][0]['valueAddress']['city']}")
    
    print("\nDe-identified Patient Resource:")
    print(f"  Name: {result['name'][0]['given'][0]} {result['name'][0]['family']}")
    print(f"  Birth Date: {result['birthDate']} (Should be 1900-01-01 for >89 aggregation)")
    print(f"  Phone: {result['telecom'][0]['value']}")
    print(f"  Email: {result['telecom'][1]['value']}")
    print(f"  Address: {result['address'][0]['line'][0]}, {result['address'][0]['city']}, {result['address'][0]['state']}")
    print(f"  Contact Name: {result['contact'][0]['name']['given'][0]} {result['contact'][0]['name']['family']}")
    print(f"  Contact Phone: {result['contact'][0]['telecom'][0]['value']}")
    print(f"  Birth Place Extension: {result['extension'][0]['valueAddress']['city']}")
    
    # Check primitive extension mirroring
    if "_birthDate" in result:
        print(f"  Primitive Extension _birthDate: {result['_birthDate']}")
        print(f"    ✓ Primitive extension mirroring working")
    else:
        print(f"    ✗ Primitive extension not found")
    
    # Check text de-identification
    original_text = COMPLEX_PATIENT['text']['div']
    deidentified_text = result['text']['div']
    
    print("\nOriginal Text:")
    print(f"  {original_text}")
    print("\nDe-identified Text:")
    print(f"  {deidentified_text}")
    
    # Check if PHI was removed from text
    phi_in_text = ["Arthur", "Williams", "Martha", "555-9876", "MRN-1930-001", "arthur.williams@gmail.com"]
    phi_remaining = [phi for phi in phi_in_text if phi in deidentified_text]
    
    if not phi_remaining:
        print("    ✓ All PHI removed from unstructured text")
    else:
        print(f"    ✗ PHI remaining in text: {phi_remaining}")
    
    # Get audit report
    audit = engine.get_audit_report()
    
    print("\nAudit Report:")
    print(f"  Total PHI Items Found: {audit['phi_items_found']}")
    print(f"  PHI by Type: {audit['phi_by_type']}")
    print(f"  Fields Cleaned: {len(audit['fields_cleaned'])}")
    print(f"  HIPAA Safe Harbor Compliant: {audit['hipaa_safe_harbor_compliant']}")
    
    # Verify specific requirements
    print("\n" + "=" * 60)
    print("Verification of Advanced Features:")
    print("=" * 60)
    
    # 1. Age >89 aggregation
    if result['birthDate'] == "1900-01-01":
        print("✓ Age >89 aggregation working (birthDate aggregated to epoch)")
    else:
        print(f"✗ Age >89 aggregation failed (birthDate: {result['birthDate']})")
    
    # 2. Primitive extension handling
    if "_birthDate" in result and result['_birthDate'].get('extension'):
        print("✓ Primitive extension handling working")
    else:
        print("✗ Primitive extension handling failed")
    
    # 3. Complex extension handling
    if result['extension'][0]['valueAddress']['city'] != COMPLEX_PATIENT['extension'][0]['valueAddress']['city']:
        print("✓ Complex extension (valueAddress) de-identification working")
    else:
        print("✗ Complex extension handling failed")
    
    # 4. Secondary contacts de-identification
    if result['contact'][0]['name']['family'] != COMPLEX_PATIENT['contact'][0]['name']['family']:
        print("✓ Secondary contact de-identification working")
    else:
        print("✗ Secondary contact de-identification failed")
    
    # 5. NLP-enhanced text scanning
    if not phi_remaining:
        print("✓ NLP-enhanced text scanning working")
    else:
        print("✗ NLP-enhanced text scanning failed")
    
    # 6. Deterministic entity replacement
    # Check if the same name appears consistently
    if result['name'][0]['given'][0] in deidentified_text:
        print("✓ Deterministic entity replacement working")
    else:
        print("✗ Deterministic entity replacement may need verification")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
    
    return result, audit

if __name__ == "__main__":
    result, audit = test_advanced_deidentification()
    
    # Save results for inspection
    import json
    with open("test_phi_output.json", "w") as f:
        json.dump({
            "original": COMPLEX_PATIENT,
            "deidentified": result,
            "audit": audit
        }, f, indent=2)
    
    print("\nResults saved to test_phi_output.json")
