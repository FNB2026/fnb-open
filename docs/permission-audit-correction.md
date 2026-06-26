# Permission, Audit, and Correction

## Permission Model

FNB uses a three-layer permission system:

1. **Permission.Status** — terminal gate (deny/allow based on explicit status)
2. **Ownership.Role** — role-based access override (owner > manager > viewer)
3. **Permission.Policy** — granular action-level evaluation

### Actions

| Action | Description |
|--------|-------------|
| view | Read the object |
| infer | Run AI inference on the object |
| train | Include in model training |
| export | Export the object |
| share | Share with another actor |

## Audit Model

Every sensitive operation writes an `AuditLog` entry:

- Actor identity (who)
- Action type (what)
- Object reference (which)
- Timestamp (when)
- Result (success/failure)
- IP/device context (where)

Audit logs are **append-only** and cannot be deleted or modified.

## Correction Model

FNB supports two forms of correction:

1. **PATCH** — partial update with full audit trail
   - Only owners and managers can PATCH
   - PATCH writes an update Event instead of silently mutating history

2. **Redaction** — content hiding without deletion
   - Preserves the event structure
   - Removes the content payload
   - Fully auditable

## Correction Principles

- Users can correct **any** AI-generated content
- Corrections preserve the original as a reference
- Correction history is auditable
- AI models can suggest corrections but cannot apply them without user action
