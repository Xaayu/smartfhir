# Complex FHIR Resource Edge Cases

This document lists edge cases when processing already-complex FHIR resources (not raw/mapped data).

## 1. Nested Array Structures

### Multiple Identifiers with Coding
```json
"identifier": [
  {
    "use": "usual",
    "type": {
      "coding": [{"system": "http://...", "code": "MR"}]
    },
    "system": "http://hospital.org/mrn",
    "value": "MRN123"
  }
]
```
**Edge case:** Missing nested `coding` array, or `type` as string instead of object

### Multiple Names with Different Uses
```json
"name": [
  {"use": "official", "family": "Doe", "given": ["John"]},
  {"use": "nickname", "given": ["Johnny"]}
]
```
**Edge case:** Missing `family` in nickname (valid in FHIR), empty `given` array

### Multiple Addresses
```json
"address": [
  {"use": "home", "line": ["123 Main"], "city": "Springfield"},
  {"use": "work", "line": ["456 Office"], "city": "Chicago"}
]
```
**Edge case:** `line` as string instead of array, missing required fields

## 2. CodeableConcept Fields

### MaritalStatus as Object vs String
```json
// Valid FHIR object
"maritalStatus": {
  "coding": [{"system": "http://...", "code": "S"}]
}

// Edge case: String (mapper input)
"maritalStatus": "single"
```
**Edge case:** Mixed types, missing `coding` array, invalid system URLs

### Communication Language Coding
```json
"communication": [
  {
    "language": {
      "coding": [{"system": "urn:ietf:bcp:47", "code": "en-IN"}]
    },
    "preferred": true
  }
]
```
**Edge case:** Invalid BCP 47 codes, `preferred` as string "true" instead of boolean

## 3. Reference Fields

### Reference Format Variations
```json
// Reference as string
"generalPractitioner": "Practitioner/prac-001"

// Reference as object
"generalPractitioner": {
  "reference": "Practitioner/prac-001",
  "display": "Dr. Smith"
}

// Edge case: Missing resource type
"generalPractitioner": "prac-001"
```
**Edge case:** Invalid reference format, non-existent referenced resources

### Managing Organization
```json
"managingOrganization": {
  "reference": "Organization/org-001",
  "display": "City Hospital"
}
```
**Edge case:** Reference to non-Organization resource type

## 4. Extension Arrays

### Custom Extensions
```json
"extension": [
  {
    "url": "http://example.org/fhir/StructureDefinition/patient-blood-group",
    "valueString": "O+"
  },
  {
    "url": "http://example.org/fhir/StructureDefinition/patient-nationality",
    "valueCodeableConcept": {"text": "Indian"}
  }
]
```
**Edge case:** Invalid extension URLs, missing value fields, wrong value type

## 5. Contact Arrays

### Contact with Nested Structures
```json
"contact": [
  {
    "relationship": [
      {"coding": [{"system": "http://...", "code": "N"}]}
    ],
    "name": {"family": "Doe", "given": ["Jane"]},
    "telecom": [{"system": "phone", "value": "+1-555-0123"}],
    "address": {"line": ["123 Main"], "city": "Springfield"},
    "gender": "female"
  }
]
```
**Edge case:** Missing required fields, invalid gender in contact

## 6. Photo Arrays

### Photo with URL vs Data
```json
"photo": [
  {
    "contentType": "image/jpeg",
    "url": "https://example.org/photo.jpg"
  },
  {
    "contentType": "image/png",
    "data": "base64encodedstring"
  }
]
```
**Edge case:** Invalid base64 data, non-existent URLs, invalid content types

## 7. Telecom Arrays

### Telecom with Rank and Use
```json
"telecom": [
  {
   "use": "mobile",
    "system": "phone",
    "value": "+91-9876543210",
    "rank": 1
  }
]
```
**Edge case:** Invalid phone number formats, negative rank, invalid use values

## 8. Choice Fields (Mutually Exclusive)

### DeceasedBoolean vs DeceasedDateTime
```json
// Valid: only one
"deceasedBoolean": false

// Valid: only one
"deceasedDateTime": "2020-01-01T00:00:00Z"

// Edge case: Both present (invalid in FHIR)
"deceasedBoolean": false,
"deceasedDateTime": "2020-01-01T00:00:00Z"
```

### MultipleBirthBoolean vs MultipleBirthInteger
```json
// Edge case: Both present
"multipleBirthBoolean": true,
"multipleBirthInteger": 2
```

## 9. Meta Fields

### Meta with VersionId and LastUpdated
```json
"meta": {
  "versionId": "1",
  "lastUpdated": "2026-06-30T10:30:00Z"
}
```
**Edge case:** `versionId` as number instead of string, invalid datetime format, missing timezone

## 10. Empty/Null Handling

### Empty Arrays vs Missing Fields
```json
// Valid: empty array
"identifier": []

// Edge case: null value
"identifier": null

// Edge case: array with null elements
"identifier": [null, {"system": "...", "value": "..."}]
```

### Empty Strings in Arrays
```json
"name": [
  {"use": "official", "family": "", "given": ["John"]}
]
```
**Edge case:** Empty family name (may be valid for some cultures)

## 11. Coding System URLs

### Invalid or Non-existent Systems
```json
"maritalStatus": {
  "coding": [
    {
      "system": "http://invalid-url-that-does-not-exist.org",
      "code": "S"
    }
  ]
}
```
**Edge case:** Malformed URLs, non-standard systems

## 12. Partial Dates

### BirthDate with Partial Information
```json
// Valid: year only
"birthDate": "2005"

// Valid: year-month
"birthDate": "2005-01"

// Edge case: invalid partial
"birthDate": "2005-01-32"
```

## 13. Time Zone Handling

### DateTime with Timezones
```json
"meta": {
  "lastUpdated": "2026-06-30T10:30:00+05:30"
}
```
**Edge case:** Missing timezone, invalid timezone offsets

## 14. Duplicate Identifiers

### Same System, Different Values
```json
"identifier": [
  {"system": "http://hospital.org/mrn", "value": "MRN123"},
  {"system": "http://hospital.org/mrn", "value": "MRN456"}
]
```
**Edge case:** Duplicate identifiers (same system and value)

## 15. Resource Type Mismatch

### Wrong Resource Type in Field
```json
"resourceType": "Patient",
"generalPractitioner": {
  "reference": "Patient/patient-001"  // Should be Practitioner
}
```

## 16. Array Size Limits

### Large Arrays
```json
"identifier": [/* 100+ identifiers */]
"name": [/* 50+ names */]
```
**Edge case:** Performance issues with very large arrays

## 17. Unicode and Special Characters

### Names with Unicode
```json
"name": [{"family": "Müller", "given": ["José"]}]
```
**Edge case:** Unicode normalization issues, encoding problems

## 18. Nested References

### Deeply Nested References
```json
"contact": [
  {
    "organization": {
      "reference": "Organization/org-001",
      "display": "Hospital"
    }
  }
]
```
**Edge case:** Circular references, deeply nested structures

## 19. Conditional Required Fields

### Address Conditional Fields
```json
"address": [
  {
    "use": "home",
    // Missing line but has city - may be valid depending on context
    "city": "Springfield"
  }
]
```

## 20. Period Objects

### Valid Periods
```json
"identifier": [
  {
    "period": {
      "start": "2020-01-01",
      "end": "2025-01-01"
    }
  }
]
```
**Edge case:** End before start, invalid date formats, missing start/end
