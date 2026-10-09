// SPDX-License-Identifier: Apache-2.0
import test from 'node:test';
import assert from 'node:assert/strict';
import { createExchangeClient } from '../dist/index.js';
import { world, receipt } from './helpers.mjs';
const drain = async () => { for (let index = 0; index < 16; index++) await Promise.resolve(); };
const bad = (value, category) => assert.deepEqual(value, { kind: 'failure', category });
const response = () => new Response(JSON.stringify(receipt()), { headers: { 'Content-Type': 'application/json' } });

for (const first of ['timeout', 'cancelled']) test(`A30: deterministic ${first}-first race, one settlement and late body cancellation`, async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let resolveFetch, closed = 0, settled = 0, signal;
  const caller = new AbortController();
  const api = createExchangeClient({ endpoint: 'http://127.0.0.1:8765/exchange', timeoutMs: 100,
    fetch: async (_, options) => { signal = options.signal; return new Promise(resolve => { resolveFetch = resolve; }); } });
  const pending = api.exchange(world(), { signal: caller.signal }).then(result => { settled++; return result; });
  if (first === 'timeout') { t.mock.timers.tick(100); caller.abort(); }
  else { caller.abort(); t.mock.timers.tick(100); }
  const result = await pending; bad(result, first);
  assert.equal(signal.aborted, true);
  const body = new ReadableStream({ cancel() { closed++; } });
  resolveFetch(new Response(body, { headers: { 'Content-Type': 'application/json' } }));
  await drain(); t.mock.timers.tick(1000);
  assert.equal(closed, 1); assert.equal(settled, 1); bad(result, first);
});

for (const stop of ['timeout', 'cancelled']) test(`A30: body EOF queued before ${stop}, no late accepted`, async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let bodyController, settled = 0;
  const caller = new AbortController();
  const body = new ReadableStream({ start(controller) { bodyController = controller; } });
  const api = createExchangeClient({ endpoint: 'http://127.0.0.1:8765/exchange', timeoutMs: 100,
    fetch: async () => new Response(body, { headers: { 'Content-Type': 'application/json' } }) });
  const pending = api.exchange(world(), { signal: caller.signal }).then(result => { settled++; return result; });
  await drain();
  bodyController.enqueue(new TextEncoder().encode(JSON.stringify(receipt()))); bodyController.close();
  if (stop === 'timeout') t.mock.timers.tick(100); else caller.abort();
  bad(await pending, stop); await drain(); assert.equal(settled, 1);
});

test('A30: validated result commits before abort/deadline; no surviving listener/timer', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let internalSignal, settled = 0, added = 0, removed = 0;
  const caller = new AbortController();
  const add = caller.signal.addEventListener.bind(caller.signal), remove = caller.signal.removeEventListener.bind(caller.signal);
  caller.signal.addEventListener = (...args) => { added++; return add(...args); };
  caller.signal.removeEventListener = (...args) => { removed++; return remove(...args); };
  const api = createExchangeClient({ endpoint: 'http://127.0.0.1:8765/exchange', timeoutMs: 100,
    fetch: async (_, options) => { internalSignal = options.signal; return response(); } });
  const result = await api.exchange(world(), { signal: caller.signal }).then(value => { settled++; return value; });
  assert.deepEqual(result, { kind: 'receipt', receipt: receipt() });
  caller.abort(); t.mock.timers.tick(1000); await drain();
  assert.equal(internalSignal.aborted, false); assert.equal(settled, 1); assert.equal(added, 1); assert.equal(removed, 1);
});

test('A28 A30: fetch rejection wins before abort/deadline; no exception text leak', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const caller = new AbortController();
  const api = createExchangeClient({ endpoint: 'http://127.0.0.1:8765/exchange', timeoutMs: 100,
    fetch: async () => { throw new Error('PRIVATE TEST DETAIL'); } });
  const result = await api.exchange(world(), { signal: caller.signal });
  bad(result, 'network'); caller.abort(); t.mock.timers.tick(1000); await drain(); bad(result, 'network');
});
