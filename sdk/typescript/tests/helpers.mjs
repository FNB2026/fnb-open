// SPDX-License-Identifier: Apache-2.0
import { readFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createInterface } from 'node:readline';
export const root = new URL('../../../', import.meta.url);
const openapi = JSON.parse(readFileSync(new URL('specs/openapi/object-exchange/v1/openapi.yaml', root)));
const identity = Object.fromEntries(openapi['x-fnb-protocol-schemas'].map(item => [item.schema.split('/').at(-1), item.identity_field]));
export function world(name = 'basic-memory') {
  const source = JSON.parse(readFileSync(new URL(`tests/fixtures/generated/${name}.seed-42.json`, root)));
  const objects = Object.entries(source.objects).map(([key, object]) => ({ schema: `https://raw.githubusercontent.com/FNB2026/fnb-open/v0.1.0-preview.1/specs/v0.1/${source.object_schemas[key]}`, object }));
  const validation_contexts = source.validation.map(context => {
    const roles = context.kind === 'invalidation_chain'
      ? { records: context.records.map(key => source.objects[key].invalidation_id) }
      : Object.fromEntries(Object.entries(context.members).map(([role, key]) => [role, source.objects[key][identity[source.object_schemas[key]]]]));
    return { kind: context.kind, roles };
  });
  return { transport_version: '1.0', protocol_release: 'v0.1.0-preview.1', exchange_id: ' synthetic SDK ☕ ', objects, validation_contexts };
}
export function receipt(request = world(), status = 'accepted') {
  return { transport_version: request.transport_version, protocol_release: request.protocol_release, exchange_id: request.exchange_id, status };
}
export function independent(request) {
  const replacements = new Map(request.objects.map(item => {
    const key = identity[item.schema.split('/').at(-1)];
    return [item.object[key], item.object[key] + '_second'];
  }));
  function rewrite(value) {
    if (typeof value === 'string') return replacements.get(value) ?? value;
    if (Array.isArray(value)) return value.map(rewrite);
    if (value !== null && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, rewrite(item)]));
    return value;
  }
  return rewrite(request);
}
export async function httpHarness(test, respond) {
  const sockets = new Set();
  const server = createServer(respond);
  server.on('connection', socket => { sockets.add(socket); socket.on('close', () => sockets.delete(socket)); });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  test.after(async () => { for (const socket of sockets) socket.destroy(); await new Promise(resolve => server.close(resolve)); });
  return `http://127.0.0.1:${server.address().port}/exchange`;
}
export function send(response, body, status = 200, media = status === 200 ? 'application/json' : 'application/problem+json', headers = {}) {
  response.writeHead(status, { 'Content-Type': media, ...headers });
  response.end(typeof body === 'string' || body instanceof Uint8Array ? body : JSON.stringify(body));
}
export async function mockProcess(test, mode = 'normal', noDependencies = false) {
  const python = process.env.FNB_TEST_PYTHON;
  if (!python) throw new Error('FNB_TEST_PYTHON must select hash-locked Python environment');
  const child = spawn(python, [...(noDependencies ? ['-S'] : []), new URL('mock-process.py', import.meta.url).pathname, '--mode', mode], { stdio: ['ignore', 'pipe', 'pipe'] });
  let errors = '';
  child.stderr.on('data', chunk => { errors += chunk; });
  const lines = createInterface({ input: child.stdout });
  const startup = setTimeout(() => child.kill(), 5000);
  let exited = false;
  child.on('exit', () => { exited = true; });
  test.after(async () => {
    lines.close(); clearTimeout(startup);
    if (!exited) { child.kill(); await once(child, 'exit'); }
  });
  const line = await Promise.race([once(lines, 'line').then(([line]) => line), once(child, 'exit').then(() => { throw new Error('Mock failed: ' + errors); })]);
  clearTimeout(startup);
  return `http://127.0.0.1:${JSON.parse(line).port}/exchange`;
}
