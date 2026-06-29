import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import App from "../App";

// Mock fetch globally
global.fetch = jest.fn();

const mockPatientResponse = {
  mapping: {
    applied_rules: [
      { original_field: "PtID", mapped_to: "id", rule_type: "built_in" },
      { original_field: "Sex", mapped_to: "gender", rule_type: "built_in" }
    ],
    unmapped_fields: [],
    mapping_complete: true
  },
  validation: {
    original_valid: false,
    final_valid: true,
    errors: [
      {
        field: "gender",
        type: "rule_based",
        received: "M",
        fix: "male",
        message: "Invalid gender value 'M'.",
        explanation: "FHIR accepts only: male, female, other, unknown.",
        suggested_fix: "Change 'M' to 'male'"
      }
    ],
    warnings: []
  },
  quality: {
    grade: "A",
    score: 85,
    total_errors_found: 1,
    errors_auto_fixed: 1,
    remaining_errors: 0,
    warnings: 0
  },
  fixed_resource: {
    resourceType: "Patient",
    id: "P101",
    gender: "male"
  }
};

describe("MedTechTools Mapping UI", () => {

  beforeEach(() => {
    fetch.mockClear();
  });

  test("renders all 5 resource tabs", () => {
    render(<App />);
    expect(screen.getByText("Patient")).toBeInTheDocument();
    expect(screen.getByText("Observation")).toBeInTheDocument();
    expect(screen.getByText("Condition")).toBeInTheDocument();
    expect(screen.getByText("Encounter")).toBeInTheDocument();
    expect(screen.getByText("MedicationRequest")).toBeInTheDocument();
  });

  test("renders pipeline steps", () => {
    render(<App />);
    expect(screen.getByText("Map fields")).toBeInTheDocument();
    expect(screen.getByText("Validate")).toBeInTheDocument();
    expect(screen.getByText("Auto-fix")).toBeInTheDocument();
    expect(screen.getByText("Score")).toBeInTheDocument();
  });

  test("shows raw input textarea with sample data", () => {
    render(<App />);
    const textarea = document.querySelector("textarea");
    expect(textarea).toBeInTheDocument();
    expect(textarea.value).toContain("PtID");
  });

  test("shows validate button", () => {
    render(<App />);
    expect(screen.getByText(/Validate Patient/i)).toBeInTheDocument();
  });

  test("switches resource tabs correctly", () => {
    render(<App />);
    fireEvent.click(screen.getByText("Observation"));
    expect(screen.getByText(/Validate Observation/i)).toBeInTheDocument();
  });

  test("shows quality grade after validation", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPatientResponse
    });

    render(<App />);
    fireEvent.click(screen.getByText(/Validate Patient/i));

    await waitFor(() => {
      expect(screen.getByText("A")).toBeInTheDocument();
    });
  });

  test("shows error cards with AUTO-FIXED badge", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPatientResponse
    });

    render(<App />);
    fireEvent.click(screen.getByText(/Validate Patient/i));

    await waitFor(() => {
      expect(screen.getByText("AUTO-FIXED")).toBeInTheDocument();
    });
  });

  test("shows before and after fix values", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPatientResponse
    });

    render(<App />);
    fireEvent.click(screen.getByText(/Validate Patient/i));

    await waitFor(() => {
      expect(screen.getByText("M")).toBeInTheDocument();
      expect(screen.getByText("male")).toBeInTheDocument();
    });
  });

  test("shows stats — errors found and auto fixed", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPatientResponse
    });

    render(<App />);
    fireEvent.click(screen.getByText(/Validate Patient/i));

    await waitFor(() => {
      expect(screen.getByText("85%")).toBeInTheDocument();
    });
  });

  test("shows API connection info", () => {
    render(<App />);
    expect(screen.getByText("localhost:8000")).toBeInTheDocument();
  });

  test("textarea allows editing input", () => {
    render(<App />);
    const textarea = document.querySelector("textarea");
    fireEvent.change(textarea, {
      target: { value: '{"PtID": "P999"}' }
    });
    expect(textarea.value).toBe('{"PtID": "P999"}');
  });
});