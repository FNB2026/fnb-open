// SPDX-License-Identifier: Apache-2.0
import test from 'node:test';
import assert from 'node:assert/strict';
import { gzipSync } from 'node:zlib';
import { createExchangeClient, ConfigurationError } from '../dist/index.js';
import { problems } from '../dist/generated/wire.js';
import { world, receipt, independent, mockProcess, httpHarness, send } from './helpers.mjs';
const client = (endpoint, options = {}) => createExchangeClient({ endpoint, ...options });
const bad = (value, category = 'invalid-response') => assert.deepEqual(value, { kind: 'failure', category });

test('A01 A02 A03 A04 A05 A06: established Mock native-fetch synthetic interoperability', async t => {
  const api = client(await mockProcess(t));
  for (const name of ['basic-memory', 'relationship-correction', 'source-redaction', 'permission-withdrawal']) {
    const request = world(name), result = await api.exchange(request);
    assert.deepEqual(result, { kind: 'receipt', receipt: receipt(request) });
  }
  const first = world(), second = independent(first);
  const combined = { ...first, objects: first.objects.flatMap((object, index) => [object, second.objects[index]]), validation_contexts: [...first.validation_contexts, ...second.validation_contexts] };
  assert.deepEqual(await api.exchange(combined), { kind: 'receipt', receipt: receipt(combined) });
  for (const mutate of [
    request => { request.objects[0].object = {}; },
    request => { request.objects[0].schema = 'https://sender.invalid/never-fetch'; },
    request => { request.validation_contexts[0].roles.node = 'absent'; },
    request => { request.objects.push(structuredClone(request.objects[0])); },
    request => { request.objects.find(item => item.schema.endsWith('/block.schema.json')).object.owner_id = 'synthetic-other-owner'; },
    request => { request.objects.find(item => item.schema.endsWith('/flow-event.schema.json')).object.occurred_at = '2026-02-30T12:00:00Z'; }
  ]) {
    const request = world(); mutate(request);
    assert.deepEqual(await api.exchange(request), { kind: 'receipt', receipt: receipt(request, 'rejected') });
  }
});

test('A07 A08 A13: both verdicts require exact three-field per-call correlation and shape', async t => {
  let body = receipt(), status = 200;
  const api = client(await httpHarness(t, (_, res) => send(res, body, status)));
  for (const verdict of ['accepted', 'rejected']) for (const key of ['transport_version', 'protocol_release', 'exchange_id']) {
    body = { ...receipt(world(), verdict), [key]: 'changed' }; bad(await api.exchange(world()));
  }
  for (const mutate of [body => { delete body.exchange_id; }, body => { body.extra = true; }, body => { body.status = 'pending'; }, body => { body.exchange_id = ''; }]) {
    body = receipt(); mutate(body); bad(await api.exchange(world()));
  }
  for (const code of [201, 204, 400, 401, 403, 404, 429, 502]) { status = code; body = receipt(); bad(await api.exchange(world())); }
  status = 502; body = '<html>synthetic gateway</html>'; bad(await api.exchange(world()));
});

test('A09 A10 A11 A12 A24: all known Problems and consumer extension semantics', async t => {
  let body, status;
  const api = client(await httpHarness(t, (_, res) => send(res, body, status)));
  for (const problem of problems) {
    status = problem.status; body = { ...problem, detail: 'synthetic generic detail', extension: { ignored: true } };
    assert.deepEqual(await api.exchange(world()), { kind: 'problem', problem: { ...problem, detail: body.detail } });
    for (const change of [{ type: 'unknown' }, { title: 'wrong' }, { status: 200 }, { detail: 1 }]) {
      body = { ...problem, ...change }; bad(await api.exchange(world()));
    }
    body = { ...problem }; delete body.type; bad(await api.exchange(world()));
  }
  body = { ...problems[0] }; status = 200; bad(await api.exchange(world()));
  body = JSON.stringify(problems[0]).slice(0, -1) + ',"extension":{"x":1,"x":2}}'; status = 400;
  bad(await api.exchange(world()));
});

