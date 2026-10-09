// SPDX-License-Identifier: Apache-2.0
import { createExchangeClient, type ExchangeResult, type ObjectExchangeEnvelope } from '../src/index.js';
import type { Memory } from '../src/protocol.js';
declare const memory: Memory;
const request: ObjectExchangeEnvelope = { transport_version: '1.0', protocol_release: 'v0.1.0-preview.1', exchange_id: 'synthetic', objects: [{ schema: 'opaque-canonical-id', object: memory }], validation_contexts: [] };
void createExchangeClient({ endpoint: 'http://127.0.0.1:8765/exchange' }).exchange(request);
declare const result: ExchangeResult;
if (result.kind === 'receipt') { const verdict: 'accepted' | 'rejected' = result.receipt.status; void verdict; }
// @ts-expect-error no login or product API
createExchangeClient({ endpoint: 'https://example.invalid/exchange' }).login();
// @ts-expect-error problem is not a receipt
result.receipt;
