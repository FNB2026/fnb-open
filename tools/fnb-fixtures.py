#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Deterministic synthetic fixture world generator for the FNB protocol.

Usage:

    python3 tools/fnb-fixtures.py list
    python3 tools/fnb-fixtures.py generate basic-memory --seed 42
    python3 tools/fnb-fixtures.py generate source-redaction --seed 7 --out world.json
    python3 tools/fnb-fixtures.py check

A "world" is a set of synthetic protocol objects that refer to each other
consistently, so a third party can exercise an implementation without any real
user data. Output is a pure function of (scenario, seed): the same pair always
produces the same bytes.

Two deliberate boundaries:

* This tool does not re-implement protocol semantics. It constructs objects, and
  ``tools/validate-public-artifacts.py`` remains the single authority that judges
  them, using the same chain validators the public conformance suite uses.
* Randomness comes from an explicit SplitMix64 generator rather than the
  standard library's ``random`` module, so reproducibility does not depend on
  CPython internals.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

PROTOCOL_RELEASE = "v0.1.0-preview.1"
WORLD_VERSION = "1.0"
GENERATOR = "fnb-fixtures"
REFERENCE_SEED = 42
REFERENCE_DIR = Path("tests/fixtures/generated")

# Identifier prefixes are fixed by the frozen schemas. The generator mints only
# prefixed identifiers, so a world can never carry a malformed identifier.
PREFIXES = {
    "actor": "fnb_actor_",
    "event": "fnb_evt_",
    "node": "fnb_node_",
    "inference": "fnb_inf_",
    "explanation": "fnb_exp_",
    "draft": "fnb_draft_",
    "correction": "fnb_corr_",
    "block": "fnb_block_",
    "memory": "fnb_mem_",
    "relationship": "fnb_rel_",
    "invalidation": "fnb_inv_",
    "source_change": "fnb_srcchg_",
    "permission_snapshot": "fnb_permsnap_",
    "audit": "fnb_audit_",
}

# Mirrors the transition table the public validator enforces. The generator needs
# it to choose a legal reason for a chosen transition; it does not judge results.
TRANSITION_REASONS = {
    ("active", "stale"): "source_stale",
    ("active", "redacted"): "source_redacted",
    ("active", "deleted"): "source_deleted",
    ("active", "permission_withdrawn"): "permission_withdrawn",
    ("stale", "active"): "source_restored",
    ("stale", "redacted"): "source_redacted",
    ("stale", "deleted"): "source_deleted",
    ("stale", "permission_withdrawn"): "permission_withdrawn",
    ("redacted", "deleted"): "source_deleted",
    ("permission_withdrawn", "active"): "permission_restored",
    ("permission_withdrawn", "redacted"): "source_redacted",
    ("permission_withdrawn", "deleted"): "source_deleted",
}

MASK64 = (1 << 64) - 1
EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FixtureError(Exception):
    """Raised when a world cannot be constructed as requested."""


class DeterministicRng:
    """SplitMix64. Explicit so output is independent of the host's random module."""

    def __init__(self, seed: int) -> None:
        if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
            raise FixtureError("seed must be a non-negative integer")
        self._state = (seed ^ 0x9E3779B97F4A7C15) & MASK64

    def next_u64(self) -> int:
        self._state = (self._state + 0x9E3779B97F4A7C15) & MASK64
        value = self._state
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK64
        return (value ^ (value >> 31)) & MASK64

    def below(self, bound: int) -> int:
        if bound <= 0:
            raise FixtureError("bound must be positive")
        return self.next_u64() % bound

    def pick(self, items):
        if not items:
            raise FixtureError("cannot pick from an empty sequence")
        return items[self.below(len(items))]

    def token(self, length: int = 8) -> str:
        return f"{self.next_u64():016x}"[:length]


