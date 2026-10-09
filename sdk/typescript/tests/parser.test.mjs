// SPDX-License-Identifier: Apache-2.0
import test from 'node:test';
import assert from 'node:assert/strict';
import { parseStrict } from '../dist/json.js';
const limits = { bytes: 65536, depth: 64, tokens: 32768 };
const parse = (text, budget = limits) => parseStrict(new TextEncoder().encode(text), budget);
test('D04 A14 A15 A19 A20: parser grammar and developer hostile-token corpus', () => {
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

test('D04 A14 A19: escaped keys, Unicode strings and prototype-sensitive collisions', () => {
  for (const [one, two] of [
    ['a', '\\u0061'], ['☕', '\\u2615'], ['😀', '\\ud83d\\ude00'],
    ['__proto__', '\\u005f_proto__'], ['constructor', '\\u0063onstructor'],
    ['a/b', 'a\\/b'], ['quote\\"key', 'quote\\u0022key']
  ]) {
    assert.throws(() => parse(`{"${one}":1,"${two}":2}`));
    assert.throws(() => parse(`{"outer":[{"${one}":1,"${two}":2}]}`));
  }
  for (const raw of ['"\\u0000"', '"\\ud83d\\ude00"', '"\\ud800"', '"\\udc00"',
    '"\\\\\\\"\\/\\b\\f\\n\\r\\t"', '{"a":0,"A":1}', '{"é":0,"e\\u0301":1}']) {
    assert.equal(JSON.stringify(parse(raw)), JSON.stringify(JSON.parse(raw)), raw);
  }
  // JSON permits escaped unpaired UTF-16 surrogates; invalid raw UTF-8 is
  // rejected separately. Keys are compared decoded, not Unicode-normalized.
  for (const raw of ['"\\uD80"', '"\\u000G"', '"\\x00"', '"\\"', '"unterminated', '\u00a0null', '\u000bnull']) assert.throws(() => parse(raw), raw);
});

test('D04 A20: exact byte/depth/token and safe-number boundaries', () => {
  const deepest = '['.repeat(63) + '0' + ']'.repeat(63);
  assert.doesNotThrow(() => parse(deepest));
  assert.throws(() => parse('[' + deepest + ']'));
  assert.doesNotThrow(() => parse('[0,1]', { ...limits, tokens: 3 }));
  assert.throws(() => parse('[0,1,2]', { ...limits, tokens: 3 }));
  assert.doesNotThrow(() => parse('{"x":1}', { ...limits, tokens: 3 }));
  assert.throws(() => parse('{"x":1}', { ...limits, tokens: 2 }));
  assert.equal(parse('"☕"', { ...limits, bytes: 5 }), '☕');
  assert.throws(() => parse('"☕"', { ...limits, bytes: 4 }));
  for (const raw of ['9007199254740991', '-9007199254740991', '1.7976931348623157e308', '5e-324']) {
    // Integral Numbers outside the safe-integer range are intentionally rejected,
    // including large finite exponent forms. Fractional Number semantics remain.
    if (Number.isInteger(Number(raw)) && !Number.isSafeInteger(Number(raw))) assert.throws(() => parse(raw));
    else assert.equal(parse(raw), Number(raw));
  }
  for (const raw of ['9007199254740992', '-9007199254740992', '1e309', '-1e309', '+1', '1e+', '0x1']) assert.throws(() => parse(raw), raw);
  for (const bytes of [[0xe2, 0x82], [0xf4, 0x90, 0x80, 0x80], [0x80], [0xc1, 0xbf]]) assert.throws(() => parseStrict(Uint8Array.from(bytes), limits));
});

test('D04 A14 A19: deterministic 512-case valid grammar corpus and duplicate mutations', () => {
  for (let index = 0; index < 512; index++) {
    const key = `k${index}`, value = { [key]: [index, index / 8, Boolean(index % 2), null, `☕ ${index} \\"\n`], nested: { ['__proto__']: { safe: index } } };
    const raw = JSON.stringify(value);
    assert.equal(JSON.stringify(parse(raw)), raw);
    // Independently specified duplicate rejection; JSON.parse would erase it.
    assert.throws(() => parse(`{"${key}":0,"${key}":1}`));
  }
  assert.equal({}.safe, undefined);
});
