# AI Inference and Explanation

## AIInference

Every AI judgment in FNB creates a structured `AIInference` record:

| Field | Description |
|-------|-------------|
| model_id | Which model produced the inference |
| input_hash | Hash of the input data |
| output_hash | Hash of the output data |
| confidence | Model confidence score (0.0 - 1.0) |
| claim_type | Type of claim (relationship, memory, classification, etc.) |
| evidence_ids | References to supporting evidence |
| state_delta | What changed as a result |

## Explanation

Every AI inference that affects user data must have a corresponding `Explanation` — a human-readable rationale.

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
