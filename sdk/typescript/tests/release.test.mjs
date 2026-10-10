// SPDX-License-Identifier: Apache-2.0
// Release-preparation tests: closed package allowlist, strict tar framing,
// external evidence bundle, SPDX 2.3 SBOM and the tag/immutable policy preflight.
// Nothing here publishes.
import test from 'node:test';
import assert from 'node:assert/strict';
import { copyFileSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { gunzipSync, gzipSync } from 'node:zlib';
import { ALLOWLIST, readTarGz, verifyArchive, writeTarGz } from '../scripts/release/archive.mjs';
import {
  EVIDENCE_ASSETS, MANIFEST_NAME, TARBALL_NAME, checkImmutableReleases, generateBundle, verifyBundle, verifyTagBindingPolicy,
} from '../scripts/release/evidence.mjs';

const cwd = new URL('../', import.meta.url).pathname;
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const CANDIDATE = '0'.repeat(40);
const CREATED = '2026-10-11T00:00:00Z';
const TOOLCHAIN = { node: 'v22.23.3', npm: '10.9.9', typescript: '7.0.2', python: '3.12.13', os: 'test', arch: 'test' };
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

// Build and pack once per test process; every mutation test clones the bundle.
let bundleCache = null;
function baseBundle() {
  if (bundleCache) return bundleCache;
  command('npm', ['run', 'build']);
  const packFolder = scratch('fnb-release-pack-');
  const info = JSON.parse(command('npm', ['pack', '--offline', '--json', '--ignore-scripts', '--pack-destination', packFolder]))[0];
  const out = scratch('fnb-release-evidence-');
  generateBundle({ tarballPath: join(packFolder, info.filename), outDir: out, commit: CANDIDATE, created: CREATED, toolchain: TOOLCHAIN });
  bundleCache = { out, info, packFolder, tarballPath: join(packFolder, info.filename) };
  return bundleCache;
}
function cloneBundle() {
  const source = baseBundle().out;
  const target = scratch('fnb-release-evidence-copy-');
  for (const name of readdirSync(source)) copyFileSync(join(source, name), join(target, name));
  return target;
}
function mutateManifest(directory, mutate) {
  const path = join(directory, MANIFEST_NAME);
  const manifest = JSON.parse(readFileSync(path, 'utf8'));
  mutate(manifest);
  writeFileSync(path, `${JSON.stringify(manifest, null, 2)}\n`);
}

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
  const foreign = readTarGz(writeTarGz([{ name: 'a.txt', mode: 0o644, data: Buffer.from('x') }]));
  assert.equal(verifyArchive(foreign).ok, false);
});

test('A46: strict tar framing fails closed on truncation, padding and trailing data', () => {
  const entries = [{ name: 'package/a.txt', mode: 0o644, typeflag: '0', size: 3, data: Buffer.from('abc') }];
  const valid = gunzipSync(writeTarGz(entries));
  assert.equal(readTarGz(gzipSync(valid)).length, 1);
  // A valid npm pack archive must still parse under the stricter reader.
  const packed = gunzipSync(readFileSync(baseBundle().tarballPath));
  assert.equal(verifyArchive(readTarGz(gzipSync(packed))).ok, true);
  const cases = {
    'missing tar end-of-archive marker': valid.subarray(0, 1024),
    'truncated tar end-of-archive marker': valid.subarray(0, valid.length - 512),
    'non-zero data after tar end-of-archive marker': Buffer.concat([valid.subarray(0, valid.length - 1), Buffer.from([1])]),
    'truncated tar member': valid.subarray(0, 514),
  };
  for (const [message, raw] of Object.entries(cases)) {
    assert.throws(() => readTarGz(gzipSync(raw)), new RegExp(message), message);
  }
  const badPadding = Buffer.from(valid);
  badPadding[512 + 3] = 1; // first byte of the member's zero padding
  assert.throws(() => readTarGz(gzipSync(badPadding)), /non-zero member padding/);
});

test('A42: same-workspace pack determinism (NOT an independent-environment proof)', () => {
  // This runs one build and two packs in a single workspace, so it proves pack
  // determinism only. Independent clean-checkout reproducibility is demonstrated
  // separately by scripts/release/repro-check.mjs and recorded in the preparation
  // report with both environments, toolchains, lock hashes and real tarball SHA-256s.
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
  const out = cloneBundle();
  assert.deepEqual(readdirSync(out).sort(), [...EVIDENCE_ASSETS, MANIFEST_NAME].sort());
  const manifest = JSON.parse(readFileSync(join(out, MANIFEST_NAME), 'utf8'));
  assert.equal(manifest.selfExcluded, MANIFEST_NAME);
  assert.ok(!manifest.assets.some(asset => asset.filename === MANIFEST_NAME));
  assert.equal(manifest.assets.length, EVIDENCE_ASSETS.length);
  assert.equal(manifest.package.memberCount, 28);
  assert.equal(manifest.commit, CANDIDATE);
  assert.equal(manifest.package.tarball, TARBALL_NAME);
  assert.equal(verifyBundle({ directory: out }).ok, true);
  const victim = join(out, 'release-provenance.json');
  writeFileSync(victim, readFileSync(victim, 'utf8').replace('Apache-2.0', 'MIT'));
  const tampered = verifyBundle({ directory: out });
  assert.equal(tampered.ok, false);
  assert.ok(tampered.errors.some(error => error.includes('sha256 mismatch')));
});

