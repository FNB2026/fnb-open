# RFC-0005: Reference Type Ontology

## Status

Draft — **not accepted**. Submitted for the minimum seven-day public comment
window required by [RFC-0000](./0000-rfc-process.md). This document proposes a
model; it does not decide one. It adds no schema, changes no enum, and modifies
no frozen artifact. Any implementation of this model requires a **new protocol
release**, not an edit to `v0.1.0-preview.1`.

## Summary

The public protocol has several role-specific reference vocabularies and several
reference fields that belong to no declared vocabulary at all. The protocol has
never stated whether these vocabularies are subsets of one global object-type
list or independent role-specific admissibility lists, nor what namespace,
identity form, or resolution behaviour each reference field carries.

This RFC names that missing layer the **Reference Type Ontology**, fixes the
vocabularies it must describe, declares the five properties every reference field
must state, and answers the concrete modelling questions that the next protocol
release needs before any reference check (`Gate 3a`/`3b`/`3c`) can be enabled.

The single most important finding: **the vocabularies are not wrong because they
differ. They are under-specified because their members are not bound to identity
namespaces or resolution policies.** The correct fix is a role declaration per
reference field, not a single merged enum.

## Motivation

A reference is not just a string. A consumer reading
`"target_type": "memory"` and `"target_id": "..."` needs to know whether the
identifier is a protocol-object identifier, an opaque external token, or a
namespace that has no object schema. The v0.1 preview does not say.

Three concrete failures follow from the gap, all observable in the frozen
schemas:

1. **Unbound type names.** `memory.sources[].object_type` admits `message`, but
   no `message` object exists in the 14 frozen schemas and no `fnb_message_*`
   namespace is declared anywhere.
2. **Undeclared namespaces.** `flow-event.flow_id` is a **required** field with
   no pattern and no corresponding object; `memory.sources[].source_id` carries a
   fixture value in an `fnb_source_` namespace that appears in no schema.
3. **Unstated resolution behaviour.** `permission-snapshot.source_ref`,
   `source-state-change.source_ref`, and `flow-event.source_ref` are unconstrained
   by design, yet nothing in the protocol says they are *allowed* to be
   unresolvable. A naive consumer that treats every reference as an
   internal-object pointer would reject valid objects.

Without a reference type ontology, any reference check is forced to choose
between being too loose (it checks nothing) and being wrong (it fails valid
opaque references, or retro-tightens the frozen acceptance set).

## Design

### 1. Scope and non-goals

In scope:

- the set of object types the public protocol defines;
- the role-specific reference vocabularies already present in the frozen schemas;
- five properties every reference field must state;
- the mapping from each reference class to reference-resolution check states.

Explicitly out of scope, and not decided or implied by this RFC:

- modifying `specs/v0.1/` or the immutable `v0.1.0-preview.1` tag;
- tightening any existing fixture or the frozen acceptance set;
- replication, federation, convergence, or scope snapshots;
- an Apply Ledger, cursor, or exchange transport;
- any product code, private API, storage, worker, or authentication behaviour;
- adding a Flow, Message, or Source object schema.

### 2. Evidence base

Every statement below is derived from the frozen schemas; this section is the
forensic record so that the model can be re-checked from Git alone. Patterns are
quoted as they appear in the schemas under `specs/v0.1/`.

**Protocol object identity namespaces (14 frozen schemas).**

| Object | Identity field | Pattern |
| --- | --- | --- |
| Actor | `actor_id` | `^fnb_actor_[A-Za-z0-9_-]+$` |
| Asset | `asset_id` | `^fnb_asset_` |
| Memory | `memory_id` | `^fnb_mem_` |
| FlowEvent | `event_id` | `^fnb_evt_` |
| Node | `node_id` | `^fnb_node_` |
| BlockDraft | `draft_id` | `^fnb_draft_` |
| Block | `block_id` | `^fnb_block_` |
| Relationship | `relationship_id` | `^fnb_rel_` |
| AIInference | `inference_id` | `^fnb_inf_` |
| CorrectionPatch | `correction_id` | `^fnb_corr_` |
| PermissionSnapshot | `permission_snapshot_id` | `^fnb_permsnap_` |
| SourceStateChange | `source_change_id` | `^fnb_srcchg_` |
| InvalidationRecord | `invalidation_id` | `^fnb_inv_` |
| AuditTombstone | `audit_id` | `^fnb_audit_` |

