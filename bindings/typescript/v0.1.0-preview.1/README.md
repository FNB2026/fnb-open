# FNB Protocol TypeScript Bindings — v0.1.0-preview.1

Declaration-only TypeScript types for the frozen FNB protocol preview.

**TypeScript bindings are a static developer convenience, not a replacement for
JSON Schema conformance.** A binding can hold for code that the FNB schemas still
reject, because TypeScript cannot express several JSON Schema runtime
constraints. `tsc --noEmit` passing is not an FNB conformance pass.

## Generated, not hand-authored

Every `*.d.ts` file in this directory is produced from the frozen protocol
artifacts. Do not edit them by hand; the change would be reverted by the next
generation and would fail CI.

```bash
python3 tools/generate-bindings.py            # write
python3 tools/generate-bindings.py --check    # verify committed files are current
```

The generator is manifest-driven: it reads
`specs/v0.1/releases/v0.1.0-preview.1/schema-digests.json`, verifies every schema
byte length and SHA-256 digest, verifies each `$id` is pinned to the
`v0.1.0-preview.1` tag namespace, and only then renders. It fails closed on any
JSON Schema keyword it does not explicitly support, so no schema semantics are
dropped silently.

Each file carries the protocol version, its source schema path, and the source
SHA-256, so a single file taken in isolation still identifies exactly which
frozen schema it was generated from.

## What the types express

| JSON Schema | TypeScript |
| --- | --- |
| `type`, `enum`, `const` | scalar and literal unions |
| `properties`, `required`, `additionalProperties` | interface members, optional members |
| `items` | array element types |
| `allOf` + `if`/`then` | discriminated unions (see below) |
| `pattern`, `format`, `minLength`, `minItems`, `uniqueItems`, `minimum`, `maximum` | JSDoc only — declared, not enforced |
| `additionalProperties: false` | JSDoc only — TypeScript excess-property checks apply to object literals, not to values of a wider type |

Conditional protocol requirements are rendered as discriminated unions rather
than as wide interfaces. For example `new_state: "deleted"` with
`reason_code: "source_restored"` is rejected by the FNB schema, and it does not
type-check either:

```ts
type SourceStateChange =
  | (SourceStateChangeBase & { new_state: "deleted"; reason_code: "source_deleted" })
  | (SourceStateChangeBase & { new_state: "active"; reason_code: "source_restored" | "permission_restored" })
  | /* ... */;
```

Where a rule narrows a runtime-only constraint (for example the stricter
`trigger_id` pattern required by `trigger_type: "parent_invalidation"`), the
narrowing is recorded in JSDoc next to the member instead of being presented as
if the type system enforced it.

## Consumption

```ts
import type { Memory, SourceStateChange } from "./v0.1.0-preview.1";
```

The declarations have no runtime footprint and no dependency on any FNB product
service.

## Scope

These are protocol object types only. They deliberately contain no client
object, no transport call, no authentication header, and no product endpoint.
Adding any of those would turn this layer into a private product API surface.

## License

Apache-2.0. See [`LICENSE-CODE.md`](../../../LICENSE-CODE.md).
