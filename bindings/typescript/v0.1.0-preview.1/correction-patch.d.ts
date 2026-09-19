/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/correction-patch.schema.json
 * Source SHA-256: 3fc57c14a1b255cfa38b241fda8ea19134d7428862415eaf3866afccb5d53d60
 * Regenerate with: python3 tools/generate-bindings.py
 */

/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface CorrectionPatch {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_corr_`. */
  correction_id: string;
  actor_id: string;
  target_type: "node" | "block_draft" | "block" | "memory" | "relationship" | "ai_inference";
  target_id: string;
  operation: "confirm" | "reject" | "replace" | "redact";
  path?: string;
  before?: string | number | boolean | Record<string, unknown> | unknown[] | null;
  after?: string | number | boolean | Record<string, unknown> | unknown[] | null;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  reason: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: format `date-time`. */
  created_at: string;
}
