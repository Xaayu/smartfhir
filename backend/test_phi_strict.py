"""
Strict PHI De-identification Test Case
Tests high-risk data leakage vectors including:
- Human names in clinical contexts (Dr. Robert Chen, Eleanor, Arthur)
- Primitive extensions with nested timestamps (_birthDate with valueDateTime)
- Multi-entity demographic scrubbing
- Aggressive age obfuscation (>89 rule)
"""

from phi_deidentifier import PHIDeidentifier, deidentify

# Complex test case with high-risk PHI elements
STRICT_TEST_PATIENT = {
    "resourceType": "Patient",
    "id": "PT-1942-002",  # PHI: Patient ID (age >89 in 2026)
    "name": [{
        "family": "Chen",
        "given": ["Eleanor", "May"],
        "prefix": ["Mrs."]
    }],  # PHI: Patient name (Eleanor)
    "birthDate": "1942-11-23",  # PHI: Birth date (age 84 in 2026 - borderline, but we'll test >89 logic with older date)
    "gender": "female",
    "telecom": [
        {"system": "phone", "value": "+1-555-0199"},
        {"system": "email", "value": "eleanor.chen@hospital.org"}
    ],
    "address": [{
        "line": ["456 Oak Avenue"],
        "city": "Springfield",
        "state": "IL",
        "postalCode": "62701",
        "country": "USA"
    }],
    "contact": [{
        "name": {
            "family": "Chen",
            "given": ["Arthur"]
        },  # PHI: Husband name (Arthur)
        "telecom": [
            {"system": "phone", "value": "+1-555-0200"}
        ],
        "address": {
            "line": ["456 Oak Avenue"],
            "city": "Springfield",
            "state": "IL",
            "postalCode": "62701"
        },
        "relationship": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                "code": "HUSB",
                "display": "husband"
            }]
        }],
        "identifier": [{
            "system": "http://hospital.org/contact-id",
            "value": "CONTACT-ARTHUR-001"
        }]  # PHI: Contact identifier
    }],
    "generalPractitioner": [{
        "display": "Dr. Robert Chen",  # PHI: Practitioner name (Dr. Robert Chen)
        "reference": "Practitioner/PR-ROBERT-CHEN"
    }],
    "identifier": [{
        "system": "http://hospital.org/mrn",
        "value": "MRN-1942-002"
    }],
    # Primitive extension with nested timestamp (HIGH RISK)
    "_birthDate": {
        "id": "birthDate-1",
        "extension": [{
            "url": "http://hl7.org/fhir/StructureDefinition/patient-birthTime",
            "valueDateTime": "1942-11-23T04:15:00Z"  # PHI: Exact timestamp in primitive extension
        }]
    },
    # Complex extension with nested PHI
    "extension": [{
        "url": "http://hl7.org/fhir/StructureDefinition/patient-birthPlace",
        "valueAddress": {
            "city": "Chicago",
            "state": "IL",
            "postalCode": "60601"
        }
    }],
    "link": [{
        "type": "seealso",
        "other": {
            "reference": "Patient/PT-RELATED-001"  # PHI: Related patient reference
        }
    }],
    "managingOrganization": {
        "display": "Springfield General Hospital",  # PHI: Organization name
        "reference": "Organization/ORG-SPRINGFIELD"
    },
    "text": {
        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">Patient Eleanor Chen was admitted. Her husband Arthur called at 555-0200. Dr. Robert Chen referred her. Contact backup: eleanor.chen@gmail.com. MRN: MRN-1942-002.</div>"
    }  # PHI in unstructured text: Eleanor, Arthur, Dr. Robert Chen, phone, email, MRN
}

# Test case with age >89 for aggressive obfuscation
ELDERLY_PATIENT = {
    "resourceType": "Patient",
    "id": "PT-1930-003",
    "name": [{
        "family": "Williams",
        "given": ["Margaret"]
    }],
    "birthDate": "1930-01-15",  # PHI: Birth date (age 96 in 2026 - should trigger >89 rule)
    "gender": "female",
    "_birthDate": {
        "extension": [{
            "url": "http://hl7.org/fhir/StructureDefinition/patient-birthTime",
            "valueDateTime": "1930-01-15T08:30:00Z"  # PHI: Exact timestamp for elderly patient
        }]
    }
}

