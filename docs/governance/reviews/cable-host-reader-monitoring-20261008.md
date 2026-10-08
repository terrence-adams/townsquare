# Cable host-reader monitoring record — 2026-10-08

**work item:** `VR-20261008-townsquare-181`  
**implementation branch:** `cable/townsquare-host-reader-20261008`  
**reviewer:** Eddie Brock / Codex seat on Venom  
**current disposition:** `IMPLEMENTATION_REVIEW_PASS` — Story remains `WORKING`; merge, deployment, and operator acceptance have not occurred

## Operator authority and specifications

The operator directly authorized Eddie to control this implementation handoff:

> I am authorizing you to oversee and dictate the work and review and provide feedback and guidance as to the implementation per the operator's designated specifications and desire to have this MVP up and running for the Canary project.

The operator then directed the monitoring standard:

> You have to keep an eye on the agents for Claude and Anthropic. They have a tendency to create bloat and do reviews on work that hasn't been done, and a tendency to not follow through on orders and guidance. So I want you to coordinate and monitor Ezetti Brock and ensure that they're adhering to the specifications and the guidance, and then reference my directives as proof, as well as quoting the new enforced charter for the Town Square and any supporting documents like rules of engagement.

The current MVP directive also remains applicable: prioritize working core functionality and defer concerns that do not affect it.

The operator subsequently adopted a Vertical admission rule for Cable: no implementation, investigation, design, review, testing, or operational work proceeds unless it has a matching approved Feature or Story assigned to an agent. The durable Cable rule is recorded in `docs/vertical-poc/cable-agent-story-gate-20261008.md`. The current reader work is admitted under `VR-20261008-townsquare-181`; adjacent work is not.

## Governing source

TownSquare Charter v1.0 was adopted and made effective by operator decision `TS-CHARTER-1.0-ADOPTION-20261007T0540060363929Z`. The adoption record identifies release commit `14a91f41da3f63a14e427e573f3fe4e0a40f1925` and adopts all seven release components together.

Applicable adopted rules:

> **TSC-ROE-01 MUST — retrieve.** Before a consequential action, retrieve current record, adopted governance, dependency set, scope, criteria, and required evidence.

> **TSC-WRK-01 MUST — accountable work.** A Request has an accountable agent, current addressee, and (when acceptance is required) versioned criteria before resolution. Delegation changes addressee, never accountability. The operator is not an ordinary owner or addressee.

> **TSC-WRK-02 MUST — independent closure.** `RESOLVED` is an evidence-backed completion claim. `CLOSED` requires a cited decision by an authorized acceptor who is outside the complete authorship set of the accepted work.

> **TSC-ROE-05 MUST — close independently.** The acceptor is outside the complete authorship set and cites criterion dispositions and evidence.

> **TSC-REC-02 MUST — append-only evidence.** A committed object is never edited or deleted. Correction, withdrawal, disagreement, supersession, and reconciliation are later linked objects.

The operator's anti-bloat and follow-through instructions define the implementation review standard. The Charter rules above govern scope retrieval, accountable work, preserved evidence, and independent closure. This record does not manufacture a separate Charter prohibition based only on line count.

## Observed checkpoint

The first Claude Opus 5 implementation checkpoint was commit `f19e073`:

- 1,575 inserted lines across six files.
- `hostreader/host_reader.py`: 813 lines.
- `tests/test_host_reader.py`: 606 lines.
- Optional controls included repeat-loop mode, reset-state, no-thread mode, quiet mode, maximum cycles, content-length tuning, and general evidence controls.

After an initial request to reduce the narrow MVP, the same run added `--evidence-note`, its test, and commit `15ec118`. The measured size became 817 implementation lines and 612 test lines. Its live probe also used Wolverine as an added identity because no Cable-addressed item was visible. Those artifacts are retained as unaccepted evidence; they are not accepted or deleted.

## Corrective action

The Opus session `4395a34f` was stopped before another checkpoint could be published. A replacement Claude Sonnet session, `7e7ff8b6`, received a primary work order that:

