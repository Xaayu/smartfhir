"""
Test enhanced HIPAA de-identification with strict validation constraints.
Tests:
1. Structure & URL schema protection
2. Enhanced NLP scanning for names, relationships, employers, neighborhoods
3. Gender consistency in name generation
4. Age 90+ date redaction across all timestamps
5. Custom identifier extension pseudonymization
"""

import json
from phi_deidentifier import PHIDeidentifier, deidentify

def test_schema_protection():
    """Test that schema URLs and XML namespaces are protected"""
    print("Testing schema URL protection...")
    
    resource = {
        "resourceType": "Patient",
        "id": "test-patient",
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-birthPlace",
                "valueAddress": {
                    "city": "Manhattan",
                    "state": "NY"
                }
            },
            {
                "url": "http://custom.org/StructureDefinition/patient-employer",
                "valueString": "Acme Corporation"
            }
        ],
        "text": {
            "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">Patient notes</div>"
        }
    }
    
    engine = PHIDeidentifier(mode="pseudonymize")
    result = engine.deidentify_resource(resource)
    
    # Check that HL7 schema URL is preserved
    hl7_url = result["extension"][0]["url"]
    assert "hl7.org/fhir/StructureDefinition" in hl7_url, "HL7 schema URL should be preserved"
    
    # Check that custom extension URL is preserved but value is pseudonymized
    custom_url = result["extension"][1]["url"]
    assert custom_url == "http://custom.org/StructureDefinition/patient-employer", "Custom extension URL should be preserved"
    assert result["extension"][1]["valueString"] != "Acme Corporation", "Custom extension value should be pseudonymized"
    
    # Check that XML namespace is preserved
    assert "xmlns" in result["text"]["div"], "XML namespace should be preserved"
    
    print("✓ Schema URL protection test passed")


def test_enhanced_nlp_scanning():
    """Test enhanced NLP scanning for names, relationships, employers, neighborhoods"""
    print("Testing enhanced NLP scanning...")
    
    resource = {
        "resourceType": "Patient",
        "id": "test-patient",
        "gender": "male",
        "name": [{
            "family": "Smith",
            "given": ["John"]
        }],
        "text": {
            "div": "Patient John Smith lives in Manhattan with his wife Mary. He works at Acme Corporation and was referred by Dr. Johnson. Contact him at 555-1234."
        }
    }
    
    engine = PHIDeidentifier(mode="pseudonymize")
    result = engine.deidentify_resource(resource)
    
    text_div = result["text"]["div"]
    
    # Check that neighborhood is pseudonymized
    assert "Manhattan" not in text_div, "Neighborhood should be pseudonymized"
    
    # Check that employer is pseudonymized
    assert "Acme Corporation" not in text_div, "Employer should be pseudonymized"
    
    # Check that phone is pseudonymized
    assert "555-1234" not in text_div, "Phone should be pseudonymized"
    
    # Check that names are consistently pseudonymized
    assert "John Smith" not in text_div, "Patient name should be pseudonymized"
    
    print("✓ Enhanced NLP scanning test passed")


def test_gender_consistency():
    """Test that names are gender-consistent"""
    print("Testing gender consistency...")
    
    # Test male patient
    male_resource = {
        "resourceType": "Patient",
        "id": "male-patient",
        "gender": "male",
        "name": [{
            "family": "Smith",
            "given": ["John"]
        }],
        "text": {
            "div": "Patient John Smith was seen by Dr. Williams."
        }
    }
    
    engine = PHIDeidentifier(mode="pseudonymize")
    male_result = engine.deidentify_resource(male_resource)
    
    # Test female patient
    female_resource = {
        "resourceType": "Patient",
        "id": "female-patient",
        "gender": "female",
        "name": [{
            "family": "Johnson",
            "given": ["Mary"]
        }],
        "text": {
            "div": "Patient Mary Johnson was seen by Dr. Williams."
        }
    }
    
    engine = PHIDeidentifier(mode="pseudonymize")
    female_result = engine.deidentify_resource(female_resource)
    
    # Both should have names pseudonymized
    assert "John Smith" not in male_result["text"]["div"], "Male patient name should be pseudonymized"
    assert "Mary Johnson" not in female_result["text"]["div"], "Female patient name should be pseudonymized"
    
    print("✓ Gender consistency test passed")


def test_age_90_plus_redaction():
    """Test aggressive date redaction for 90+ patients"""
    print("Testing age 90+ date redaction...")
    
    # Create a patient born in 1930 (90+ years old)
    resource = {
        "resourceType": "Patient",
        "id": "elderly-patient",
        "gender": "female",
        "birthDate": "1930-05-15",
        "name": [{
            "family": "Williams",
            "given": ["Eleanor"]
        }],
        "meta": {
            "lastUpdated": "2024-01-15T10:30:00Z"
        },
        "text": {
            "div": "Patient born in 1930, seen on 2024-01-15"
        }
    }
    
    engine = PHIDeidentifier(mode="pseudonymize")
    result = engine.deidentify_resource(resource)
    
    # Birth date should be >89
    assert result["birthDate"] == ">89", "Birth date for 90+ should be >89"
    
    # Meta timestamp should be redacted
    assert result["meta"]["lastUpdated"] == ">89", "Timestamp for 90+ should be >89"
    
    # Birth year in text should be removed
    assert "1930" not in result["text"]["div"], "Birth year in text should be removed for 90+"
    
    print("✓ Age 90+ date redaction test passed")


