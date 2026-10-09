/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/source-state-change.schema.json
 * Source SHA-256: 13b7d6af687eb3d4dd9fddb449e0cc957762e6d45f7f4351c228e5f548a6dba7
 * Regenerate with: python3 tools/generate-bindings.py
 */

/**
 * A portable record that a source's usability or permission state changed. It contains no source content or authorization credential.
 * Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false.
 * Conditional protocol requirements are expressed by the SourceStateChange union; this interface holds only the unconditional fields.
 */
export interface SourceStateChangeBase {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_srcchg_`. */
  source_change_id: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  source_ref: string;
  previous_state: "active" | "stale" | "redacted" | "deleted" | "permission_withdrawn";
  new_state: "active" | "stale" | "redacted" | "deleted" | "permission_withdrawn";
  reason_code: "source_redacted" | "source_deleted" | "source_stale" | "permission_withdrawn" | "source_restored" | "permission_restored";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: format `date-time`. */
  effective_at: string;
}
export type SourceStateChange = SourceStateChangeBase & (
  | {
      new_state: "permission_withdrawn";
      reason_code: "permission_withdrawn";
    }
  | {
      new_state: "deleted";
      reason_code: "source_deleted";
    }
  | {
      new_state: "redacted";
      reason_code: "source_redacted";
    }
  | {
      new_state: "active";
      reason_code: "source_restored" | "permission_restored";
    }
  | {
      new_state: "stale";
      reason_code: "source_stale";
    }
);
