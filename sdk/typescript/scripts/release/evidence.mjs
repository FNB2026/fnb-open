// SPDX-License-Identifier: Apache-2.0
// Release evidence tooling for the Object Exchange TypeScript SDK preview.
//
// This builds and verifies the *external* release evidence bundle described by the
// approved release boundary plan (§4-§5): the installable tarball, an external SPDX
// 2.3 SBOM for the actual archive, external provenance, release notes, byte-identical
// license/notice copies, and a self-excluding `artifact-digests.json` manifest.
//
// It never publishes: no tag, GitHub Release, registry call or credential is made.
// Evidence is written outside the tracked tree so the candidate source commit, the
// external provenance and any future signed tag cannot form a hash cycle.
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { copyFileSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readTarGz, verifyArchive, sha256 } from './archive.mjs';

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../../../..');
export const PACKAGE_DIR = join(ROOT, 'sdk/typescript');
export const MANIFEST_NAME = 'artifact-digests.json';
export const TARBALL_NAME = 'fnb-object-exchange-ts-sdk-0.1.0-preview.1.tgz';
export const RELEASE_TAG = 'object-exchange-ts-sdk-v0.1.0-preview.1';
export const EVIDENCE_ASSETS = Object.freeze([
  TARBALL_NAME,
  'release-provenance.json',
  'release-sbom.spdx.json',
  'RELEASE-NOTES.md',
  'LICENSE-APACHE-2.0.txt',
  'NOTICE.md',
]);
const bytes = path => readFileSync(path);
const digestOf = path => sha256(bytes(path));
const stable = value => `${JSON.stringify(value, null, 2)}\n`;

function toolVersion(command, args) {
  try { return execFileSync(command, args, { encoding: 'utf8' }).trim(); } catch { return null; }
}

// ---------------------------------------------------------------- SPDX 2.3 SBOM

export function buildSbom({ members, packageName, version, commit, nodeVersion, created }) {
  const namespace = `https://www.fnbapp.net/spdx/sdk-release/${sha256(`${packageName}@${version}:${commit}`)}`;
  const files = members.map((member, index) => ({
    SPDXID: `SPDXRef-File-${String(index + 1).padStart(2, '0')}`,
    fileName: `./${member.path}`,
    checksums: [
      { algorithm: 'SHA256', checksumValue: member.sha256 },
      { algorithm: 'SHA1', checksumValue: member.sha1 },
    ],
    licenseConcluded: 'Apache-2.0',
    licenseInfoInFiles: ['Apache-2.0'],
    copyrightText: 'NOASSERTION',
  }));
  const sdk = {
    SPDXID: 'SPDXRef-Package',
    name: packageName,
    versionInfo: version,
    downloadLocation: 'NOASSERTION',
    filesAnalyzed: true,
    licenseConcluded: 'Apache-2.0',
    licenseDeclared: 'Apache-2.0',
    copyrightText: 'NOASSERTION',
    comment: 'GitHub Preview candidate archive; not published to any package registry.',
  };
  const runtime = {
    SPDXID: 'SPDXRef-External-NodeRuntime',
    name: 'Node.js runtime (external, consumer supplied)',
    versionInfo: nodeVersion ?? 'NOASSERTION',
    downloadLocation: 'https://nodejs.org/',
    filesAnalyzed: false,
    licenseDeclared: 'MIT',
    copyrightText: 'NOASSERTION',
    comment: 'External runtime not contained in this archive; supplied by the consumer.',
  };
  const development = {
    SPDXID: 'SPDXRef-External-Development',
    name: 'typescript',
    versionInfo: '7.0.2',
    downloadLocation: 'https://registry.npmjs.org/typescript/-/typescript-7.0.2.tgz',
    filesAnalyzed: false,
    licenseDeclared: 'Apache-2.0',
    copyrightText: 'NOASSERTION',
    comment: 'Build/development dependency; not shipped in the archive and not a runtime dependency.',
  };
  const relationships = [
    { spdxElementId: 'SPDXRef-DOCUMENT', relationshipType: 'DESCRIBES', relatedSpdxElement: sdk.SPDXID },
    { spdxElementId: runtime.SPDXID, relationshipType: 'RUNTIME_DEPENDENCY_OF', relatedSpdxElement: sdk.SPDXID },
    { spdxElementId: development.SPDXID, relationshipType: 'BUILD_DEPENDENCY_OF', relatedSpdxElement: sdk.SPDXID },
    ...files.map(file => ({ spdxElementId: sdk.SPDXID, relationshipType: 'CONTAINS', relatedSpdxElement: file.SPDXID })),
  ];
  return {
    spdxVersion: 'SPDX-2.3',
    dataLicense: 'CC0-1.0',
    SPDXID: 'SPDXRef-DOCUMENT',
    name: `${packageName} ${version} release archive`,
    documentNamespace: namespace,
    creationInfo: { created, creators: ['Tool: fnb-open-sdk-release-tooling'] },
    packages: [sdk, runtime, development],
    files,
    relationships,
  };
}

