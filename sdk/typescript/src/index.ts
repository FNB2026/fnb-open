// SPDX-License-Identifier: Apache-2.0
import { BoundaryError, parseStrict, snapshot, type Json } from "./json.js";
import { problems, versions, wireSchemas, type ObjectExchangeEnvelope, type ObjectExchangeReceipt } from "./generated/wire.js";
export type { ObjectExchangeEnvelope, ObjectExchangeReceipt, ValidationContext, ExchangeItem } from "./generated/wire.js";

export type Problem = { type: string; title: string; status: 400 | 413 | 415 | 500; detail?: string };
export type FailureCategory = "configuration" | "invalid-input" | "invalid-response" | "response-limit" | "cancelled" | "timeout" | "network" | "internal";
export type ExchangeResult = { kind: "receipt"; receipt: ObjectExchangeReceipt }
  | { kind: "problem"; problem: Problem }
  | { kind: "failure"; category: FailureCategory };
type Caps = { requestBytes: number; objects: number; responseBytes: number; depth: number; tokens: number };
export type ClientOptions = { endpoint: string; fetch?: typeof globalThis.fetch; timeoutMs?: number; limits?: Partial<Caps> };
export type ExchangeOptions = { signal?: AbortSignal };
export type ExchangeClient = { exchange(input: ObjectExchangeEnvelope, options?: ExchangeOptions): Promise<ExchangeResult> };
export class ConfigurationError extends Error {
  constructor() { super("Invalid SDK configuration"); }
}
const DEFAULTS: Caps = { requestBytes: 1048576, objects: 256, responseBytes: 65536, depth: 64, tokens: 32768 };
const failure = (category: FailureCategory): ExchangeResult => ({ kind: "failure", category });
const record = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null && !Array.isArray(value);

// Interpreter only for the narrow, locally generated wire metadata. Domain
// schema IDs are opaque strings: there is no lookup or FNB domain judge here.
type Schema = { $ref?: string; oneOf?: readonly Schema[]; const?: unknown; enum?: readonly unknown[];
  type?: string; minLength?: number; minItems?: number; uniqueItems?: boolean;
  required?: readonly string[]; properties?: Record<string, Schema>; additionalProperties?: boolean; items?: Schema };
function wireValid(schema: Schema, data: unknown): boolean {
  if (schema.$ref) {
    const name = schema.$ref.split("/").at(-1)! as keyof typeof wireSchemas;
    return Object.hasOwn(wireSchemas, name) && wireValid(wireSchemas[name], data);
  }
  if (schema.oneOf) return schema.oneOf.filter(candidate => wireValid(candidate, data)).length === 1;
  if (Object.hasOwn(schema, "const") && data !== schema.const) return false;
  if (schema.enum && !schema.enum.includes(data)) return false;
  if (schema.type === "string") return typeof data === "string" && data.length >= (schema.minLength ?? 0);
  if (schema.type === "array") {
    if (!Array.isArray(data) || data.length < (schema.minItems ?? 0)) return false;
    if (schema.uniqueItems && new Set(data.map(item => JSON.stringify(item))).size !== data.length) return false;
    return !schema.items || data.every(item => wireValid(schema.items!, item));
  }
  if (schema.type === "object") {
    if (!record(data) || schema.required?.some(key => !Object.hasOwn(data, key))) return false;
    const properties = schema.properties ?? {};
    return Object.keys(data).every(key => Object.hasOwn(properties, key)
      ? wireValid(properties[key]!, data[key]) : schema.additionalProperties !== false);
  }
  return schema.type === undefined;
}

function mediaMatches(actual: string | null, expected: string): boolean {
  if (actual === null) return false;
  const parts = actual.split(";").map(part => part.trim().toLowerCase());
  return parts[0] === expected && (parts.length === 1 || (parts.length === 2 && parts[1] === "charset=utf-8"));
}

function decodeResult(response: Response, bytes: Uint8Array, input: ObjectExchangeEnvelope, caps: Caps): ExchangeResult {
  const bad = () => failure("invalid-response");
  const encoding = response.headers.get("Content-Encoding");
  if (encoding !== null && encoding.trim().toLowerCase() !== "identity") return bad();
  const type = response.headers.get("Content-Type");
  const expected = response.status === 200 ? "application/json" : "application/problem+json";
  if (!mediaMatches(type, expected)) return bad();
  const body = parseStrict(bytes, { bytes: caps.responseBytes, depth: caps.depth, tokens: caps.tokens });
  if (!record(body)) return bad();
  if (response.status === 200) {
    if (!wireValid(wireSchemas.ObjectExchangeReceipt, body)) return bad();
    if (["transport_version", "protocol_release", "exchange_id"].some(key => body[key] !== input[key as keyof ObjectExchangeEnvelope])) return bad();
    return { kind: "receipt", receipt: {
      transport_version: body.transport_version as string,
      protocol_release: body.protocol_release as string,
      exchange_id: body.exchange_id as string,
      status: body.status as "accepted" | "rejected"
    } };
  }
  const known = problems.find(item => item.type === body.type && item.title === body.title && item.status === body.status && item.status === response.status);
  if (!known || (Object.hasOwn(body, "detail") && typeof body.detail !== "string")) return bad();
  // RFC consumer rule: unknown extension members are ignored, not returned.
  const problem: Problem = { ...known };
  if (typeof body.detail === "string") problem.detail = body.detail;
  return { kind: "problem", problem };
}

