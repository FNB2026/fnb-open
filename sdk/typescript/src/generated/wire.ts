// SPDX-License-Identifier: Apache-2.0
// Generated; do not edit. No domain validity claim.
export type ObjectExchangeEnvelope = { "transport_version": string; "protocol_release": string; "exchange_id": string; "objects": Array<ExchangeItem>; "validation_contexts": Array<ValidationContext> };
export type ExchangeItem = { "schema": string; "object": object };
export type ValidationContext = ProtocolChainContext | SourceStateChainContext | InvalidationChainContext;
export type ProtocolChainContext = { "kind": "protocol_chain"; "roles": { "flow_event": string; "node": string; "ai_inference": string; "block_draft": string; "correction": string; "block": string } };
export type SourceStateChainContext = { "kind": "source_state_chain"; "roles": { "permission_snapshot": string; "source_state_change": string; "invalidation": string } };
export type InvalidationChainContext = { "kind": "invalidation_chain"; "roles": { "records": Array<string> } };
export type ObjectExchangeReceipt = { "transport_version": string; "protocol_release": string; "exchange_id": string; "status": "accepted" | "rejected" };
export type MalformedEnvelope = { "type": "https://www.fnbapp.net/problems/object-exchange/1.0/malformed-envelope"; "title": "Malformed exchange envelope"; "status": 400; "detail"?: string };
export type UnsupportedMediaType = { "type": "https://www.fnbapp.net/problems/object-exchange/1.0/unsupported-media-type"; "title": "Unsupported exchange representation"; "status": 415; "detail"?: string };
export type PayloadTooLarge = { "type": "https://www.fnbapp.net/problems/object-exchange/1.0/payload-too-large"; "title": "Exchange payload too large"; "status": 413; "detail"?: string };
export type UnsupportedTransportVersion = { "type": "https://www.fnbapp.net/problems/object-exchange/1.0/unsupported-transport-version"; "title": "Unsupported transport version"; "status": 400; "detail"?: string };
export type UnsupportedProtocolRelease = { "type": "https://www.fnbapp.net/problems/object-exchange/1.0/unsupported-protocol-release"; "title": "Unsupported protocol release"; "status": 400; "detail"?: string };
export type EvaluationFailure = { "type": "https://www.fnbapp.net/problems/object-exchange/1.0/evaluation-failure"; "title": "Exchange evaluation unavailable"; "status": 500; "detail"?: string };
export const wireSchemas = {
  "ObjectExchangeEnvelope": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "transport_version",
      "protocol_release",
      "exchange_id",
      "objects",
      "validation_contexts"
    ],
    "properties": {
      "transport_version": {
        "type": "string",
        "minLength": 1,
        "description": "Supported value: 1.0. Unsupported non-empty values are a distinct transport error, not protocol rejection."
      },
      "protocol_release": {
        "type": "string",
        "minLength": 1,
        "description": "Supported release: v0.1.0-preview.1. No inference of future release profiles."
      },
      "exchange_id": {
        "type": "string",
        "minLength": 1,
        "description": "Exact receipt correlation; no authentication or idempotency."
      },
      "objects": {
        "type": "array",
        "minItems": 1,
        "items": {
          "$ref": "#/components/schemas/ExchangeItem"
        }
      },
      "validation_contexts": {
        "type": "array",
        "items": {
          "$ref": "#/components/schemas/ValidationContext"
        }
      }
    }
  },
  "ExchangeItem": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "schema",
      "object"
    ],
    "properties": {
      "schema": {
        "type": "string",
        "minLength": 1,
        "description": "Exact frozen canonical $id. Unknown non-empty identifiers are protocol-invalid (200 rejected), never fetched."
      },
      "object": {
        "type": "object",
        "description": "Envelope grammar only. Frozen domain schema and semantic validity are evaluated separately; failures return 200 rejected."
      }
    }
  },
  "ValidationContext": {
    "oneOf": [
      {
        "$ref": "#/components/schemas/ProtocolChainContext"
      },
      {
        "$ref": "#/components/schemas/SourceStateChainContext"
      },
      {
        "$ref": "#/components/schemas/InvalidationChainContext"
      }
    ]
  },
  "ProtocolChainContext": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "kind",
      "roles"
    ],
    "properties": {
      "kind": {
        "const": "protocol_chain"
      },
      "roles": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "flow_event",
          "node",
          "ai_inference",
          "block_draft",
          "correction",
          "block"
        ],
        "properties": {
          "flow_event": {
            "type": "string",
            "minLength": 1
          },
          "node": {
            "type": "string",
            "minLength": 1
          },
          "ai_inference": {
            "type": "string",
            "minLength": 1
          },
          "block_draft": {
            "type": "string",
            "minLength": 1
          },
          "correction": {
            "type": "string",
            "minLength": 1
          },
          "block": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  },
  "SourceStateChainContext": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "kind",
      "roles"
    ],
    "properties": {
      "kind": {
        "const": "source_state_chain"
      },
      "roles": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "permission_snapshot",
          "source_state_change",
          "invalidation"
        ],
        "properties": {
          "permission_snapshot": {
            "type": "string",
            "minLength": 1
          },
          "source_state_change": {
            "type": "string",
            "minLength": 1
          },
          "invalidation": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  },
  "InvalidationChainContext": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "kind",
      "roles"
    ],
    "properties": {
      "kind": {
        "const": "invalidation_chain"
      },
      "roles": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "records"
        ],
        "properties": {
          "records": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": true,
            "items": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      }
    }
  },
  "ObjectExchangeReceipt": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "transport_version",
      "protocol_release",
      "exchange_id",
      "status"
    ],
    "properties": {
      "transport_version": {
        "type": "string",
        "minLength": 1
      },
      "protocol_release": {
        "type": "string",
        "minLength": 1
      },
      "exchange_id": {
        "type": "string",
        "minLength": 1
      },
      "status": {
        "enum": [
          "accepted",
          "rejected"
        ]
      }
    }
  },
  "MalformedEnvelope": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "type",
      "title",
      "status"
    ],
    "properties": {
      "type": {
        "const": "https://www.fnbapp.net/problems/object-exchange/1.0/malformed-envelope"
      },
      "title": {
        "const": "Malformed exchange envelope"
      },
      "status": {
        "type": "integer",
        "const": 400
      },
      "detail": {
        "type": "string",
        "description": "Generic explanation only. Do not echo identifiers, contents, paths, secrets, or traces."
      }
    }
  },
  "UnsupportedMediaType": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "type",
      "title",
      "status"
    ],
    "properties": {
      "type": {
        "const": "https://www.fnbapp.net/problems/object-exchange/1.0/unsupported-media-type"
      },
      "title": {
        "const": "Unsupported exchange representation"
      },
      "status": {
        "type": "integer",
        "const": 415
      },
      "detail": {
        "type": "string",
        "description": "Generic explanation only. Do not echo identifiers, contents, paths, secrets, or traces."
      }
    }
  },
  "PayloadTooLarge": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "type",
      "title",
      "status"
    ],
    "properties": {
      "type": {
        "const": "https://www.fnbapp.net/problems/object-exchange/1.0/payload-too-large"
      },
      "title": {
        "const": "Exchange payload too large"
      },
      "status": {
        "type": "integer",
        "const": 413
      },
      "detail": {
        "type": "string",
        "description": "Generic explanation only. Do not echo identifiers, contents, paths, secrets, or traces."
      }
    }
  },
  "UnsupportedTransportVersion": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "type",
      "title",
      "status"
    ],
    "properties": {
      "type": {
        "const": "https://www.fnbapp.net/problems/object-exchange/1.0/unsupported-transport-version"
      },
      "title": {
        "const": "Unsupported transport version"
      },
      "status": {
        "type": "integer",
        "const": 400
      },
      "detail": {
        "type": "string",
        "description": "Generic explanation only. Do not echo identifiers, contents, paths, secrets, or traces."
      }
    }
  },
  "UnsupportedProtocolRelease": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "type",
      "title",
      "status"
    ],
    "properties": {
      "type": {
        "const": "https://www.fnbapp.net/problems/object-exchange/1.0/unsupported-protocol-release"
      },
      "title": {
        "const": "Unsupported protocol release"
      },
      "status": {
        "type": "integer",
        "const": 400
      },
      "detail": {
        "type": "string",
        "description": "Generic explanation only. Do not echo identifiers, contents, paths, secrets, or traces."
      }
    }
  },
  "EvaluationFailure": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "type",
      "title",
      "status"
    ],
    "properties": {
      "type": {
        "const": "https://www.fnbapp.net/problems/object-exchange/1.0/evaluation-failure"
      },
      "title": {
        "const": "Exchange evaluation unavailable"
      },
      "status": {
        "type": "integer",
        "const": 500
      },
      "detail": {
        "type": "string",
        "description": "Generic explanation only. Do not echo identifiers, contents, paths, secrets, or traces."
      }
    }
  }
} as const;
export const versions = { transport: "1.0", protocol: "v0.1.0-preview.1" } as const;
export const problems = [
  {
    "type": "https://www.fnbapp.net/problems/object-exchange/1.0/malformed-envelope",
    "title": "Malformed exchange envelope",
    "status": 400
  },
  {
    "type": "https://www.fnbapp.net/problems/object-exchange/1.0/unsupported-media-type",
    "title": "Unsupported exchange representation",
    "status": 415
  },
  {
    "type": "https://www.fnbapp.net/problems/object-exchange/1.0/payload-too-large",
    "title": "Exchange payload too large",
    "status": 413
  },
  {
    "type": "https://www.fnbapp.net/problems/object-exchange/1.0/unsupported-transport-version",
    "title": "Unsupported transport version",
    "status": 400
  },
  {
    "type": "https://www.fnbapp.net/problems/object-exchange/1.0/unsupported-protocol-release",
    "title": "Unsupported protocol release",
    "status": 400
  },
  {
    "type": "https://www.fnbapp.net/problems/object-exchange/1.0/evaluation-failure",
    "title": "Exchange evaluation unavailable",
    "status": 500
  }
] as const;
