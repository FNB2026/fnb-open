# Local Object Exchange Mock

License: Apache-2.0. This development tool wraps the unchanged evaluator frozen
at `object-exchange-v1.0.0-preview.1`. It is **not a production service, FNB
reference implementation, or third-party implementation certification tool**.
It creates no compatibility report, authentication surface, or SDK contract.

## Start and test

From the repository root, create a local environment and install hash-locked
dependencies (installation may need network; running the mock does not):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r tools/requirements-validation.lock
.venv/bin/python tools/object-exchange-mock.py
```

Default endpoint: `http://127.0.0.1:8765/exchange`. Stop with Ctrl-C.
Only numeric IPv4 loopback addresses are accepted; binding `0.0.0.0`, a LAN
address, or a hostname is rejected. Do not expose this mock through a proxy,
tunnel, port forward, or production deployment. Loopback is not authentication:
other local programs can access it. Use synthetic data only.

```bash
.venv/bin/python tools/object-exchange-contract.py
.venv/bin/python -m unittest discover -s tests/conformance/transport -p 'test_*.py' -v
.venv/bin/python -O -m unittest discover -s tests/conformance/transport -p 'test_*.py'
```

The combined suite retains all 31 frozen offline tests and adds actual loopback
HTTP tests. Those tests construct envelopes from the existing generated worlds;
no private material, real accounts, databases, or FNB API is used. Every socket,
thread, and temporary test directory is closed on completion.

## Boundaries and HTTP behavior

The only binding route is exact `POST /exchange` (no query string). HTTP/1.x
requests must have one decimal `Content-Length`; chunked transfer encoding is
not supported. Duplicate or invalid length headers and incomplete bodies get
`400 malformed-envelope`. Missing/duplicate Content-Type or duplicate
Content-Encoding get `415 unsupported-media-type`. Representation checking
uses the frozen probe before waiting for the body. Unsupported methods and
paths receive local HTTP errors, not new protocol routes or receipts.

Responses have the contract's exact Content-Type, explicit byte Content-Length,
UTF-8 JSON, and `Connection: close`. The server is serial and responds as
HTTP/1.0. It does not promise streaming, concurrency, keep-alive, HTTP/2, TLS,
or production availability. Defaults are 1 MiB (`--max-bytes 1048576`), 256
objects (`--max-objects 256`), and a 5-second socket read deadline
(`--request-timeout 5`). These positive local limits are not protocol constants.
Byte capacity may abort before reading with `413`; the shared probe enforces
object capacity after decoding. Body read deadlines and evaluator timeouts
return `500 evaluation-failure`, never a verdict. Socket deadlines are not a
hard CPU time budget for validation; this tool is for bounded local testing only.
Framing/header failures before the route is reached are infrastructure errors.

Every exchange rechecks the frozen 10-asset transport digest manifest and then
the published schema set through the unchanged contract probe. Missing/corrupt
material, unavailable imports/format handlers, or internal exceptions fail
closed with generic `500` Problem Details, without paths or stack traces.
Restart after repairing startup material/dependencies. The shared frozen
evaluator owns strict UTF-8 JSON parsing, nested duplicate/nonfinite rejection,
stage ordering, object rules, direct cross-object rules, explicit validation
contexts, status mapping, and receipt correlation. The wrapper also verifies
successful receipts against the shared receipt checker before sending them.

`200 rejected` means a readable supported envelope contains invalid protocol
material. It must not become `400`. `200 accepted` means only the bounded public
validation passed: **no storage, application, permission grant, historical
closure, persistence, or side effect is implied**. The three correlation fields
are echoed exactly, with no additional receipt semantics.

There is no outbound HTTP client, DNS/schema URL retrieval, database, filesystem
write, account service, or private backend integration in the request handler.
Requests exist transiently in memory; URL/header/body logging is disabled.
Tests prohibit outbound connection/DNS calls and common write APIs during an
actual exchange, and exercise missing/corrupt material and validator failures.
These checks are evidence about this wrapper, not an OS sandbox guarantee for
arbitrary code or a security certification.

This work does not alter the frozen [OpenAPI](../specs/openapi/object-exchange/v1/openapi.yaml),
[RFC-0004](../rfcs/0004-protocol-object-exchange.md), schema release, manifests,
offline probe/tests, or either published tag. It remains a Draft PR pending
independent review; no release or SDK work is authorized here.
