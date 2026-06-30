"""
HL7 v2 Message Parser
Parses ER7 format (pipe-delimited) HL7 v2 messages and extracts segments.
"""

import re
from typing import Dict, List, Optional, Tuple
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
        
        # Validate basic structure
        if not message.startswith("MSH"):
            errors.append({
                "type": "parsing_error",
                "field": "MSH",
                "message": "HL7 message must start with MSH segment",
                "received": message[:20] if len(message) >= 20 else message
            })
        
        # Parse encoding characters from MSH
        if len(message) >= 8:
            try:
                self.encoding_chars = message[3:8]
                if len(self.encoding_chars) >= 4:
                    self.field_separator = self.encoding_chars[0]
                    self.component_separator = self.encoding_chars[1]
                    self.subcomponent_separator = self.encoding_chars[2]
                    self.repetition_separator = self.encoding_chars[3]
                    if len(self.encoding_chars) >= 5:
                        self.escape_character = self.encoding_chars[4]
            except Exception as e:
                errors.append({
                    "type": "parsing_error",
                    "field": "MSH",
                    "message": f"Failed to parse encoding characters: {str(e)}",
                    "received": message[3:8]
                })
        
        # Split into segments
        segment_strings = self._split_segments(message)
        
        # Parse each segment
        segments = {}
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
                
                # Extract message type from MSH
                if segment_id == "MSH" and len(segment.fields) >= 9:
                    message_type_field = segment.fields[8] if len(segment.fields) > 8 else "UNKNOWN"
                    # Split message type (e.g., "ORU^R01" -> message_type="ORU", trigger_event="R01")
                    if "^" in message_type_field:
                        parts = message_type_field.split("^")
                        message_type = parts[0] if len(parts) > 0 else "UNKNOWN"
                        trigger_event = parts[1] if len(parts) > 1 else "UNKNOWN"
                    else:
                        message_type = message_type_field
                        trigger_event = "UNKNOWN"
                    message_structure = segment.fields[10] if len(segment.fields) > 10 else "UNKNOWN"
                    
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
        # First 3 characters are segment ID
        segment_id = segment_str[:3]
        
        # Split fields
        if len(segment_str) > 3:
            fields_str = segment_str[3:]
            fields = fields_str.split(self.field_separator)
        else:
            fields = []
        
        return HL7Segment(
            segment_id=segment_id,
            fields=fields,
            raw=segment_str
        )
    
    def get_field(self, segment: HL7Segment, field_index: int, component_index: int = None) -> Optional[str]:
        """
        Get a field from a segment, optionally a specific component.
        
        Args:
            segment: HL7Segment object
            field_index: 0-based field index (field 1 is index 0 after segment ID)
            component_index: Optional component index within the field
            
        Returns:
            Field value or component value, or None if not found
        """
        # Adjust for segment ID (field 1 in HL7 is index 0 in fields list)
        actual_index = field_index - 1
        
        if actual_index < 0 or actual_index >= len(segment.fields):
            return None
        
        field_value = segment.fields[actual_index]
        
        if field_value == "" or field_value is None:
            return None
        
        if component_index is not None:
            components = field_value.split(self.component_separator)
            if component_index < len(components):
                return components[component_index]
            return None
        
        return field_value
    
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


def parse_hl7_message(message: str) -> HL7Message:
    """Convenience function to parse an HL7 message"""
    parser = HL7Parser()
    return parser.parse(message)