Embedded objects also carry identities: `ai-inference.explanation.explanation_id`
= `^fnb_exp_`; `asset.variants[].variant_id` and
`relationship.evidence[].evidence_id` are `type=string` with no pattern and are
scoped to their parent. They are not independently addressable.

**Every referencing field, with its current constraint.** A "discriminator" is a
sibling enum field that names the target's type.

| # | Schema | Field | Discriminator | Current constraint | Class |
| --- | --- | --- | --- | --- | --- |
| 1 | memory | `owner_id` | — | `type=string` | fixed-type (unconstrained) |
| 2 | memory | `sources[].source_id` | — | `type=string` | opaque / undeclared namespace |
| 3 | memory | `sources[].object_id` | `object_type` (5) | `type=string` | typed internal |
| 4 | memory | `sources[].content_hash` | — | `type=string` | digest |
| 5 | asset | `owner_id` | — | `type=string` | fixed-type (unconstrained) |
| 6 | asset | `content_hash`, `variants[].content_hash` | — | `minLength=16` | digest |
| 7 | flow-event | `flow_id` | — | `type=string`, **required** | undeclared namespace (grouping) |
| 8 | flow-event | `actor_id` | — | `type=string` | fixed-type (unconstrained) |
| 9 | flow-event | `source_ref` | — | `type=string` | opaque |
| 10 | flow-event | `permission_snapshot_id` | — | `type=string` | fixed-type (unconstrained) |
| 11 | node | `source_event_ids[]` | — | items `type=string` | fixed-type array (unconstrained) |
| 12 | block-draft | `owner_id` | — | `type=string` | fixed-type (unconstrained) |
| 13 | block-draft | `source_node_ids[]` | — | items `type=string` | fixed-type array (unconstrained) |
| 14 | block-draft | `inference_id` | — | `type=string` | fixed-type (unconstrained) |
| 15 | block | `owner_id` | — | `^fnb_actor_` | fixed-type |
| 16 | block | `source_node_ids[]` | — | items `type=string` | fixed-type array (unconstrained) |
| 17 | block | `draft_id` | — | `^fnb_draft_` | fixed-type |
| 18 | block | `correction_id` | — | `^fnb_corr_` | fixed-type |
| 19 | block | `confirmed_by_actor_id` | — | `^fnb_actor_` | fixed-type |
| 20 | block | `confirmation_event_id` | — | `^fnb_evt_` | fixed-type |
| 21 | relationship | `participant_ids[]` | — | items `^fnb_actor_` | fixed-type array |
| 22 | relationship | `assertions[].actor_id` | — | `^fnb_actor_` | fixed-type |
| 23 | relationship | `assertions[].confirmation_event_id` | — | `^fnb_evt_` | fixed-type |
| 24 | relationship | `evidence[].source_id` | `source_type` (4) | `type=string` | typed internal |
| 25 | ai-inference | `input_refs[]` | — | items `type=string` | polymorphic |
| 26 | ai-inference | `explanation.evidence_refs[]` | — | items `type=string` | polymorphic |
| 27 | correction-patch | `actor_id` | — | `type=string` | fixed-type (unconstrained) |
| 28 | correction-patch | `target_id` | `target_type` (6) | `type=string` | typed internal |
| 29 | invalidation-record | `trigger_id` | `trigger_type` (4) | `minLength=1` | typed internal (trigger class) |
| 30 | invalidation-record | `parent_invalidation_id` | — | `^fnb_inv_` | fixed-type |
| 31 | invalidation-record | `target_id` | `target_type` (6) | `minLength=1` | typed internal |
| 32 | invalidation-record | `actor_id` | — | `minLength=1` | fixed-type (unconstrained) |
| 33 | invalidation-record | `idempotency_key` | — | `sha256:[0-9a-f]{64}` | digest token |
| 34 | permission-snapshot | `source_ref` | — | `minLength=1` | opaque |
| 35 | source-state-change | `source_ref` | — | `minLength=1` | opaque |
| 36 | audit-tombstone | `target_type` | — | enum (7), **no target id** | vocabulary without an identifier |

