// SPDX-License-Identifier: Apache-2.0
// Release archive integrity tooling: a dependency-free tar reader plus the
// closed 28-path package allowlist from the approved release boundary plan (§3).
// No network access and no third-party dependency is used here.
import { gunzipSync, gzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';

// Closed allowlist, relative to the tarball `package/` root. Extending this set
// requires an explicit, independently reviewed revision of the release plan.
export const ALLOWLIST = Object.freeze([
  'LICENSE-APACHE-2.0.txt',
  'NOTICE.md',
  'README.md',
  'package.json',
  'provenance.json',
  'sbom.spdx.json',
  'dist/index.js',
  'dist/index.d.ts',
  'dist/json.js',
  'dist/json.d.ts',
  'dist/protocol.js',
  'dist/protocol.d.ts',
  'dist/generated/wire.js',
  'dist/generated/wire.d.ts',
  'dist/generated/protocol/actor.d.ts',
  'dist/generated/protocol/ai-inference.d.ts',
  'dist/generated/protocol/asset.d.ts',
  'dist/generated/protocol/audit-tombstone.d.ts',
  'dist/generated/protocol/block-draft.d.ts',
  'dist/generated/protocol/block.d.ts',
  'dist/generated/protocol/correction-patch.d.ts',
  'dist/generated/protocol/flow-event.d.ts',
  'dist/generated/protocol/invalidation-record.d.ts',
  'dist/generated/protocol/memory.d.ts',
  'dist/generated/protocol/node.d.ts',
  'dist/generated/protocol/permission-snapshot.d.ts',
  'dist/generated/protocol/relationship.d.ts',
  'dist/generated/protocol/source-state-change.d.ts',
]);

export const REGULAR_MODE = 0o644;
const PREFIX = 'package/';
const BLOCK = 512;
const text = (buffer, start, end) => buffer.toString('utf8', start, end).replace(/\0.*$/, '').trim();
const octal = (buffer, start, end) => {
  const value = text(buffer, start, end);
  if (value === '') return 0;
  if (!/^[0-7]+$/.test(value)) throw new Error(`invalid tar octal field: ${JSON.stringify(value)}`);
  return parseInt(value, 8);
};
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const sha1 = bytes => createHash('sha1').update(bytes).digest('hex');

function headerChecksum(header) {
  let total = 0;
  for (let index = 0; index < BLOCK; index += 1) total += index >= 148 && index < 156 ? 0x20 : header[index];
  return total;
}

// Reads a gzipped tar archive into explicit entries. Rejects malformed headers,
// truncated members and non-regular member types rather than guessing.
export function readTarGz(buffer) {
  const raw = gunzipSync(buffer);
  const entries = [];
  let offset = 0;
  let longName = null;
  while (offset + BLOCK <= raw.length) {
    const header = raw.subarray(offset, offset + BLOCK);
    if (header.every(byte => byte === 0)) break;
    if (headerChecksum(header) !== octal(header, 148, 156)) throw new Error('tar header checksum mismatch');
    const size = octal(header, 124, 136);
    const typeflag = String.fromCharCode(header[156]);
    const body = raw.subarray(offset + BLOCK, offset + BLOCK + size);
    if (body.length !== size) throw new Error('truncated tar member');
    offset += BLOCK + Math.ceil(size / BLOCK) * BLOCK;
    if (typeflag === 'L') { longName = body.toString('utf8').replace(/\0.*$/, ''); continue; }
    const prefix = text(header, 345, 500);
    const base = longName ?? text(header, 0, 100);
    longName = null;
    const name = prefix ? `${prefix}/${base}` : base;
    entries.push({ name, mode: octal(header, 100, 108), typeflag, size, data: Buffer.from(body) });
  }
  if (longName !== null) throw new Error('dangling tar long name');
  return entries;
}

// Writes a gzipped tar archive (used by negative-path tests and tooling checks).
export function writeTarGz(entries) {
  const blocks = [];
  for (const entry of entries) {
    const name = Buffer.from(entry.name, 'utf8');
    const data = Buffer.from(entry.data ?? '');
    const header = Buffer.alloc(BLOCK);
    if (name.length > 100) throw new Error('test helper only supports short names');
    name.copy(header, 0);
    header.write((entry.mode ?? REGULAR_MODE).toString(8).padStart(7, '0'), 100, 'utf8');
    for (const [start, end, value] of [[108, 116, 0], [116, 124, 0], [136, 148, 0]]) header.write(value.toString(8).padStart(11, '0'), start, end, 'utf8');
    header.write(data.length.toString(8).padStart(11, '0'), 124, 136, 'utf8');
    header.write(entry.typeflag ?? '0', 156, 'utf8');
    header.write('ustar\0', 257, 'utf8');
    header.write('00', 263, 'utf8');
    header.write(headerChecksum(header).toString(8).padStart(6, '0') + '\0 ', 148, 'utf8');
    blocks.push(header, data, Buffer.alloc((BLOCK - (data.length % BLOCK)) % BLOCK));
  }
  blocks.push(Buffer.alloc(BLOCK * 2));
  return gzipSync(Buffer.concat(blocks), { level: 9 });
}

// Verifies an archive against the closed allowlist. Returns every violation it
// finds so a failure is diagnosable, and never treats a partial match as success.
// Member names must carry the single npm `package/` root, which is stripped so the
// allowlist stays expressed in reviewable package-relative paths.
export function verifyArchive(entries) {
  const errors = [];
  const seen = new Set();
  const members = [];
  for (const entry of entries) {
    const { mode, typeflag, size } = entry;
    if (typeflag !== '0' && typeflag !== '\0') errors.push(`non-regular member (typeflag ${JSON.stringify(typeflag)}): ${entry.name}`);
    if (entry.name.startsWith('/') || /^[A-Za-z]:[\\/]/.test(entry.name)) errors.push(`absolute path: ${entry.name}`);
    if (entry.name.split('/').includes('..')) errors.push(`traversal path: ${entry.name}`);
    if (entry.name.includes('\\')) errors.push(`backslash path: ${entry.name}`);
    if (!entry.name.startsWith(PREFIX)) { errors.push(`member outside the ${PREFIX} root: ${entry.name}`); continue; }
    const name = entry.name.slice(PREFIX.length);
    if (name.startsWith('/') || name.startsWith('./')) errors.push(`non-canonical path: ${entry.name}`);
    if (seen.has(name)) errors.push(`duplicate member: ${name}`);
    seen.add(name);
    if ((mode & 0o7000) !== 0) errors.push(`unsafe mode bits (setuid/setgid/sticky): ${name}`);
    if ((mode & 0o022) !== 0) errors.push(`group/world writable member: ${name}`);
    if (!ALLOWLIST.includes(name)) errors.push(`not in closed allowlist: ${name}`);
    members.push({ path: name, size, mode, sha256: sha256(entry.data), sha1: sha1(entry.data) });
  }
  for (const name of ALLOWLIST) if (!seen.has(name)) errors.push(`missing allowlisted member: ${name}`);
  members.sort((left, right) => (left.path < right.path ? -1 : left.path > right.path ? 1 : 0));
  return { ok: errors.length === 0, errors, members };
}

export { sha256, sha1 };
