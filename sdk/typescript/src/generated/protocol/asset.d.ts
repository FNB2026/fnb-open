/**
 * GENERATED FILE — DO NOT EDIT.
 * FNB Protocol: v0.1.0-preview.1
 * Source: specs/v0.1/asset.schema.json
 * Source SHA-256: 93c8051452758384c9c470d1ee4a26070375aded08f2f94755edb6438988b23b
 * Regenerate with: python3 tools/generate-bindings.py
 */

/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface AssetVariant {
  variant_id: string;
  kind: "original" | "thumbnail" | "compressed" | "derived";
  content_hash?: string;
}
/** Runtime JSON Schema constraint, not expressible in TypeScript: additionalProperties is false. */
export interface Asset {
  /** Runtime JSON Schema constraint, not expressible in TypeScript: pattern `^fnb_asset_`. */
  asset_id: string;
  owner_id: string;
  media_type: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: minLength `16`. */
  content_hash: string;
  /** Runtime JSON Schema constraint, not expressible in TypeScript: format `date-time`. */
  created_at: string;
  variants?: AssetVariant[];
}