Two structural facts recorded here because later sections depend on them:

- `relationship.participant_ids[]` items **do** carry a pattern, so arrays are
  fully capable of carrying reference constraints. The missing patterns on
  `source_node_ids[]`, `source_event_ids[]`, and `input_refs[]` are omissions,
  not schema limitations.
- `actor.actor_id` uses the stricter `^fnb_actor_[A-Za-z0-9_-]+$` while every
  reference to an actor uses the looser `^fnb_actor_`. Same semantic field,
  different validation strength.

### 3. The vocabularies

Five reference vocabularies are present in the frozen schemas, plus two
vocabularies that are **not** reference vocabularies and must not be conflated
with them.

| # | Vocabulary | Field | Members | Question it answers |
| --- | --- | --- | --- | --- |
| V1 | CorrectableType | `correction-patch.target_type` | node, block_draft, block, memory, relationship, ai_inference | what may be directly corrected |
| V2 | InvalidatableType | `invalidation-record.target_type` | node, block_draft, block, memory, relationship, ai_inference | what may be invalidated (identical to V1) |
| V3 | AuditTargetType | `audit-tombstone.target_type` | node, block_draft, block, memory, relationship, ai_inference, **source** | what may be retained as an audit trace |
| V4 | MemorySourceType | `memory.sources[].object_type` | asset, event, node, block, **message** | what may be Memory source material |
| V5 | EvidenceSourceType | `relationship.evidence[].source_type` | event, node, block, memory | what may be Relationship evidence |

On a different axis entirely:

| Vocabulary | Field | Members | Meaning |
| --- | --- | --- | --- |
| TriggerCategory | `invalidation-record.trigger_type` | correction_patch, source_change, permission_change, parent_invalidation | the *class of event* that triggered invalidation |
| NodeType | `node.node_type` | message, person, event, evidence, memory, relation, device, ai_inference | a **node classification**, not a reference target |

`TriggerCategory` and `NodeType` are listed to prevent a recurring category
error: their members are not object types and do not imply the existence of
object schemas. `NodeType` overlapping on the strings `message`, `event`, and
`memory` does not make it a reference vocabulary.

Two naming hazards are recorded here as findings, not resolved here:

- **Aliasing.** `MemorySourceType` and `EvidenceSourceType` use the member name
  `event`, but the object that carries an event identity is the **FlowEvent**
  schema (`fnb_evt_`). There is no object whose type name is `event`. Likewise
  `block_draft` names the **BlockDraft** schema.
- **Overloading.** `message` appears both as a MemorySourceType member (an object
  type) and as a `node_type` member (a node classification). The two meanings
  must never be assumed equal.

### 4. Subset relations

```text
ProtocolObjectType   = the 14 frozen protocol objects, each with one identity namespace

CorrectableType       subset of ProtocolObjectType       (6/6)
InvalidatableType     subset of ProtocolObjectType       (6/6, equal to CorrectableType)
EvidenceSourceType    subset of ProtocolObjectType       (4/4, under event -> FlowEvent aliasing)
AuditTargetType       NOT a subset                        (6/7; source is not a ProtocolObjectType)
MemorySourceType      subset of ProtocolObjectType       (5/5; message is an unbound protocol object type)
TriggerCategory       NOT on this axis
```

The correct reading is therefore **not** "one global enum with five subsets". It
is:

