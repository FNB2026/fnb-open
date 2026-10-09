// SPDX-License-Identifier: Apache-2.0
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, mkdtempSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
const cwd = new URL('../', import.meta.url).pathname;
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
function command(executable, args, folder = cwd) {
  const result = spawnSync(executable, args, { cwd: folder, encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr + result.stdout);
  return result.stdout;
}
test('A35 A36 A37 A38: deterministic inputs, zero-runtime-dependency audit and offline packed ESM consumer', t => {
  const python = process.env.FNB_TEST_PYTHON;
  assert.ok(python);
  command(python, ['scripts/generate.py', '--check']);
  const before = readFileSync(join(cwd, 'src/generated/wire.ts'));
  command(python, ['scripts/generate.py']); command(python, ['scripts/generate.py']);
  assert.deepEqual(readFileSync(join(cwd, 'src/generated/wire.ts')), before);
  const source = ['src/index.ts', 'src/json.ts'].map(name => readFileSync(join(cwd, name), 'utf8')).join('\n');
  for (const forbidden of ['node:fs', 'node:http', 'node:https', 'axios', 'localStorage', 'WebSocket', 'XMLHttpRequest']) assert.ok(!source.includes(forbidden), forbidden);
  const pkg = JSON.parse(readFileSync(join(cwd, 'package.json')));
  assert.equal(pkg.private, true); assert.equal(pkg.dependencies, undefined); assert.equal(pkg.optionalDependencies, undefined);
  assert.equal(pkg.scripts.postinstall, undefined); assert.equal(pkg.scripts.prepare, undefined);
  const lock = JSON.parse(readFileSync(join(cwd, 'package-lock.json')));
  for (const [name, item] of Object.entries(lock.packages)) if (name) {
    assert.ok(item.dev); assert.ok(item.integrity.startsWith('sha512-')); assert.ok(item.resolved.startsWith('https://registry.npmjs.org/'));
    assert.ok(!item.hasInstallScript);
  }
  const sbom = JSON.parse(readFileSync(join(cwd, 'sbom.spdx.json'))); assert.equal(sbom.packages.length, Object.keys(lock.packages).length);
  const provenance = JSON.parse(readFileSync(join(cwd, 'provenance.json')));
  for (const [name, hash] of Object.entries(provenance.binding_sha256)) {
    assert.equal(digest(readFileSync(join(cwd, '../../', name))), hash);
    assert.equal(digest(readFileSync(join(cwd, 'src/generated/protocol/', name.split('/').at(-1)))), hash);
  }
  const scratch = mkdtempSync(join(tmpdir(), 'fnb-sdk-consumer-'));
  t.after(() => rmSync(scratch, { recursive: true, force: true })); // Exact fresh test-owned directory only.
  const packs = [];
  for (let index = 0; index < 2; index++) {
    command('npm', ['run', 'build']);
    const info = JSON.parse(command('npm', ['pack', '--offline', '--json', '--ignore-scripts', '--pack-destination', scratch]))[0];
    assert.ok(info.files.every(item => !/node_modules|tests\/|src\/|\.env|scripts\//.test(item.path)));
    for (const required of ['LICENSE-APACHE-2.0.txt', 'NOTICE.md', 'provenance.json', 'sbom.spdx.json', 'dist/index.js', 'dist/protocol.d.ts']) assert.ok(info.files.some(item => item.path === required), required);
    packs.push(digest(readFileSync(join(scratch, info.filename))));
  }
  assert.equal(packs[0], packs[1]);
  writeFileSync(join(scratch, 'package.json'), JSON.stringify({ name: 'synthetic-sdk-consumer', private: true, type: 'module' }));
  const tarball = readdirSync(scratch).find(name => name.endsWith('.tgz'));
  command('npm', ['install', '--offline', '--ignore-scripts', '--no-audit', '--no-fund', join(scratch, tarball)], scratch);
  writeFileSync(join(scratch, 'consumer.mjs'), `import { createExchangeClient } from 'fnb-object-exchange-sdk-workspace';\nconst c = createExchangeClient({endpoint:'http://127.0.0.1:8765/exchange'});\nif (typeof c.exchange !== 'function' || 'login' in c) throw Error('bad API');\n`);
  command(process.execPath, ['consumer.mjs'], scratch);
  writeFileSync(join(scratch, 'consumer.mts'), `import {createExchangeClient, type ObjectExchangeEnvelope} from 'fnb-object-exchange-sdk-workspace';\nimport type {Memory} from 'fnb-object-exchange-sdk-workspace/protocol';\ndeclare const memory: Memory;\nconst request: ObjectExchangeEnvelope = {transport_version:'1.0',protocol_release:'v0.1.0-preview.1',exchange_id:'synthetic',objects:[{schema:'opaque',object:memory}],validation_contexts:[]};\nvoid createExchangeClient({endpoint:'http://127.0.0.1:8765/exchange'}).exchange(request);\n`);
  command(join(cwd, 'node_modules/.bin/tsc'), ['--noEmit', '--strict', '--module', 'NodeNext', '--moduleResolution', 'NodeNext', '--target', 'ES2022', 'consumer.mts'], scratch);
  assert.ok(existsSync(join(scratch, 'node_modules/fnb-object-exchange-sdk-workspace/dist/generated/protocol/memory.d.ts')));
});
