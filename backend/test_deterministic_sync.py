"""
Comprehensive test for deterministic entity syncing and clinician anonymization.
Tests the enhanced PHI de-identification requirements:
1. Context-Aware NER Syncing between structured fields and unstructured text
2. Clinician Anonymization (Dr. [Name] patterns)
3. Dynamic Age Aggregation (>89 years)
"""

from phi_deidentifier import PHIDeidentifier
import json

# Test case 1: Deterministic entity syncing
DETERMINISTIC_SYNC_TEST = {
    "resourceType": "Patient",
    "id": "PT-DETERMINISTIC-001",
    "name": [{
        "family": "Johnson",
        "given": ["Sarah", "Marie"]
    }],
    "birthDate": "1985-03-15",
    "gender": "female",
    "contact": [{
        "name": {
            "family": "Johnson",
            "given": ["Michael"]
        },
        "relationship": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                "code": "HUSB",
                "display": "husband"
            }]
        }]
    }],
    "text": {
        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">Patient Sarah Johnson was admitted. Her husband Michael called at 555-0123. Dr. Robert Smith examined her. Sarah reported pain. Michael is her emergency contact.</div>"
    }
}

# Test case 2: Clinician anonymization
CLINICIAN_ANONYMIZATION_TEST = {
    "resourceType": "Patient",
    "id": "PT-CLINICIAN-001",
    "name": [{
        "family": "Williams",
        "given": ["James"]
    }],
    "birthDate": "1975-08-22",
    "gender": "male",
    "text": {
        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">Patient James Williams was seen by Dr. Emily Chen. Doctor Michael Brown provided consultation. The attending physician Dr. Sarah Davis ordered tests. James Williams, MD was the referring provider.</div>"
    }
}

# Test case 3: Dynamic age aggregation (>89)
AGE_AGGREGATION_TEST = {
    "resourceType": "Patient",
    "id": "PT-ELDERLY-001",
    "name": [{
        "family": "Anderson",
        "given": ["Margaret"]
    }],
    "birthDate": "1925-04-10",  # Age > 89 in 2026
    "gender": "female",
    "_birthDate": {
        "extension": [{
            "url": "http://hl7.org/fhir/StructureDefinition/patient-birthTime",
            "valueDateTime": "1925-04-10T08:30:00Z"
        }]
    },
    "text": {
        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">Patient Margaret Anderson, born in 1925, was admitted for geriatric care.</div>"
    }
}

# Test case 4: Combined complex scenario
COMPLEX_TEST = {
    "resourceType": "Patient",
    "id": "PT-COMPLEX-001",
    "name": [{
        "family": "Garcia",
        "given": ["Carlos", "Alejandro"]
    }],
    "birthDate": "1932-11-30",  # Age > 89
    "gender": "male",
    "contact": [{
        "name": {
            "family": "Garcia",
            "given": ["Maria"]
        },
        "relationship": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                "display": "wife"
            }]
        }]
    }],
    "generalPractitioner": [{
        "display": "Dr. Patricia Martinez",
        "reference": "Practitioner/PR-MARTINEZ"
    }],
    "_birthDate": {
        "extension": [{
            "url": "http://hl7.org/fhir/StructureDefinition/patient-birthTime",
            "valueDateTime": "1932-11-30T14:20:00Z"
        }]
    },
    "text": {
        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">Patient Carlos Garcia was admitted. His wife Maria Garcia contacted Dr. Patricia Martinez. Dr. Martinez examined Carlos. Maria called at 555-9876. Carlos was born in 1932.</div>"
    }
}