def test_strict_deidentification():
    """Test strict PHI de-identification with high-risk scenarios"""
    
    print("Testing Strict PHI De-identification")
    print("=" * 70)
    
    # Test 1: Standard complex patient
    print("\nTest 1: Complex Patient with Multiple PHI Types")
    print("-" * 70)
    
    engine = PHIDeidentifier(mode="pseudonymize")
    result = engine.deidentify_resource(STRICT_TEST_PATIENT)
    
    print("\nOriginal PHI Elements:")
    print(f"  Patient Name: Eleanor Chen")
    print(f"  Husband Name: Arthur Chen")
    print(f"  Practitioner: Dr. Robert Chen")
    print(f"  Birth Date: {STRICT_TEST_PATIENT['birthDate']}")
    print(f"  _birthDate timestamp: {STRICT_TEST_PATIENT['_birthDate']['extension'][0]['valueDateTime']}")
    print(f"  Contact ID: {STRICT_TEST_PATIENT['contact'][0]['identifier'][0]['value']}")
    print(f"  Related Patient: {STRICT_TEST_PATIENT['link'][0]['other']['reference']}")
    print(f"  Organization: {STRICT_TEST_PATIENT['managingOrganization']['display']}")
    
    print("\nDe-identified Results:")
    print(f"  Patient Name: {result['name'][0]['given'][0]} {result['name'][0]['family']}")
    print(f"  Husband Name: {result['contact'][0]['name']['given'][0]} {result['contact'][0]['name']['family']}")
    print(f"  Practitioner: {result['generalPractitioner'][0]['display']}")
    print(f"  Birth Date: {result['birthDate']}")
    if "_birthDate" in result and "extension" in result["_birthDate"]:
        print(f"  _birthDate timestamp: {result['_birthDate']['extension'][0].get('valueDateTime', 'REMOVED')}")
    else:
        print(f"  _birthDate timestamp: REMOVED")
    print(f"  Contact ID: {result['contact'][0]['identifier'][0]['value']}")
    print(f"  Related Patient: {result['link'][0]['other']['reference']}")
    print(f"  Organization: {result['managingOrganization']['display']}")
    
    # Check text de-identification
    original_text = STRICT_TEST_PATIENT['text']['div']
    deidentified_text = result['text']['div']
    
    print("\nOriginal Text:")
    print(f"  {original_text}")
    print("\nDe-identified Text:")
    print(f"  {deidentified_text}")
    
    # Verify specific PHI removal
    phi_in_text = ["Eleanor", "Chen", "Arthur", "Robert", "555-0200", "MRN-1942-002", "eleanor.chen@gmail.com"]
    phi_remaining = [phi for phi in phi_in_text if phi in deidentified_text]
    
    if not phi_remaining:
        print("  ✓ All PHI removed from unstructured text")
    else:
        print(f"  ✗ PHI remaining in text: {phi_remaining}")
    
    # Verify primitive extension timestamp handling
    if "_birthDate" in result:
        if "extension" in result["_birthDate"]:
            timestamp = result["_birthDate"]["extension"][0].get("valueDateTime", "")
            if timestamp != STRICT_TEST_PATIENT["_birthDate"]["extension"][0]["valueDateTime"]:
                print("  ✓ Primitive extension timestamp de-identified")
            else:
                print("  ✗ Primitive extension timestamp NOT de-identified (HIGH RISK)")
        else:
            print("  ✓ Primitive extension timestamp removed")
    else:
        print("  ✓ Primitive extension _birthDate removed")
    
    # Verify multi-entity scrubbing
    if result['contact'][0]['name']['family'] != STRICT_TEST_PATIENT['contact'][0]['name']['family']:
        print("  ✓ Contact name de-identified")
    else:
        print("  ✗ Contact name NOT de-identified")
    
    if result['contact'][0]['identifier'][0]['value'] != STRICT_TEST_PATIENT['contact'][0]['identifier'][0]['value']:
        print("  ✓ Contact identifier de-identified")
    else:
        print("  ✗ Contact identifier NOT de-identified")
    
    if result['link'][0]['other']['reference'] != STRICT_TEST_PATIENT['link'][0]['other']['reference']:
        print("  ✓ Related patient reference de-identified")
    else:
        print("  ✗ Related patient reference NOT de-identified")
    
    if result['managingOrganization']['display'] != STRICT_TEST_PATIENT['managingOrganization']['display']:
        print("  ✓ Organization name de-identified")
    else:
        print("  ✗ Organization name NOT de-identified")
    
    # Test 2: Elderly patient with >89 rule
    print("\n" + "=" * 70)
    print("Test 2: Elderly Patient (>89 Age Obfuscation)")
    print("-" * 70)
    
    engine2 = PHIDeidentifier(mode="pseudonymize")
    result2 = engine2.deidentify_resource(ELDERLY_PATIENT)
    
    print(f"\nOriginal Birth Date: {ELDERLY_PATIENT['birthDate']} (Age: 96)")
    print(f"Original _birthDate timestamp: {ELDERLY_PATIENT['_birthDate']['extension'][0]['valueDateTime']}")
    print(f"\nDe-identified Birth Date: {result2['birthDate']}")
    if "_birthDate" in result2 and "extension" in result2["_birthDate"]:
        print(f"De-identified _birthDate timestamp: {result2['_birthDate']['extension'][0].get('valueDateTime', 'REMOVED')}")
    else:
        print(f"De-identified _birthDate timestamp: REMOVED")
    
    # Verify >89 rule
    if result2['birthDate'] == ">89":
        print("  ✓ Age >89 obfuscation working (birthDate = '>89')")
    else:
        print(f"  ✗ Age >89 obfuscation failed (birthDate = {result2['birthDate']})")
    
    # Test with different modes
    print("\n" + "=" * 70)
    print("Test 3: Age >89 with Different Modes")
    print("-" * 70)
    
    for mode in ["redact", "mask", "pseudonymize"]:
        engine_mode = PHIDeidentifier(mode=mode)
        result_mode = engine_mode.deidentify_resource(ELDERLY_PATIENT)
        print(f"\nMode: {mode}")
        print(f"  Birth Date: {result_mode['birthDate']}")
        
        if mode == "redact" and result_mode['birthDate'] is None:
            print("  ✓ Redact mode: birthDate set to null")
        elif mode == "mask" and result_mode['birthDate'] == ">89":
            print("  ✓ Mask mode: birthDate set to '>89'")
        elif mode == "pseudonymize" and result_mode['birthDate'] == ">89":
            print("  ✓ Pseudonymize mode: birthDate set to '>89'")
        else:
            print(f"  ✗ Mode {mode} not handling >89 correctly")
    
    # Get audit report
    audit = engine.get_audit_report()
    
    print("\n" + "=" * 70)
    print("Audit Report")
    print("=" * 70)
    print(f"Total PHI Items Found: {audit['phi_items_found']}")
    print(f"PHI by Type: {audit['phi_by_type']}")
    print(f"Fields Cleaned: {len(audit['fields_cleaned'])}")
    print(f"HIPAA Safe Harbor Compliant: {audit['hipaa_safe_harbor_compliant']}")
    
    print("\n" + "=" * 70)
    print("Verification Summary")
    print("=" * 70)
    
    verification_checks = [
        ("Dr. Robert Chen removed from text", "Robert" not in deidentified_text),
        ("Eleanor removed from text", "Eleanor" not in deidentified_text),
        ("Arthur removed from text", "Arthur" not in deidentified_text),
        ("Primitive extension timestamp handled", timestamp != STRICT_TEST_PATIENT["_birthDate"]["extension"][0]["valueDateTime"]),
        ("Contact name de-identified", result['contact'][0]['name']['family'] != STRICT_TEST_PATIENT['contact'][0]['name']['family']),
        ("Contact identifier de-identified", result['contact'][0]['identifier'][0]['value'] != STRICT_TEST_PATIENT['contact'][0]['identifier'][0]['value']),
        ("Related patient reference de-identified", result['link'][0]['other']['reference'] != STRICT_TEST_PATIENT['link'][0]['other']['reference']),
        ("Organization name de-identified", result['managingOrganization']['display'] != STRICT_TEST_PATIENT['managingOrganization']['display']),
        ("Age >89 obfuscation working", result2['birthDate'] == ">89"),
    ]
    
    for check_name, check_result in verification_checks:
        status = "✓" if check_result else "✗"
        print(f"{status} {check_name}")
    
    all_passed = all(check[1] for check in verification_checks)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("ALL VERIFICATION CHECKS PASSED")
    else:
        print("SOME VERIFICATION CHECKS FAILED")
    print("=" * 70)
    
    return result, result2, audit

if __name__ == "__main__":
    result, result2, audit = test_strict_deidentification()
    
    # Save results for inspection
    import json
    with open("test_phi_strict_output.json", "w") as f:
        json.dump({
            "original_strict": STRICT_TEST_PATIENT,
            "deidentified_strict": result,
            "original_elderly": ELDERLY_PATIENT,
            "deidentified_elderly": result2,
            "audit": audit
        }, f, indent=2, default=str)
    
    print("\nResults saved to test_phi_strict_output.json")
