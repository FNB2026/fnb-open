// SPDX-License-Identifier: Apache-2.0
import { readdirSync, mkdirSync, copyFileSync } from 'node:fs';
const source = new URL('../src/generated/protocol/', import.meta.url);
const target = new URL('../dist/generated/protocol/', import.meta.url);
mkdirSync(target, { recursive: true });
for (const name of readdirSync(source)) {
  // The frozen extensionless index is archived in source, not a NodeNext entry.
  if (name.endsWith('.d.ts') && name !== 'index.d.ts') copyFileSync(new URL(name, source), new URL(name, target));
}
