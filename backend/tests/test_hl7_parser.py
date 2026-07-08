from hl7_parser import HL7Parser


def test_hl7_parser_handles_msh_repetitions_subcomponents_and_escapes():
    hl7 = (
        'MSH|^~\\&|APP|FAC|LAB|FAC|20260702123045||ADT^A08|MSG000001|P|2.5\r'
        'PID|1||MRN12345^^^MRN~SSN987654321^^^SSN~NPI1234567890^^^NPI|123456789|DOE^JOHN^^^^|19670515|M|'
        '123 MAIN ST^APT 4B&UNIT 5^SUITE 100^BOSTON^MA^02110|^PRN^PH^^^617^5550100|^WPN^PH^^^617^5550199\r'
        'OBX|1|ST|718-7^Hemoglobin^LN||Test\\.B\\value\\.T\\|g/dL|||N'
    )

    parser = HL7Parser()
    parsed = parser.parse(hl7)

    msh = parsed.segments["MSH"][0]
    pid = parsed.segments["PID"][0]
    obx = parsed.segments["OBX"][0]

    assert parsed.message_type == "ADT"
    assert parsed.trigger_event == "A08"
    assert msh.fields[0] == "|"
    assert msh.fields[1] == "^~\\&"
    assert parser.get_field(msh, 9) == "ADT"

    repeated_ids = parser.get_repeated_fields(pid, 3)
    assert repeated_ids == ["MRN12345^^^MRN", "SSN987654321^^^SSN", "NPI1234567890^^^NPI"]
    assert parser.get_field(pid, 11, 1, 0) == "APT 4B"
    assert parser.get_field(pid, 11, 1, 1) == "UNIT 5"

    assert parser.get_field(obx, 5) == "Testvalue"


def test_hl7_parser_isolates_nte_segments_across_carriage_variations():
    hl7 = (
        'MSH|^~\\&|APP|FAC|LAB|FAC|20260702123045||ADT^A08|MSG000001|P|2.5\r'
        'PID|1||123456789|DOE^JOHN\r'
        'NTE|1|L|Patient requested follow-up\r'
    )

    parser = HL7Parser()
    parsed = parser.parse(hl7)

    assert "NTE" in parsed.segments
    assert len(parsed.segments["NTE"]) == 1
    assert parsed.segments["NTE"][0].segment_id == "NTE"
    assert parser.get_field(parsed.segments["NTE"][0], 3) == "Patient requested follow-up"
