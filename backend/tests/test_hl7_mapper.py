import pytest
from hl7_mapper import HL7Mapper


def test_oru_r01_obx_numeric_and_string_mapping():
    hl7 = (
        'MSH|^~\\&|LAB|HOSP|EHR|HOSP|202407010830||ORU^R01|12345|P|2.5\r'
        'PID|||123456||Doe^John||19800101|M|||123 Main St^^Metropolis^NY^12345||555-5555|||S\r'
        'PV1||I|W^123^1^HOSP||||1234^Smith^Jane|||||||||||1234567890|||||||||||||||||202407010830\r'
        'OBR|1||1001^Lab|718-7^Hemoglobin^LN|||202407010800|||||||||12345^Smith^Jane||202407010830\r'
        'OBX|1|NM|718-7^Hemoglobin^LN||13.5|g/dL|12-16|H|||F|||202407010825\r'
        'OBX|2|ST|18790-0^Glucose^LN||fasting|mg/dL|||N|||F|||202407010825\r'
    )

    mapper = HL7Mapper()
    result = mapper.map_to_fhir(hl7)
    bundle = result["bundle"]

    assert result["message_type"] == "ORU^R01"
    assert len(bundle["entry"]) == 5

    observation_entries = [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Observation"]
    assert len(observation_entries) == 2

    numeric_obs = observation_entries[0]
    assert numeric_obs["valueQuantity"]["value"] == 13.5
    assert numeric_obs["valueQuantity"]["unit"] == "g/dL"
    assert numeric_obs["valueQuantity"]["code"] == "g/dL"
    assert numeric_obs["interpretation"]["coding"][0]["code"] == "H"

    string_obs = observation_entries[1]
    assert string_obs["valueString"] == "fasting"
    assert string_obs["code"]["coding"][0]["code"] == "18790-0"
    assert string_obs["code"]["coding"][0]["display"] == "Glucose"


def test_oru_r01_missing_optional_fields_do_not_crash():
    hl7 = (
        'MSH|^~\\&|LAB|HOSP|EHR|HOSP|202407010830||ORU^R01|12345|P|2.5\r'
        'PID|||123456||Doe^John||19800101|M|||123 Main St^^Metropolis^NY^12345||555-5555|||S\r'
        'OBX|1|NM|718-7^Hemoglobin^LN||||||N|||F|||202407010825\r'
    )

    mapper = HL7Mapper()
    result = mapper.map_to_fhir(hl7)
    bundle = result["bundle"]

    assert result["message_type"] == "ORU^R01"
    observation_entries = [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Observation"]
    assert len(observation_entries) == 1
    assert observation_entries[0].get("valueQuantity") is None
    assert observation_entries[0].get("valueString") is None
    assert observation_entries[0]["code"]["coding"][0]["code"] == "718-7"
