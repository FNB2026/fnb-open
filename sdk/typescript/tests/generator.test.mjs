// SPDX-License-Identifier: Apache-2.0
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
test('A35: unsupported wire keyword and external reference fail generation', () => {
  const code = `import importlib.util\nfrom pathlib import Path\np=Path('sdk/typescript/scripts/generate.py')\ns=importlib.util.spec_from_file_location('test_sdk_generator',p)\nm=importlib.util.module_from_spec(s)\ns.loader.exec_module(m)\nfor bad in ({'type':'string','maxLength':3},{'$ref':'https://sender.invalid/schema'}):\n try: m.check_schema(bad)\n except ValueError: pass\n else: raise SystemExit('unsupported input accepted')\n`;
  const result = spawnSync(process.env.FNB_TEST_PYTHON, ['-c', code], { cwd: new URL('../../../', import.meta.url), encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
});
