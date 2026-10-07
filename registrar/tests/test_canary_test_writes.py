"""Core POC contract for isolated, explicitly non-authoritative writes."""

from registrar.tests.mvp_fixture import NativeLedgerCase, OPENING


class CanaryTestWriteTests(NativeLedgerCase):
    def test_verified_canary_grant_allows_only_its_exact_host_action_and_thread(self):
        self.ledger.clear_authority_proof()
        payload = {
            **OPENING,
            "thread_id": "canary-host-routing",
            "owner": "venom",
            "addressee": "wolverine",
        }
        receipt = self.receipt("venom", "request:open", payload["thread_id"], "new")
        self.assert_code(
            "context_required",
            self.ledger.post_event,
            "venom", "without-canary-grant", receipt, "new", payload,
        )

        # The failed attempt does not consume the receipt because authority is
        # resolved before any event effect.  A verified CANARY_TEST proof can
        # therefore authorize exactly this isolated fixture action.
        proof = {
            "authority_class": "CANARY_TEST",
            "audience": "townsquare-canary-ledger-api",
            "service_id": "townsquare-ledger-v0",
            "key_id": "townsquare-canary-test:poc",
            "nonce": "canary-test-nonce-0000000001",
            "scope": {"action": "request:open", "object_id": payload["thread_id"]},
        }
        result = self.ledger.post_event(
            "venom", "with-canary-grant", receipt, "new", payload,
            verified_canary_test_proof=proof,
        )
        self.assertEqual("CANARY_TEST", result["authority_class"])
        self.assertEqual("NON-AUTHORITATIVE", result["runtime_authority"])
        event = self.ledger.get_thread(
            payload["thread_id"], principal="venom", capabilities={"post:read"},
        )["events"][0]
        self.assertEqual("canary-test:request:open", event["authority_scope"])

    def test_canary_grant_with_wrong_scope_remains_blocked(self):
        self.ledger.clear_authority_proof()
        payload = {
            **OPENING,
            "thread_id": "canary-scope-negative",
            "owner": "venom",
            "addressee": "wolverine",
        }
        receipt = self.receipt("venom", "request:open", payload["thread_id"], "new")
        proof = {
            "authority_class": "CANARY_TEST",
            "audience": "townsquare-canary-ledger-api",
            "service_id": "townsquare-ledger-v0",
            "key_id": "townsquare-canary-test:poc",
            "nonce": "canary-test-nonce-0000000002",
            "scope": {"action": "request:resolve", "object_id": payload["thread_id"]},
        }
        self.assert_code(
            "context_required",
            self.ledger.post_event,
            "venom", "wrong-canary-scope", receipt, "new", payload,
            verified_canary_test_proof=proof,
        )
