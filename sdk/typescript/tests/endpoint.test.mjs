// SPDX-License-Identifier: Apache-2.0
import test from 'node:test';
import assert from 'node:assert/strict';
import { createExchangeClient, ConfigurationError } from '../dist/index.js';

test('D08 A26: reject noncanonical numeric IPv4 before URL normalization', () => {
  assert.equal(new URL('http://127.0.0.01/exchange').hostname, '127.0.0.1');
  for (const host of ['127.0.0.01', '127.00.0.1', '127.000.0.1', '127.01.0.1', '127.0.0.001',
    '0177.0.0.1', '127.0.0.256', '127.256.0.1', '127.999.0.1', '127.-1.0.1',
    '127.1', '2130706433', '0x7f.0.0.1', '%31%32%37.0.0.1', 'localhost', '[::1]']) {
    assert.throws(() => createExchangeClient({ endpoint: `http://${host}/exchange` }), ConfigurationError, host);
  }
});

test('D08 A26: canonical decimal loopback boundaries pass; HTTPS policy unchanged', () => {
  for (const endpoint of ['http://127.0.0.0/exchange', 'http://127.0.0.1:8765/exchange',
    'http://127.0.0.2/exchange', 'http://127.10.20.30/exchange', 'http://127.255.255.255:65535/exchange',
    'HTTP://127.0.0.1/exchange', 'https://example.invalid/exchange']) {
    assert.equal(typeof createExchangeClient({ endpoint }).exchange, 'function', endpoint);
  }
  assert.throws(() => createExchangeClient({ endpoint: 'https://user:pass@example.invalid/exchange' }), ConfigurationError);
});
