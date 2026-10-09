/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/block-draft.schema.json
 * Source SHA-256: 2fe16e4c37fdaf8e30f057bf4845cb7b083f18ff9bea0a631721b9152eed77b0
 * Regenerate with: python3 tools/generate-bindings.py
 */

/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface BlockDraft {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_draft_`. */
  draft_id: string;
  owner_id: string;
  block_type: "memory" | "relation" | "knowledge" | "task" | "asset" | "credit";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minItems `1`. */
  source_node_ids: string[];
  inference_id: string;
  proposed_title?: string;
  proposed_summary?: string;
  status: "pending" | "confirmed" | "rejected" | "rewritten";
}
