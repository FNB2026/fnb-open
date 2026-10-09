// SPDX-License-Identifier: Apache-2.0
// Duplicate-aware transport JSON machinery; not a domain validator.
export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
export type Budgets = { bytes: number; depth: number; tokens: number };
export class BoundaryError extends Error {
  constructor(readonly category: "invalid-input" | "invalid-response" | "response-limit") {
    super(category);
  }
}

export function snapshot(input: unknown, limits: Budgets): Json {
  let tokens = 0, chars = 0;
  const active = new Set<object>();
  const fail = (): never => { throw new BoundaryError("invalid-input"); };
  function visit(value: unknown, depth: number): Json {
    if (++tokens > limits.tokens || depth > limits.depth) return fail();
    if (typeof value === "string") {
      chars += value.length;
      if (chars > limits.bytes) return fail();
      return value;
    }
    if (typeof value === "number") {
      if (!Number.isFinite(value) || (Number.isInteger(value) && !Number.isSafeInteger(value))) return fail();
      return value;
    }
    if (value === null || typeof value === "boolean") return value;
    if (typeof value !== "object" || active.has(value)) return fail();
    const proto: unknown = Object.getPrototypeOf(value);
    const array = Array.isArray(value);
    if (array ? proto !== Array.prototype : proto !== null && proto !== Object.prototype) return fail();
    const descriptors = Object.getOwnPropertyDescriptors(value);
    const keys = Reflect.ownKeys(descriptors);
    if (keys.some(key => typeof key !== "string")) return fail();
    active.add(value);
    let result: Json;
    if (array) {
      const length = descriptors.length?.value as unknown;
      if (typeof length !== "number" || length > limits.tokens || keys.length !== length + 1) return fail();
      const items: Json[] = [];
      for (let index = 0; index < length; index++) {
        const field = descriptors[String(index)];
        if (!field || !field.enumerable || !("value" in field)) return fail();
        items.push(visit(field.value, depth + 1));
      }
      result = items;
    } else {
      const record: { [key: string]: Json } = Object.create(null) as { [key: string]: Json };
      for (const key of keys as string[]) {
        chars += key.length;
        if (++tokens > limits.tokens || chars > limits.bytes) return fail();
        const field = descriptors[key]!;
        if (!field.enumerable || !("value" in field)) return fail();
        record[key] = visit(field.value, depth + 1);
      }
      result = record;
    }
    active.delete(value);
    return result;
  }
  return visit(input, 1);
}

export function parseStrict(bytes: Uint8Array, limits: Budgets): Json {
  const fail = (): never => { throw new BoundaryError("invalid-response"); };
  if (bytes.byteLength > limits.bytes) throw new BoundaryError("response-limit");
  if (bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) return fail();
  let text: string;
  try { text = new TextDecoder("utf-8", { fatal: true }).decode(bytes); }
  catch { return fail(); }
  let cursor = 0, tokens = 0;
  const space = () => { while (/[\x20\t\r\n]/.test(text[cursor] ?? "") && cursor < text.length) cursor++; };
  function string(): string {
    const start = cursor++;
    while (cursor < text.length) {
      const char = text[cursor++];
      if (char === '"') {
        // JSON.parse is used ONLY on one scalar string token, never on an
        // object/document where it could erase duplicate-member evidence.
        try { return JSON.parse(text.slice(start, cursor)) as string; }
        catch { return fail(); }
      }
      if (char === "\\") cursor++;
    }
    return fail();
  }
  function value(depth: number): Json {
    if (++tokens > limits.tokens || depth > limits.depth) return fail();
    space();
    const first = text[cursor];
    if (first === '"') return string();
    if (first === "{" || first === "[") {
      cursor++;
      space();
      const array = first === "[", end = array ? "]" : "}";
      const list: Json[] = [], record: { [key: string]: Json } = Object.create(null) as { [key: string]: Json };
      if (text[cursor] === end) { cursor++; return array ? list : record; }
      while (cursor < text.length) {
        space();
        if (array) list.push(value(depth + 1));
        else {
          if (text[cursor] !== '"' || ++tokens > limits.tokens) return fail();
          const key = string();
          if (Object.hasOwn(record, key)) return fail();
          space();
          if (text[cursor++] !== ":") return fail();
          record[key] = value(depth + 1);
        }
        space();
        const separator = text[cursor++];
        if (separator === end) return array ? list : record;
        if (separator !== ",") return fail();
      }
      return fail();
    }
    for (const [literal, decoded] of [["true", true], ["false", false], ["null", null]] as const) {
      if (text.startsWith(literal, cursor)) { cursor += literal.length; return decoded; }
    }
    const match = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/.exec(text.slice(cursor));
    if (!match) return fail();
    cursor += match[0].length;
    const number = Number(match[0]);
    if (!Number.isFinite(number) || (Number.isInteger(number) && !Number.isSafeInteger(number))) return fail();
    return number;
  }
  const result = value(1);
  space();
  if (cursor !== text.length) return fail();
  return result;
}