test('A14 A15 A16 A17 A20: actual native-fetch hostile JSON, media and encoding', async t => {
  let body = '', media = 'application/json', headers = {};
  const api = client(await httpHarness(t, (_, res) => send(res, body, 200, media, headers)));
  for (const raw of [
    '{"x":1,"x":2}', '{"x":{"a":1,"a":2}}', '{"x":1,"\\u0078":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}',
    '{}{}', '[]', '', '{"x":1e999}', '{"x":9007199254740993}', '{"x":"\\uZZZZ"}', '{"x":"raw\nline"}',
    Buffer.from([0xff]), Buffer.from([0xef, 0xbb, 0xbf, 0x7b, 0x7d]), '[[[[[[[[[[0]]]]]]]]]]'
  ]) { body = raw; bad(await api.exchange(world())); }
  body = receipt();
  for (const type of ['text/html', 'application/problem+json', 'application/json; charset=latin1', 'application/json; profile=x', 'application/json, application/json']) {
    media = type; bad(await api.exchange(world()));
  }
  media = 'Application/JSON; Charset=UTF-8';
  for (const encoding of [undefined, 'identity', 'Identity', 'IDENTITY']) {
    headers = encoding ? { 'Content-Encoding': encoding } : {};
    assert.equal((await api.exchange(world())).kind, 'receipt');
  }
  // Native fetch transparently decodes gzip, but visible non-identity encoding
  // still triggers failure. This is not a raw compressed-wire byte claim.
  headers = { 'Content-Encoding': 'gzip' }; body = gzipSync(JSON.stringify(receipt()));
  bad(await api.exchange(world()));
  media = ''; headers = {}; body = receipt(); bad(await api.exchange(world()));
});

test('A18 A19 A25: input safety, no domain judge, no request coercion or dispatch', async () => {
  let sent = 0;
  const api = client('http://127.0.0.1:8765/exchange', { fetch: async () => { sent++; return new Response(JSON.stringify(receipt()), { headers: { 'Content-Type': 'application/json' } }); } });
  const cyclic = {}; cyclic.self = cyclic;
  const getter = {}; Object.defineProperty(getter, 'sensitive', { enumerable: true, get() { throw new Error('getter ran'); } });
  const custom = { toJSON() { return {}; } };
  const sparse = Array(2);
  for (const value of [cyclic, getter, custom, sparse, undefined, NaN, Infinity, 1n, Symbol(), () => {}, new Date(), Number.MAX_SAFE_INTEGER + 1]) {
    const request = world(); request.objects[0].object.test = value; bad(await api.exchange(request), 'invalid-input');
  }
  for (const change of [{ transport_version: '9.0' }, { protocol_release: 'v9' }, { extra: true }, { objects: [] }]) bad(await api.exchange({ ...world(), ...change }), 'invalid-input');
  assert.equal(sent, 0);
  const request = world(); request.objects[0].object = JSON.parse('{"__proto__":{"safe":true},"constructor":1,"n":0.125}');
  assert.equal((await api.exchange(request)).kind, 'receipt'); assert.equal({}.safe, undefined); assert.equal(sent, 1);
});

test('A21 A22 A23: receiver limits and fail-closed faults remain Problem results', async t => {
  for (const mode of ['bytes', 'objects', 'internal', 'missing-schema', 'corrupt-schema', 'corrupt-manifest']) {
    const result = await client(await mockProcess(t, mode)).exchange(world());
    assert.equal(result.kind, 'problem'); assert.equal(result.problem.status, mode === 'bytes' || mode === 'objects' ? 413 : 500);
  }
  assert.equal((await client(await mockProcess(t, 'normal', true)).exchange(world())).problem.status, 500);
});

test('A26 A27: URL policy, native byte body, no credential/custom-header or redirect send', async t => {
  for (const endpoint of ['http://localhost:8765/exchange', 'http://192.0.2.1/exchange', 'http://0.0.0.0/exchange', 'http://2130706433/exchange', 'https://user:pass@example.invalid/exchange', 'https://example.invalid/other', 'https://example.invalid/exchange?', 'https://example.invalid/exchange#x', 'file:///exchange']) assert.throws(() => client(endpoint), ConfigurationError);
  assert.throws(() => client('https://example.invalid/exchange', { headers: { Authorization: 'not-supported' } }), ConfigurationError);
  let calls = 0;
  const endpoint = await httpHarness(t, (req, res) => {
    calls++;
    assert.equal(req.method, 'POST'); assert.ok(Number(req.headers['content-length']) > 0); assert.equal(req.headers['transfer-encoding'], undefined);
    assert.equal(req.headers.authorization, undefined); assert.equal(req.headers.cookie, undefined);
    res.writeHead(302, { Location: endpoint }); res.end();
  });
  bad(await client(endpoint).exchange(world()), 'network'); assert.equal(calls, 1);
});

