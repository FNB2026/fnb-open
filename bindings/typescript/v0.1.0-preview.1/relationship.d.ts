/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/relationship.schema.json
 * Source SHA-256: bf372f3dc3caa237061b25ba912cc18695696670251a8d67ad5c4fe5c4c6d6b1
 * Regenerate with: python3 tools/generate-bindings.py
 */

/**
 * Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false.
 * Conditional protocol requirements are expressed by the RelationshipAssertion union; this interface holds only the unconditional fields.
 */
export interface RelationshipAssertionBase {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_actor_`. */
  actor_id: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  relationship_kind: string;
  confirmation_state: "candidate" | "confirmed" | "rejected" | "contested";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: format `date-time`. */
  confirmed_at?: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_evt_`. */
  confirmation_event_id?: string;
  visibility_scope: "private" | "participants" | "shared" | "public";
}
export type RelationshipAssertion = RelationshipAssertionBase & (
  | {
      confirmation_state: "confirmed";
      confirmation_event_id: string;
      confirmed_at: string;
    }
  | { confirmation_state: "candidate" | "contested" | "rejected"; }
);
/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface RelationshipEvidence {
  evidence_id: string;
  source_type: "event" | "node" | "block" | "memory";
  source_id: string;
  stance: "supports" | "contests" | "context";
}
/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface Relationship {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_rel_`. */
  relationship_id: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minItems `2`; array items must be unique. */
  participant_ids: string[];
  lifecycle_state: "active" | "contested" | "redacted";
  /**
   * Participant-specific views; no assertion defines the relationship for every participant.
   * Runtime JSON Schema constraint, not expressible in TypeScript: minItems `1`.
   */
  assertions: RelationshipAssertion[];
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minItems `1`. */
  evidence: RelationshipEvidence[];
}