def test_deterministic_entity_syncing():
    """Test that names in structured fields are consistently replaced in unstructured text"""
    print("\n" + "="*70)
    print("Test 1: Deterministic Entity Syncing")
    print("="*70)
    
    engine = PHIDeidentifier(mode="pseudonymize")
    result = engine.deidentify_resource(DETERMINISTIC_SYNC_TEST)
    
    # Extract structured names
    patient_family = result['name'][0]['family']
    patient_given = result['name'][0]['given'][0]
    contact_family = result['contact'][0]['name']['family']
    contact_given = result['contact'][0]['name']['given'][0]
    
    print(f"\nStructured De-identification:")
    print(f"  Patient: {patient_given} {patient_family}")
    print(f"  Contact: {contact_given} {contact_family}")
    
    # Check text de-identification
    original_text = DETERMINISTIC_SYNC_TEST['text']['div']
    deidentified_text = result['text']['div']
    
    print(f"\nOriginal Text: {original_text}")
    print(f"De-identified Text: {deidentified_text}")
    
    # Verify deterministic syncing
    checks = []
    
    # Check if patient names from structured fields appear in text with same replacements
    if patient_given in deidentified_text and patient_family in deidentified_text:
        checks.append(("Patient name synced in text", True))
        print(f"  ✓ Patient name '{patient_given} {patient_family}' consistently used in text")
    else:
        checks.append(("Patient name synced in text", False))
        print(f"  ✗ Patient name not consistently synced in text")
    
    if contact_given in deidentified_text and contact_family in deidentified_text:
        checks.append(("Contact name synced in text", True))
        print(f"  ✓ Contact name '{contact_given} {contact_family}' consistently used in text")
    else:
        checks.append(("Contact name synced in text", False))
        print(f"  ✗ Contact name not consistently synced in text")
    
    # Check original names are removed
    if "Sarah" not in deidentified_text and "Johnson" not in deidentified_text:
        checks.append(("Original patient name removed", True))
        print(f"  ✓ Original patient name 'Sarah Johnson' removed from text")
    else:
        checks.append(("Original patient name removed", False))
        print(f"  ✗ Original patient name still present in text")
    
    if "Michael" not in deidentified_text:
        checks.append(("Original contact name removed", True))
        print(f"  ✓ Original contact name 'Michael' removed from text")
    else:
        checks.append(("Original contact name removed", False))
        print(f"  ✗ Original contact name still present in text")
    
    return result, checks

def test_clinician_anonymization():
    """Test clinician anonymization patterns"""
    print("\n" + "="*70)
    print("Test 2: Clinician Anonymization")
    print("="*70)
    
    engine = PHIDeidentifier(mode="pseudonymize")
    result = engine.deidentify_resource(CLINICIAN_ANONYMIZATION_TEST)
    
    original_text = CLINICIAN_ANONYMIZATION_TEST['text']['div']
    deidentified_text = result['text']['div']
    
    print(f"\nOriginal Text: {original_text}")
    print(f"De-identified Text: {deidentified_text}")
    
    checks = []
    
    # Check for clinician patterns
    original_clinicians = ["Dr. Emily Chen", "Doctor Michael Brown", "Dr. Sarah Davis", "James Williams, MD"]
    
    for clinician in original_clinicians:
        if clinician not in deidentified_text:
            checks.append((f"Clinician '{clinician}' anonymized", True))
            print(f"  ✓ Clinician '{clinician}' anonymized")
        else:
            checks.append((f"Clinician '{clinician}' anonymized", False))
            print(f"  ✗ Clinician '{clinician}' not anonymized")
    
    # Check that "Dr." pattern is handled
    if "Dr." in deidentified_text:
        checks.append(("Dr. pattern replaced with fake clinician", True))
        print(f"  ✓ Dr. pattern replaced with fake clinician names")
    else:
        checks.append(("Dr. pattern replaced with fake clinician", False))
        print(f"  ✗ Dr. pattern not properly handled")
    
    # Test different modes
    print("\nTesting different modes:")
    for mode in ["redact", "mask", "pseudonymize"]:
        engine_mode = PHIDeidentifier(mode=mode)
        result_mode = engine_mode.deidentify_resource(CLINICIAN_ANONYMIZATION_TEST)
        text_mode = result_mode['text']['div']
        
        if mode == "redact" and "[PROVIDER]" in text_mode:
            print(f"  ✓ Redact mode: Uses [PROVIDER] placeholder")
            checks.append(("Redact mode uses [PROVIDER]", True))
        elif mode == "mask" and "Dr. [REDACTED]" in text_mode:
            print(f"  ✓ Mask mode: Uses Dr. [REDACTED]")
            checks.append(("Mask mode uses Dr. [REDACTED]", True))
        elif mode == "pseudonymize" and "Dr." in text_mode and "Emily Chen" not in text_mode:
            print(f"  ✓ Pseudonymize mode: Uses fake clinician names")
            checks.append(("Pseudonymize mode uses fake names", True))
        else:
            print(f"  ✗ Mode {mode} not handling clinician anonymization correctly")
            checks.append((f"{mode} mode clinician handling", False))
    
    return result, checks

