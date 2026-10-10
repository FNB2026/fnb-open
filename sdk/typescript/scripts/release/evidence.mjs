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
import { execFileSync } from 'node:child_process';
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { ALLOWLIST, readTarGz, verifyArchive, sha256 } from './archive.mjs';

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../../../..');
export const PACKAGE_DIR = join(ROOT, 'sdk/typescript');
export const MANIFEST_NAME = 'artifact-digests.json';
export const MANIFEST_SCHEMA = 'fnb-sdk-release-artifact-digests/v1';
export const PROVENANCE_NAME = 'release-provenance.json';
export const SBOM_NAME = 'release-sbom.spdx.json';
export const PROVENANCE_SCHEMA = 'fnb-sdk-release-provenance/v1';
export const TARBALL_NAME = 'fnb-object-exchange-ts-sdk-0.1.0-preview.1.tgz';
export const RELEASE_TAG = 'object-exchange-ts-sdk-v0.1.0-preview.1';
export const EVIDENCE_ASSETS = Object.freeze([
  TARBALL_NAME,
  PROVENANCE_NAME,
  SBOM_NAME,
  'RELEASE-NOTES.md',
  'LICENSE-APACHE-2.0.txt',
  'NOTICE.md',
]);
const HEX40 = /^[0-9a-f]{40}$/;
const HEX64 = /^[0-9a-f]{64}$/;
const bytes = path => readFileSync(path);
const digestOf = path => sha256(bytes(path));
const stable = value => `${JSON.stringify(value, null, 2)}\n`;
const isHex = (value, pattern) => typeof value === 'string' && pattern.test(value);

function toolVersion(command, args) {
  try { return execFileSync(command, args, { encoding: 'utf8' }).trim(); } catch { return null; }
}

