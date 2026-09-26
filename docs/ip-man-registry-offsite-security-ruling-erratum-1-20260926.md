<!-- extracted (not a plain splice: this SubagentHandback delivered the document inside a larger report, delimited by BEGIN FILE/END FILE markers, because ip-man has no write tool; the surrounding preamble/summary text is not part of this file) sha256=9d5d20a85747a2f723467f7f40f1ac2b0026b03326d3d37b5260c8a9116f8494 source=C--Workspace/6e6cb5f4-3f6f-4870-bf90-c7795b59dbcb/subagents/agent-a7f01575feaa11a9b.jsonl:94 message=msg_011CfSqsjjxCE9gU7QArYfT5 -->
# Registry `binding: offsite`: ruling, erratum 1 — which field R3b reads

**Author:** ip-man (Claude) · **Date:** 2026-09-26 · **Status:** design clarification only. I only read; I wrote, ran and built nothing.
**Amends:** `C:\Repo\townsquare\docs\ip-man-registry-offsite-security-ruling-20260926.md` ("the ruling"), with the SHA-256 the session recorded when it saved the ruling. The ruling itself is not edited.
**Raised by:** helio-gracie's GAME PLAN on the ruling, relayed by the session.
**Proposed path:** `C:\Repo\townsquare\docs\ip-man-registry-offsite-security-ruling-erratum-1-20260926.md`, on branch `internal`, not pushed.
**Recusal:** the ruling's recusal carries over, and it covers this erratum too.
**Shorthand:** as in the ruling.
- A *bound-offsite row* is the review's term: a row whose stored binding, stripped, is `offsite`.
- A *section-only offsite row* is a row whose stored section is `offsite` while its stored binding is not.

## 1. The ruling

**R3b reads the stored binding only.**
- It fires when `is_offsite(existing["binding"])` is true and the body carries no explicit binding.
- It never reads the stored section.

**Where the ruling was wrong.**
- In §2.5, "an existing offsite row" is to be read as "an existing bound-offsite row".
- I used the term defined in §2.1 where I meant the narrower one. That contradicted §2.1's own statement: "I do not widen R3b".

**What §2.1's definition governs.** The definition (binding *or* section is offsite) governs three things:
- S1;
- default-deny;
- the consistency that R3c enforces.

It does not define R3b's trigger. §2.8's line on S1 is read the same way:
- R3b protects bound-offsite rows;
- a section-only offsite row can come only from a direct DB edit (see §2 below).

No C1 label is needed. I agree with Helio's finding, and declaring the term in the rule text is what C2(b) would require anyway.

## 2. Why binding only

These reasons are unchanged from the ruling's §2.1.
- **What R3b guards.** It guards a stored offsite binding against being re-bound silently. A row whose binding is not offsite has no offsite binding to re-bind.
- **Where a section-only offsite row can come from.** Once R3c is in place, neither `/register` nor the legacy path can produce one.
  - Every write stores both fields from one validated body.
  - `normalize_record` always sets both fields.
  - A stale write sets neither.
  - So only a direct DB edit can make such a row.
- **Reading section as well would change which writes are accepted,** and no reviewer has seen that change. gsp's G1 fix closed this path with R3c and default-deny. It did not widen R3b.

## 3. R3b and R3c on the same body: intentional overlap, neither narrowed

- **They are different checks.**
  - R3c reads only the body: its section against its own binding. It runs on every write, whether the row is new or already exists.
  - R3b reads the stored row's binding against the body's binding.
- **R3c is not a check for new rows only.**
  - T9b's third case, `{section: offsite}` on an existing host row that has a key, is an existing row.
  - It is the path that run 04 measured, and R3c must catch it.
- **They overlap on exactly one kind of input:** an existing bound-offsite row, with a body that carries `section: offsite` and no explicit binding.
  - R3c answers, because `validate_record` returns 400 before R3 runs. R3b is never reached.
  - The body is refused either way, and the row is unchanged either way.
- **Neither check is narrowed.**
  - Narrowing R3c to new rows would need the stored row inside `validate_record`, and it would reopen run 04's path.
  - Narrowing R3b to skip bodies that R3c already refuses would add a special case that changes nothing.
- **Testing the overlap.** A test that hits it asserts three things: the 400, the substrings `offsite` and `binding`, and the unchanged row. It does not assert which rule answered.

## 4. Tests

- **T4e and T4f stand as written.**
  - Their "offsite row in place" is created through `POST /register` with `binding: offsite`, the shape T1 uses, so its stored binding and section are both offsite.
  - They test R3b's trigger on the stored binding.
- **New test, T4g, which pins the reading.**
  1. Write a row straight into the isolated test DB, with binding `unknown`, section `offsite`, and no key.
  2. Send `POST /register {agent, pubkey: K}`, with no binding and no section.
  3. Expect **200**. The stored row becomes `unknown`/`host_bound` and holds K, and the feed carries K: default-deny publishes an `unknown`/`host_bound` row, as T6b's bishop-shape case shows.

  A 400 here means R3b was widened to read the section, and T4g fails.
- **What T4g records.** It records the direct-edit residual described in the ruling's §2.1; it does not endorse that residual.
- **T4g does not breach Done-when (4).** The key is never stored on an offsite row, because the same write that stores it also re-binds the row.

```
WORK ORDER — amended lines only; everything else in the ruling stands
- Document: the session saves this erratum byte for byte, with its SHA-256, at
  C:\Repo\townsquare\docs\ip-man-registry-offsite-security-ruling-erratum-1-20260926.md (internal, not
  pushed), ideally before bruce-lee is dispatched. No new review round: it brings the wording back to the
  reviewed design (Addendum 1's R3b read the stored binding, and gsp's G1 fix did not widen it), and it adds
  one pinning test.
- Coordinate: helio-gracie — this closes the ambiguity his GAME PLAN raised; CHECKPOINT as he planned.
- Implement:
    (1) ronda-rousey adds T4g (§4). T4e and T4f are unchanged.
    (2) bruce-lee: R3b reads existing["binding"] only, through is_offsite.
- Peer review: gsp's hunk check now includes one more item: R3b reads existing["binding"] only, and never
  the stored section.
- Watch for: an implementer "completing" R3b with the section, by analogy with §2.1. T4g fails if that
  happens.
```