export function createExchangeClient(options: ClientOptions): ExchangeClient {
  const invalid = (): never => { throw new ConfigurationError(); };
  if (!record(options) || Object.keys(options).some(key => !["endpoint", "fetch", "timeoutMs", "limits"].includes(key))) return invalid();
  if (typeof options.endpoint !== "string" || /[?#]/.test(options.endpoint)) return invalid();
  let endpoint: URL;
  try { endpoint = new URL(options.endpoint); } catch { return invalid(); }
  if (endpoint.username || endpoint.password || endpoint.pathname !== "/exchange") return invalid();
  if (endpoint.protocol !== "https:") {
    // Deliberately reject hostname resolution and alternative numeric spellings.
    if (endpoint.protocol !== "http:" || !/^127\.(?:[0-9]{1,3}\.){2}[0-9]{1,3}$/.test(endpoint.hostname)
        || !/^http:\/\/127\.(?:[0-9]{1,3}\.){2}[0-9]{1,3}(?::[0-9]+)?\/exchange$/i.test(options.endpoint)) return invalid();
  }
  const fetcher = options.fetch ?? globalThis.fetch;
  if (typeof fetcher !== "function") return invalid();
  const timeout = options.timeoutMs ?? 10000;
  if (!Number.isInteger(timeout) || timeout < 1 || timeout > 60000) return invalid();
  const caps = { ...DEFAULTS };
  if (options.limits !== undefined) {
    if (!record(options.limits)) return invalid();
    for (const [key, value] of Object.entries(options.limits)) {
      if (!Object.hasOwn(DEFAULTS, key) || !Number.isInteger(value) || value < 1 || value > DEFAULTS[key as keyof Caps]) return invalid();
      caps[key as keyof Caps] = value;
    }
  }
  return Object.freeze({
    async exchange(input: ObjectExchangeEnvelope, call: ExchangeOptions = {}): Promise<ExchangeResult> {
      const started = performance.now();
      let cause: "cancelled" | "timeout" | undefined;
      let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
      let timer: ReturnType<typeof setTimeout> | undefined;
      const controller = new AbortController();
      let signal: AbortSignal | undefined;
      let terminalResolve: (value: ExchangeResult) => void = () => {};
      const terminal = new Promise<ExchangeResult>(resolve => { terminalResolve = resolve; });
      const stop = (why: "cancelled" | "timeout") => {
        if (cause !== undefined) return;
        cause = why;
        terminalResolve(failure(why));
        controller.abort();
        void reader?.cancel().catch(() => {});
      };
      const cancelled = () => stop("cancelled");
      const checkpoint = () => {
        if (cause) throw new Error("terminal");
        if (performance.now() - started >= timeout) { stop("timeout"); throw new Error("terminal"); }
      };
      try {
        if (!record(call) || Object.keys(call).some(key => key !== "signal")) return failure("invalid-input");
        signal = call.signal;
        if (signal !== undefined && !(signal instanceof AbortSignal)) return failure("invalid-input");
        if (signal?.aborted) return failure("cancelled");
        signal?.addEventListener("abort", cancelled, { once: true });
        timer = setTimeout(() => stop("timeout"), timeout);
        // Immutable detached snapshot before the first await.
        const material: Json = snapshot(input, { bytes: caps.requestBytes, depth: caps.depth, tokens: caps.tokens });
        if (!wireValid(wireSchemas.ObjectExchangeEnvelope, material) || !record(material)) return failure("invalid-input");
        const request = material as ObjectExchangeEnvelope;
        if (request.transport_version !== versions.transport || request.protocol_release !== versions.protocol || request.objects.length > caps.objects) return failure("invalid-input");
        const raw = new TextEncoder().encode(JSON.stringify(material));
        if (raw.byteLength > caps.requestBytes) return failure("invalid-input");
        checkpoint();
        const work = (async (): Promise<ExchangeResult> => {
          let phase: "fetch" | "read" | "decode" = "fetch";
          let response: Response | undefined;
          try {
            response = await fetcher(endpoint.href, { method: "POST", body: raw,
              headers: { "Content-Type": "application/json", "Accept": "application/json, application/problem+json" },
              redirect: "error", credentials: "omit", signal: controller.signal });
            checkpoint();
            if (!(response instanceof Response) || response.body === null) return failure("invalid-response");
            phase = "read";
            reader = response.body.getReader();
            const chunks: Uint8Array[] = [];
            let length = 0;
            while (true) {
              const next = await reader.read();
              checkpoint();
              if (next.done) break;
              if (!(next.value instanceof Uint8Array)) return failure("invalid-response");
              length += next.value.byteLength;
              if (length > caps.responseBytes) {
                void reader.cancel().catch(() => {});
                controller.abort();
                return failure("response-limit");
              }
              // Detach bytes from any trusted-fetch reusable backing buffer.
              chunks.push(next.value.slice());
            }
            const bytes = new Uint8Array(length);
            let offset = 0;
            for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
            phase = "decode";
            const result = decodeResult(response, bytes, request, caps);
            checkpoint();
            return result;
          } catch (error) {
            if (cause) return failure(cause);
            if (error instanceof BoundaryError) return failure(error.category);
            return failure(phase === "fetch" ? "network" : phase === "read" ? "invalid-response" : "internal");
          } finally {
            // Cancel unread/failed streams, including paths where abort won.
            void reader?.cancel().catch(() => {});
            if (!reader && response instanceof Response) void response.body?.cancel().catch(() => {});
          }
        })();
        return await Promise.race([terminal, work]);
      } catch (error) {
        if (cause) return failure(cause);
        if (error instanceof BoundaryError) return failure(error.category);
        return failure("internal");
      } finally {
        if (timer !== undefined) clearTimeout(timer);
        signal?.removeEventListener("abort", cancelled);
      }
    }
  });
}
