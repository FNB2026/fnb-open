# Data Sovereignty

FNB is built on the principle that **users own their data** — not platforms, not AI models, not third parties.

## What Data Sovereignty Means in FNB

1. **Data ownership** — all data belongs to the user who created it
2. **Data portability** — users can export all their data in standard formats
3. **Data revocation** — users can revoke access to their data at any time
4. **Data deletion** — users can delete their data (with audit trail)
5. **Inference consent** — users control whether and how AI infers from their data
6. **Training consent** — users control whether their data is used for model training
7. **Correction rights** — users can correct any AI-generated content about them
8. **Transparency** — all data operations are auditable

## How FNB Implements This

| Principle | Implementation |
|-----------|----------------|
| Data ownership | Owner field on every domain object |
| Data portability | Export API (planned) |
| Data revocation | Permission system with revocable grants |
| Data deletion | Soft delete with permanent delete option |
| Inference consent | AIInference permission action |
| Training consent | Training permission action |
| Correction rights | PATCH / Correction workflow |
| Transparency | Append-only AuditLog |

## What FNB Will Never Do

- Sell, license, or broker user data
- Train models on user data without explicit permission
- Lock user data into a proprietary format
- Require cloud storage for core functionality
- Allow AI to permanently modify user data without confirmation
- Allow third parties to access user data without explicit, revocable consent