test('A47: verifyBundle treats assets, members and provenance identity as closed sets', () => {
  assert.equal(verifyBundle({ directory: cloneBundle() }).ok, true);
  const cases = {
    'empty assets': manifest => { manifest.assets = []; },
    'empty members': manifest => { manifest.package.members = []; },
    'missing asset entry': manifest => { manifest.assets = manifest.assets.slice(1); },
    'duplicate asset entry': manifest => { manifest.assets = [...manifest.assets, manifest.assets[0]]; },
    'unknown asset name': manifest => { manifest.assets = [...manifest.assets.slice(1), { filename: 'extra.json', byteLength: 0, sha256: '0'.repeat(64) }]; },
    'renamed asset': manifest => { manifest.assets[0] = { ...manifest.assets[0], filename: 'renamed.tgz' }; },
    'tampered asset hash': manifest => { manifest.assets[0] = { ...manifest.assets[0], sha256: 'f'.repeat(64) }; },
    'tampered asset length': manifest => { manifest.assets[0] = { ...manifest.assets[0], byteLength: manifest.assets[0].byteLength + 1 }; },
    'missing member': manifest => { manifest.package.members = manifest.package.members.slice(1); },
    'duplicate member': manifest => { manifest.package.members = [...manifest.package.members, manifest.package.members[0]]; },
    'member outside allowlist': manifest => { manifest.package.members = [...manifest.package.members.slice(1), { path: 'dist/extra.js', size: 1, sha256: '0'.repeat(64) }]; },
    'tampered member hash': manifest => { manifest.package.members[0] = { ...manifest.package.members[0], sha256: 'a'.repeat(64) }; },
    'tampered member size': manifest => { manifest.package.members[0] = { ...manifest.package.members[0], size: manifest.package.members[0].size + 1 }; },
    'wrong member count': manifest => { manifest.package.memberCount = 27; },
    'wrong tarball identity': manifest => { manifest.package.tarball = 'other.tgz'; },
    'wrong release tag': manifest => { manifest.releaseTag = 'other-tag'; },
    'malformed commit': manifest => { manifest.commit = 'not-a-commit'; },
    'commit disagrees with provenance': manifest => { manifest.commit = '1'.repeat(40); },
  };
  for (const [label, mutate] of Object.entries(cases)) {
    const out = cloneBundle();
    mutateManifest(out, mutate);
    assert.equal(verifyBundle({ directory: out }).ok, false, `${label} must fail verification`);
  }
  // An unexpected extra file in the bundle is also a closed-set violation.
  const extra = cloneBundle();
  writeFileSync(join(extra, 'unexpected.txt'), 'x');
  assert.equal(verifyBundle({ directory: extra }).ok, false);
});

test('A44: generated SPDX 2.3 SBOM matches the archive and validates against the vendored official schema', () => {
  const python = process.env.FNB_TEST_PYTHON;
  assert.ok(python, 'FNB_TEST_PYTHON must select the hash-locked Python environment');
  const out = baseBundle().out;
  const sbomPath = join(out, 'release-sbom.spdx.json');
  const sbom = JSON.parse(readFileSync(sbomPath, 'utf8'));
  assert.equal(sbom.dataLicense, 'CC0-1.0');
  assert.equal(sbom.spdxVersion, 'SPDX-2.3');
  assert.equal(sbom.packages.find(item => item.SPDXID === 'SPDXRef-Package').filesAnalyzed, true);
  assert.ok(sbom.packages.some(item => item.SPDXID === 'SPDXRef-External-NodeRuntime'));
  assert.ok(sbom.packages.some(item => item.SPDXID === 'SPDXRef-External-Development'));
  assert.equal(sbom.files.length, 28);
  assert.equal(verifyBundle({ directory: out }).ok, true);
  command(python, ['scripts/release/validate-sbom.py', sbomPath]);
});

test('A45: tag-binding policy preflight and immutable-release gates fail closed (no crypto claim)', () => {
  const manifestSha256 = 'a'.repeat(64);
  const approved = ['1986135564B368B8DD3B5C6FB4D67D6F06FADC54'];
  const message = `SDK preview candidate\n\nmanifest-sha256: ${manifestSha256}\n`;
  const ok = verifyTagBindingPolicy({ tagMessage: message, manifestSha256, signerFingerprint: approved[0], approvedFingerprints: approved });
  assert.equal(ok.ok, true);
  // The preflight never claims cryptographic verification.
  assert.equal(ok.cryptographicVerification, false);
  assert.equal(verifyTagBindingPolicy({ tagMessage: message, manifestSha256, signerFingerprint: 'B'.repeat(40), approvedFingerprints: approved }).ok, false);
  assert.equal(verifyTagBindingPolicy({ tagMessage: message, manifestSha256: 'b'.repeat(64), signerFingerprint: approved[0], approvedFingerprints: approved }).ok, false);
  assert.equal(verifyTagBindingPolicy({ tagMessage: 'unsigned candidate', manifestSha256, signerFingerprint: approved[0], approvedFingerprints: approved }).ok, false);
  assert.equal(verifyTagBindingPolicy({ tagMessage: message, manifestSha256, signerFingerprint: null, approvedFingerprints: approved }).ok, false);
  assert.equal(checkImmutableReleases({ enabled: true }).enabled, true);
  assert.equal(checkImmutableReleases({ enabled: false }).enabled, false);
  assert.equal(checkImmutableReleases(undefined).enabled, false);
});
