"""
HL7 v2 Message Parser
Parses ER7 format (pipe-delimited) HL7 v2 messages and extracts segments.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class HL7Segment:
    """Represents a single HL7 segment"""
    segment_id: str
    fields: List[str]
    raw: str


@dataclass
class HL7Message:
    """Represents a complete HL7 v2 message"""
    message_type: str
    trigger_event: str
    message_structure: str
    segments: Dict[str, List[HL7Segment]]
    ordered_segments: List[HL7Segment]
    raw: str
    errors: List[Dict]


class HL7Parser:
    """Parser for HL7 v2 ER7 format messages"""
    
    def __init__(self):
        self.encoding_chars = "^~\\&"
        self.field_separator = "|"
        self.component_separator = "^"
        self.subcomponent_separator = "&"
        self.repetition_separator = "~"
        self.escape_character = "\\"
    
    def parse(self, message: str) -> HL7Message:
        """
        Parse an HL7 v2 message in ER7 format.
        
        Args:
            message: Raw HL7 message string
            
        Returns:
            HL7Message object with parsed segments
        """
        errors = []
        message = message.strip()
        
        # Reset delimiters for each parse
        self.field_separator = "|"
        self.component_separator = "^"
        self.subcomponent_separator = "&"
        self.repetition_separator = "~"
        self.escape_character = "\\"
        self.encoding_chars = "^~\\&"
        
        # Validate basic structure
        if not message.startswith("MSH"):
            errors.append({
                "type": "parsing_error",
                "field": "MSH",
                "message": "HL7 message must start with MSH segment",
                "received": message[:20] if len(message) >= 20 else message
            })
        
        # Capture field separator and encoding characters from the MSH segment
        if len(message) > 3:
            self.field_separator = message[3]
            if len(message) >= 8:
                encoding_chars = message[4:8]
                if len(encoding_chars) >= 4:
                    self.component_separator = encoding_chars[0]
                    self.repetition_separator = encoding_chars[1]
                    self.escape_character = encoding_chars[2]
                    self.subcomponent_separator = encoding_chars[3]
                    self.encoding_chars = encoding_chars
        
        # Split into segments and parse each segment
        segment_strings = self._split_segments(message)
        
        # Parse each segment
        segments = {}
        ordered_segments = []
        message_type = "UNKNOWN"
        trigger_event = "UNKNOWN"
        message_structure = "UNKNOWN"
        
        for seg_str in segment_strings:
            if not seg_str.strip():
                continue
            
            try:
                segment = self._parse_segment(seg_str)
                segment_id = segment.segment_id
                
                if segment_id not in segments:
                    segments[segment_id] = []
                segments[segment_id].append(segment)
                ordered_segments.append(segment)
                
                # Extract message type from MSH-9 (HL7 uses the field separator as MSH-1)
                if segment_id == "MSH" and len(segment.fields) >= 8:
                    message_type_field = segment.fields[7]
                    if "^" in message_type_field:
                        parts = message_type_field.split("^")
                        message_type = parts[0] if len(parts) > 0 else "UNKNOWN"
                        trigger_event = parts[1] if len(parts) > 1 else "UNKNOWN"
                    else:
                        message_type = message_type_field
                        trigger_event = "UNKNOWN"
                    message_structure = segment.fields[9] if len(segment.fields) > 9 else "UNKNOWN"
                    
            except Exception as e:
                errors.append({
                    "type": "parsing_error",
                    "field": seg_str[:3] if len(seg_str) >= 3 else "UNKNOWN",
                    "message": f"Failed to parse segment: {str(e)}",
                    "received": seg_str[:50]
                })
        
        return HL7Message(
            message_type=message_type,
            trigger_event=trigger_event,
            message_structure=message_structure,
            segments=segments,
            ordered_segments=ordered_segments,
            raw=message,
            errors=errors
        )
    
    def _split_segments(self, message: str) -> List[str]:
        """Split message into segments based on segment terminators"""
        # HL7 segments are typically separated by \r\n or just \r
        segments = re.split(r'\r\n|\r|\n', message)
        return [s.strip() for s in segments if s.strip()]
    
    def _parse_segment(self, segment_str: str) -> HL7Segment:
        """Parse a single segment string"""
        segment_id = segment_str[:3]
        fields = []
        
        if len(segment_str) > 3:
            # Fields start after the segment ID and the field separator
            fields_str = segment_str[4:] if len(segment_str) > 4 else ""
            fields = fields_str.split(self.field_separator) if fields_str else []
        
        return HL7Segment(
            segment_id=segment_id,
            fields=fields,
            raw=segment_str
        )
    
    def get_field(self, segment: HL7Segment, field_index: int, component_index: int = None, subcomponent_index: int = None) -> Optional[str]:
        """
        Get a field from a segment, optionally a specific component or subcomponent.
        
        Args:
            segment: HL7Segment object
            field_index: 1-based HL7 field index after the segment ID
            component_index: Optional component index within the field
            subcomponent_index: Optional subcomponent index within the component
            
        Returns:
            Field value or nested component/subcomponent value, or None if not found
        """
        actual_index = field_index - 1
        if actual_index < 0 or actual_index >= len(segment.fields):
            return None
        
        field_value = segment.fields[actual_index]
        if not field_value:
            return None
        
        if component_index is None:
            return field_value
        
        components = field_value.split(self.component_separator)
        if component_index < 0 or component_index >= len(components):
            return None
        component_value = components[component_index]
        if component_value == "":
            return None
        
        if subcomponent_index is None:
            return component_value
        
        subcomponents = component_value.split(self.subcomponent_separator)
        if subcomponent_index < 0 or subcomponent_index >= len(subcomponents):
            return None
        return subcomponents[subcomponent_index] or None
    
    def get_repeated_fields(self, segment: HL7Segment, field_index: int) -> List[str]:
        """Get repeated fields from a segment"""
        actual_index = field_index - 1
        
        if actual_index < 0 or actual_index >= len(segment.fields):
            return []
        
        field_value = segment.fields[actual_index]
        
        if field_value == "" or field_value is None:
            return []
        
        return field_value.split(self.repetition_separator)
    
    def parse_hl7_datetime(self, hl7_datetime: str) -> Optional[str]:
        """
        Convert HL7 datetime format to ISO 8601 format.
        HL7 format: YYYYMMDDHHMMSS+/-HHMM
        ISO format: YYYY-MM-DDTHH:MM:SS+/-HH:MM
        """
        if not hl7_datetime or len(hl7_datetime) < 8:
            return None
        
        try:
            # Parse date components
            year = hl7_datetime[0:4]
            month = hl7_datetime[4:6]
            day = hl7_datetime[6:8]
            
            iso_date = f"{year}-{month}-{day}"
            
            # Add time if present
            if len(hl7_datetime) >= 12:
                hour = hl7_datetime[8:10]
                minute = hl7_datetime[10:12]
                iso_date += f"T{hour}:{minute}"
            
            if len(hl7_datetime) >= 14:
                second = hl7_datetime[12:14]
                iso_date += f":{second}"
            
            # Add timezone if present
            if len(hl7_datetime) >= 18:
                tz_sign = hl7_datetime[14]
                tz_hour = hl7_datetime[15:17]
                tz_minute = hl7_datetime[17:19]
                iso_date += f"{tz_sign}{tz_hour}:{tz_minute}"
            
            return iso_date
        except Exception:
            return None
    
    def parse_hl7_date(self, hl7_date: str) -> Optional[str]:
        """Convert HL7 date format (YYYYMMDD) to ISO format (YYYY-MM-DD)"""
        if not hl7_date or len(hl7_date) < 8:
            return None
        
        try:
            year = hl7_date[0:4]
            month = hl7_date[4:6]
            day = hl7_date[6:8]
            return f"{year}-{month}-{day}"
        except Exception:
            return None

    def parse_hl7_time(self, hl7_time: str) -> Optional[str]:
        """Convert HL7 time format (HHMMSS[.S+] ) to ISO time string"""
        if not hl7_time or len(hl7_time) < 2:
            return None
        try:
            hour = hl7_time[0:2]
            minute = hl7_time[2:4] if len(hl7_time) >= 4 else "00"
            second = hl7_time[4:6] if len(hl7_time) >= 6 else "00"
            time_str = f"{hour}:{minute}:{second}"
            if len(hl7_time) > 6 and hl7_time[6] == ".":
                fraction = hl7_time[7:]
                time_str += f".{fraction}"
            return time_str
        except Exception:
            return None

    def split_components(self, value: Optional[str]) -> List[str]:
        """Split a field into HL7 components without raising on empty values."""
        if value is None:
            return []
        return value.split(self.component_separator)

    def split_subcomponents(self, value: Optional[str]) -> List[str]:
        """Split a component into HL7 subcomponents safely."""
        if value is None:
            return []
        return value.split(self.subcomponent_separator)

    def parse_codeable_concept(self, hl7_value: Optional[str], default_system: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Convert HL7 CE/CWE/CNE coded values into FHIR CodeableConcept."""
        if not hl7_value:
            return None
        components = self.split_components(hl7_value)
        if not components:
            return None
        code = components[0] or None
        display = components[1] if len(components) > 1 and components[1] else None
        system_label = components[2] if len(components) > 2 and components[2] else None
        
        system_map = {
            "LN": "http://loinc.org",
            "L": "http://loinc.org",
            "SNM": "http://snomed.info/sct",
            "SCT": "http://snomed.info/sct",
            "RXNORM": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "ICD-10": "http://hl7.org/fhir/sid/icd-10"
        }
        system = system_map.get(system_label, default_system)
        if not code and not display:
            return None
        coding = {}
        if code:
            coding["code"] = code
        if system:
            coding["system"] = system
        if display:
            coding["display"] = display
        concept = {"coding": [coding]} if coding else None
        if concept and display:
            concept["text"] = display
        return concept

    def parse_first_component(self, hl7_value: Optional[str]) -> Optional[str]:
        """Extract the first component from a caret-delimited HL7 value."""
        if not hl7_value:
            return None
        return self.split_components(hl7_value)[0] if self.split_components(hl7_value) else None


def parse_hl7_message(message: str) -> HL7Message:
    """Convenience function to parse an HL7 message"""
    parser = HL7Parser()
    return parser.parse(message)
