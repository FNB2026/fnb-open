// SPDX-License-Identifier: Apache-2.0
// Reproducibility evidence for the release candidate.
//
// Creates two independent detached checkouts of ONE resolved commit, builds and
// packs in each with the SAME declared toolchain, and compares the tarball
// SHA-256 and the full 28-member inventory. The declared environment is enforced:
// an executable hash-locked Python 3.12 interpreter is required, `generate.py
// --check` is never skipped, and Node/npm/TypeScript must match the pinned values,
// so two wrong-but-identical environments cannot return a compliant PASS.
//
//   FNB_TEST_PYTHON=/path/to/python node scripts/release/repro-check.mjs --commit <sha>
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, statSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { readTarGz, verifyArchive, sha256 } from './archive.mjs';

const ROOT = resolve(new URL('../../../..', import.meta.url).pathname);
const PACKAGE = join(ROOT, 'sdk/typescript');
const EXPECTED = { node: 'v22.23.3', npm: '10.9.9', typescript: '7.0.2', python: 'Python 3.12' };

function run(command, args, cwd) {
  return execFileSync(command, args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
}
function probe(command, args, cwd) {
  try { return run(command, args, cwd).trim(); } catch { return null; }
}
function fail(message) {
  process.stderr.write(`repro-check refused to run: ${message}\n`);
  process.exit(2);
}

// Resolve any revision to one full commit id; both checkouts must use exactly it.
function resolveCommit(revision) {
  const full = probe('git', ['rev-parse', '--verify', `${revision}^{commit}`], ROOT);
  if (!full || !/^[0-9a-f]{40}$/.test(full)) fail(`--commit did not resolve to a full commit id: ${revision}`);
  return full;
}

function resolvePython() {
  const python = process.env.FNB_TEST_PYTHON;
  if (!python) fail('FNB_TEST_PYTHON must point at an executable hash-locked Python 3.12 environment');
  if (!existsSync(python) || !(statSync(python).mode & 0o111)) fail(`FNB_TEST_PYTHON is not an executable file: ${python}`);
  const version = probe(python, ['--version'], ROOT);
  if (!version || !version.startsWith(EXPECTED.python)) fail(`Python must be ${EXPECTED.python}.x, found ${version}`);
  return { path: python, version };
}

function toolchainVersions(python) {
  const npm = probe('npm', ['--version'], ROOT);
  const typescript = JSON.parse(readFileSync(join(PACKAGE, 'package-lock.json'), 'utf8')).packages['node_modules/typescript'].version;
  if (process.version !== EXPECTED.node) fail(`Node must be ${EXPECTED.node}, found ${process.version}`);
  if (npm !== EXPECTED.npm) fail(`npm must be ${EXPECTED.npm}, found ${npm}`);
  if (typescript !== EXPECTED.typescript) fail(`TypeScript must be ${EXPECTED.typescript}, found ${typescript}`);
  return { node: process.version, npm, typescript, python: python.version };
}

function buildOnce(commit, label, python, commands, created) {
  const checkout = mkdtempSync(join(tmpdir(), `fnb-repro-${label}-`));
  created.push(checkout); // registered before worktree add so a failure still cleans up
  execFileSync('git', ['worktree', 'add', '--detach', checkout, commit], { cwd: ROOT, stdio: 'pipe' });
  const sdk = join(checkout, 'sdk/typescript');
  const out = join(checkout, 'out');
  mkdirSync(out, { recursive: true });
  run('npm', ['ci', '--ignore-scripts', '--no-audit', '--no-fund'], sdk);
  commands.add('npm ci --ignore-scripts');
  run(python.path, ['scripts/generate.py', '--check'], sdk); // never skipped
  commands.add('python3 scripts/generate.py --check');
  const checkedOut = probe('git', ['rev-parse', 'HEAD'], checkout);
  if (checkedOut !== commit) throw new Error(`checkout ${label} is at ${checkedOut}, not ${commit}`);
  run('npm', ['run', 'build'], sdk);
  commands.add('npm run build');
  run('npm', ['pack', '--pack-destination', out], sdk);
  commands.add('npm pack');
  const tarball = join(out, readdirSync(out).find(name => name.endsWith('.tgz')));
  const bytes = readFileSync(tarball);
  const parsed = verifyArchive(readTarGz(bytes));
  return { tarball, sha256: sha256(bytes), ok: parsed.ok, errors: parsed.errors, members: parsed.members };
}

function main(argv) {
  const index = argv.indexOf('--commit');
  if (index === -1) fail('usage: repro-check.mjs --commit <sha>');
  const commit = resolveCommit(argv[index + 1]);
  const python = resolvePython();
  const toolchain = toolchainVersions(python);
  const keep = argv.includes('--keep');
  const commands = new Set();
  const created = [];
  const results = [];
  try {
    for (const label of ['a', 'b']) results.push(buildOnce(commit, label, python, commands, created));
  } finally {
    if (!keep) for (const checkout of created) {
      try { execFileSync('git', ['worktree', 'remove', '--force', checkout], { cwd: ROOT, stdio: 'pipe' }); }
      catch { try { execFileSync('git', ['worktree', 'prune'], { cwd: ROOT, stdio: 'pipe' }); } catch { /* best effort */ } }
      rmSync(checkout, { recursive: true, force: true });
    }
  }
  const [first, second] = results;
  const membersEqual = JSON.stringify(first.members) === JSON.stringify(second.members);
  const reproducible = first.sha256 === second.sha256 && first.ok && second.ok && membersEqual;
  const report = {
    commit,
    declaredEnvironment: EXPECTED,
    toolchain,
    locks: {
      packageLockSha256: sha256(readFileSync(join(PACKAGE, 'package-lock.json'))),
      pythonRequirementsSha256: sha256(readFileSync(join(ROOT, 'tools/requirements-validation.lock'))),
    },
    commandsExecuted: [...commands],
    environments: results.map(result => ({ tarballSha256: result.sha256, memberCount: result.members.length, allowlistOk: result.ok })),
    membersEqual,
    reproducible,
  };
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  return reproducible ? 0 : 1;
}

if (process.argv[1] && import.meta.url === `file://${resolve(process.argv[1])}`) process.exit(main(process.argv.slice(2)));
