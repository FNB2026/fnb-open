/**
 * Protocol type expectations for the generated FNB bindings.
 *
 * This file is a validation fixture, NOT a protocol artifact. It is not
 * generated, and it is not part of the binding surface a third party imports.
 *
 * Each `@ts-expect-error` directive asserts that the combination below it does
 * NOT type-check. TypeScript reports an unused directive as an error, so these
 * assertions hold in both directions: if a generated union ever becomes wider
 * than the frozen schema, this file fails the `tsc --noEmit` gate.
 */

import type { Block } from "./v0.1.0-preview.1/block";
import type { InvalidationRecord } from "./v0.1.0-preview.1/invalidation-record";
import type { RelationshipAssertion } from "./v0.1.0-preview.1/relationship";
import type { SourceStateChange } from "./v0.1.0-preview.1/source-state-change";

const sourceChangeBase = {
  source_change_id: "fnb_srcchg_1",
  source_ref: "source_1",
  previous_state: "active" as const,
  effective_at: "2026-09-19T00:00:00Z",
};

// A redacted source must carry the redaction reason.
const validRedaction: SourceStateChange = {
  ...sourceChangeBase,
  new_state: "redacted",
  reason_code: "source_redacted",
};

// A restored source is the only state that accepts the two restore reasons.
const validRestoration: SourceStateChange = {
  ...sourceChangeBase,
  new_state: "active",
  reason_code: "permission_restored",
};

// @ts-expect-error deleted cannot carry "source_restored"
const deletedWithRestoreReason: SourceStateChange = { ...sourceChangeBase, new_state: "deleted", reason_code: "source_restored" };

// @ts-expect-error active cannot carry "source_redacted"
const activeWithRedactionReason: SourceStateChange = { ...sourceChangeBase, new_state: "active", reason_code: "source_redacted" };

const blockBase = {
  block_id: "fnb_block_1",
  owner_id: "fnb_actor_1",
  block_type: "memory" as const,
  source_node_ids: ["node_1"],
  confirmed_by_actor_id: "fnb_actor_1",
  confirmation_event_id: "fnb_evt_1",
  confirmed_at: "2026-09-19T00:00:00Z",
};

// An AI-derived block keeps its draft and can be confirmed or rewritten.
const aiDerivedBlock: Block = {
  ...blockBase,
  creation_mode: "ai_derived",
  draft_id: "fnb_draft_1",
  confirmation_operation: "confirm",
};

// A manual rewrite must retain the correction it applied.
const manualRewriteBlock: Block = {
  ...blockBase,
  creation_mode: "manual",
  confirmation_operation: "rewrite",
  correction_id: "fnb_corr_1",
};

// @ts-expect-error ai_derived blocks are never accepted as imports
const aiDerivedImport: Block = { ...blockBase, creation_mode: "ai_derived", draft_id: "fnb_draft_1", confirmation_operation: "accept_import" };

// @ts-expect-error ai_derived blocks without a draft_id are invalid
const aiDerivedWithoutDraft: Block = { ...blockBase, creation_mode: "ai_derived", confirmation_operation: "confirm" };

// @ts-expect-error a rewrite without a correction_id is invalid
const rewriteWithoutCorrection: Block = { ...blockBase, creation_mode: "manual", confirmation_operation: "rewrite" };

const invalidationBase = {
  invalidation_id: "fnb_inv_1",
  trigger_id: "trigger_1",
  target_type: "memory" as const,
  target_id: "memory_1",
  resulting_state: "invalidated" as const,
  idempotency_key: "sha256:" + "0".repeat(64),
  created_at: "2026-09-19T00:00:00Z",
};

const sourceChangeInvalidation: InvalidationRecord = {
  ...invalidationBase,
  trigger_type: "source_change",
  reason_code: "source_deleted",
};

// Transitive invalidation keeps its parent reference.
const parentInvalidation: InvalidationRecord = {
  ...invalidationBase,
  trigger_type: "parent_invalidation",
  parent_invalidation_id: "fnb_inv_0",
  reason_code: "upstream_invalidated",
};

// @ts-expect-error a correction trigger cannot produce "upstream_invalidated"
const correctionWithUpstreamReason: InvalidationRecord = { ...invalidationBase, trigger_type: "correction_patch", reason_code: "upstream_invalidated" };

// @ts-expect-error a permission trigger cannot produce "source_deleted"
const permissionWithSourceReason: InvalidationRecord = { ...invalidationBase, trigger_type: "permission_change", reason_code: "source_deleted" };

// @ts-expect-error parent_invalidation requires parent_invalidation_id
const parentInvalidationWithoutParent: InvalidationRecord = { ...invalidationBase, trigger_type: "parent_invalidation", reason_code: "upstream_invalidated" };

const assertionBase = {
  actor_id: "fnb_actor_1",
  relationship_kind: "colleague",
  visibility_scope: "participants" as const,
};

// A confirmed assertion records when and by which event it was confirmed.
const confirmedAssertion: RelationshipAssertion = {
  ...assertionBase,
  confirmation_state: "confirmed",
  confirmed_at: "2026-09-19T00:00:00Z",
  confirmation_event_id: "fnb_evt_1",
};

// A contested assertion carries no confirmation evidence.
const contestedAssertion: RelationshipAssertion = {
  ...assertionBase,
  confirmation_state: "contested",
};

// @ts-expect-error a confirmed assertion requires confirmed_at and confirmation_event_id
const confirmedWithoutEvidence: RelationshipAssertion = { ...assertionBase, confirmation_state: "confirmed" };

export const protocolTypeExpectations = [
  validRedaction,
  validRestoration,
  aiDerivedBlock,
  manualRewriteBlock,
  sourceChangeInvalidation,
  parentInvalidation,
  confirmedAssertion,
  contestedAssertion,
  deletedWithRestoreReason,
  activeWithRedactionReason,
  aiDerivedImport,
  aiDerivedWithoutDraft,
  rewriteWithoutCorrection,
  correctionWithUpstreamReason,
  permissionWithSourceReason,
  parentInvalidationWithoutParent,
  confirmedWithoutEvidence,
];
