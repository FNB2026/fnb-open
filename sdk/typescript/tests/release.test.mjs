// SPDX-License-Identifier: Apache-2.0
// Release-preparation tests: closed package allowlist, external evidence bundle,
// SPDX 2.3 SBOM and signed-tag/immutable-release policy. Nothing here publishes.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { ALLOWLIST, readTarGz, verifyArchive, writeTarGz } from '../scripts/release/archive.mjs';
import {
  EVIDENCE_ASSETS, MANIFEST_NAME, TARBALL_NAME, checkImmutableReleases, generateBundle, verifyBundle, verifyTagBinding,
} from '../scripts/release/evidence.mjs';

const cwd = new URL('../', import.meta.url).pathname;
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const scratchRoots = [];
function scratch(prefix) {
  const folder = mkdtempSync(join(tmpdir(), prefix));
  scratchRoots.push(folder);
  return folder;
}
function command(executable, args, folder = cwd) {
  const result = spawnSync(executable, args, { cwd: folder, encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr + result.stdout);
  return result.stdout;
}
test.after(() => { for (const folder of scratchRoots) rmSync(folder, { recursive: true, force: true }); });

test('A41: closed 28-path allowlist rejects extra, missing, duplicate, unsafe and traversal members', () => {
  const good = ALLOWLIST.map(path => ({ name: `package/${path}`, mode: 0o644, typeflag: '0', size: 3, data: Buffer.from('hi\n') }));
  const accepted = verifyArchive(good);
  assert.equal(accepted.ok, true, accepted.errors.join('\n'));
  assert.equal(accepted.members.length, 28);
  const last = good.at(-1);
  const rejections = {
    extra: [...good, { name: 'package/dist/extra.js', mode: 0o644, typeflag: '0', size: 1, data: Buffer.from('x') }],
    missing: good.slice(1),
    duplicate: [...good, good[0]],
    traversal: [...good.slice(0, 27), { ...last, name: 'package/../evil.js' }],
    absolute: [...good.slice(0, 27), { ...last, name: '/etc/passwd' }],
    symlink: [...good.slice(0, 27), { ...last, typeflag: '2' }],
    hardlink: [...good.slice(0, 27), { ...last, typeflag: '1' }],
    setuid: [...good.slice(0, 27), { ...last, mode: 0o4755 }],
    worldWritable: [...good.slice(0, 27), { ...last, mode: 0o666 }],
    outsideRoot: [...good.slice(0, 27), { ...last, name: 'package.json' }],
  };
  for (const [label, entries] of Object.entries(rejections)) {
    assert.equal(verifyArchive(entries).ok, false, `${label} must be rejected`);
  }
  // A hand-built tar that does not carry the npm `package/` root must not pass either.
  const foreign = readTarGz(writeTarGz([{ name: 'a.txt', mode: 0o644, data: Buffer.from('x') }]));
  assert.equal(verifyArchive(foreign).ok, false);
});

test('A42: real candidate pack is exactly the allowlist and two isolated packs agree byte-for-byte', () => {
  command('npm', ['run', 'build']);
  const packs = [];
  for (let index = 0; index < 2; index++) {
    const folder = scratch(`fnb-release-pack-${index}-`);
    const info = JSON.parse(command('npm', ['pack', '--offline', '--json', '--ignore-scripts', '--pack-destination', folder]))[0];
    const tarball = readFileSync(join(folder, info.filename));
    const parsed = verifyArchive(readTarGz(tarball));
    assert.equal(parsed.ok, true, parsed.errors.join('\n'));
    packs.push({ sha256: digest(tarball), members: parsed.members });
  }
  assert.equal(packs[0].sha256, packs[1].sha256);
  assert.deepEqual(packs[0].members, packs[1].members);
});

test('A43: external evidence bundle is self-excluding, verifiable and tamper-evident', () => {
  command('npm', ['run', 'build']);
  const packFolder = scratch('fnb-release-pack-');
  const info = JSON.parse(command('npm', ['pack', '--offline', '--json', '--ignore-scripts', '--pack-destination', packFolder]))[0];
  const out = scratch('fnb-release-evidence-');
  const created = '2026-10-11T00:00:00Z';
  const commit = '0'.repeat(40);
  generateBundle({
    tarballPath: join(packFolder, info.filename), outDir: out, commit, created,
    toolchain: { node: 'v22.23.3', npm: '10.9.9', typescript: '7.0.2', python: '3.12.13', os: process.platform, arch: process.arch },
  });
  assert.deepEqual(readdirSync(out).sort(), [...EVIDENCE_ASSETS, MANIFEST_NAME].sort());
  const manifest = JSON.parse(readFileSync(join(out, MANIFEST_NAME), 'utf8'));
  assert.equal(manifest.selfExcluded, MANIFEST_NAME);
  assert.ok(!manifest.assets.some(asset => asset.filename === MANIFEST_NAME));
  assert.equal(manifest.assets.length, EVIDENCE_ASSETS.length);
  assert.equal(manifest.package.memberCount, 28);
  assert.equal(manifest.commit, commit);
  assert.equal(manifest.package.tarball, TARBALL_NAME);
  assert.equal(verifyBundle({ directory: out }).ok, true);
  // Tampering with any listed asset must be detected by the recomputed digests.
  const victim = join(out, 'release-provenance.json');
  writeFileSync(victim, readFileSync(victim, 'utf8').replace('Apache-2.0', 'MIT'));
  const tampered = verifyBundle({ directory: out });
  assert.equal(tampered.ok, false);
  assert.ok(tampered.errors.some(error => error.includes('sha256 mismatch')));
});

test('A44: generated SPDX 2.3 SBOM matches the archive and validates against the vendored official schema', () => {
  const python = process.env.FNB_TEST_PYTHON;
  assert.ok(python, 'FNB_TEST_PYTHON must select the hash-locked Python environment');
  command('npm', ['run', 'build']);
  const packFolder = scratch('fnb-release-pack-');
  const info = JSON.parse(command('npm', ['pack', '--offline', '--json', '--ignore-scripts', '--pack-destination', packFolder]))[0];
  const out = scratch('fnb-release-evidence-');
  generateBundle({
    tarballPath: join(packFolder, info.filename), outDir: out, commit: '0'.repeat(40), created: '2026-10-11T00:00:00Z',
    toolchain: { node: 'v22.23.3', npm: '10.9.9', typescript: '7.0.2', python: '3.12.13', os: process.platform, arch: process.arch },
  });
  const sbomPath = join(out, 'release-sbom.spdx.json');
  const sbom = JSON.parse(readFileSync(sbomPath, 'utf8'));
  assert.equal(sbom.dataLicense, 'CC0-1.0');
  assert.equal(sbom.packages.find(item => item.SPDXID === 'SPDXRef-Package').filesAnalyzed, true);
  assert.ok(sbom.packages.some(item => item.SPDXID === 'SPDXRef-External-NodeRuntime'));
  assert.ok(sbom.packages.some(item => item.SPDXID === 'SPDXRef-External-Development'));
  assert.equal(sbom.files.length, 28);
  assert.equal(verifyBundle({ directory: out }).ok, true);
  command(python, ['scripts/release/validate-sbom.py', sbomPath]);
});

test('A45: signed-tag binding and immutable-release gates fail closed', () => {
  const manifestSha256 = 'a'.repeat(64);
  const approved = ['1986135564B368B8DD3B5C6FB4D67D6F06FADC54'];
  const message = `SDK preview candidate\n\nmanifest-sha256: ${manifestSha256}\n`;
  assert.equal(verifyTagBinding({ tagMessage: message, manifestSha256, signerFingerprint: approved[0], approvedFingerprints: approved }).ok, true);
  assert.equal(verifyTagBinding({ tagMessage: message, manifestSha256, signerFingerprint: 'B'.repeat(40), approvedFingerprints: approved }).ok, false);
  assert.equal(verifyTagBinding({ tagMessage: message, manifestSha256: 'b'.repeat(64), signerFingerprint: approved[0], approvedFingerprints: approved }).ok, false);
  assert.equal(verifyTagBinding({ tagMessage: 'unsigned candidate', manifestSha256, signerFingerprint: approved[0], approvedFingerprints: approved }).ok, false);
  assert.equal(verifyTagBinding({ tagMessage: message, manifestSha256, signerFingerprint: null, approvedFingerprints: approved }).ok, false);
  assert.equal(checkImmutableReleases({ enabled: true }).enabled, true);
  assert.equal(checkImmutableReleases({ enabled: false }).enabled, false);
  assert.equal(checkImmutableReleases(undefined).enabled, false);
});
