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

Audit logs are **append-only while retained**: an existing record is never
silently edited. Append-only does not override a valid redaction or deletion
request. When identifiable audit data must be removed, an implementation may
delete it or, only with a valid bounded retention basis, replace it with the
data-minimized `AuditTombstone` defined by RFC-0002.

## Correction Model

FNB supports two forms of correction:

1. **PATCH** — partial update with full audit trail
   - Only owners and managers can PATCH
   - PATCH writes an update Event instead of silently mutating history

2. **Redaction** — removal of content and identifying references
   - Invalidates downstream derived objects deterministically
   - Removes the identifiable payload and references in scope
   - May leave only a bounded `AuditTombstone` when retention has a valid basis

## Correction Principles

- Users can correct **any** AI-generated content
- Corrections preserve the original as a reference only while that identifiable
  history may lawfully remain
- Correction history is auditable only for as long as its identifiable records
  may lawfully remain
- AI models can suggest corrections but cannot apply them without user action