def test_custom_identifier_extensions():
    """Test aggressive pseudonymization of custom identifier extensions"""
    print("Testing custom identifier extension pseudonymization...")
    
    resource = {
        "resourceType": "Patient",
        "id": "test-patient",
        "extension": [
            {
                "url": "http://custom.org/fhir/StructureDefinition/patient-employer",
                "valueString": "Microsoft Corporation"
            },
            {
                "url": "http://custom.org/fhir/StructureDefinition/school-tracking",
                "valueReference": {
                    "reference": "Organization/harvard-university",
                    "display": "Harvard University"
                }
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-birthPlace",
                "valueString": "Boston"
            }
        ]
    }
    
    engine = PHIDeidentifier(mode="pseudonymize")
    result = engine.deidentify_resource(resource)
    
    # Custom employer extension should be pseudonymized
    employer_ext = next(e for e in result["extension"] if "employer" in e["url"])
    assert employer_ext["valueString"] != "Microsoft Corporation", "Employer value should be pseudonymized"
    
    # Custom school tracking extension should be pseudonymized
    school_ext = next(e for e in result["extension"] if "school" in e["url"])
    assert school_ext["valueReference"]["display"] != "Harvard University", "School display should be pseudonymized"
    assert school_ext["valueReference"]["reference"] != "Organization/harvard-university", "School reference should be pseudonymized"
    
    # HL7 standard extension should be handled normally (not aggressively)
    hl7_ext = next(e for e in result["extension"] if "hl7.org" in e["url"])
    assert hl7_ext["url"] == "http://hl7.org/fhir/StructureDefinition/patient-birthPlace", "HL7 URL should be preserved"
    
    print("✓ Custom identifier extension test passed")


def test_comprehensive_patient():
    """Test comprehensive patient resource with all features"""
    print("Testing comprehensive patient resource...")
    
    resource = {
        "resourceType": "Patient",
        "id": "comprehensive-test",
        "gender": "male",
        "birthDate": "1985-03-20",
        "name": [{
            "use": "official",
            "family": "Anderson",
            "given": ["Robert", "James"]
        }],
        "telecom": [{
            "system": "phone",
            "value": "212-555-7890",
            "use": "home"
        }],
        "address": [{
            "line": ["123 Main Street"],
            "city": "Brooklyn",
            "state": "NY",
            "postalCode": "11201"
        }],
        "extension": [
            {
                "url": "http://custom.org/fhir/StructureDefinition/patient-employer",
                "valueString": "Google Inc"
            }
        ],
        "text": {
            "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">Patient Robert James Anderson lives in Brooklyn. He works at Google Inc and was referred by Dr. Sarah Miller. His wife Jennifer called at 212-555-7890.</div>"
        },
        "meta": {
            "lastUpdated": "2024-02-01T14:30:00Z"
        }
    }
    
    engine = PHIDeidentifier(mode="pseudonymize")
    result = engine.deidentify_resource(resource)
    
    # Check structured fields
    assert result["name"][0]["family"] != "Anderson", "Family name should be pseudonymized"
    assert result["name"][0]["given"][0] != "Robert", "Given name should be pseudonymized"
    assert result["address"][0]["city"] != "Brooklyn", "City should be pseudonymized"
    assert result["telecom"][0]["value"] != "212-555-7890", "Phone should be pseudonymized"
    
    # Check text field
    text_div = result["text"]["div"]
    assert "Robert" not in text_div, "Name should be pseudonymized in text"
    assert "Anderson" not in text_div, "Name should be pseudonymized in text"
    assert "Brooklyn" not in text_div, "Neighborhood should be pseudonymized in text"
    assert "Google Inc" not in text_div, "Employer should be pseudonymized in text"
    assert "212-555-7890" not in text_div, "Phone should be pseudonymized in text"
    
    # Check XML namespace preservation
    assert "xmlns" in text_div, "XML namespace should be preserved"
    
    # Check custom extension
    employer_ext = next(e for e in result["extension"] if "employer" in e["url"])
    assert employer_ext["valueString"] != "Google Inc", "Employer in extension should be pseudonymized"
    
    print("✓ Comprehensive patient test passed")


def run_all_tests():
    """Run all enhanced de-identification tests"""
    print("=" * 60)
    print("Running Enhanced HIPAA De-identification Tests")
    print("=" * 60)
    
    test_schema_protection()
    test_enhanced_nlp_scanning()
    test_gender_consistency()
    test_age_90_plus_redaction()
    test_custom_identifier_extensions()
    test_comprehensive_patient()
    
    print("=" * 60)
    print("All tests passed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
