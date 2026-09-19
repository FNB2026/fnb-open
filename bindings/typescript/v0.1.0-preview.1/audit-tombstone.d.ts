/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/audit-tombstone.schema.json
 * Source SHA-256: a3dea4e9d9c7c2ca31a41300adc25de016920cb7ef0df554751a2b0d34f37dd4
 * Regenerate with: python3 tools/generate-bindings.py
 */

/**
 * A data-minimized audit record that may replace an identifiable correction or deletion record when retention has a valid basis.
 * Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false.
 */
export interface AuditTombstone {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_audit_`. */
  audit_id: string;
  action: "redact" | "delete";
  target_type: "node" | "block_draft" | "block" | "memory" | "relationship" | "ai_inference" | "source";
  outcome: "completed" | "denied" | "failed";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: format `date`. */
  occurred_on: string;
  retention_basis: "statutory_obligation" | "active_security_incident" | "active_dispute";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: format `date`. */
  purge_after: string;
}
