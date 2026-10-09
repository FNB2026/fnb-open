/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/permission-snapshot.schema.json
 * Source SHA-256: 1db31d60b3c26b035c9c5882e653276d839ebb990cd7ae54895505eec1eea302
 * Regenerate with: python3 tools/generate-bindings.py
 */

/**
 * Portable permission facts captured when a source was used; this is not an authentication credential or ACL export.
 * Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false.
 */
export interface PermissionSnapshot {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_permsnap_`. */
  permission_snapshot_id: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `1`. */
  source_ref: string;
  subject_scope: "owner" | "participant" | "authorized_recipient";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minItems `1`; array items must be unique. */
  allowed_actions: "view" | "infer" | "train" | "export" | "share"[];
  visibility_scope: "private" | "shared" | "public";
  basis: "user_consent" | "delegated_authority" | "legal_obligation";
  /** Runtime JSON Schema constraint, not expressible in TypeScript: format `date-time`. */
  captured_at: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: format `date-time`. */
  expires_at?: string;
}
