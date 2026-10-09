/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/ai-inference.schema.json
 * Source SHA-256: d531deb174976fbcae6800d4104028cb442fb88f62f09dc055c56a31b53b1365
 * Regenerate with: python3 tools/generate-bindings.py
 */

/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface AIInferenceModel {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  provider: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  name: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  version: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `8`. */
  configuration_fingerprint: string;
}
/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface AIInferenceExplanation {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_exp_`. */
  explanation_id: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  rationale: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minItems `1`; array items must be unique. */
  evidence_refs: string[];
  limitations?: string[];
}
/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface AIInference {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_inf_`. */
  inference_id: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  purpose: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
  model: AIInferenceModel;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minItems `1`; array items must be unique. */
  input_refs: string[];
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  output_summary: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: maximum `1`; minimum `0`. */
  confidence: number;
  inference_status: "completed" | "superseded";
  confirmation_status: "candidate" | "confirmed" | "rejected";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
  explanation: AIInferenceExplanation;
}
