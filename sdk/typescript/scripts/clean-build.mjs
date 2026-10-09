// SPDX-License-Identifier: Apache-2.0
// Only this package's generated output is disposable; never a caller path.
import { readFileSync, rmSync } from 'node:fs';
const pkg = JSON.parse(readFileSync(new URL('../package.json', import.meta.url)));
if (pkg.name !== 'fnb-object-exchange-sdk-workspace' || pkg.private !== true) throw new Error('Unexpected build workspace');
rmSync(new URL('../dist/', import.meta.url), { recursive: true, force: true });