class World:
    """Accumulates schema-valid leaf objects, mints unique ids, advances one clock."""

    def __init__(self, scenario: str, seed: int) -> None:
        self.scenario = scenario
        self.seed = seed
        self.rng = DeterministicRng(seed)
        self.objects: dict[str, Any] = {}
        self.schemas: dict[str, str] = {}
        self.validation: list[dict[str, Any]] = []
        self._minted: set[str] = set()
        self._clock = 0

    def mint(self, kind: str) -> str:
        try:
            prefix = PREFIXES[kind]
        except KeyError as error:
            raise FixtureError(f"unknown identifier kind {kind!r}") from error
        for _ in range(64):
            candidate = f"{prefix}{self.rng.token(8)}"
            if candidate not in self._minted:
                self._minted.add(candidate)
                return candidate
        raise FixtureError(f"could not mint a unique {kind} identifier")

    def timestamp(self, minutes: int = 5) -> str:
        self._clock += minutes
        return (EPOCH + timedelta(minutes=self._clock)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def date(self, days: int) -> str:
        return (EPOCH + timedelta(days=days)).strftime("%Y-%m-%d")

    def add(self, name: str, schema: str, instance: dict[str, Any]) -> dict[str, Any]:
        if name in self.objects:
            raise FixtureError(f"duplicate object name {name!r}")
        self.objects[name] = instance
        self.schemas[name] = schema
        return instance

    def chain(self, kind: str, **payload: Any) -> None:
        self.validation.append({"kind": kind, **payload})

    def document(self) -> dict[str, Any]:
        return {
            "world_version": WORLD_VERSION,
            "protocol_release": PROTOCOL_RELEASE,
            "generator": GENERATOR,
            "scenario": self.scenario,
            "seed": self.seed,
            "object_schemas": self.schemas,
            "objects": self.objects,
            "validation": self.validation,
        }


def idempotency_key(record: dict[str, Any]) -> str:
    """Canonical key over the trigger and target tuple, as the protocol defines it."""
    material = "|".join(
        [
            record["trigger_type"],
            record["trigger_id"],
            record["target_type"],
            record["target_id"],
            record["resulting_state"],
        ]
    )
    return f"sha256:{hashlib.sha256(material.encode('utf-8')).hexdigest()}"


def add_actor(world: World, name: str, display: str, kind: str = "person") -> dict[str, Any]:
    return world.add(
        name,
        "actor.schema.json",
        {
            "actor_id": world.mint("actor"),
            "kind": kind,
            "display_name": display,
            "status": "active",
        },
    )


def add_memory(world: World, name: str, owner_id: str, title: str, summary: str,
               source_ref: str, lifecycle_state: str = "active") -> dict[str, Any]:
    return world.add(
        name,
        "memory.schema.json",
        {
            "memory_id": world.mint("memory"),
            "owner_id": owner_id,
            "title": title,
            "summary": summary,
            "status": "confirmed" if lifecycle_state == "active" else "candidate",
            "lifecycle_state": lifecycle_state,
            "confidence": round(0.4 + world.rng.below(40) / 100, 2),
            "sources": [
                {
                    "source_id": f"fnb_src_{world.rng.token(8)}",
                    "object_type": "event",
                    "object_id": f"fnb_evt_{world.rng.token(8)}",
                    "content_hash": f"sha256:{world.rng.token(16)}",
                }
            ],
        },
    )


def build_basic_memory(world: World) -> None:
    """Flow event to confirmed AI-derived Block, with its Memory."""
    owner = add_actor(world, "owner", "Synthetic Owner")

    event = world.add(
        "flow_event",
        "flow-event.schema.json",
        {
            "event_id": world.mint("event"),
            "flow_id": f"fnb_flow_{world.rng.token(8)}",
            "event_type": "message",
            "occurred_at": world.timestamp(),
            "actor_id": owner["actor_id"],
            "source_ref": "synthetic://chat/basic-memory",
            "content_preview": world.rng.pick(
                [
                    "We agreed to review the draft next week.",
                    "Coffee tomorrow at nine.",
                    "Send the summary after the call.",
                ]
            ),
        },
    )

    node = world.add(
        "node",
        "node.schema.json",
        {
            "node_id": world.mint("node"),
            "node_type": "memory",
            "source_event_ids": [event["event_id"]],
            "status": "confirmed",
            "label": world.rng.pick(["Synthetic plan", "Synthetic appointment"]),
        },
    )

    inference = world.add(
        "ai_inference",
        "ai-inference.schema.json",
        {
            "inference_id": world.mint("inference"),
            "purpose": "propose a memory for user confirmation",
            "model": {
                "provider": "synthetic-provider",
                "name": "synthetic-summarizer",
                "version": "0.1.0",
                "configuration_fingerprint": f"sha256:{world.rng.token(16)}",
            },
            "input_refs": [event["event_id"], node["node_id"]],
            "output_summary": "Draft memory about a review commitment.",
            "confidence": round(0.5 + world.rng.below(40) / 100, 2),
            "inference_status": "completed",
            "confirmation_status": "confirmed",
            "explanation": {
                "explanation_id": world.mint("explanation"),
                "rationale": "Derived only from the synthetic event and node it references.",
                "evidence_refs": [event["event_id"], node["node_id"]],
                "limitations": ["synthetic fixture; not a product judgement"],
            },
        },
    )

    draft = world.add(
        "block_draft",
        "block-draft.schema.json",
        {
            "draft_id": world.mint("draft"),
            "owner_id": owner["actor_id"],
            "block_type": "memory",
            "source_node_ids": [node["node_id"]],
            "inference_id": inference["inference_id"],
            "proposed_title": "Synthetic review commitment",
            "proposed_summary": "Review the draft next week.",
            "status": "confirmed",
        },
    )

    correction = world.add(
        "correction",
        "correction-patch.schema.json",
        {
            "correction_id": world.mint("correction"),
            "actor_id": owner["actor_id"],
            "target_type": "block_draft",
            "target_id": draft["draft_id"],
            "operation": "confirm",
            "reason": "synthetic confirmation",
            "created_at": world.timestamp(),
        },
    )

    block = world.add(
        "block",
        "block.schema.json",
        {
            "block_id": world.mint("block"),
            "owner_id": owner["actor_id"],
            "block_type": "memory",
            "creation_mode": "ai_derived",
            "source_node_ids": [node["node_id"]],
            "draft_id": draft["draft_id"],
            "title": draft["proposed_title"],
            "summary": draft["proposed_summary"],
            "confirmed_by_actor_id": owner["actor_id"],
            "confirmation_event_id": world.mint("event"),
            "confirmation_operation": "confirm",
            "confirmed_at": world.timestamp(),
        },
    )

    add_memory(
        world,
        "memory",
        owner["actor_id"],
        block["title"],
        block["summary"],
        "synthetic://chat/basic-memory",
    )

    world.chain(
        "protocol_chain",
        members={
            "flow_event": "flow_event",
            "node": "node",
            "ai_inference": "ai_inference",
            "block_draft": "block_draft",
            "correction": "correction",
            "block": "block",
        },
    )


def build_relationship_correction(world: World) -> None:
    """Contested relationship, rejected correction, and transitive invalidation to Memory."""
    first = add_actor(world, "actor_first", "Synthetic Actor A")
    second = add_actor(world, "actor_second", "Synthetic Actor B")

    event = world.add(
        "flow_event",
        "flow-event.schema.json",
        {
            "event_id": world.mint("event"),
            "flow_id": f"fnb_flow_{world.rng.token(8)}",
            "event_type": "meeting",
            "occurred_at": world.timestamp(),
            "actor_id": first["actor_id"],
            "source_ref": "synthetic://calendar/relationship-correction",
            "content_preview": "Synthetic working session.",
        },
    )

    relationship = world.add(
        "relationship",
        "relationship.schema.json",
        {
            "relationship_id": world.mint("relationship"),
            "participant_ids": [first["actor_id"], second["actor_id"]],
            "lifecycle_state": "contested",
            "assertions": [
                {
                    "actor_id": first["actor_id"],
                    "relationship_kind": "colleague",
                    "confirmation_state": "confirmed",
                    "confirmed_at": world.timestamp(),
                    "confirmation_event_id": world.mint("event"),
                    "visibility_scope": "participants",
                },
                {
                    "actor_id": second["actor_id"],
                    "relationship_kind": "colleague",
                    "confirmation_state": "contested",
                    "visibility_scope": "participants",
                },
            ],
            "evidence": [
                {
                    "evidence_id": f"fnb_evid_{world.rng.token(8)}",
                    "source_type": "event",
                    "source_id": event["event_id"],
                    "stance": "supports",
                },
                {
                    "evidence_id": f"fnb_evid_{world.rng.token(8)}",
                    "source_type": "event",
                    "source_id": event["event_id"],
                    "stance": "contests",
                },
            ],
        },
    )

    memory = add_memory(
        world,
        "memory",
        first["actor_id"],
        "Synthetic derived note",
        "Derived from the contested synthetic relationship.",
        "synthetic://calendar/relationship-correction",
    )

    correction = world.add(
        "correction",
        "correction-patch.schema.json",
        {
            "correction_id": world.mint("correction"),
            "actor_id": second["actor_id"],
            "target_type": "relationship",
            "target_id": relationship["relationship_id"],
            "operation": "reject",
            "reason": "synthetic rejection of the asserted relationship",
            "created_at": world.timestamp(),
        },
    )

    direct = {
        "invalidation_id": world.mint("invalidation"),
        "trigger_type": "correction_patch",
        "trigger_id": correction["correction_id"],
        "target_type": "relationship",
        "target_id": relationship["relationship_id"],
        "resulting_state": "invalidated",
        "reason_code": "correction_rejected",
        "created_at": world.timestamp(),
    }
    direct["idempotency_key"] = idempotency_key(direct)
    world.add("invalidation_direct", "invalidation-record.schema.json", direct)

    transitive = {
        "invalidation_id": world.mint("invalidation"),
        "trigger_type": "parent_invalidation",
        "trigger_id": direct["idempotency_key"],
        "parent_invalidation_id": direct["invalidation_id"],
        "target_type": "memory",
        "target_id": memory["memory_id"],
        "resulting_state": "review_required",
        "reason_code": "upstream_invalidated",
        "created_at": world.timestamp(),
    }
    transitive["idempotency_key"] = idempotency_key(transitive)
    world.add("invalidation_transitive", "invalidation-record.schema.json", transitive)

    world.chain(
        "invalidation_chain",
        records=["invalidation_direct", "invalidation_transitive"],
    )


def build_permission_withdrawal(world: World) -> None:
    """Withdrawn permission snapshot, its source change, and the required invalidation."""
    build_source_state_world(
        world,
        new_state="permission_withdrawn",
        source_ref="synthetic://drive/shared-folder",
        retention_days=30,
    )


def build_source_redaction(world: World) -> None:
    """Redacted source, its source-change invalidation, and a data-minimized tombstone."""
    build_source_state_world(
        world,
        new_state="redacted",
        source_ref="synthetic://chat/redacted-thread",
        retention_days=90,
    )
    world.add(
        "audit_tombstone",
        "audit-tombstone.schema.json",
        {
            "audit_id": world.mint("audit"),
            "action": "redact",
            "target_type": "source",
            "outcome": "completed",
            "occurred_on": world.date(0),
            "retention_basis": "statutory_obligation",
            "purge_after": world.date(365),
        },
    )


def build_source_state_world(
    world: World, new_state: str, source_ref: str, retention_days: int
) -> None:
    previous_state = "active"
    reason = TRANSITION_REASONS.get((previous_state, new_state))
    if reason is None:
        raise FixtureError(f"{previous_state} -> {new_state} is not an allowed source transition")

    owner = add_actor(world, "owner", "Synthetic Owner")

    world.add(
        "permission_snapshot",
        "permission-snapshot.schema.json",
        {
            "permission_snapshot_id": world.mint("permission_snapshot"),
            "source_ref": source_ref,
            "subject_scope": "participant",
            "allowed_actions": (
                ["view", "infer"] if new_state == "permission_withdrawn" else ["view"]
            ),
            "visibility_scope": "private",
            "basis": "user_consent",
            "captured_at": world.timestamp(),
            "expires_at": (EPOCH + timedelta(days=retention_days)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )

    change = world.add(
        "source_state_change",
        "source-state-change.schema.json",
        {
            "source_change_id": world.mint("source_change"),
            "source_ref": source_ref,
            "previous_state": previous_state,
            "new_state": new_state,
            "reason_code": reason,
            "effective_at": world.timestamp(),
        },
    )

    memory = add_memory(
        world,
        "memory",
        owner["actor_id"],
        "Synthetic derived memory",
        f"Derived from {source_ref}.",
        source_ref,
        lifecycle_state="redacted" if new_state == "redacted" else "active",
    )

    invalidation = {
        "invalidation_id": world.mint("invalidation"),
        "trigger_type": (
            "permission_change" if new_state == "permission_withdrawn" else "source_change"
        ),
        "trigger_id": change["source_change_id"],
        "target_type": "memory",
        "target_id": memory["memory_id"],
        "resulting_state": "invalidated",
        "reason_code": reason,
        "created_at": world.timestamp(),
    }
    invalidation["idempotency_key"] = idempotency_key(invalidation)
    world.add("invalidation", "invalidation-record.schema.json", invalidation)

    world.chain(
        "source_state_chain",
        members={
            "permission_snapshot": "permission_snapshot",
            "source_state_change": "source_state_change",
            "invalidation": "invalidation",
        },
    )


SCENARIOS: dict[str, Callable[[World], None]] = {
    "basic-memory": build_basic_memory,
    "relationship-correction": build_relationship_correction,
    "permission-withdrawal": build_permission_withdrawal,
    "source-redaction": build_source_redaction,
}
SCENARIO_SUMMARY = {
    "basic-memory": "flow event to confirmed AI-derived block, draft, correction, and memory",
    "relationship-correction": (
        "contested relationship, rejected correction, and transitive invalidation to memory"
    ),
    "permission-withdrawal": (
        "withdrawn permission snapshot, source change, and required permission-change invalidation"
    ),
    "source-redaction": (
        "redacted source, source-change invalidation, and a data-minimized audit tombstone"
    ),
}


def render(scenario: str, seed: int) -> str:
    if scenario not in SCENARIOS:
        raise FixtureError(
            f"unknown scenario {scenario!r}; known scenarios: {', '.join(sorted(SCENARIOS))}"
        )
    world = World(scenario, seed)
    SCENARIOS[scenario](world)
    return json.dumps(world.document(), ensure_ascii=False, indent=2) + "\n"


def reference_path(scenario: str) -> Path:
    return REFERENCE_DIR / f"{scenario}.seed-{REFERENCE_SEED}.json"


def run_check(root: Path) -> int:
    stale: list[str] = []
    expected: set[str] = set()
    for scenario in sorted(SCENARIOS):
        target = reference_path(scenario)
        expected.add(target.name)
        first = render(scenario, REFERENCE_SEED)
        if first != render(scenario, REFERENCE_SEED):
            stale.append(f"unstable:   {target.as_posix()} (two renders of one seed differ)")
            continue
        path = root / target
        if not path.exists():
            stale.append(f"missing:    {target.as_posix()}")
        elif path.read_text(encoding="utf-8") != first:
            stale.append(f"stale:      {target.as_posix()}")

    directory = root / REFERENCE_DIR
    if directory.is_dir():
        for candidate in sorted(directory.glob("*.json")):
            if candidate.name not in expected:
                stale.append(f"unexpected: {REFERENCE_DIR.as_posix()}/{candidate.name}")

    if stale:
        print("generated fixture worlds are not current:", file=sys.stderr)
        for item in stale:
            print(f"  {item}", file=sys.stderr)
        print(
            "\nRun: python3 tools/fnb-fixtures.py generate <scenario> --seed 42 --out <path>",
            file=sys.stderr,
        )
        return 1
    print(
        f"fixture worlds current: {len(SCENARIOS)} scenarios at seed {REFERENCE_SEED}, "
        "stable across repeated renders"
    )
    return 0


def run_generate(args: argparse.Namespace, root: Path) -> int:
    text = render(args.scenario, args.seed)
    if not args.out:
        sys.stdout.write(text)
        return 0
    target = Path(args.out)
    if not target.is_absolute():
        target = root / target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"wrote {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fnb-fixtures",
        description=(
            "Generate deterministic synthetic FNB protocol worlds. Output depends "
            "only on the scenario and the seed; no network or product service is used."
        ),
    )
    parser.add_argument("--root", default=".", help="repository checkout root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="list the available scenarios")

    generate = subparsers.add_parser("generate", help="render one synthetic world")
    generate.add_argument("scenario")
    generate.add_argument("--seed", type=int, default=REFERENCE_SEED)
    generate.add_argument("--out", help="write to this path instead of stdout")
    generate.set_defaults(func=run_generate)

    check = subparsers.add_parser(
        "check", help="verify the committed reference worlds are current and stable"
    )
    check.set_defaults(func=lambda args, root: run_check(root))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.root).resolve()
    if args.command == "list":
        for scenario in sorted(SCENARIOS):
            print(f"{scenario}: {SCENARIO_SUMMARY[scenario]}")
        return 0
    try:
        return args.func(args, root)
    except FixtureError as error:
        print(f"fnb-fixtures: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
