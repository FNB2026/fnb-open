// SPDX-License-Identifier: Apache-2.0
import test from 'node:test';
import assert from 'node:assert/strict';
import { parseStrict } from '../dist/json.js';
const limits = { bytes: 65536, depth: 64, tokens: 32768 };
const parse = (text, budget = limits) => parseStrict(new TextEncoder().encode(text), budget);
test('D04 A14 A15 A19 A20: parser grammar and independent hostile-token corpus', () => {
  for (const raw of ['{"x":1,"x":2}', '{"x":1,"\\u0078":2}', '{"x":{"a":1,"a":2}}', '[1,]', '{"x":1,}', '01', '1.', '1e', '--1', 'NaN', 'Infinity', '-Infinity', '{} true', '"\\q"', '"\\u12"', '"\u0000"', '{"a" 1}', '{a:1}', '[}', '{]', '1e999', '9007199254740993']) assert.throws(() => parse(raw), raw);
  for (const raw of ['null', 'true', 'false', '0', '-0', '0.125', '-1.2e+3', '"\\u0061\\n"', '{"a":[true,null,"☕"]}', '{"__proto__":{"safe":true},"constructor":1}']) {
    const actual = parse(raw); assert.equal(JSON.stringify(actual), JSON.stringify(JSON.parse(raw)), raw);
  }
  assert.equal({}.safe, undefined);
  assert.throws(() => parse('[[0]]', { ...limits, depth: 2 }));
  assert.throws(() => parse('{"x":1}', { ...limits, tokens: 2 }));
  assert.throws(() => parse('"12345"', { ...limits, bytes: 2 }));
  assert.throws(() => parseStrict(Uint8Array.from([0xc0, 0xaf]), limits));
  assert.throws(() => parseStrict(Uint8Array.from([0xed, 0xa0, 0x80]), limits));
  assert.throws(() => parseStrict(Uint8Array.from([0xef, 0xbb, 0xbf, 0x30]), limits));
});
