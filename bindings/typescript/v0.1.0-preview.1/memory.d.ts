/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/memory.schema.json
 * Source SHA-256: 940e9a3347f370d83cdf554ebe86582b31c463e37ad18eafcdb97fbed68a9b32
 * Regenerate with: python3 tools/generate-bindings.py
 */

/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface MemorySource {
  source_id: string;
  object_type: "asset" | "event" | "node" | "block" | "message";
  object_id: string;
  content_hash?: string;
}
/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface Memory {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_mem_`. */
  memory_id: string;
  owner_id: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  title: string;
  summary?: string;
  /** User-governed confirmation state. */
  status: "candidate" | "confirmed" | "rejected";
  /** Retention and visibility lifecycle, independent of confirmation. */
  lifecycle_state: "active" | "archived" | "redacted" | "deleted";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: maximum `1`; minimum `0`. */
  confidence?: number;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minItems `1`. */
  sources: MemorySource[];
}
