# TownSquare Vertical POC tracker

This directory is an append-only, Git-tracked compatibility ledger for the Vertical work model. It is not a native Vertical store, an enforcement engine, or a deployment control path.

`townsquare-work-events.jsonl` is the POC source of truth. Each LF-only JSON object has a unique prefixed POC event and thread identity, dense per-thread and global ordering, fixed claimed time, duplicate-free serialized actor provenance, and a SHA-256 over its canonical object without `poc_content_sha256`. `poc_ref` is only a stable display label.

## Record fields

`schema_version` is the literal `"1"`; `canonicalization_profile` is `rfc8785+townsquare-vertical-poc-safeint/1`; and RFC 8785 canonical JSON (including UTF-16 key ordering) is used before calculating `poc_content_sha256`. `poc_event_uid` is the immutable prefixed event identity, `poc_thread_uid` is the prefixed chain identity, `poc_seq` is dense inside that chain, and `poc_global_order` is dense across the ledger. `actor_provenance` is a duplicate-free JSON string. `claimed_at`, `basis_kind`, and `basis_ref` state what was reported and why; a measured `basis_ref` is immutable and content-addressed.

Work openings state `role_acted_under: project-owner`; transitions state the permitted role and carry both `base_event_id` and `expected_head` for compare-and-append. Reporting-only metadata is `vertical_level`, `parent_ref`, `depends_on_refs`, `owner`, `creation_owner`, `fulfillment_owner`, `review_owner`, and `operator_acceptance_owner`. None of that metadata creates authority.

The only ordinary lifecycle transitions are `OPEN->WORKING`, `OPEN->BLOCKED`, `OPEN->CANCELLED`, `WORKING->BLOCKED`, `WORKING->RESOLVED`, `WORKING->CANCELLED`, `BLOCKED->WORKING`, `BLOCKED->CANCELLED`, `RESOLVED->WORKING`, `RESOLVED->CLOSED`, and `RESOLVED->CANCELLED`. A transition carries the required single-line reason fields and must name the immediately prior head.

Open a work item with `unit-of-work`, state `OPEN`, a goal, JSON-list definition of done, and the pinned workflow event reference. Append a transition rather than changing the opening. A transition names the immediately preceding event in both `base_event_id` and `expected_head`. Metadata such as owner, milestone, parent, and dependency is visible reporting metadata only; it cannot change lifecycle, authority, acceptance, or blockers.

Run `python tools/render-vertical-poc-roadmap.py` from the repository root. The renderer strictly parses every record, verifies hashes, identities, references, dense chains, workflow openings, and permitted transitions before writing. On any error it leaves the existing roadmap unchanged. It neither queries a clock nor controls runtime or deployment.

For a native migration, freeze and hash this ledger, validate it again, replay once in global order with compare-and-append, allocate native UUIDv7 identities, and preserve `migration-map.json` for both POC identities, both hashes, and both order domains. Wonderland may only consume resulting projections; it may not mutate or authorize source work.