// Structural self-consistency of a generated SBOM against the archive members.
export function verifySbom(sbom, { members, packageName, version }) {
  const errors = [];
  if (sbom.spdxVersion !== 'SPDX-2.3' || sbom.dataLicense !== 'CC0-1.0') errors.push('not an SPDX 2.3 / CC0-1.0 document');
  if (sbom.SPDXID !== 'SPDXRef-DOCUMENT') errors.push('document SPDXID must be SPDXRef-DOCUMENT');
  const sdk = (sbom.packages ?? []).find(item => item.SPDXID === 'SPDXRef-Package');
  if (!sdk) errors.push('missing SPDXRef-Package');
  else if (sdk.name !== packageName || sdk.versionInfo !== version) errors.push('package identity mismatch with tarball');
  const listed = new Map((sbom.files ?? []).map(file => [file.fileName.replace(/^\.\//, ''), file]));
  if (listed.size !== members.length) errors.push(`file count ${listed.size} != archive member count ${members.length}`);
  for (const member of members) {
    const file = listed.get(member.path);
    if (!file) { errors.push(`SBOM missing archive member: ${member.path}`); continue; }
    const sha = (file.checksums ?? []).find(item => item.algorithm === 'SHA256');
    if (!sha || sha.checksumValue !== member.sha256) errors.push(`SBOM SHA256 mismatch for ${member.path}`);
  }
  for (const name of listed.keys()) if (!members.some(member => member.path === name)) errors.push(`SBOM lists a non-archived file: ${name}`);
  const ids = new Set([...(sbom.packages ?? []), ...(sbom.files ?? [])].map(item => item.SPDXID));
  for (const relation of sbom.relationships ?? []) {
    if (!ids.has(relation.spdxElementId) && relation.spdxElementId !== 'SPDXRef-DOCUMENT') errors.push(`relationship source not defined: ${relation.spdxElementId}`);
    if (!ids.has(relation.relatedSpdxElement)) errors.push(`relationship target not defined: ${relation.relatedSpdxElement}`);
  }
  return { ok: errors.length === 0, errors };
}

// ------------------------------------------------------------ external provenance

export function buildProvenance({ commit, toolchain, ciRun = null }) {
  const embedded = JSON.parse(readFileSync(join(PACKAGE_DIR, 'provenance.json'), 'utf8'));
  const pkg = JSON.parse(readFileSync(join(PACKAGE_DIR, 'package.json'), 'utf8'));
  return {
    schemaVersion: 'fnb-sdk-release-provenance/v1',
    repository: 'FNB2026/fnb-open',
    commit,
    releaseTag: RELEASE_TAG,
    publication: { path: 'A-github-preview', authorized: false, note: 'Prepared only; no tag, release or registry publication is authorized.' },
    package: { name: pkg.name, version: pkg.version, private: pkg.private, license: pkg.license, tarball: TARBALL_NAME },
    toolchain,
    locks: {
      packageLock: { path: 'sdk/typescript/package-lock.json', sha256: digestOf(join(PACKAGE_DIR, 'package-lock.json')) },
      pythonRequirements: { path: 'tools/requirements-validation.lock', sha256: digestOf(join(ROOT, 'tools/requirements-validation.lock')) },
    },
    upstream: {
      schemaRelease: embedded.schema_release,
      transportTag: embedded.transport_tag,
      bindingSnapshotCommit: embedded.binding_snapshot_commit,
      transportManifestSha256: embedded.transport_manifest_sha256,
      declarationSha256: embedded.binding_sha256,
      canonicalSchemaIds: embedded.canonical_schema_ids,
    },
    build: {
      commands: [
        'python3 sdk/typescript/scripts/generate.py --check',
        'npm ci --prefix sdk/typescript --ignore-scripts --no-audit --no-fund',
        'npm run build --prefix sdk/typescript',
        'npm run typecheck --prefix sdk/typescript',
        'npm test --prefix sdk/typescript',
        'npm pack --prefix sdk/typescript',
      ],
      ciRun,
    },
    notes: 'External provenance for the release candidate. It references the candidate source commit; the commit does not contain this file, so no hash cycle exists with provenance, the digest manifest or a future signed tag. No local absolute paths, credentials or private inputs are recorded.',
  };
}

// ------------------------------------------------------- self-excluding manifest

export function buildManifest({ directory, commit, members }) {
  const assets = EVIDENCE_ASSETS.map(name => ({ filename: name, byteLength: bytes(join(directory, name)).length, sha256: digestOf(join(directory, name)) }))
    .sort((left, right) => (left.filename < right.filename ? -1 : 1));
  return {
    schemaVersion: 'fnb-sdk-release-artifact-digests/v1',
    releaseTag: RELEASE_TAG,
    commit,
    selfExcluded: MANIFEST_NAME,
    assets,
    package: {
      tarball: TARBALL_NAME,
      memberCount: members.length,
      members: members.map(member => ({ path: member.path, size: member.size, sha256: member.sha256 })),
    },
    hashCycle: 'none: this manifest is excluded from its own asset list, is not committed into the source tree, and is not referenced by any asset it lists.',
  };
}

// ----------------------------------------------------------------- bundle writer

export function generateBundle({ tarballPath, outDir, commit, created, toolchain, ciRun = null }) {
  const archiveBytes = bytes(tarballPath);
  const parsed = verifyArchive(readTarGz(archiveBytes));
  if (!parsed.ok) throw new Error(`tarball rejected by the closed allowlist:\n${parsed.errors.join('\n')}`);
  const pkg = JSON.parse(readFileSync(join(PACKAGE_DIR, 'package.json'), 'utf8'));
  mkdirSync(outDir, { recursive: true });
  copyFileSync(tarballPath, join(outDir, TARBALL_NAME));
  copyFileSync(join(PACKAGE_DIR, 'LICENSE-APACHE-2.0.txt'), join(outDir, 'LICENSE-APACHE-2.0.txt'));
  copyFileSync(join(PACKAGE_DIR, 'NOTICE.md'), join(outDir, 'NOTICE.md'));
  copyFileSync(join(PACKAGE_DIR, 'RELEASE-NOTES.md'), join(outDir, 'RELEASE-NOTES.md'));
  const sbom = buildSbom({ members: parsed.members, packageName: pkg.name, version: pkg.version, commit, nodeVersion: toolchain?.node ?? null, created });
  const sbomCheck = verifySbom(sbom, { members: parsed.members, packageName: pkg.name, version: pkg.version });
  if (!sbomCheck.ok) throw new Error(`generated SBOM is inconsistent:\n${sbomCheck.errors.join('\n')}`);
  writeFileSync(join(outDir, 'release-sbom.spdx.json'), stable(sbom));
  writeFileSync(join(outDir, 'release-provenance.json'), stable(buildProvenance({ commit, toolchain, ciRun })));
  writeFileSync(join(outDir, MANIFEST_NAME), stable(buildManifest({ directory: outDir, commit, members: parsed.members })));
  return { members: parsed.members, tarballSha256: sha256(archiveBytes) };
}

// ----------------------------------------------------------------- bundle verify

export function verifyBundle({ directory }) {
  const errors = [];
  const manifestPath = join(directory, MANIFEST_NAME);
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  const present = readdirSync(directory).sort();
  const expected = [...EVIDENCE_ASSETS, MANIFEST_NAME].sort();
  for (const name of expected) if (!present.includes(name)) errors.push(`missing evidence asset: ${name}`);
  for (const name of present) if (!expected.includes(name)) errors.push(`unexpected file in evidence bundle: ${name}`);
  if (manifest.selfExcluded !== MANIFEST_NAME) errors.push('manifest must exclude itself');
  if ((manifest.assets ?? []).some(asset => asset.filename === MANIFEST_NAME)) errors.push('manifest lists itself as an asset');
  for (const asset of manifest.assets ?? []) {
    const path = join(directory, asset.filename);
    if (!present.includes(asset.filename)) continue;
    const data = bytes(path);
    if (data.length !== asset.byteLength) errors.push(`byte length mismatch: ${asset.filename}`);
    if (sha256(data) !== asset.sha256) errors.push(`sha256 mismatch: ${asset.filename}`);
  }
  const tarball = join(directory, TARBALL_NAME);
  const parsed = verifyArchive(readTarGz(bytes(tarball)));
  if (!parsed.ok) errors.push(...parsed.errors);
  if (parsed.members.length !== manifest.package?.memberCount) errors.push('tarball member count differs from manifest');
  for (const member of manifest.package?.members ?? []) {
    const match = parsed.members.find(candidate => candidate.path === member.path);
    if (!match) { errors.push(`manifest member not in tarball: ${member.path}`); continue; }
    if (match.size !== member.size || match.sha256 !== member.sha256) errors.push(`manifest member digest mismatch: ${member.path}`);
  }
  // No hash cycle: no listed asset may embed the manifest's own digest.
  const selfDigest = digestOf(manifestPath);
  for (const name of EVIDENCE_ASSETS) {
    if (bytes(join(directory, name)).includes(selfDigest)) errors.push(`asset embeds the manifest digest (cycle): ${name}`);
  }
  return { ok: errors.length === 0, errors };
}

// ------------------------------------------------------- tag / immutability policy

export const MANIFEST_DIGEST_LINE = /^manifest-sha256:\s*([0-9a-f]{64})$/m;

// Dry-run of the future signed annotated tag binding. Verifies the tag message
// binds the manifest SHA-256 and that the signer fingerprint was independently
// approved. It creates nothing and cannot be satisfied by an unsigned tag.
export function verifyTagBinding({ tagMessage, manifestSha256, signerFingerprint, approvedFingerprints }) {
  const errors = [];
  const match = MANIFEST_DIGEST_LINE.exec(tagMessage ?? '');
  if (!match) errors.push('tag message does not bind a manifest-sha256 line');
  else if (match[1] !== manifestSha256) errors.push('tag-bound manifest digest does not match the manifest');
  if (!signerFingerprint) errors.push('no signer fingerprint supplied');
  else if (!(approvedFingerprints ?? []).map(value => value.toUpperCase()).includes(signerFingerprint.toUpperCase())) errors.push('signer fingerprint is not independently approved');
  return { ok: errors.length === 0, errors };
}

// Interprets the read-only GitHub Immutable Releases API response.
export function checkImmutableReleases(payload) {
  const enabled = payload?.enabled === true;
  return { enabled, errors: enabled ? [] : ['repository Immutable Releases is not enabled'] };
}

// ------------------------------------------------------------------------- CLI

function main(argv) {
  const [command, ...rest] = argv;
  const flags = new Map();
  for (let index = 0; index < rest.length; index += 2) flags.set(rest[index].replace(/^--/, ''), rest[index + 1]);
  if (command === 'generate') {
    const toolchain = {
      node: process.version,
      npm: toolVersion('npm', ['--version']),
      typescript: JSON.parse(readFileSync(join(PACKAGE_DIR, 'package-lock.json'), 'utf8')).packages['node_modules/typescript'].version,
      python: toolVersion('python3', ['--version']),
      os: process.platform,
      arch: process.arch,
    };
    const result = generateBundle({
      tarballPath: resolve(flags.get('tarball')),
      outDir: resolve(flags.get('out')),
      commit: flags.get('commit'),
      created: flags.get('created'),
      toolchain,
      ciRun: flags.get('ci') ?? null,
    });
    process.stdout.write(`evidence written to ${resolve(flags.get('out'))}\ntarball sha256 ${result.tarballSha256}\nmembers ${result.members.length}\n`);
    return 0;
  }
  if (command === 'verify') {
    const result = verifyBundle({ directory: resolve(flags.get('dir')) });
    for (const error of result.errors) process.stdout.write(`FAIL ${error}\n`);
    process.stdout.write(result.ok ? 'release evidence bundle verified\n' : `release evidence bundle invalid (${result.errors.length})\n`);
    return result.ok ? 0 : 1;
  }
  process.stderr.write('usage: evidence.mjs generate --tarball <tgz> --out <dir> --commit <sha> --created <iso> [--ci <id>]\n       evidence.mjs verify --dir <dir>\n');
  return 2;
}

if (process.argv[1] && import.meta.url === `file://${resolve(process.argv[1])}`) process.exit(main(process.argv.slice(2)));