function runValidator(command, args) {
  execFileSync(command, args, { stdio: 'inherit' });
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
  const pkg = JSON.parse(readFileSync(join(PACKAGE_DIR, 'package.json'), 'utf8'));
  const assets = EVIDENCE_ASSETS.map(name => ({ filename: name, byteLength: bytes(join(directory, name)).length, sha256: digestOf(join(directory, name)) }))
    .sort((left, right) => (left.filename < right.filename ? -1 : 1));
  return {
    schemaVersion: MANIFEST_SCHEMA,
    releaseTag: RELEASE_TAG,
    commit,
    selfExcluded: MANIFEST_NAME,
    assets,
    package: {
      name: pkg.name,
      version: pkg.version,
      private: pkg.private,
      license: pkg.license,
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

// Strictly verifies a generated evidence bundle. Everything is treated as a
// closed set: missing, duplicate, extra or renamed assets/members, malformed
// entries, digest/length drift, and any disagreement with the external
// provenance are all failures. It never infers success from a partial match.
export function verifyBundle({ directory }) {
  const errors = [];
  const manifestPath = join(directory, MANIFEST_NAME);
  if (!existsSync(manifestPath)) return { ok: false, errors: [`missing ${MANIFEST_NAME}`] };
  let manifest;
  try { manifest = JSON.parse(readFileSync(manifestPath, 'utf8')); }
  catch (error) { return { ok: false, errors: [`${MANIFEST_NAME} is not valid JSON: ${error.message}`] }; }

  // Closed set of bundle files.
  const present = readdirSync(directory).sort();
  const expected = [...EVIDENCE_ASSETS, MANIFEST_NAME].sort();
  for (const name of expected) if (!present.includes(name)) errors.push(`missing evidence asset: ${name}`);
  for (const name of present) if (!expected.includes(name)) errors.push(`unexpected file in evidence bundle: ${name}`);

  // Manifest header identity.
  if (manifest.schemaVersion !== MANIFEST_SCHEMA) errors.push(`manifest schemaVersion is not ${MANIFEST_SCHEMA}`);
  if (manifest.selfExcluded !== MANIFEST_NAME) errors.push('manifest must exclude itself');
  if (manifest.releaseTag !== RELEASE_TAG) errors.push(`manifest releaseTag is not ${RELEASE_TAG}`);
  if (!isHex(manifest.commit, HEX40)) errors.push('manifest commit is not a 40-hex commit id');

  // Assets: closed set with no missing, duplicate, extra or malformed entries.
  const assets = Array.isArray(manifest.assets) ? manifest.assets : [];
  if (!Array.isArray(manifest.assets)) errors.push('manifest assets is not an array');
  if (assets.length !== EVIDENCE_ASSETS.length) errors.push(`manifest asset count ${assets.length} != ${EVIDENCE_ASSETS.length}`);
  const assetNames = assets.map(asset => asset?.filename);
  if (new Set(assetNames).size !== assetNames.length) errors.push('manifest lists duplicate asset entries');
  for (const name of EVIDENCE_ASSETS) if (!assetNames.includes(name)) errors.push(`manifest is missing an asset entry: ${name}`);
  for (const name of assetNames) if (!EVIDENCE_ASSETS.includes(name)) errors.push(`manifest lists an unknown asset: ${name}`);
  for (const asset of assets) {
    if (typeof asset?.filename !== 'string' || !isHex(asset?.sha256, HEX64) || !Number.isInteger(asset?.byteLength) || asset.byteLength < 0) {
      errors.push(`malformed manifest asset entry: ${JSON.stringify(asset?.filename)}`);
      continue;
    }
    if (!EVIDENCE_ASSETS.includes(asset.filename) || !present.includes(asset.filename)) continue;
    const data = bytes(join(directory, asset.filename));
    if (data.length !== asset.byteLength) errors.push(`asset byte length mismatch: ${asset.filename}`);
    if (sha256(data) !== asset.sha256) errors.push(`asset sha256 mismatch: ${asset.filename}`);
  }

  // Package inventory: closed set equal to the 28-path allowlist.
  const pkg = manifest.package ?? {};
  if (pkg.tarball !== TARBALL_NAME) errors.push(`manifest tarball identity is not ${TARBALL_NAME}`);
  if (pkg.memberCount !== ALLOWLIST.length) errors.push(`manifest memberCount ${pkg.memberCount} != ${ALLOWLIST.length}`);
  const members = Array.isArray(pkg.members) ? pkg.members : [];
  if (!Array.isArray(pkg.members)) errors.push('manifest package.members is not an array');
  if (members.length !== ALLOWLIST.length) errors.push(`manifest member count ${members.length} != closed allowlist ${ALLOWLIST.length}`);
  const memberPaths = members.map(member => member?.path);
  if (new Set(memberPaths).size !== memberPaths.length) errors.push('manifest lists duplicate members');
  for (const path of ALLOWLIST) if (!memberPaths.includes(path)) errors.push(`manifest is missing an allowlisted member: ${path}`);
  for (const path of memberPaths) if (!ALLOWLIST.includes(path)) errors.push(`manifest member is outside the closed allowlist: ${path}`);

  // Members must match the actual archive bytes and the manifest digests.
  const tarballPath = join(directory, TARBALL_NAME);
  let parsed = null;
  const archiveBytes = new Map();
  if (existsSync(tarballPath)) {
    const entries = readTarGz(bytes(tarballPath));
    parsed = verifyArchive(entries);
    if (!parsed.ok) errors.push(...parsed.errors);
    for (const entry of entries) {
      if (entry.typeflag === '0' || entry.typeflag === '\0') archiveBytes.set(entry.name.replace(/^package\//, ''), entry.data);
    }
  }
  for (const member of members) {
    if (typeof member?.path !== 'string' || !isHex(member?.sha256, HEX64) || !Number.isInteger(member?.size) || member.size < 0) {
      errors.push(`malformed manifest member entry: ${JSON.stringify(member?.path)}`);
      continue;
    }
    if (!ALLOWLIST.includes(member.path) || !parsed) continue;
    const match = parsed.members.find(candidate => candidate.path === member.path);
    if (match && (match.size !== member.size || match.sha256 !== member.sha256)) errors.push(`manifest member digest differs from archive: ${member.path}`);
  }

  // The declared identity must match the package.json actually inside the archive,
  // so tampering the manifest and provenance together (with refreshed asset
  // digests) still fails: the archived bytes are not under the attacker's control.
  const archivedPackageJson = archiveBytes.get('package.json');
  if (archivedPackageJson) {
    let identity = null;
    try { identity = JSON.parse(archivedPackageJson.toString('utf8')); }
    catch (error) { errors.push(`archived package.json is not valid JSON: ${error.message}`); }
    if (identity) {
      for (const key of ['name', 'version', 'private', 'license']) {
        if (identity[key] !== pkg[key]) errors.push(`archived package.json ${key} (${JSON.stringify(identity[key])}) differs from the manifest (${JSON.stringify(pkg[key])})`);
      }
    }
  } else if (parsed) {
    errors.push('archive does not contain package.json for identity binding');
  }

  // External LICENSE/NOTICE copies must be byte-identical to the packaged files.
  for (const name of ['LICENSE-APACHE-2.0.txt', 'NOTICE.md']) {
    const inside = archiveBytes.get(name);
    if (inside && existsSync(join(directory, name)) && !inside.equals(bytes(join(directory, name)))) {
      errors.push(`external ${name} differs from the packaged copy`);
    }
  }

  // Cross-check manifest identity against the external provenance.
  let provenance = null;
  const provenancePath = join(directory, PROVENANCE_NAME);
  if (existsSync(provenancePath)) {
    try { provenance = JSON.parse(readFileSync(provenancePath, 'utf8')); }
    catch (error) { errors.push(`${PROVENANCE_NAME} is not valid JSON: ${error.message}`); }
    if (provenance) {
      if (provenance.schemaVersion !== PROVENANCE_SCHEMA) errors.push(`provenance schemaVersion is not ${PROVENANCE_SCHEMA}`);
      if (provenance.commit !== manifest.commit) errors.push('provenance commit differs from manifest commit');
      if (provenance.releaseTag !== manifest.releaseTag) errors.push('provenance releaseTag differs from manifest releaseTag');
      if (provenance.package?.tarball !== pkg.tarball) errors.push('provenance tarball identity differs from manifest');
      if (provenance.package?.name !== pkg.name) errors.push('provenance package name differs from manifest');
      if (provenance.package?.version !== pkg.version) errors.push('provenance package version differs from manifest');
      if (provenance.package?.private !== pkg.private) errors.push('provenance package private flag differs from manifest');
      if (provenance.package?.license !== pkg.license) errors.push('provenance package license differs from manifest');
    }
  }

  // External SBOM must describe exactly the real archive members (set and digests).
  const sbomPath = join(directory, SBOM_NAME);
  if (existsSync(sbomPath)) {
    let sbom = null;
    try { sbom = JSON.parse(readFileSync(sbomPath, 'utf8')); }
    catch (error) { errors.push(`${SBOM_NAME} is not valid JSON: ${error.message}`); }
    if (sbom && parsed) {
      const check = verifySbom(sbom, { members: parsed.members, packageName: pkg.name, version: pkg.version });
      for (const message of check.errors) errors.push(`SBOM: ${message}`);
    }
  }

  // No hash cycle: no listed asset may embed the manifest's own digest.
  const selfDigest = digestOf(manifestPath);
  for (const name of EVIDENCE_ASSETS) {
    if (existsSync(join(directory, name)) && bytes(join(directory, name)).includes(selfDigest)) errors.push(`asset embeds the manifest digest (cycle): ${name}`);
  }
  return { ok: errors.length === 0, errors };
}

// ------------------------------------------------------- tag / immutability policy

export const MANIFEST_DIGEST_LINE = /^manifest-sha256:\s*([0-9a-f]{64})$/m;

// READ-ONLY POLICY PREFLIGHT — NOT cryptographic signature verification.
//
// This only checks declared parameters: that a supplied tag message binds the
// expected manifest SHA-256 and that a supplied signer fingerprint appears in a
// supplied approved list. It does not open a tag object, run `git verify-tag`,
// check a GPG signature or establish key trust. A caller can pass any values, so
// a pass here is not evidence of authenticity. Real publication must independently
// verify the signed tag object and the trusted key identity; G15 stays
// BLOCKED/UNDECIDED until that identity is approved by a separate decision.
export function verifyTagBindingPolicy({ tagMessage, manifestSha256, signerFingerprint, approvedFingerprints }) {
  const errors = [];
  const match = MANIFEST_DIGEST_LINE.exec(tagMessage ?? '');
  if (!match) errors.push('tag message does not bind a manifest-sha256 line');
  else if (match[1] !== manifestSha256) errors.push('tag-bound manifest digest does not match the manifest');
  if (!signerFingerprint) errors.push('no signer fingerprint supplied');
  else if (!(approvedFingerprints ?? []).map(value => value.toUpperCase()).includes(signerFingerprint.toUpperCase())) errors.push('signer fingerprint is not in the supplied approved list');
  return { ok: errors.length === 0, errors, cryptographicVerification: false };
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
    const python = process.env.FNB_TEST_PYTHON ?? 'python3';
    const toolchain = {
      node: process.version,
      npm: toolVersion('npm', ['--version']),
      typescript: JSON.parse(readFileSync(join(PACKAGE_DIR, 'package-lock.json'), 'utf8')).packages['node_modules/typescript'].version,
      python: toolVersion(python, ['--version']),
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
    const directory = resolve(flags.get('dir'));
    const result = verifyBundle({ directory });
    for (const error of result.errors) process.stdout.write(`FAIL ${error}\n`);
    // Non-skippable independent SPDX schema validation of the external SBOM: the
    // command fails rather than silently skipping this step.
    const python = process.env.FNB_TEST_PYTHON;
    if (!python) {
      process.stdout.write('FAIL FNB_TEST_PYTHON is required to run the SPDX schema validation\n');
      return 1;
    }
    const validator = fileURLToPath(new URL('validate-sbom.py', import.meta.url));
    try { runValidator(python, [validator, join(directory, SBOM_NAME)]); }
    catch (error) { process.stdout.write(`FAIL SPDX schema validation failed: ${error.message}\n`); return 1; }
    process.stdout.write(result.ok ? 'release evidence bundle verified\n' : `release evidence bundle invalid (${result.errors.length})\n`);
    return result.ok ? 0 : 1;
  }
  process.stderr.write('usage: evidence.mjs generate --tarball <tgz> --out <dir> --commit <sha> --created <iso> [--ci <id>]\n       evidence.mjs verify --dir <dir>\n');
  return 2;
}

if (process.argv[1] && import.meta.url === `file://${resolve(process.argv[1])}`) process.exit(main(process.argv.slice(2)));
