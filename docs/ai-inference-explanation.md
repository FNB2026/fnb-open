# AI Inference and Explanation

## AIInference

Every AI judgment in FNB creates a structured `AIInference` record:

| Field | Description |
|-------|-------------|
| model | Provider, model name, version, and configuration fingerprint |
| input_refs | Permission-aware references used as model inputs |
| output_summary | Human-readable summary of the model output |
| confidence | Model confidence score (0.0 - 1.0) |
| inference_status | Model-record lifecycle: completed or superseded |
| confirmation_status | Separate user decision: candidate, confirmed, or rejected |
| explanation | Rationale, evidence references, and known limitations |

## Explanation

Every persisted AI inference in the public protocol must have a corresponding
`Explanation` — a human-readable rationale with at least one evidence reference.
Those evidence references must resolve through the inference's permission-aware
inputs.

An Explanation must answer:

- **What** was inferred?
- **Why** was it inferred? (based on what data/evidence)
- **How confident** is the inference?
- **What would change** if the user confirms it?
- **How can the user correct it?**

## AI Boundaries

- AI can **suggest** relationships, memories, and blocks
- AI **cannot** directly create or modify any user-facing object
- All AI-generated content must pass through the **Draft → Confirm/Reject/Rewrite** workflow
- All AI operations are **audited**
- All AI operations produce **explanations**
