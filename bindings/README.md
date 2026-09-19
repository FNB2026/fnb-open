# FNB Protocol Bindings

Generated language bindings for the frozen FNB protocol preview.

These are **type definitions**, not an SDK. They describe protocol objects
(`Actor`, `Memory`, `Block`, `Relationship`, `PermissionSnapshot`, ...) and
nothing else. There is intentionally no client object, no login, no request
helper, and no transport here: an SDK would begin to imply a product API, and
the public protocol is not one.

## Layout

```text
bindings/
  typescript/
    .gitignore             keeps installed packages out of the tree
    package.json          pinned validation toolchain (private, not published)
    package-lock.json     exact TypeScript version and integrity hashes
    tsconfig.json         declaration type-check configuration
    protocol-type-expectations.ts
                          bidirectional assertions on the generated unions
    v0.1.0-preview.1/      generated declarations for the frozen preview
```

Bindings are generated per released protocol version, so a consumer can pin a
directory to a protocol tag rather than tracking a moving tree.

## Source of truth

The 14 JSON Schemas under `specs/v0.1/` are the only source of truth. Bindings
are generated, never hand-authored, and CI regenerates them and fails on any
byte difference.

`protocol-type-expectations.ts` is the one hand-written TypeScript file here. It
is a validation fixture, not a protocol artifact: it uses `@ts-expect-error` so
the compiler both accepts the valid combinations and rejects the ones the frozen
schemas forbid.

## Status

Preview. The protocol itself remains pre-release, and these bindings carry no
stability promise beyond the tag they were generated from. A later protocol
version produces a new directory; generated content is never replaced in place.

See [`typescript/v0.1.0-preview.1/README.md`](./typescript/v0.1.0-preview.1/README.md)
for what the types do and do not express.

## License

Apache-2.0. See [`LICENSE-CODE.md`](../LICENSE-CODE.md).
