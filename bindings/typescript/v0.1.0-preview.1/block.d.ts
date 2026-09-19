/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/block.schema.json
 * Source SHA-256: f90b4877b5975341cea3eac12e4e17bc6936e565dfb656f542b7bec90fdeef2f
 * Regenerate with: python3 tools/generate-bindings.py
 */

/**
 * Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false.
 * Conditional protocol requirements are expressed by the Block union; this interface holds only the unconditional fields.
 */
export interface BlockBase {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_block_`. */
  block_id: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_actor_`. */
  owner_id: string;
  block_type: "memory" | "relation" | "knowledge" | "task" | "asset" | "credit";
  creation_mode: "manual" | "imported" | "ai_derived";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minItems `1`. */
  source_node_ids: string[];
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_draft_`. */
  draft_id?: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_corr_`. */
  correction_id?: string;
  title?: string;
  summary?: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_actor_`. */
  confirmed_by_actor_id: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_evt_`. */
  confirmation_event_id: string;
  confirmation_operation: "confirm" | "rewrite" | "accept_import";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: format `date-time`. */
  confirmed_at: string;
}
export type Block = BlockBase & (
  | {
      confirmation_operation: "rewrite";
      creation_mode: "ai_derived";
      correction_id: string;
      draft_id: string;
    }
  | {
      confirmation_operation: "rewrite";
      creation_mode: "imported" | "manual";
      correction_id: string;
    }
  | {
      confirmation_operation: "confirm";
      creation_mode: "ai_derived";
      draft_id: string;
    }
  | {
      confirmation_operation: "accept_import" | "confirm";
      creation_mode: "imported" | "manual";
    }
);
