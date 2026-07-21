"""Test script to verify mapper functionality"""
import sys
import json
from mapper import map_to_fhir, enhanced_map_to_fhir, get_all_mappings

def test_basic_patient_mapping():
    """Test basic patient data mapping"""
    print("Testing basic patient mapping...")
    
    test_data = {
        "patient_id": "12345",
        "first_name": "John",
        "last_name": "Doe",
        "dob": "1990-01-15",
        "gender": "M",
        "phone": "555-1234",
        "email": "john.doe@example.com",
        "address": "123 Main St",
        "city": "Metropolis",
        "state": "NY",
        "zip": "12345"
    }
    
    result = map_to_fhir(test_data, resource_type="Patient", enable_advanced=False)
    
    print(f"Mapping complete: {result['mapping_complete']}")
    print(f"Overall confidence: {result['overall_confidence']:.2f}")
    print(f"Fields mapped: {result['fields_mapped']}")
    print(f"Unmapped fields: {len(result['unmapped_fields'])}")
    
    # Debug: check applied rules
    print("\nApplied rules:")
    for rule in result['applied_rules']:
        print(f"  {rule['original_field']} -> {rule['mapped_to']} ({rule['rule_type']})")
    
    if result['mapped_resource']:
        print("\nMapped resource:")
        print(json.dumps(result['mapped_resource'], indent=2))
    
    if result['unmapped_fields']:
        print("\nUnmapped fields:")
        for field in result['unmapped_fields']:
            print(f"  - {field['field']}: {field['message']}")
    
    return result

def test_observation_mapping():
    """Test observation data mapping"""
    print("\n\nTesting observation mapping...")
    
    test_data = {
        "patient_id": "12345",
        "test_name": "Blood Pressure",
        "result": "120/80",
        "unit": "mmHg",
        "test_date": "2024-01-15",
        "status": "final"
    }
    
    result = map_to_fhir(test_data, resource_type="Observation")
    
    print(f"Mapping complete: {result['mapping_complete']}")
    print(f"Overall confidence: {result['overall_confidence']:.2f}")
    print(f"Fields mapped: {result['fields_mapped']}")
    print(f"Unmapped fields: {len(result['unmapped_fields'])}")
    
    if result['mapped_resource']:
        print("\nMapped resource:")
        print(json.dumps(result['mapped_resource'], indent=2))
    
    if result['unmapped_fields']:
        print("\nUnmapped fields:")
        for field in result['unmapped_fields']:
            print(f"  - {field['field']}: {field['message']}")
    
    return result

def test_enhanced_mapping():
    """Test enhanced mapping with advanced features"""
    print("\n\nTesting enhanced mapping with advanced features...")
    
    test_data = {
        "custom_patient_id": "PAT-001",
        "full_name": "Jane Smith",
        "date_of_birth": "1985-05-20",
        "sex": "F",
        "mobile_number": "555-9876",
        "email_address": "jane.smith@example.com",
        "street_address": "456 Oak Ave",
        "city_name": "Gotham",
        "state_code": "NJ",
        "postal_code": "54321"
    }
    
    result = enhanced_map_to_fhir(test_data, resource_type="Patient", enable_advanced=True)
    
    print(f"Mapping complete: {result['mapping_complete']}")
    print(f"Overall confidence: {result['overall_confidence']:.2f}")
    print(f"Fields mapped: {result['fields_mapped']}")
    print(f"Unmapped fields: {len(result['unmapped_fields'])}")
    
    if result['mapped_resource']:
        print("\nMapped resource:")
        print(json.dumps(result['mapped_resource'], indent=2))
    
    if result['unmapped_fields']:
        print("\nUnmapped fields:")
        for field in result['unmapped_fields']:
            print(f"  - {field['field']}: {field['message']}")
    
    return result

def test_get_all_mappings():
    """Test retrieving all mappings"""
    print("\n\nTesting get_all_mappings...")
    
    mappings = get_all_mappings("Patient")
    
    print(f"Resource type: {mappings['resource_type']}")
    print(f"Total built-in mappings: {mappings['total_built_in']}")
    print(f"Total user-defined mappings: {mappings['total_user_defined']}")
    print(f"Total learned mappings: {mappings['total_learned']}")
    
    return mappings

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("CODE MAPPER FUNCTIONALITY TEST")
        print("=" * 60)
        
        # Run tests
        test_basic_patient_mapping()
        test_observation_mapping()
        test_enhanced_mapping()
        test_get_all_mappings()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
