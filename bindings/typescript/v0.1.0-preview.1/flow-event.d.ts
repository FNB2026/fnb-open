/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/flow-event.schema.json
 * Source SHA-256: 46dd93f1adb6452f7a33373d7807f2515a9a7c38926ffd1e3a2d803639352b74
 * Regenerate with: python3 tools/generate-bindings.py
 */

/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface FlowEvent {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_evt_`. */
  event_id: string;
  flow_id: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  event_type: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: format `date-time`. */
  occurred_at: string;
  actor_id: string;
  source_ref: string;
  content_preview?: string;
  permission_snapshot_id?: string;
}
