// SPDX-License-Identifier: Apache-2.0
import test from 'node:test';
import assert from 'node:assert/strict';
import { gzipSync } from 'node:zlib';
import { createExchangeClient } from '../dist/index.js';
import { httpHarness, send, receipt, world } from './helpers.mjs';

test('A19 A23: native fetch exposes decoded bytes but retains gzip headers; SDK fails closed', async t => {
  let plain = JSON.stringify(receipt());
  const endpoint = await httpHarness(t, (_request, response) => {
    const compressed = gzipSync(plain);
    send(response, compressed, 200, 'application/json', {
      'Content-Encoding': 'gzip', 'Content-Length': String(compressed.length),
    });
  });
  const raw = await fetch(endpoint, { method: 'POST', body: '{}' });
  assert.equal(raw.headers.get('content-encoding'), 'gzip');
  assert.equal(Number(raw.headers.get('content-length')), gzipSync(plain).length);
  assert.equal(await raw.text(), plain);
  const api = createExchangeClient({ endpoint, limits: { responseBytes: 512 } });
  assert.deepEqual(await api.exchange(world()), { kind: 'failure', category: 'invalid-response' });
  plain = ' '.repeat(2048) + JSON.stringify(receipt());
  assert.ok(gzipSync(plain).length < 512);
  assert.deepEqual(await api.exchange(world()), { kind: 'failure', category: 'response-limit' });
});

test('A23 A28: native chunked stream budget and premature EOF cannot become a receipt', async t => {
  let mode = 'chunked';
  const endpoint = await httpHarness(t, (_request, response) => {
    response.writeHead(200, { 'Content-Type': 'application/json',
      ...(mode === 'truncated' ? { 'Content-Length': '10000', Connection: 'close' } : {}) });
    response.write(JSON.stringify(receipt()));
    response.end(mode === 'chunked' ? ' '.repeat(1024) : '');
  });
  const api = createExchangeClient({ endpoint, timeoutMs: 2000, limits: { responseBytes: 512 } });
  assert.deepEqual(await api.exchange(world()), { kind: 'failure', category: 'response-limit' });
  mode = 'truncated';
  assert.deepEqual(await api.exchange(world()), { kind: 'failure', category: 'invalid-response' });
});
