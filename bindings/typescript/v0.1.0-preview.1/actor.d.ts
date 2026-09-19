/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/actor.schema.json
 * Source SHA-256: 55775a488ffc58d876e5ddc290eb20141b2cca08e9345d5f8ff8995e8aa3c2b7
 * Regenerate with: python3 tools/generate-bindings.py
 */

/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface Actor {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_actor_[A-Za-z0-9_-]+$`. */
  actor_id: string;
  kind: "person" | "agent" | "system";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  display_name: string;
  status?: "active" | "inactive" | "redacted";
}