```text
ProtocolObjectType     the global object-type set

CorrectableType        subset of ProtocolObjectType                    role-specific, closed
InvalidatableType      subset of ProtocolObjectType                    role-specific, closed
EvidenceSourceType     subset of ProtocolObjectType                    role-specific, closed
AuditTargetType        = CorrectableType union ExternalSourceType      role-specific, open at one member
MemorySourceType       subset of ProtocolObjectType                    role-specific, closed (message unbound)
```

The same model, expressed as the four identity categories the protocol must never
collapse into one bucket:

```text
ProtocolObjectType
├── currently bound protocol objects   (the 14 frozen objects)
└── message                            (unbound; intended future protocol object)

ExternalSourceType
└── source                             (genuinely opaque / external)

GroupingNamespace
└── flow_id                            (protocol-owned namespace; not an object)

TriggerCategory
└── permission_change                  (event / category axis; not object identity)
```

`ExternalSourceType` is a **role**, not an object type. It has exactly one known
member today, `source`, and it exists to say "this reference is deliberately not
an internal object". Keeping the four categories distinct is the point: an
unbound future object (`message`), a genuinely opaque external reference
(`source`), a protocol-owned non-object namespace (`flow_id`), and a trigger
category (`permission_change`) must not be merged into a single "has no schema"
bucket, because they carry different identity, resolution, and future-proofing
consequences.

### 5. The five properties every reference field must state

| # | Property | Values |
| --- | --- | --- |
| 1 | **role** | what the reference means: correction_target, invalidation_target, audit_target, memory_source, evidence_source, source, flow_grouping, trigger, provenance, polymorphic_input |
| 2 | **discriminator vocabulary** | the sibling enum that types the target, or `none` |
| 3 | **namespace** | protocol-object · protocol-owned-grouping · external-or-opaque · sub-object · digest |
| 4 | **expected identity form** | a pattern, a type-specific form, or `unrestricted` |
| 5 | **resolution policy** | MUST-RESOLVE · MAY-RESOLVE · OPAQUE-ALLOWED · FORMAT-ONLY |

**Role is not optional.** Without a declared role there is no way to decide
whether a reference should be checked for type compatibility at all — and
running a type-compatibility check on an opaque reference produces a false
invalid verdict.

### 6. Per-class declaration

**Class A — typed internal (discriminated, protocol-object target).**

| Field | role | discriminator | namespace | identity form | resolution |
| --- | --- | --- | --- | --- | --- |
| `correction-patch.target_id` | correction_target | `target_type` | protocol-object | target-type-specific | MUST-RESOLVE |
| `invalidation-record.target_id` | invalidation_target | `target_type` | protocol-object | target-type-specific | MUST-RESOLVE |
| `relationship.evidence[].source_id` | evidence_source | `source_type` | protocol-object | target-type-specific | MAY-RESOLVE |
| `memory.sources[].object_id` | memory_source | `object_type` | protocol-object **except** `message` | target-type-specific **except** `message` | MAY-RESOLVE |
| `invalidation-record.trigger_id` | trigger | `trigger_type` | protocol-object (per trigger class) | trigger-class-specific | MUST-RESOLVE |

**Class B — fixed-type (patterned, no discriminator).** `block.owner_id`,
`block.confirmed_by_actor_id`, `block.draft_id`, `block.correction_id`,
`block.confirmation_event_id`, `invalidation-record.parent_invalidation_id`,
`relationship.participant_ids[]`, `relationship.assertions[].actor_id`,
`relationship.assertions[].confirmation_event_id`.
role = fixed referent · discriminator = none · namespace = protocol-object ·
identity form = the pattern itself · resolution = MUST-RESOLVE or MAY-RESOLVE
per field.

**Class C — fixed-type with the pattern omitted.** The same referents as Class B
but currently unconstrained: `memory.owner_id`, `asset.owner_id`,
`correction-patch.actor_id`, `invalidation-record.actor_id`, `flow-event.actor_id`,
`flow-event.permission_snapshot_id`, `block-draft.owner_id`,
`block-draft.inference_id`, `node.source_event_ids[]`, `block.source_node_ids[]`.
Recorded as drift; whether to add the missing patterns is a decision for the next
release, **not** for this RFC.

