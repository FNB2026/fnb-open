/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/invalidation-record.schema.json
 * Source SHA-256: bc71b84d31763e26d4553f0cf62755840634394a7e855c1f152764e735e8a786
 * Regenerate with: python3 tools/generate-bindings.py
 */

/**
 * An append-only record that propagates a correction, source change, permission change, or upstream invalidation to one derived object.
 * Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false.
 * Conditional protocol requirements are expressed by the InvalidationRecord union; this interface holds only the unconditional fields.
 */
export interface InvalidationRecordBase {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_inv_`. */
  invalidation_id: string;
  trigger_type: "correction_patch" | "source_change" | "permission_change" | "parent_invalidation";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  trigger_id: string;
  /**
   * Trace reference for a parent invalidation. This identifier is not used when computing the idempotency key.
   * Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_inv_`.
   */
  parent_invalidation_id?: string;
  target_type: "node" | "block_draft" | "block" | "memory" | "relationship" | "ai_inference";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  target_id: string;
  resulting_state: "invalidated" | "review_required";
  reason_code: "correction_rejected" | "correction_replaced" | "correction_redacted" | "source_redacted" | "source_deleted" | "source_stale" | "permission_withdrawn" | "upstream_invalidated";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^sha256:[0-9a-f]{64}$`. */
  idempotency_key: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  actor_id?: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: format `date-time`. */
  created_at: string;
}
export type InvalidationRecord = InvalidationRecordBase & (
  | {
      trigger_type: "parent_invalidation";
      /** pattern `^fnb_inv_` */
      parent_invalidation_id: string;
      reason_code: "upstream_invalidated";
      /** pattern `^sha256:[0-9a-f]{64}$` */
      trigger_id: string;
    }
  | {
      trigger_type: "correction_patch";
      reason_code: "correction_rejected" | "correction_replaced" | "correction_redacted";
    }
  | {
      trigger_type: "permission_change";
      reason_code: "permission_withdrawn";
    }
  | {
      trigger_type: "source_change";
      reason_code: "source_redacted" | "source_deleted" | "source_stale";
    }
);