def test_dynamic_age_aggregation():
    """Test dynamic age aggregation for patients >89"""
    print("\n" + "="*70)
    print("Test 3: Dynamic Age Aggregation (>89 years)")
    print("="*70)
    
    engine = PHIDeidentifier(mode="pseudonymize")
    result = engine.deidentify_resource(AGE_AGGREGATION_TEST)
    
    print(f"\nOriginal Birth Date: {AGE_AGGREGATION_TEST['birthDate']}")
    print(f"De-identified Birth Date: {result['birthDate']}")
    
    checks = []
    
    # Check birthDate aggregation
    if result['birthDate'] == ">89":
        checks.append(("Birth date aggregated to >89", True))
        print(f"  ✓ Birth date correctly aggregated to '>89'")
    else:
        checks.append(("Birth date aggregated to >89", False))
        print(f"  ✗ Birth date not aggregated: {result['birthDate']}")
    
    # Check extension timestamp aggregation
    if "_birthDate" in result:
        ext_timestamp = result['_birthDate']['extension'][0].get('valueDateTime', '')
        print(f"Extension timestamp: {ext_timestamp}")
        
        if ext_timestamp == ">89":
            checks.append(("Extension timestamp aggregated to >89", True))
            print(f"  ✓ Extension timestamp correctly aggregated to '>89'")
        else:
            checks.append(("Extension timestamp aggregated to >89", False))
            print(f"  ✗ Extension timestamp not aggregated: {ext_timestamp}")
    
    # Check text mentions
    original_text = AGE_AGGREGATION_TEST['text']['div']
    deidentified_text = result['text']['div']
    
    print(f"\nOriginal Text: {original_text}")
    print(f"De-identified Text: {deidentified_text}")
    
    if "1925" not in deidentified_text:
        checks.append(("Birth year removed from text", True))
        print(f"  ✓ Birth year '1925' removed from text")
    else:
        checks.append(("Birth year removed from text", False))
        print(f"  ✗ Birth year still present in text")
    
    # Test different modes
    print("\nTesting different modes:")
    for mode in ["redact", "mask", "pseudonymize"]:
        engine_mode = PHIDeidentifier(mode=mode)
        result_mode = engine_mode.deidentify_resource(AGE_AGGREGATION_TEST)
        
        if mode == "redact" and result_mode['birthDate'] is None:
            print(f"  ✓ Redact mode: birthDate set to null")
            checks.append(("Redact mode birthDate null", True))
        elif mode in ["mask", "pseudonymize"] and result_mode['birthDate'] == ">89":
            print(f"  ✓ {mode.capitalize()} mode: birthDate set to '>89'")
            checks.append((f"{mode.capitalize()} mode birthDate >89", True))
        else:
            print(f"  ✗ Mode {mode} not handling age aggregation correctly")
            checks.append((f"{mode} mode age aggregation", False))
    
    return result, checks