test('A28 A29 A31: actual stalled/truncated streams, deadline and incremental cap', async t => {
  let mode = 'headers';
  const api = client(await httpHarness(t, (_, res) => {
    if (mode === 'headers') return;
    if (mode === 'body') { res.writeHead(200, { 'Content-Type': 'application/json' }); res.flushHeaders(); return; }
    if (mode === 'truncated') { res.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': '100' }); res.write('{}'); setTimeout(() => res.destroy(), 10); return; }
    send(res, ' '.repeat(1000));
  }), { timeoutMs: 150, limits: { responseBytes: 512 } });
  bad(await api.exchange(world()), 'timeout'); mode = 'body'; bad(await api.exchange(world()), 'timeout');
  mode = 'truncated'; bad(await api.exchange(world())); mode = 'large'; bad(await api.exchange(world()), 'response-limit');
  bad(await client('http://127.0.0.1:1/exchange').exchange(world()), 'network');
});

test('A30 A32 A33 A34: abort races, late success, snapshot and per-call state', async () => {
  const responses = [], seen = [];
  const api = client('http://127.0.0.1:8765/exchange', { timeoutMs: 25, fetch: async (_, options) => {
    const request = JSON.parse(new TextDecoder().decode(options.body)); seen.push(request);
    return new Promise(resolve => responses.push(() => resolve(new Response(JSON.stringify(receipt(request)), { headers: { 'Content-Type': 'application/json' } }))));
  } });
  const pre = new AbortController(); pre.abort(); bad(await api.exchange(world(), { signal: pre.signal }), 'cancelled'); assert.equal(seen.length, 0);
  const request = world(), pending = api.exchange(request); request.exchange_id = 'mutated';
  bad(await pending, 'timeout'); responses.shift()(); await new Promise(resolve => setTimeout(resolve, 5)); assert.notEqual(seen[0].exchange_id, 'mutated');
  const abort = new AbortController(), cancelled = api.exchange(world(), { signal: abort.signal }); abort.abort(); bad(await cancelled, 'cancelled'); responses.shift()();
  let requests = [];
  const concurrent = client('http://127.0.0.1:8765/exchange', { fetch: async (_, options) => new Promise(resolve => requests.push({ request: JSON.parse(new TextDecoder().decode(options.body)), resolve })) });
  const one = concurrent.exchange({ ...world(), exchange_id: 'one' }), two = concurrent.exchange({ ...world(), exchange_id: 'two' });
  requests[1].resolve(new Response(JSON.stringify(receipt(requests[1].request)), { headers: { 'Content-Type': 'application/json' } }));
  requests[0].resolve(new Response(JSON.stringify(receipt(requests[0].request)), { headers: { 'Content-Type': 'application/json' } }));
  assert.equal((await one).receipt.exchange_id, 'one'); assert.equal((await two).receipt.exchange_id, 'two');
  requests = [];
  const swappedOne = concurrent.exchange({ ...world(), exchange_id: 'one' }), swappedTwo = concurrent.exchange({ ...world(), exchange_id: 'two' });
  requests[0].resolve(new Response(JSON.stringify(receipt(requests[1].request)), { headers: { 'Content-Type': 'application/json' } }));
  requests[1].resolve(new Response(JSON.stringify(receipt(requests[0].request)), { headers: { 'Content-Type': 'application/json' } }));
  bad(await swappedOne); bad(await swappedTwo);
  assert.throws(() => client('https://example.invalid/exchange', { fetch: 1 }), ConfigurationError);
});

test('A30 A34: cancellation during body and listener/reader cleanup, unexpected injected responses', async () => {
  const abort = new AbortController();
  let added = 0, removed = 0, cancelled = 0;
  const originalAdd = abort.signal.addEventListener.bind(abort.signal), originalRemove = abort.signal.removeEventListener.bind(abort.signal);
  abort.signal.addEventListener = (...args) => { added++; return originalAdd(...args); };
  abort.signal.removeEventListener = (...args) => { removed++; return originalRemove(...args); };
  const body = new ReadableStream({ cancel() { cancelled++; } });
  const api = client('http://127.0.0.1:8765/exchange', { fetch: async () => new Response(body, { headers: { 'Content-Type': 'application/json' } }) });
  const pending = api.exchange(world(), { signal: abort.signal });
  await new Promise(resolve => setTimeout(resolve, 5)); abort.abort(); bad(await pending, 'cancelled');
  assert.equal(added, 1); assert.equal(removed, 1); assert.equal(cancelled, 1);
  bad(await client('http://127.0.0.1:8765/exchange', { fetch: async () => undefined }).exchange(world()));
  bad(await client('http://127.0.0.1:8765/exchange', { fetch: async () => { throw new Error('untrusted detail'); } }).exchange(world()), 'network');
});
