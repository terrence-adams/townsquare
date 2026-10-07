"""Acceptance tests for the TownSquare Vertical-model POC tracker.

These tests intentionally describe the public file contract, rather than an
implementation API.  The renderer is invoked in a disposable copy of the POC
artifacts using its documented default paths.  That keeps malformed-ledger
tests from mutating the Git-tracked ledger or roadmap.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "vertical-poc"
LEDGER = DOCS / "townsquare-work-events.jsonl"
SCHEMA = DOCS / "townsquare-work-event.schema.json"
README = DOCS / "README.md"
RENDERER = ROOT / "tools" / "render-vertical-poc-roadmap.py"
ROADMAP = ROOT / "docs" / "townsquare-vertical-poc-roadmap.md"
DESIGN = DOCS / "townsquare-vertical-poc-design.md"

PROFILE = "rfc8785+townsquare-vertical-poc-safeint/1"
SAFE_INT = 9007199254740991
POC_EVENT_PREFIX = "urn:townsquare:vertical-poc:event:"
POC_THREAD_PREFIX = "urn:townsquare:vertical-poc:thread:"
UUIDV7 = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
RFC3339_OFFSET = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
REQUIRED_PROVENANCE = {
    "provider", "model_id", "model_family", "runtime", "runtime_version",
    "host", "agent_name", "basis",
}
WORKFLOW_STATES = ["OPEN", "WORKING", "BLOCKED", "RESOLVED", "CLOSED", "CANCELLED"]
WORKFLOW_EDGES = {
    "OPEN->WORKING", "OPEN->BLOCKED", "OPEN->CANCELLED",
    "WORKING->BLOCKED", "WORKING->RESOLVED", "WORKING->CANCELLED",
    "BLOCKED->WORKING", "BLOCKED->CANCELLED",
    "RESOLVED->WORKING", "RESOLVED->CLOSED", "RESOLVED->CANCELLED",
}
REQUIRED_COLUMNS = [
    "Milestone", "POC ref", "Level", "Title", "Lifecycle", "Delivery status",
    "Evidence/basis", "Review/gate", "Next action", "Reported at",
    "Owners (non-authoritative)",
]
DELIVERABLE_REFS = {
    "VR-20261006-townsquare-070", "VR-20261006-townsquare-040",
    "VR-20261006-townsquare-060",
    "VR-20261006-townsquare-120", "VR-20261006-townsquare-130",
    "VR-20261006-townsquare-140", "VR-20261006-townsquare-150",
    "VR-20261006-townsquare-170", "VR-20261006-townsquare-180",
}


class DuplicateKey(ValueError):
    pass


def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_loads(text: str) -> Any:
    return json.loads(text, object_pairs_hook=no_duplicates)


def canonical_bytes(value: dict[str, Any]) -> bytes:
    """RFC 8785 object key order is UTF-16 code-unit order; POC bans floats."""
    def ordered(item: Any) -> Any:
        if isinstance(item, dict):
            return {key: ordered(item[key]) for key in sorted(item, key=lambda key: key.encode("utf-16be"))}
        if isinstance(item, list):
            return [ordered(entry) for entry in item]
        return item
    return json.dumps(ordered(value), ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def event_hash(event: dict[str, Any]) -> str:
    payload = copy.deepcopy(event)
    payload.pop("poc_content_sha256", None)
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def load_ledger(path: Path = LEDGER) -> list[dict[str, Any]]:
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "ledger must not have a UTF-8 BOM"
    assert b"\r" not in raw, "ledger must use LF only"
    assert raw.endswith(b"\n"), "ledger must end with exactly one LF"
    assert not raw.endswith(b"\n\n"), "ledger must not contain a blank final record"
    text = raw.decode("utf-8")
    return [strict_loads(line) for line in text[:-1].split("\n")]


def write_ledger(path: Path, events: list[dict[str, Any]]) -> None:
    for event in events:
        event["poc_content_sha256"] = event_hash(event)
    path.write_bytes(b"".join(canonical_bytes(event) + b"\n" for event in events))


def assert_integer_tree(test: unittest.TestCase, value: Any) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        test.assertLessEqual(abs(value), SAFE_INT)
    elif isinstance(value, float):
        test.fail("POC ledger accepts a non-integer JSON number")
    elif isinstance(value, dict):
        for nested in value.values():
            assert_integer_tree(test, nested)
    elif isinstance(value, list):
        for nested in value:
            assert_integer_tree(test, nested)


def all_poc_refs(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value} if value.startswith(POC_EVENT_PREFIX) else set()
    if isinstance(value, list):
        return set().union(*(all_poc_refs(v) for v in value)) if value else set()
    if isinstance(value, dict):
        return set().union(*(all_poc_refs(v) for v in value.values())) if value else set()
    return set()


class VerticalPocTestCase(unittest.TestCase):
    def require_implementation(self) -> None:
        missing = [str(p.relative_to(ROOT)) for p in (LEDGER, SCHEMA, README, RENDERER, ROADMAP) if not p.is_file()]
        if missing:
            self.skipTest("Vertical POC implementation artifacts are not present: " + ", ".join(missing))

    def isolated_workspace(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        self.require_implementation()
        td = tempfile.TemporaryDirectory()
        work = Path(td.name) / "tracker"
        (work / "docs" / "vertical-poc").mkdir(parents=True)
        (work / "tools").mkdir()
        for source in (LEDGER, SCHEMA, README, DESIGN):
            shutil.copy2(source, work / source.relative_to(ROOT))
        shutil.copy2(RENDERER, work / RENDERER.relative_to(ROOT))
        return td, work

    def render(self, work: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(work / "tools" / RENDERER.name)],
            cwd=work, text=True, capture_output=True, timeout=30,
            env={**os.environ, "TZ": "UTC"},
        )


class TestArtifactPresence(VerticalPocTestCase):
    def test_five_implementation_artifacts_exist(self) -> None:
        missing = [str(p.relative_to(ROOT)) for p in (LEDGER, SCHEMA, README, RENDERER, ROADMAP) if not p.is_file()]
        self.assertFalse(missing, "Bruce-owned POC artifacts missing: " + ", ".join(missing))


class TestLedgerContract(VerticalPocTestCase):
    def setUp(self) -> None:
        self.require_implementation()
        self.events = load_ledger()

    def test_schema_and_canonical_hashes(self) -> None:
        schema = strict_loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema.get("$schema"))
        self.assertEqual("object", schema.get("type"))
        self.assertFalse(schema.get("additionalProperties", True))
        self.assertEqual("1", schema.get("properties", {}).get("schema_version", {}).get("const"))
        self.assertEqual(PROFILE, schema.get("properties", {}).get("canonicalization_profile", {}).get("const"))
        for key in ("poc_event_uid", "poc_thread_uid", "poc_seq", "poc_global_order", "poc_content_sha256", "event_type", "state", "actor", "actor_provenance", "role_acted_under", "claimed_at", "basis_kind", "basis_ref"):
            self.assertIn(key, schema.get("properties", {}), f"schema lacks {key}")
        for event in self.events:
            self.assertEqual("1", event.get("schema_version"))
            self.assertEqual(PROFILE, event.get("canonicalization_profile"))
            self.assertRegex(event.get("poc_content_sha256", ""), r"^[0-9a-f]{64}$")
            self.assertEqual(event_hash(event), event["poc_content_sha256"])
            assert_integer_tree(self, event)

    def test_identity_and_json_string_provenance(self) -> None:
        seen_events: set[str] = set()
        for event in self.events:
            event_uid, thread_uid = event["poc_event_uid"], event["poc_thread_uid"]
            self.assertTrue(event_uid.startswith(POC_EVENT_PREFIX))
            self.assertTrue(thread_uid.startswith(POC_THREAD_PREFIX))
            self.assertRegex(event_uid.removeprefix(POC_EVENT_PREFIX), UUIDV7)
            self.assertRegex(thread_uid.removeprefix(POC_THREAD_PREFIX), UUIDV7)
            self.assertNotIn(event_uid, seen_events)
            seen_events.add(event_uid)
            self.assertNotEqual(event.get("poc_ref"), event_uid)
            self.assertNotEqual(event.get("poc_ref"), thread_uid)
            provenance = strict_loads(event["actor_provenance"])
            self.assertIsInstance(event["actor_provenance"], str)
            self.assertTrue(REQUIRED_PROVENANCE <= provenance.keys())
            self.assertRegex(event["claimed_at"], RFC3339_OFFSET)
            self.assertIn(event["basis_kind"], {"measured", "inferred", "assumed", "reported-by"})
            if event["basis_kind"] in {"measured", "reported-by"}:
                self.assertTrue(event.get("basis_ref"))

    def test_ordering_references_and_chains(self) -> None:
        by_uid = {event["poc_event_uid"]: event for event in self.events}
        self.assertEqual(list(range(len(self.events))), [event["poc_global_order"] for event in self.events])
        chains: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in self.events:
            chains[event["poc_thread_uid"]].append(event)
            for ref in all_poc_refs(event):
                if ref == event["poc_event_uid"]:
                    continue
                self.assertIn(ref, by_uid, f"dangling POC ref {ref}")
                self.assertLess(by_uid[ref]["poc_global_order"], event["poc_global_order"], "forward POC reference")
        for chain in chains.values():
            chain.sort(key=lambda event: event["poc_seq"])
            self.assertEqual(list(range(len(chain))), [event["poc_seq"] for event in chain])
            opening = chain[0]
            if opening.get("event_type") == "unit-of-work":
                self.assertEqual("OPEN", opening["state"])
            else:
                self.assertEqual("decision", opening.get("event_type"))
                self.assertEqual("RECORDED", opening.get("state"))
            self.assertNotIn("base_event_id", opening)
            self.assertNotIn("expected_head", opening)
            for previous, current in zip(chain, chain[1:]):
                edge = f"{previous['state']}->{current['state']}"
                self.assertIn(edge, WORKFLOW_EDGES)
                self.assertEqual(previous["poc_event_uid"], current.get("base_event_id"))
                self.assertEqual(previous["poc_event_uid"], current.get("expected_head"))

    def test_workflow_record_and_openings(self) -> None:
        workflow = [e for e in self.events if e.get("decision_type") == "workflow-definition"]
        self.assertEqual(1, len(workflow))
        workflow_event = workflow[0]
        self.assertEqual("VR-20261006-townsquare-000", workflow_event.get("poc_ref"))
        self.assertEqual("decision", workflow_event.get("event_type"))
        self.assertEqual("RECORDED", workflow_event.get("state"))
        body = workflow_event.get("workflow") or workflow_event
        self.assertEqual("townsquare-vertical-poc-workflow/1", body.get("workflow_profile"))
        self.assertEqual(WORKFLOW_STATES, body.get("workflow_states"))
        transitions = body.get("workflow_transitions")
        self.assertIsInstance(transitions, list)
        self.assertEqual(11, len(transitions))
        self.assertEqual(WORKFLOW_EDGES, {item.get("transition_id") for item in transitions})
        for transition in transitions:
            self.assertEqual(
                {"transition_id", "from_state", "to_state", "allowed_roles", "required_fields", "requirements", "validators"},
                set(transition),
            )
            self.assertEqual(f"{transition['from_state']}->{transition['to_state']}", transition["transition_id"])
            self.assertTrue(transition["allowed_roles"])
            self.assertTrue(set(transition["allowed_roles"]) <= {"implementer", "project-owner"})
            self.assertEqual(len(transition["allowed_roles"]), len(set(transition["allowed_roles"])))
            self.assertEqual(len(transition["required_fields"]), len(set(transition["required_fields"])))
            self.assertEqual(len(transition["validators"]), len(set(transition["validators"])))
            for requirement in transition["requirements"]:
                self.assertEqual({"role", "artifact_type"}, set(requirement))
        for event in self.events:
            if event.get("event_type") == "unit-of-work" and event.get("poc_seq") == 0:
                self.assertEqual(workflow_event["poc_event_uid"], event.get("workflow_ref"))
                self.assertIsInstance(event.get("definition_of_done"), list)
                self.assertTrue(all(isinstance(v, str) for v in event["definition_of_done"]))

    def test_seed_states_and_non_authority_metadata(self) -> None:
        openings = {e["poc_ref"]: e for e in self.events if e.get("poc_seq") == 0 and e.get("poc_ref")}
        self.assertTrue(DELIVERABLE_REFS <= openings.keys())
        self.assertNotIn("VR-20261006-townsquare-050", DELIVERABLE_REFS)
        latest: dict[str, dict[str, Any]] = {}
        for event in self.events:
            latest[event["poc_thread_uid"]] = event
        latest_by_ref = {opening["poc_ref"]: latest[opening["poc_thread_uid"]] for opening in openings.values()}
        for ref in ("VR-20261006-townsquare-060", "VR-20261006-townsquare-061", "VR-20261006-townsquare-062", "VR-20261006-townsquare-040", "VR-20261006-townsquare-043", "VR-20261006-townsquare-050", "VR-20261006-townsquare-051", "VR-20261006-townsquare-052", "VR-20261006-townsquare-070", "VR-20261006-townsquare-072"):
            self.assertEqual("WORKING", latest_by_ref[ref]["state"], ref)
        for ref in ("VR-20261006-townsquare-063",):
            self.assertEqual("WORKING", latest_by_ref[ref]["state"], ref)
        for ref in ("VR-20261006-townsquare-073", "VR-20261006-townsquare-074", "VR-20261006-townsquare-075", "VR-20261006-townsquare-076"):
            self.assertEqual("OPEN", latest_by_ref[ref]["state"], ref)
        self.assertFalse(any(event["state"] in {"RESOLVED", "CLOSED"} for event in self.events))
        for event in self.events:
            self.assertNotEqual("BLOCKED", event.get("delivery_status"), "status label must not replace lifecycle")
        for ref in DELIVERABLE_REFS:
            event = openings[ref]
            for key in ("milestone", "creation_owner", "fulfillment_owner", "review_owner", "operator_acceptance_owner"):
                self.assertTrue(event.get(key), f"{ref} is missing required reporting metadata {key}")
            self.assertEqual("operator", str(event["operator_acceptance_owner"]).lower())

    def test_exact_seed_evidence_status_and_actionable_governance(self) -> None:
        openings = {e["poc_ref"]: e for e in self.events if e.get("poc_seq") == 0 and e.get("poc_ref")}
        for ref in ("VR-20261006-townsquare-010", "VR-20261006-townsquare-020", "VR-20261006-townsquare-030"):
            self.assertEqual("source-implemented", openings[ref].get("delivery_status"), ref)
        backup = openings["VR-20261006-townsquare-052"]
        self.assertEqual("measured", backup.get("basis_kind"))
        self.assertRegex(backup.get("basis_ref", ""), r"^artifact:.*#sha256=[0-9a-f]{64}$")
        for ref in ("VR-20261006-townsquare-060", "VR-20261006-townsquare-061", "VR-20261006-townsquare-062"):
            event = openings[ref]
            self.assertEqual("measured", event.get("basis_kind"), ref)
            self.assertEqual(
                "artifact:docs/governance/reviews/eddie-brock-governance-review-6239f12-20261006.md#sha256=9a503268fd1c6180d25d4da822db8174ba2378ee7ed32f5795fd85005fead104",
                event.get("basis_ref"), ref,
            )
            self.assertNotIn("no lifecycle authority", event.get("current_gate", "").lower())
            self.assertNotIn("record a checked", event.get("next_action", "").lower())
            self.assertTrue(event.get("current_gate"))
            self.assertTrue(event.get("next_action"))

    def test_rfc8785_utf16_key_order_vector(self) -> None:
        self.assertEqual(
            '{"😀":"astral","\ue000":"bmp"}'.encode("utf-8"),
            canonical_bytes({"\ue000": "bmp", "😀": "astral"}),
        )

    def test_readme_operating_contract_is_complete_and_readable(self) -> None:
        text = README.read_text(encoding="utf-8")
        for token in (
            "schema_version", "poc_ref", "poc_event_uid", "poc_thread_uid", "poc_seq",
            "poc_global_order", "poc_content_sha256", "canonicalization_profile", "actor_provenance",
            "role_acted_under", "claimed_at", "basis_kind", "basis_ref", "base_event_id",
            "expected_head", "vertical_level", "parent_ref", "depends_on_refs", "owner",
            "creation_owner", "fulfillment_owner", "review_owner", "operator_acceptance_owner",
            "OPEN->WORKING", "RESOLVED->CLOSED", "BLOCKED->WORKING", "compare-and-append",
            "migration-map.json", "RFC 8785",
        ):
            self.assertIn(token, text, f"README must define {token}")


class TestRendererContract(VerticalPocTestCase):
    def assert_invalid_preserves_target(self, work: Path, detail: str) -> None:
        target = work / "docs" / "townsquare-vertical-poc-roadmap.md"
        target.write_bytes(b"preserve-this-output\n")
        result = self.render(work)
        self.assertNotEqual(0, result.returncode, detail)
        self.assertEqual(b"preserve-this-output\n", target.read_bytes(), detail)

    def test_invalid_schema_meta_schema_type_fails_before_render(self) -> None:
        td, work = self.isolated_workspace()
        with td:
            schema = work / "docs" / "vertical-poc" / SCHEMA.name
            schema.write_text('{"$schema":"https://json-schema.org/draft/2020-12/schema","type":7}\n', encoding="utf-8", newline="\n")
            self.assert_invalid_preserves_target(work, "invalid schema keyword type was accepted without full meta-schema validation")

    def test_missing_role_acted_under_fails_before_render(self) -> None:
        td, work = self.isolated_workspace()
        with td:
            ledger = work / "docs" / "vertical-poc" / LEDGER.name
            events = load_ledger(ledger)
            event = next(e for e in events if e.get("event_type") == "unit-of-work")
            event.pop("role_acted_under")
            write_ledger(ledger, events)
            self.assert_invalid_preserves_target(work, "missing role_acted_under was accepted")

    def test_missing_transition_reason_text_fails_before_render(self) -> None:
        td, work = self.isolated_workspace()
        with td:
            ledger = work / "docs" / "vertical-poc" / LEDGER.name
            events = load_ledger(ledger)
            event = next(e for e in events if e.get("event_type") == "unit-of-work" and e.get("poc_seq") == 1)
            self.assertIn("reason_text", event, "seed must make this an isolated required-field probe")
            event.pop("reason_text")
            write_ledger(ledger, events)
            self.assert_invalid_preserves_target(work, "transition missing its required reason_text was accepted")

    def test_mutable_measured_basis_ref_fails_before_render(self) -> None:
        td, work = self.isolated_workspace()
        with td:
            ledger = work / "docs" / "vertical-poc" / LEDGER.name
            events = load_ledger(ledger)
            event = next(e for e in events if e.get("basis_kind") == "measured")
            event["basis_ref"] = "artifact:docs/governance/latest-review.md"
            write_ledger(ledger, events)
            self.assert_invalid_preserves_target(work, "mutable measured basis_ref was accepted")

    def test_changed_pinned_workflow_role_fails_before_render(self) -> None:
        td, work = self.isolated_workspace()
        with td:
            ledger = work / "docs" / "vertical-poc" / LEDGER.name
            events = load_ledger(ledger)
            workflow = next(e for e in events if e.get("decision_type") == "workflow-definition")
            workflow["workflow"]["workflow_transitions"][0]["allowed_roles"] = ["project-owner"]
            write_ledger(ledger, events)
            self.assert_invalid_preserves_target(work, "changed pinned workflow role was accepted")

    def test_schema_rejects_unknown_property(self) -> None:
        td, work = self.isolated_workspace()
        with td:
            ledger = work / "docs" / "vertical-poc" / LEDGER.name
            events = load_ledger(ledger)
            event = next(e for e in events if e.get("event_type") == "unit-of-work")
            event["undeclared_schema_probe"] = "must be rejected by additionalProperties:false"
            write_ledger(ledger, events)
            self.assert_invalid_preserves_target(work, "undeclared event property was accepted")

    def test_schema_rejects_out_of_range_safe_integer(self) -> None:
        td, work = self.isolated_workspace()
        with td:
            ledger = work / "docs" / "vertical-poc" / LEDGER.name
            events = load_ledger(LEDGER)
            event = next(e for e in events if e.get("event_type") == "unit-of-work")
            event["poc_seq"] = SAFE_INT + 1
            write_ledger(ledger, events)
            self.assert_invalid_preserves_target(work, "out-of-range safe integer was accepted")

    def test_repeat_render_is_byte_identical_and_has_required_table(self) -> None:
        td, work = self.isolated_workspace()
        with td:
            first = self.render(work)
            self.assertEqual(0, first.returncode, first.stderr)
            roadmap = work / "docs" / "townsquare-vertical-poc-roadmap.md"
            first_bytes = roadmap.read_bytes()
            second = self.render(work)
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertEqual(first_bytes, roadmap.read_bytes())
            text = first_bytes.decode("utf-8")
            header = "| " + " | ".join(REQUIRED_COLUMNS) + " |"
            self.assertIn(header, text)
            self.assertNotRegex(text, r"(?i)(rendered at|generated at|\bnow\b)")

    def test_fail_atomic_for_malformed_and_dangling_input(self) -> None:
        td, work = self.isolated_workspace()
        with td:
            target = work / "docs" / "townsquare-vertical-poc-roadmap.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            sentinel = b"do-not-replace-on-invalid-ledger\n"
            target.write_bytes(sentinel)
            ledger = work / "docs" / "vertical-poc" / LEDGER.name
            ledger.write_bytes(b'{"x":1,"x":2}\n')
            result = self.render(work)
            self.assertNotEqual(0, result.returncode)
            self.assertEqual(sentinel, target.read_bytes())
            target.unlink()
            result = self.render(work)
            self.assertNotEqual(0, result.returncode)
            self.assertFalse(target.exists(), "renderer created output after failed full validation")

    def test_rejects_dangling_and_invalid_transition_after_rehash(self) -> None:
        td, work = self.isolated_workspace()
        with td:
            ledger = work / "docs" / "vertical-poc" / LEDGER.name
            target = work / "docs" / "townsquare-vertical-poc-roadmap.md"
            target.write_bytes(b"unchanged\n")
            events = load_ledger(ledger)
            opening = next(event for event in events if event.get("event_type") == "unit-of-work" and event["poc_seq"] == 0)
            opening["workflow_ref"] = POC_EVENT_PREFIX + "01800000-0000-7000-8000-000000000000"
            write_ledger(ledger, events)
            self.assertNotEqual(0, self.render(work).returncode, "dangling workflow reference accepted")
            self.assertEqual(b"unchanged\n", target.read_bytes())

            events = load_ledger(LEDGER)
            transition = next(event for event in events if event.get("event_type") == "unit-of-work" and event["poc_seq"] == 1)
            transition["state"] = "CLOSED"  # OPEN->CLOSED is not one of the eleven edges.
            write_ledger(ledger, events)
            self.assertNotEqual(0, self.render(work).returncode, "unlisted transition accepted")
            self.assertEqual(b"unchanged\n", target.read_bytes())

    def test_metadata_change_does_not_create_a_transition_or_authority(self) -> None:
        td, work = self.isolated_workspace()
        with td:
            ledger = work / "docs" / "vertical-poc" / LEDGER.name
            original_events = load_ledger(ledger)
            changed_events = copy.deepcopy(original_events)
            opening = next(event for event in changed_events if event.get("event_type") == "unit-of-work" and event["poc_seq"] == 0)
            old_state = opening["state"]
            opening["owner"] = "metadata-only-test-owner"
            opening["milestone"] = "metadata-only-test-milestone"
            opening["depends_on_refs"] = []
            write_ledger(ledger, changed_events)
            result = self.render(work)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(old_state, load_ledger(ledger)[opening["poc_global_order"]]["state"])
            projection = (work / "docs" / "townsquare-vertical-poc-roadmap.md").read_text(encoding="utf-8")
            self.assertIn("metadata-only-test-owner", projection)
            self.assertIn("metadata-only-test-milestone", projection)

    def test_rejects_lf_and_numeric_violations_before_render(self) -> None:
        td, work = self.isolated_workspace()
        with td:
            ledger = work / "docs" / "vertical-poc" / LEDGER.name
            target = work / "docs" / "townsquare-vertical-poc-roadmap.md"
            target.write_bytes(b"stable\n")
            for payload in (b'\xef\xbb\xbf{}\n', b'{}\r\n', b'{"n":1.0}\n', b'{"n":true}\n', b'{}'):
                ledger.write_bytes(payload)
                result = self.render(work)
                self.assertNotEqual(0, result.returncode, payload)
                self.assertEqual(b"stable\n", target.read_bytes(), payload)

    def test_renderer_has_no_deployment_or_wall_clock_path(self) -> None:
        self.require_implementation()
        source = RENDERER.read_text(encoding="utf-8").lower()
        for forbidden in ("docker compose", "kubectl", "powercfg", "cutover", "rollback", "datetime.now", "time.time("):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