**Class D — polymorphic, undiscriminated.** `ai-inference.input_refs[]` and
`ai-inference.explanation.evidence_refs[]`. role = polymorphic_input ·
discriminator = none · namespace = external-or-opaque (or a future declared
union) · identity form = unrestricted · resolution = OPAQUE-ALLOWED. RFC-0002
already constrains evidence refs *semantically* (at least one evidence reference
must resolve through the inference's inputs); that constraint is semantic and
does not by itself create a type vocabulary.

**Class E — opaque / external / undeclared namespace.**
`flow-event.source_ref`, `permission-snapshot.source_ref`,
`source-state-change.source_ref`, `flow-event.flow_id`,
`memory.sources[].source_id`. Declarations follow in section 8.

**Class F — digest tokens.** `invalidation-record.idempotency_key`,
`memory.sources[].content_hash`, `asset.content_hash`,
`asset.variants[].content_hash`. role = digest · namespace = digest ·
identity form = algorithm-prefixed hex · resolution = FORMAT-ONLY. These are not
object references.

### 7. Normative answers to the reference-ontology questions

**Q1 — Which vocabularies are subsets of `ProtocolObjectType`?**
`CorrectableType` (6/6), `InvalidatableType` (6/6), `EvidenceSourceType` (4/4
under the `event` -> FlowEvent alias), and `MemorySourceType` (5/5, because
`message` is a protocol object type that is not yet bound) are subsets.
`AuditTargetType` is the one vocabulary that is not a subset, because `source`
is an external member rather than a protocol object. `TriggerCategory` is not on
this axis. The protocol must therefore declare each vocabulary individually as
closed, or as closed-with-one-external-member; it must not assert a single
global superset.

**Q2 — Which vocabularies allow external or opaque?**
By role design, only `MemorySourceType` and `EvidenceSourceType` may in principle
admit external sources, and `AuditTargetType` actually contains one (`source`).
However, the external escape hatch **already exists as a separate field**
(`source_id` / `source_ref`), not as an enum member. This RFC therefore
recommends that the enum vocabularies stay protocol-object-only and that external
sources continue to be expressed through the sibling opaque identifier field.
Adding external members to a discriminated enum would force every consumer to
implement an "unrecognized member" branch, whereas the opaque field is already
unconditionally valid.

**Q3 — Is `message` a protocol object?**
`message` is an **Unbound Protocol Object Type**, and this RFC fixes that
disposition rather than leaving it open. The existing semantics already place
`message` on the internal-object side: `memory.sources[]` carries an `object_type`
discriminator together with `object_id`, not the `source_ref` / `source_id` opaque
escape hatch, and `node.node_type` also contains `message` as a classification.
Reclassifying it as external/opaque now would produce a worse drift — the same
`message` treated as an object classification in one place and as a non-object
opaque thing in another. The reason to make it a protocol object is therefore the
existing reference semantics, not the mere fact that a product has messages.

**Decision (normative direction):**

- `message` is intended to become a Protocol Object Type in a future protocol
  release.
- RFC-0005 does **not** define the Message object schema.
- Until a Message object definition is accepted:
  - no `fnb_message_*` identity pattern is normative (the Message namespace is
    not fixed by this RFC);
  - no Gate 3b type-compatibility check is enabled for
    `memory.sources[].object_type == "message"`;
  - existing v0.1 behaviour remains valid;
  - `message` MUST NOT be reclassified as external/opaque merely to close the gap.

This keeps the ontology question ("what category is it?") separate from the
object-definition question ("what is its schema?"). Because `message` has no
identity form yet, `memory.sources[].object_id` remains the one discriminated
position that cannot be made fully Gate 3b-compatible in the next release.

**Q4 — Is `source` an object type, a namespace, or a pure opaque category?**
`source` is a **pure external/opaque reference category**. It is not a
`ProtocolObjectType`; it has no schema; it has no declared identity namespace.
The `fnb_source_` string appearing in `candidate-memory.json`
(`source_id: "fnb_source_synthetic_001"`) is a **non-normative local prefix in a
fixture**, not a protocol namespace: `memory.sources[].source_id` has no pattern,
so the prefix is owned by the example author, not by the protocol. The protocol
must **not** adopt `fnb_source_` as a constrained namespace — doing so would
convert a deliberately opaque position into an internal-object position and
retro-tighten the frozen acceptance set.

**Q5 — Should `flow_id`'s Flow become a protocol object, or is `flow_id` its own
namespace?**
`flow_id` belongs to a third category that the protocol has not yet named:
a **protocol-owned grouping namespace without an object schema**. It cannot be
treated as a fixed internal reference (there is no Flow object to resolve), and
it must not be treated as fully opaque, because it is a **required** field whose
values must be stable across the events of one flow. Recommendation: declare
`fnb_flow_*` a protocol-owned **grouping** namespace whose values are
non-resolvable by design, and do **not** introduce a Flow object schema merely to
give `flow_id` a resolution target.

**Q6 — Which fields can enable Gate 3b (type compatibility) in the future?**
Gate 3b compares a reference against its discriminator. It can only be total on
fields whose discriminator vocabulary is fully bound to identity forms.

| Field | Gate 3b eligibility |
| --- | --- |
| `correction-patch.target_id` | eligible — 6/6 members bound |
| `invalidation-record.target_id` | eligible — 6/6 members bound |
| `relationship.evidence[].source_id` | eligible — 4/4 members bound |
| `memory.sources[].object_id` | **blocked** while `message` is unbound |
| `invalidation-record.trigger_id` | eligible in a **non-object** sense — compares the trigger class against its expected identity form |
| Class B / Class C fixed-type fields | not applicable — the pattern already encodes the type |
| Class D / Class E / Class F | never eligible |

Gate 3b must **not** be enabled against `v0.1.0-preview.1`; enabling it there
would retro-tighten the frozen acceptance set. It enters with a new protocol
release.

**Q7 — Which fields may only ever have syntax or opaque handling?**
Permanently opaque, resolved by no type vocabulary:
`permission-snapshot.source_ref`, `source-state-change.source_ref`,
`flow-event.source_ref`, `flow-event.flow_id`, `memory.sources[].source_id`,
`ai-inference.input_refs[]`, `ai-inference.explanation.evidence_refs[]`.
These may receive a syntax check if the protocol later chooses to declare one,
but never a type-compatibility check. Class B fields get syntax only (their
pattern is their type). Class F fields get format validation only.

**Q8 — Which resolution states may each class take?**
Gate 3c recognises `EXISTS`, `OUT_OF_SCOPE`, `MISSING`, `OPAQUE-ALLOWED`. The
critical rule: **`MISSING` is a permitted resolution state, not a protocol
verdict.** A syntactically valid, type-compatible reference to an object that has
not reached this consumer is legitimate. Conflating `MISSING` with `3a`/`3b`
failure would reject valid data.

| Class | Allowed 3c states |
| --- | --- |
| typed internal, target exists locally | EXISTS · OUT_OF_SCOPE · MISSING |
| typed internal, `message` member | OPAQUE-ALLOWED · OUT_OF_SCOPE |
| fixed-type (Class B), actor/event/record refs | EXISTS · OUT_OF_SCOPE · MISSING |
| polymorphic (Class D) | OPAQUE-ALLOWED · OUT_OF_SCOPE |
| opaque / external (Class E) | OPAQUE-ALLOWED · OUT_OF_SCOPE |
| `flow_id` (grouping) | OUT_OF_SCOPE · OPAQUE-ALLOWED — never EXISTS-required |
| `trigger_id` -> `parent_invalidation` | EXISTS required at emission; may later become OUT_OF_SCOPE after retention prunes the parent; never MISSING-as-violation |
| digest tokens (Class F) | not applicable — FORMAT-ONLY |

### 8. Application to the frozen reference positions

| Position | role | namespace | identity form | resolution | 3b | 3c states |
| --- | --- | --- | --- | --- | --- | --- |
| `correction-patch.target_id` | correction_target | protocol-object | target-type-specific | MUST-RESOLVE | eligible | EXISTS · OUT_OF_SCOPE · MISSING |
| `invalidation-record.target_id` | invalidation_target | protocol-object | target-type-specific | MUST-RESOLVE | eligible | EXISTS · OUT_OF_SCOPE · MISSING |
| `invalidation-record.trigger_id` | trigger | protocol-object | trigger-class-specific | MUST-RESOLVE | eligible (non-object) | per trigger class (see Q8) |
| `memory.sources[].object_id` | memory_source | protocol-object except `message` | target-type-specific except `message` | MAY-RESOLVE | blocked on `message` | EXISTS · OUT_OF_SCOPE · MISSING · OPAQUE-ALLOWED (for `message`) |
| `relationship.evidence[].source_id` | evidence_source | protocol-object | target-type-specific | MAY-RESOLVE | eligible | EXISTS · OUT_OF_SCOPE · MISSING |
| `flow-event.flow_id` | flow_grouping | protocol-owned-grouping | opaque grouping token | OPAQUE-ALLOWED | no | OUT_OF_SCOPE · OPAQUE-ALLOWED |
| `flow-event.source_ref` | provenance | external-or-opaque | unrestricted | OPAQUE-ALLOWED | no | OPAQUE-ALLOWED · OUT_OF_SCOPE |
| `permission-snapshot.source_ref` | source | external-or-opaque | unrestricted | OPAQUE-ALLOWED | no | OPAQUE-ALLOWED · OUT_OF_SCOPE |
| `source-state-change.source_ref` | source | external-or-opaque | unrestricted | OPAQUE-ALLOWED | no | OPAQUE-ALLOWED · OUT_OF_SCOPE |
| `memory.sources[].source_id` | source | external-or-opaque | unrestricted | OPAQUE-ALLOWED | no | OPAQUE-ALLOWED · OUT_OF_SCOPE |
| `ai-inference.input_refs[]` | polymorphic_input | external-or-opaque | unrestricted | OPAQUE-ALLOWED | no | OPAQUE-ALLOWED · OUT_OF_SCOPE |
| `ai-inference.explanation.evidence_refs[]` | polymorphic_input | external-or-opaque | unrestricted | OPAQUE-ALLOWED | no | OPAQUE-ALLOWED · OUT_OF_SCOPE |

This yields five opaque positions that a future release must keep
unconstrained (the three `source_ref`s, `flow_id`, and
`memory.sources[].source_id`) and one discriminated position that cannot yet be
fully typed (`memory.sources[].object_id`, on `message`).

### 9. Gate mapping

| Check | Applies to | Status now |
| --- | --- | --- |
| **Gate 3.0** reference classification | every reference field | defined by this RFC (role/namespace/identity form) |
| **Gate 3a** reference syntax | Class A/B/C | enabled on `v0.1` for already-patterned positions; Class D/E must not be given a syntax constraint |
| **Gate 3b** reference type compatibility | Class A (and non-object `trigger_id`) | **not enabled** on `v0.1`; enters with the next release |
| **Gate 3c** reference resolution state | all classes except F | per Q8; `MISSING` is a state, not a verdict |

Gate 3.0 must run first; otherwise the protocol cannot know whether `source_ref`
is subject to 3b at all. Gates 3a, 3b, and 3c must remain separate verdicts;
merging them misclassifies a valid-but-not-yet-present reference as invalid.

### 10. What this RFC changes

Nothing on disk. No schema, enum, pattern, fixture, binding, or release digest
changes. This RFC is an input to a future protocol release; it is a prerequisite
for that release's reference work, not a change to `v0.1.0-preview.1`.

## Data Sovereignty Impact

Users gain an explicit, checkable statement of what each reference means and
where it points. Today an opaque external source and an internal object
reference look identical at the schema level; that ambiguity makes it harder to
reason about what a system may resolve and retain. Naming the roles does not
weaken control — it makes the existing boundary legible. No reference becomes
resolvable that was not already resolvable, and no opaque position becomes an
internal object.

## Privacy Impact

The ontology preserves the current privacy posture rather than relaxing it. It
keeps `source_ref`, `flow_id`, and `source_id` explicitly non-resolvable, so no
implementation can be required to resolve or retain external identities.
`AuditTombstone.target_type` carries no target identifier, and this RFC does not
add one; the tombstone keeps proving only that a class of action occurred.
Declaring `source` an external/opaque category prevents accidentally converting
a privacy-preserving opaque reference into an internal object pointer.

## AI Explainability Impact

`ai-inference.input_refs[]` and `explanation.evidence_refs[]` are declared
polymorphic and opaque. This RFC does not add a type vocabulary to them, so
RFC-0002's semantic requirement — that evidence references resolve through the
inference's inputs — remains the governing constraint and is not replaced by a
weaker syntax check. Where a discriminator does exist (`memory.sources`,
`relationship.evidence`), the ontology makes it explicit what a referenced
object is, which is a precondition for explaining *why* a derived object exists.

## Compatibility

Additive and non-breaking by construction. This RFC creates no new field, no new
enum member, and no new pattern, so no currently valid object becomes invalid and
no currently invalid object becomes valid. It does not change the frozen
acceptance set of `v0.1.0-preview.1`. Its recommendations are addressed to a
future protocol release; acting on them requires a new version, tag, and digest
manifest, per the publication rules in
[`specs/v0.1/README.md`](../specs/v0.1/README.md).

## Alternatives

- **One merged global enum for all reference vocabularies.** Rejected. It would
  force `asset` to be a valid correction target and `ai_inference` to be valid
  relationship evidence, neither of which is intended, and it would collapse a
  deliberately role-specific admissibility decision into a single list.
- **Assert "every reference must match the target object's `_id` pattern".**
  Rejected. It is simultaneously too loose (it says nothing about fields with no
  pattern) and too strong (it would convert opaque external references into
  invalid internal references).
- **Give `flow_id` a pattern and add a Flow schema.** Rejected as the primary
  recommendation. A Flow object introduced only to satisfy a required field would
  add a protocol object with no independent semantics, and would retro-tighten a
  frozen field. Declaring a grouping namespace is smaller and more honest.
- **Retrofit the ontology into `v0.1.0-preview.1`.** Rejected outright. It would
  violate the immutable publication boundary and retro-tighten the acceptance
  set.
- **Leave the vocabularies as they are and document nothing.** Rejected. It
  leaves every reference check and every cross-implementation consumer guessing
  what a reference means, which is the defect this RFC exists to name.

## Open Questions

1. **`fnb_source_` namespace.** Should the protocol explicitly declare it
   non-normative and example-only, or replace it in fixtures with a neutral value
   in a later release? Either way, no retro-tightening of the frozen fixture is
   proposed here.
2. **Flow object.** Should a Flow object ever exist, or does `flow_id` remain a
   grouping namespace permanently?
3. **Alias resolution.** Is member name `event` formally defined as the FlowEvent
   object, and `block_draft` as BlockDraft? An explicit member-to-object mapping
   table is likely needed in the next release.
4. **`NodeType` boundary.** Should the RFC process own `node.node_type`, or is it
   a product classification that stays out of the reference ontology? A
   `node_type` value such as `message` must not be read as a reference type.
5. **`input_refs` / `evidence_refs` union.** Should the next release declare an
   explicit allowed-type union, or keep them permanently opaque? Declaring a
   union would make them Gate 3b-eligible; keeping them opaque preserves the
   current flexibility.
6. **Same-name field drift.** Should `owner_id` and `actor_id` references be
   given a consistent constraint strength in the next release? This RFC records
   the drift but does not decide it.
7. **`parent_invalidation_id` after retention.** Once the parent record is
   pruned under an AuditTombstone, does the child reference become OUT_OF_SCOPE,
   or does retention require the parent to be kept? Recorded, not decided.
