#!/usr/bin/env python3
"""Strict, deterministic projector for the TownSquare Vertical POC ledger."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "vertical-poc" / "townsquare-work-events.jsonl"
SCHEMA = ROOT / "docs" / "vertical-poc" / "townsquare-work-event.schema.json"
TARGET = ROOT / "docs" / "townsquare-vertical-poc-roadmap.md"
PROFILE = "rfc8785+townsquare-vertical-poc-safeint/1"
EVENT = "urn:townsquare:vertical-poc:event:"
THREAD = "urn:townsquare:vertical-poc:thread:"
UUID7 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
TIME = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$")
SHA = re.compile(r"^[0-9a-f]{64}$")
EDGES = {"OPEN->WORKING", "OPEN->BLOCKED", "OPEN->CANCELLED", "WORKING->BLOCKED", "WORKING->RESOLVED", "WORKING->CANCELLED", "BLOCKED->WORKING", "BLOCKED->CANCELLED", "RESOLVED->WORKING", "RESOLVED->CLOSED", "RESOLVED->CANCELLED"}
PROVENANCE = {"provider", "model_id", "model_family", "runtime", "runtime_version", "host", "agent_name", "basis"}
PINNED_TRANSITIONS = [
    ("OPEN->WORKING", ["implementer"], ["reason_category", "reason_text"], [], ["system-forward-reason"]),
    ("OPEN->BLOCKED", ["implementer"], ["blocked_attempt_ref", "reason_category", "reason_text", "reason_trigger_ref"], [], ["blocked-attempt-valid", "explicit-reason"]),
    ("OPEN->CANCELLED", ["implementer", "project-owner"], ["reason_category", "reason_text"], [], ["explicit-reason"]),
    ("WORKING->BLOCKED", ["implementer"], ["blocked_attempt_ref", "reason_category", "reason_text", "reason_trigger_ref"], [], ["blocked-attempt-valid", "explicit-reason"]),
    ("WORKING->RESOLVED", ["implementer"], ["artifact_ref", "cites_decision", "evidence_refs", "reason_category", "reason_text"], [{"role":"architect","artifact_type":"design-of-record"}], ["artifact-and-design-decision-current", "system-forward-reason"]),
    ("WORKING->CANCELLED", ["implementer", "project-owner"], ["reason_category", "reason_text"], [], ["explicit-reason"]),
    ("BLOCKED->WORKING", ["implementer"], ["clears_blocked_attempt_ref", "evidence_refs", "reason_category", "reason_text"], [], ["all-blocked-conditions-cleared", "system-forward-reason"]),
    ("BLOCKED->CANCELLED", ["implementer", "project-owner"], ["reason_category", "reason_text"], [], ["explicit-reason"]),
    ("RESOLVED->WORKING", ["project-owner"], ["reason_category", "reason_text", "reason_trigger_ref"], [], ["review-trigger-valid", "explicit-reason"]),
    ("RESOLVED->CLOSED", ["project-owner"], ["cites_decision", "evidence_refs", "reason_category", "reason_text"], [{"role":"architect","artifact_type":"design-of-record"},{"role":"architect","artifact_type":"conformance-ruling"}], ["acceptance-decision-current", "independent-acceptance", "system-forward-reason"]),
    ("RESOLVED->CANCELLED", ["project-owner"], ["reason_category", "reason_text"], [], ["explicit-reason"]),
]

class DuplicateKey(ValueError): pass
def pairs(items):
    result = {}
    for k, v in items:
        if k in result: raise DuplicateKey("duplicate JSON key: " + k)
        result[k] = v
    return result
def loads(raw): return json.loads(raw, object_pairs_hook=pairs)
def _rfc8785_order(value):
    if isinstance(value, list): return [_rfc8785_order(item) for item in value]
    if isinstance(value, dict):
        return {key: _rfc8785_order(value[key]) for key in sorted(value, key=lambda key: key.encode("utf-16be"))}
    return value
def canon(value): return json.dumps(_rfc8785_order(value), ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
def digest(event):
    value = dict(event); value.pop("poc_content_sha256", None)
    return hashlib.sha256(canon(value)).hexdigest()
def references(value):
    if isinstance(value, str): return {value} if value.startswith(EVENT) else set()
    if isinstance(value, list): return set().union(*(references(x) for x in value)) if value else set()
    if isinstance(value, dict): return set().union(*(references(x) for x in value.values())) if value else set()
    return set()
def integers(value, errors, where):
    if isinstance(value, bool): return
    if isinstance(value, int):
        if abs(value) > 9007199254740991: errors.append(where + ": unsafe integer")
    elif isinstance(value, float): errors.append(where + ": non-integer number")
    elif isinstance(value, list):
        for n, x in enumerate(value): integers(x, errors, f"{where}[{n}]")
    elif isinstance(value, dict):
        for k, x in value.items(): integers(x, errors, f"{where}.{k}")
def esc(value): return str(value).replace("|", "\\|").replace("\n", " ")

def read_events(errors):
    try: raw = LEDGER.read_bytes()
    except OSError as exc: errors.append(str(exc)); return []
    if raw.startswith(b"\xef\xbb\xbf"): errors.append("ledger has BOM")
    if b"\r" in raw: errors.append("ledger has CR")
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"): errors.append("ledger must have exactly one final LF")
    try: text = raw.decode("utf-8")
    except UnicodeDecodeError as exc: errors.append("invalid UTF-8: " + str(exc)); return []
    events = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line: errors.append(f"blank ledger record {number}"); continue
        try: events.append(loads(line))
        except Exception as exc: errors.append(f"record {number}: {exc}")
    return events

def validate(events, errors):
    try:
        schema = loads(SCHEMA.read_text(encoding="utf-8"))
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema": errors.append("schema meta-schema missing")
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
    except Exception as exc: errors.append("schema: " + str(exc))
    else:
        for number, event in enumerate(events):
            for error in validator.iter_errors(event): errors.append(f"event {number}: schema {error.message}")
    ids = {}; chains = defaultdict(list)
    for n, e in enumerate(events):
        where = f"event {n}"
        integers(e, errors, where)
        required = ["schema_version", "canonicalization_profile", "poc_event_uid", "poc_thread_uid", "poc_seq", "poc_global_order", "poc_content_sha256", "event_type", "state", "actor", "actor_provenance", "claimed_at", "basis_kind"]
        for key in required:
            if key not in e: errors.append(f"{where}: missing {key}")
        if e.get("schema_version") != "1" or e.get("canonicalization_profile") != PROFILE: errors.append(f"{where}: profile/version")
        if e.get("poc_global_order") != n: errors.append(f"{where}: global order")
        uid, tid = e.get("poc_event_uid", ""), e.get("poc_thread_uid", "")
        if not isinstance(uid, str) or not uid.startswith(EVENT) or not UUID7.fullmatch(uid[len(EVENT):]): errors.append(f"{where}: event identity")
        if not isinstance(tid, str) or not tid.startswith(THREAD) or not UUID7.fullmatch(tid[len(THREAD):]): errors.append(f"{where}: thread identity")
        if uid in ids: errors.append(f"{where}: duplicate event identity")
        ids[uid] = e; chains[tid].append(e)
        if not SHA.fullmatch(e.get("poc_content_sha256", "")) or digest(e) != e.get("poc_content_sha256"): errors.append(f"{where}: content hash")
        if not isinstance(e.get("claimed_at"), str) or not TIME.fullmatch(e["claimed_at"]): errors.append(f"{where}: claimed time")
        if e.get("basis_kind") not in {"measured", "inferred", "assumed", "reported-by"}: errors.append(f"{where}: basis kind")
        if e.get("basis_kind") in {"measured", "reported-by"} and not e.get("basis_ref"): errors.append(f"{where}: missing basis reference")
        if e.get("basis_kind") == "measured" and not re.search(r"(?:#sha256=[0-9a-f]{64}$|git:[0-9a-f]{40}:)", str(e.get("basis_ref", ""))): errors.append(f"{where}: mutable measured basis")
        try:
            p = loads(e.get("actor_provenance", ""))
            if not isinstance(p, dict) or not PROVENANCE <= p.keys(): errors.append(f"{where}: actor provenance")
        except Exception: errors.append(f"{where}: actor provenance")
    for e in events:
        for ref in references(e):
            if ref == e.get("poc_event_uid"): continue
            target = ids.get(ref)
            if target is None or target.get("poc_global_order", 10**20) >= e.get("poc_global_order", -1): errors.append(f"event {e.get('poc_global_order')}: bad reference")
    workflow = [e for e in events if e.get("decision_type") == "workflow-definition"]
    if len(workflow) != 1: errors.append("need exactly one workflow decision")
    workflow_id = workflow[0]["poc_event_uid"] if len(workflow) == 1 else None
    for tid, chain in chains.items():
        chain.sort(key=lambda x: x.get("poc_seq", -1))
        if [x.get("poc_seq") for x in chain] != list(range(len(chain))): errors.append(f"thread {tid}: sequence")
        if not chain: continue
        first = chain[0]
        if first.get("event_type") == "unit-of-work":
            if first.get("state") != "OPEN" or first.get("workflow_ref") != workflow_id: errors.append(f"thread {tid}: opening")
            if first.get("role_acted_under") != "project-owner": errors.append(f"thread {tid}: opening role")
            if not isinstance(first.get("definition_of_done"), list) or not all(isinstance(x, str) for x in first["definition_of_done"]): errors.append(f"thread {tid}: definition of done")
        elif not (first.get("event_type") == "decision" and first.get("state") == "RECORDED"): errors.append(f"thread {tid}: decision opening")
        if "base_event_id" in first or "expected_head" in first: errors.append(f"thread {tid}: opening head")
        for previous, current in zip(chain, chain[1:]):
            if f"{previous.get('state')}->{current.get('state')}" not in EDGES: errors.append(f"thread {tid}: illegal transition")
            if current.get("base_event_id") != previous.get("poc_event_uid") or current.get("expected_head") != previous.get("poc_event_uid"): errors.append(f"thread {tid}: head")
            if current.get("role_acted_under") != "implementer": errors.append(f"thread {tid}: transition role")
            if not isinstance(current.get("reason_text"), str) or not current["reason_text"]: errors.append(f"thread {tid}: transition reason")
    if len(workflow) == 1:
        actual = workflow[0].get("workflow", {}).get("workflow_transitions")
        expected = [{"transition_id": edge, "from_state": edge.split("->")[0], "to_state": edge.split("->")[1], "allowed_roles": roles, "required_fields": fields, "requirements": requirements, "validators": validators} for edge, roles, fields, requirements, validators in PINNED_TRANSITIONS]
        if actual != expected: errors.append("workflow: pinned definition changed")
    return ids, chains

def render(events, chains):
    opens = []
    for chain in chains.values():
        chain.sort(key=lambda x: x["poc_seq"])
        if chain[0].get("event_type") != "unit-of-work": continue
        opening, last = chain[0], chain[-1]
        def latest(key):
            for event in reversed(chain):
                if key in event: return event[key]
            return "UNKNOWN"
        owners = "; ".join(f"{key.replace('_', ' ')}: {latest(key) if key == 'owner' else opening.get(key, 'UNKNOWN')}" for key in ("owner", "creation_owner", "fulfillment_owner", "review_owner", "operator_acceptance_owner"))
        evidence = latest("basis_ref")
        opens.append((opening["poc_ref"], [latest("milestone"), opening["poc_ref"], latest("vertical_level"), opening.get("goal", "UNKNOWN"), last["state"], latest("delivery_status"), evidence, latest("current_gate"), latest("next_action"), last["claimed_at"], owners]))
    opens.sort()
    columns = ["Milestone", "POC ref", "Level", "Title", "Lifecycle", "Delivery status", "Evidence/basis", "Review/gate", "Next action", "Reported at", "Owners (non-authoritative)"]
    lines = ["# TownSquare Vertical POC roadmap", "", "Generated projection of the append-only POC ledger. It is not an authority, workflow gate, or native Vertical record.", "", "## Milestones 0–5", "", "0 — Program contract; 1 — Deployable MVP; 2 — Shared contracts; 3 — Governing package; 4 — Convergence and integration; 5 — Bounded pilot and acceptance.", "", "| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    lines += ["| " + " | ".join(esc(x) for x in row) + " |" for _, row in opens]
    lines += ["", "## Boundary", "", "TownSquare remains the coordination record, Vertical remains the work-model target, and Wonderland is read-only. Labels, owners, milestones, and dependencies are reporting metadata only.", ""]
    return "\n".join(lines).encode("utf-8")

def main():
    errors = []; events = read_events(errors)
    if events: _, chains = validate(events, errors)
    else: chains = {}
    if errors:
        for error in errors: print(error, file=sys.stderr)
        return 1
    content = render(events, chains)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".vertical-poc-", dir=TARGET.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    return 0
if __name__ == "__main__": sys.exit(main())
