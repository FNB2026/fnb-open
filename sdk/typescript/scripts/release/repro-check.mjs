// SPDX-License-Identifier: Apache-2.0
// Reproducibility evidence for the release candidate.
//
// Creates two independent detached checkouts of one commit, builds and packs in
// each with the same declared toolchain, and compares the tarball SHA-256 and the
// full 28-member inventory. It prints the environments, commands and real hashes
// so the result is independently reviewable. It publishes nothing.
//
//   FNB_TEST_PYTHON=/path/to/python node scripts/release/repro-check.mjs --commit <sha>
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { readTarGz, verifyArchive, sha256 } from './archive.mjs';

const ROOT = resolve(new URL('../../../..', import.meta.url).pathname);
const PACKAGE = join(ROOT, 'sdk/typescript');

function run(command, args, cwd) {
  return execFileSync(command, args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
}
function versionOf(command, args) {
  try { return run(command, args, ROOT).trim(); } catch { return null; }
}

function buildOnce(commit, label) {
  const checkout = mkdtempSync(join(tmpdir(), `fnb-repro-${label}-`));
  execFileSync('git', ['worktree', 'add', '--detach', checkout, commit], { cwd: ROOT, stdio: 'pipe' });
  const out = join(checkout, 'out');
  const sdk = join(checkout, 'sdk/typescript');
  const python = process.env.FNB_TEST_PYTHON;
  run('npm', ['ci', '--ignore-scripts', '--no-audit', '--no-fund'], sdk);
  if (python) run(python, ['scripts/generate.py', '--check'], sdk);
  run('npm', ['run', 'build'], sdk);
  run('npm', ['pack', '--pack-destination', out], sdk);
  const tarball = join(out, readdirSync(out).find(name => name.endsWith('.tgz')));
  const parsed = verifyArchive(readTarGz(readFileSync(tarball)));
  return { checkout, out, tarball, sha256: sha256(readFileSync(tarball)), ok: parsed.ok, errors: parsed.errors, members: parsed.members };
}

function main(argv) {
  const commit = argv[argv.indexOf('--commit') + 1];
  if (!commit) { process.stderr.write('usage: repro-check.mjs --commit <sha>\n'); return 2; }
  const keep = argv.includes('--keep');
  const results = [];
  try {
    for (const label of ['a', 'b']) results.push(buildOnce(commit, label));
  } finally {
    if (!keep) for (const result of results) {
      try { execFileSync('git', ['worktree', 'remove', '--force', result.checkout], { cwd: ROOT, stdio: 'pipe' }); } catch { /* best effort */ }
      rmSync(result.checkout, { recursive: true, force: true });
    }
  }
  const [first, second] = results;
  const membersEqual = JSON.stringify(first.members) === JSON.stringify(second.members);
  const reproducible = first.sha256 === second.sha256 && membersEqual && first.ok && second.ok;
  const report = {
    commit,
    toolchain: {
      node: versionOf(process.execPath, ['--version']),
      npm: versionOf('npm', ['--version']),
      python: process.env.FNB_TEST_PYTHON ? versionOf(process.env.FNB_TEST_PYTHON, ['--version']) : null,
      os: process.platform,
      arch: process.arch,
    },
    locks: {
      packageLockSha256: sha256(readFileSync(join(PACKAGE, 'package-lock.json'))),
      pythonRequirementsSha256: sha256(readFileSync(join(ROOT, 'tools/requirements-validation.lock'))),
    },
    commands: ['npm ci --ignore-scripts', 'python3 scripts/generate.py --check', 'npm run build', 'npm pack'],
    environments: results.map(result => ({ tarballSha256: result.sha256, memberCount: result.members.length, allowlistOk: result.ok })),
    membersEqual,
    reproducible,
  };
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  return reproducible ? 0 : 1;
}

if (process.argv[1] && import.meta.url === `file://${resolve(process.argv[1])}`) process.exit(main(process.argv.slice(2)));