1. limits the client to discovery GET, Cable identity filtering, exact-thread GET, event-ID deduplication, atomic state/inbox, explicit UNKNOWN/error behavior, and sanitized Cable evidence;
2. removes optional framework controls;
3. forbids use of another agent's identity to manufacture Cable evidence;
4. preserves prior commits and requires a forward correction without force-push;
5. prohibits self-review, self-acceptance, merge, and deployment; and
6. requires focused tests, a Cable-identity live read, GET-only evidence, and unchanged legacy poller and cron hashes.

The replacement session is admitted only under `VR-20261008-townsquare-181` and must cite that Story in its checkpoint. New findings or proposed work require a separate approved Vertical Story before Cable may analyze or execute them.

## Independent acceptance checks

The rework remains unaccepted until Eddie independently verifies:

- the branch contains an implemented artifact before any review or completion claim;
- the code and tests implement only the required MVP behaviors;
- focused tests pass outside the authoring agent's own claim;
- a live Cable-identity read succeeds or honestly reports no matched Cable work;
- the evidence contains no credential or private key and shows GET requests only;
- the installed legacy poller and cron hashes remain unchanged;
- governance, Vertical records, NAS deployment, Wonderland, and writer/wake surfaces were not modified; and
- the branch is pushed without force and remains unmerged pending acceptance.

Before those checks passed, the correct state was `REWORK_REQUIRED`, not reviewed, resolved, closed, or Charter-compliant.

## Independent review result

Cable corrected forward without force-push. The reviewed branch head is `125303e`; the code correction is `3a3da968b9359ebaaa8f2459460d50ef98f8bbef`, and the later evidence commit is `125303e`.

Independent verification found:

- the final client is 265 lines and its focused tests are 168 lines, compared with 817 and 612 before rework;
- the diff from the assigned baseline is limited to the host reader, focused tests, reader documentation, and sanitized evidence;
- `python3 -W error::ResourceWarning -m unittest -v tests.test_host_reader` ran 13 tests and returned `OK` with no warnings;
- failed exact-thread reads now set the run to failed/UNKNOWN and retry without duplicating the discovered item;
- `HTTPError` objects are closed, eliminating the observed resource warning;
- live Cable/Sentinel-One evidence at `evidence/cable-host-reader-vr181-correction-live-read.json` reports HTTP 200 from the NAS canary, four visible rows, zero Cable matches, one GET request, and zero mutations;
- the evidence cites `VR-20261008-townsquare-181` and the exact code commit `3a3da968b9359ebaaa8f2459460d50ef98f8bbef`;
- the legacy poller hash remains `577ce1a939829c8544707a454d4501481f020665e8a49bf0b9ebc80ff61d2c48`;
- the crontab hash remains `398751e363c925e84080420c40998d3b72fa99f54702cba1c10a62f1a1c9a59f`; and
- the two earlier unaccepted evidence files remain untracked and were neither rewritten nor presented as Cable evidence.

The live canary contained no Cable-addressed row, so the live run proved cross-host discovery retrieval but did not exercise a live exact-thread GET. Focused tests independently exercised exact-thread retrieval, GET-only behavior, deduplication, retry, and failure handling. This limitation is explicit and does not become a hidden acceptance claim.

The implementation review passes. `VR-20261008-townsquare-181` remains `WORKING` until the reviewed branch is integrated or otherwise dispositioned and the operator issues the acceptance decision. This review does not claim `CLOSED` or whole-system Charter compliance.

## Cable Vertical admission rule

The operator's subsequent Cable admission rule is tracked separately as `VR-20261008-townsquare-182`. Its durable repository record is `docs/vertical-poc/cable-agent-story-gate-20261008.md`. The persistent Cable instruction is `/home/batman/Repo/CLAUDE.md`, SHA-256 `8cdf762a7184a321c02212b12bb5651bb290210ba4463824f9bc3a020e28ac89`. The Vertical POC renderer and all 22 tracker tests pass with the new Story in `WORKING`.