def test_complex_scenario():
    """Test combined complex scenario with all features"""
    print("\n" + "="*70)
    print("Test 4: Complex Combined Scenario")
    print("="*70)
    
    engine = PHIDeidentifier(mode="pseudonymize")
    result = engine.deidentify_resource(COMPLEX_TEST)
    
    original_text = COMPLEX_TEST['text']['div']
    deidentified_text = result['text']['div']
    
    print(f"\nOriginal Text: {original_text}")
    print(f"De-identified Text: {deidentified_text}")
    
    checks = []
    
    # Check age aggregation
    if result['birthDate'] == ">89":
        checks.append(("Age >89 aggregated", True))
        print(f"  ✓ Age >89 correctly aggregated")
    else:
        checks.append(("Age >89 aggregated", False))
        print(f"  ✗ Age >89 not aggregated: {result['birthDate']}")
    
    # Check extension timestamp
    if "_birthDate" in result:
        ext_timestamp = result['_birthDate']['extension'][0].get('valueDateTime', '')
        if ext_timestamp == ">89":
            checks.append(("Extension timestamp aggregated", True))
            print(f"  ✓ Extension timestamp aggregated to '>89'")
        else:
            checks.append(("Extension timestamp aggregated", False))
            print(f"  ✗ Extension timestamp: {ext_timestamp}")
    
    # Check deterministic name syncing
    patient_family = result['name'][0]['family']
    patient_given = result['name'][0]['given'][0]
    contact_family = result['contact'][0]['name']['family']
    contact_given = result['contact'][0]['name']['given'][0]
    
    if patient_given in deidentified_text and patient_family in deidentified_text:
        checks.append(("Patient name synced in complex text", True))
        print(f"  ✓ Patient name '{patient_given} {patient_family}' synced in text")
    else:
        checks.append(("Patient name synced in complex text", False))
        print(f"  ✗ Patient name not synced")
    
    if contact_given in deidentified_text and contact_family in deidentified_text:
        checks.append(("Contact name synced in complex text", True))
        print(f"  ✓ Contact name '{contact_given} {contact_family}' synced in text")
    else:
        checks.append(("Contact name synced in complex text", False))
        print(f"  ✗ Contact name not synced")
    
    # Check clinician anonymization
    if "Dr. Patricia Martinez" not in deidentified_text:
        checks.append(("Clinician anonymized in complex text", True))
        print(f"  ✓ Clinician 'Dr. Patricia Martinez' anonymized")
    else:
        checks.append(("Clinician anonymized in complex text", False))
        print(f"  ✗ Clinician not anonymized")
    
    # Check original names removed
    if "Carlos" not in deidentified_text and "Garcia" not in deidentified_text:
        checks.append(("Original names removed from complex text", True))
        print(f"  ✓ Original names 'Carlos' and 'Garcia' removed")
    else:
        checks.append(("Original names removed from complex text", False))
        print(f"  ✗ Original names still present")
    
    # Check birth year removed from text
    if "1932" not in deidentified_text:
        checks.append(("Birth year removed from complex text", True))
        print(f"  ✓ Birth year '1932' removed from text")
    else:
        checks.append(("Birth year removed from complex text", False))
        print(f"  ✗ Birth year still present in text")
    
    return result, checks

def main():
    """Run all tests and generate comprehensive report"""
    print("\n" + "="*70)
    print("COMPREHENSIVE DETERMINISTIC ENTITY SYNCING TEST SUITE")
    print("="*70)
    
    all_checks = []
    
    # Test 1: Deterministic entity syncing
    result1, checks1 = test_deterministic_entity_syncing()
    all_checks.extend([(f"Test 1: {name}", result) for name, result in checks1])
    
    # Test 2: Clinician anonymization
    result2, checks2 = test_clinician_anonymization()
    all_checks.extend([(f"Test 2: {name}", result) for name, result in checks2])
    
    # Test 3: Dynamic age aggregation
    result3, checks3 = test_dynamic_age_aggregation()
    all_checks.extend([(f"Test 3: {name}", result) for name, result in checks3])
    
    # Test 4: Complex combined scenario
    result4, checks4 = test_complex_scenario()
    all_checks.extend([(f"Test 4: {name}", result) for name, result in checks4])
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in all_checks if result)
    total = len(all_checks)
    
    for check_name, result in all_checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    # Save results
    with open("test_deterministic_sync_output.json", "w") as f:
        json.dump({
            "deterministic_sync": {
                "original": DETERMINISTIC_SYNC_TEST,
                "deidentified": result1
            },
            "clinician_anonymization": {
                "original": CLINICIAN_ANONYMIZATION_TEST,
                "deidentified": result2
            },
            "age_aggregation": {
                "original": AGE_AGGREGATION_TEST,
                "deidentified": result3
            },
            "complex_scenario": {
                "original": COMPLEX_TEST,
                "deidentified": result4
            },
            "summary": {
                "total_checks": total,
                "passed_checks": passed,
                "failed_checks": total - passed,
                "all_checks": all_checks
            }
        }, f, indent=2, default=str)
    
    print("\nResults saved to test_deterministic_sync_output.json")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
