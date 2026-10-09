/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/node.schema.json
 * Source SHA-256: 5c750dd4d2d7a567e6f1be1d8e775d2ee54b2ed05c860102d1a7e2c40baca9c6
 * Regenerate with: python3 tools/generate-bindings.py
 */

/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface Node {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_node_`. */
  node_id: string;
  node_type: "message" | "person" | "event" | "evidence" | "memory" | "relation" | "device" | "ai_inference";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minItems `1`. */
  source_event_ids: string[];
  status: "candidate" | "confirmed" | "rejected";
  label?: string;
}
