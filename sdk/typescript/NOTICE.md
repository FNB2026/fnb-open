# Unpublished SDK workspace notice

SPDX-License-Identifier: Apache-2.0

This explicitly licensed SDK development directory is Apache-2.0, including its
runtime, generation scripts, tests, copied declarations and generated metadata.
The full license is bundled as `LICENSE-APACHE-2.0.txt`. FNB names and marks
remain reserved; no npm namespace is asserted. Documentation outside this
directory follows the repository's path-based documentation license.

Upstream FNB public schema/transport artifacts and declaration snapshots are
Apache-2.0; see `provenance.json` for immutable sources and byte digests. The
workspace SPDX inventory also lists locked development compiler/platform
packages; these are not runtime dependencies. It is not a release attestation.
Node's runtime/native fetch is supplied by the caller/runtime, not vendored here.
The generated SPDX document's metadata is explicitly CC0-1.0 as declared in
its dataLicense field; this does not relicense referenced packages or code.

The release-preparation candidate additionally produces an **external** SPDX 2.3
SBOM, provenance and self-excluding digest manifest outside the tracked tree.
Those describe the actual archive and are distinct from the embedded
development-lock inventory above. This directory and its archive remain
unpublished; nothing here is a signed release attestation.
