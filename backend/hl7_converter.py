"""
HL7 v2 to FHIR Converter
Main conversion orchestrator with detailed error handling and explanations.
"""

from typing import Dict, List, Any, Optional
from hl7_parser import HL7Message, HL7Parser
from hl7_mapper import HL7Mapper
from explainer import explain_errors


class HL7Converter:
    """Main converter for HL7 v2 to FHIR with error handling"""
    
    def __init__(self):
        self.parser = HL7Parser()
        self.mapper = HL7Mapper()
    
    def convert(self, hl7_message: str, explain_errors_flag: bool = True) -> Dict[str, Any]:
        """
        Convert HL7 v2 message to FHIR Bundle with error handling.
        
        Args:
            hl7_message: Raw HL7 message string
            explain_errors_flag: Whether to use AI to explain errors
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating if conversion succeeded
            - bundle: FHIR Bundle resource
            - errors: List of errors with explanations
            - message_type: HL7 message type
        """
        result = {
            "success": False,
            "bundle": None,
            "errors": [],
            "message_type": "UNKNOWN"
        }
        
        # Step 1: Parse HL7 message
        try:
            parsed = self.parser.parse(hl7_message)
            result["message_type"] = f"{parsed.message_type}^{parsed.trigger_event}"
            
            # Add parsing errors
            for error in parsed.errors:
                result["errors"].append({
                    "type": "parsing_error",
                    "field": error.get("field", "UNKNOWN"),
                    "message": error.get("message", "Unknown parsing error"),
                    "received": error.get("received", ""),
                    "explanation": self._explain_parsing_error(error),
                    "suggested_fix": self._suggest_parsing_fix(error),
                    "fix": None
                })
            
        except Exception as e:
            result["errors"].append({
                "type": "parsing_error",
                "field": "MESSAGE",
                "message": f"Failed to parse HL7 message: {str(e)}",
                "received": hl7_message[:100] if len(hl7_message) >= 100 else hl7_message,
                "explanation": "The HL7 message could not be parsed. This usually means the message format is invalid or malformed.",
                "suggested_fix": "Ensure the message starts with MSH segment and uses proper HL7 v2 ER7 format with pipe (|) delimiters.",
                "fix": None
            })
            return result
        
        # Step 2: Map to FHIR
        try:
            mapping_result = self.mapper.map_to_fhir(hl7_message)
            result["bundle"] = mapping_result["bundle"]
            
            # Add mapping errors
            for error in mapping_result["errors"]:
                result["errors"].append({
                    "type": "mapping_error",
                    "field": error.get("field", "UNKNOWN"),
                    "message": error.get("message", "Unknown mapping error"),
                    "received": error.get("received", ""),
                    "explanation": self._explain_mapping_error(error),
                    "suggested_fix": self._suggest_mapping_fix(error),
                    "fix": None
                })
            
        except Exception as e:
            result["errors"].append({
                "type": "mapping_error",
                "field": "MESSAGE",
                "message": f"Failed to map HL7 to FHIR: {str(e)}",
                "received": hl7_message[:100] if len(hl7_message) >= 100 else hl7_message,
                "explanation": "The HL7 message could not be mapped to FHIR resources. This may be due to unsupported message type or missing required segments.",
                "suggested_fix": "Ensure the message type is supported (ADT^A01, ORU^R01, ORM^O01) and contains required segments (PID, PV1, OBX, ORC).",
                "fix": None
            })
            return result
        
        # Step 3: Validate FHIR resources
        validation_errors = self._validate_fhir_bundle(result["bundle"])
        for error in validation_errors:
            result["errors"].append(error)
        
        # Step 4: Explain errors using AI if requested
        if explain_errors_flag and result["errors"]:
            try:
                # Prepare errors for AI explanation
                ai_errors = []
                for error in result["errors"]:
                    if error.get("type") in ["mapping_error", "validation_error"]:
                        ai_errors.append({
                            "type": "ai_needed",
                            "field": error.get("field", "UNKNOWN"),
                            "message": error.get("message", ""),
                            "received": error.get("received", "")
                        })
                
                if ai_errors:
                    explained = explain_errors(ai_errors, {"hl7_message": hl7_message})
                    # Update errors with AI explanations
                    ai_index = 0
                    for i, error in enumerate(result["errors"]):
                        if error.get("type") in ["mapping_error", "validation_error"] and ai_index < len(explained):
                            result["errors"][i]["explanation"] = explained[ai_index].get("explanation", error.get("explanation"))
                            result["errors"][i]["suggested_fix"] = explained[ai_index].get("suggested_fix", error.get("suggested_fix"))
                            result["errors"][i]["fix"] = explained[ai_index].get("fix")
                            ai_index += 1
            except Exception as e:
                # AI explanation failed, keep rule-based explanations
                pass
        
        # Determine success
        result["success"] = (
            result["bundle"] is not None and
            len([e for e in result["errors"] if e.get("type") == "parsing_error"]) == 0
        )
        
        return result
    
    def _explain_parsing_error(self, error: Dict[str, Any]) -> str:
        """Provide rule-based explanation for parsing errors"""
        field = error.get("field", "")
        message = error.get("message", "")
        
        if field == "MSH" and "must start with MSH" in message:
            return "HL7 v2 messages must begin with the MSH (Message Header) segment. This segment contains metadata about the message including encoding characters, message type, and timestamp."
        
        if "encoding characters" in message.lower():
            return "The MSH segment contains encoding characters at positions 4-8 that define how fields and components are separated. These must be properly formatted."
        
        if "segment" in message.lower():
            return f"The {field} segment could not be parsed. This may be due to incorrect delimiter usage or malformed segment structure."
        
        return message
    
    def _suggest_parsing_fix(self, error: Dict[str, Any]) -> str:
        """Suggest fixes for parsing errors"""
        field = error.get("field", "")
        message = error.get("message", "")
        
        if field == "MSH" and "must start with MSH" in message:
            return "Add MSH segment at the beginning of the message. Example: MSH|^~\\&|SENDING|FACILITY|RECEIVING|FACILITY|202301011200||ADT^A01|123456|P|2.5"
        
        if "encoding characters" in message.lower():
            return "Ensure MSH field 4 contains exactly 4 characters defining the field separator, component separator, subcomponent separator, and repetition separator. Default is ^~\\&"
        
        if "segment" in message.lower():
            return f"Check the {field} segment format. Ensure it uses the correct delimiters (| for fields, ^ for components) and has the required number of fields."
        
        return "Review the HL7 v2 standard format and ensure proper delimiter usage."
    
    def _explain_mapping_error(self, error: Dict[str, Any]) -> str:
        """Provide rule-based explanation for mapping errors"""
        field = error.get("field", "")
        message = error.get("message", "")
        
        if "unsupported message type" in message.lower():
            return f"The HL7 message type {field} is not currently supported. Supported types include ADT^A01 (admit), ORU^R01 (observation), and ORM^O01 (order)."
        
        if "missing required segment" in message.lower():
            return f"The message is missing a required segment. {field} segment is needed to create the corresponding FHIR resource."
        
        return message
    
    def _suggest_mapping_fix(self, error: Dict[str, Any]) -> str:
        """Suggest fixes for mapping errors"""
        field = error.get("field", "")
        message = error.get("message", "")
        
        if "unsupported message type" in message.lower():
            return "Use a supported message type (ADT^A01, ORU^R01, ORM^O01) or extend the mapper to support additional message types."
        
        if "missing required segment" in message.lower():
            return f"Add the {field} segment to the HL7 message with the required fields."
        
        return "Ensure the HL7 message contains all required segments for the message type."
    
    def _validate_fhir_bundle(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Basic validation of the FHIR Bundle"""
        errors = []
        
        if not bundle or bundle.get("resourceType") != "Bundle":
            errors.append({
                "type": "validation_error",
                "field": "Bundle",
                "message": "Invalid FHIR Bundle resource",
                "received": str(bundle.get("resourceType", "None")),
                "explanation": "The mapped resource is not a valid FHIR Bundle.",
                "suggested_fix": "Ensure the mapper creates a valid Bundle resource with resourceType: 'Bundle'.",
                "fix": None
            })
            return errors
        
        # Validate entries
        entries = bundle.get("entry", [])
        for i, entry in enumerate(entries):
            resource = entry.get("resource", {})
            if not resource.get("resourceType"):
                errors.append({
                    "type": "validation_error",
                    "field": f"Bundle.entry[{i}].resourceType",
                    "message": "Missing resourceType in Bundle entry",
                    "received": str(resource),
                    "explanation": "Each resource in the Bundle must have a resourceType field.",
                    "suggested_fix": "Ensure all resources have a valid resourceType (Patient, Encounter, Observation, etc.).",
                    "fix": None
                })
        
        return errors


def convert_hl7_to_fhir(hl7_message: str, explain_errors: bool = True) -> Dict[str, Any]:
    """Convenience function to convert HL7 to FHIR with error handling"""
    converter = HL7Converter()
    return converter.convert(hl7_message, explain_errors)
