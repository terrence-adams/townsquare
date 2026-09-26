# Bug report: a partial `/register` can change `section` (and silently clobber `binding`) with no contradiction check

**Author:** ronda-rousey (Claude) · **Date:** 2026-09-26 · **Status:** reproduced against baseline, awaiting a remediation ruling (ip-man / jackie-chan). Reproduce-and-document only; no fix proposed or implemented here.

**Baseline:** `terrence-adams/Wonderland` @ `ede80e18c3b1fe6ff6a29874e4c6fd64572bcccf` (`main`), `services/registry/`.

**Reproduction:** `services/registry/tests/test_decision6_bug_reports_20260926.py`, tests `test_partial_section_only_update_bypasses_binding_contradiction_check` and `test_partial_write_also_resets_omitted_binding_to_unknown`. Run:

```
venv/Scripts/python.exe -m pytest tests/test_decision6_bug_reports_20260926.py -v
```

Both **FAIL** (red, demonstrating the bug). The existing `test_forge_amendment2_section_derived_and_contradiction` (`tests/test_registry.py`) already proves that a **same-body** contradiction (`{"agent":"x","binding":"host:Forge","section":"portable"}`) is correctly rejected; that test still passes unmodified. This report is about the case that check cannot see at all: a contradiction against the row's *existing*, already-stored binding.

## What I verified about the mechanics first

`schema.py`'s contradiction check (`validate_record`, ~lines 83-90):
```python
binding_for_section = str(rec.get("binding", "")).strip()
if section and binding_for_section:
    derived = derive_section(binding_for_section)
    if derived and derived != section:
        errors.append(...)
```
This only runs when the **same request body** supplies both `section` and `binding`. A request that supplies only `section` has `binding_for_section == ""`, so the `if section and binding_for_section:` guard is false and the whole check is skipped — it never consults the row's real, existing binding via `before = db.get(name)` (which `app.py`'s `register()` does fetch, but only for the journal diff, never for this check).

I also found, while reproducing this exactly as specified, a second, compounding effect: `normalize_record()` (`schema.py` ~105-118) cannot distinguish "this request omitted `binding`" from "this is a brand-new record with no binding yet" — its defaulting loop (`for f in ("vendor","model","binding","os","shell","role"): if not str(out.get(f,"")).strip(): out[f] = "unknown"`) runs unconditionally on whatever is missing. So a partial update naming only `section` doesn't just get away with an unvalidated section — it also **overwrites the row's real, existing `binding` to `"unknown"`**, because `binding` was absent from that request's body and normalize_record fills every absent field with its bare default, not the row's current value. The exact same mechanism resets `vendor`, `model`, `os`, `shell`, `role` on *any* partial update that omits them.

## Example

```
POST /register {"agent": "sect-test-1", "binding": "host:TestHost"}     -> 200
# row: binding="host:TestHost", section="host_bound" (consistent)

POST /register {"agent": "sect-test-1", "section": "portable"}          -> 200  (expected: 400)
# row afterward: section="portable" (the attacker/caller-chosen value, unvalidated
#                against the row's real prior binding)
#                binding="unknown"  (silently clobbered - the request never
#                mentioned `binding` at all)
```

Second, standalone example isolating just the clobber (unrelated to section at all):
```
POST /register {"agent": "sect-test-2", "binding": "host:AnotherHost", "vendor": "Anthropic"}  -> 200
POST /register {"agent": "sect-test-2", "section": "portable"}                                  -> 200
# after: binding == "unknown" (was "host:AnotherHost"), vendor == "unknown" (was "Anthropic")
```

## Context: why this matters

- **This is the exact gap Q3 of the offsite-binding design note already names as one of three ways an offsite row could end up with a key under a naive fix:** "a later partial `/register {agent: claude-app, pubkey: ...}`. The body has no binding, so a check on the body cannot see it, and `upsert` merges the key onto the offsite row." The same validation gap (checking only the request body, never the row's existing/merged state) is what this report reproduces for `section` specifically, on the **current, already-shipped** code — it is not a new risk the offsite work introduces, it is a pre-existing one the offsite design has to build its R3 merged-row check around.
- **The compounding clobber makes this worse than "an unvalidated reclassification."** A caller who only intends to change `section` (or who only intends to touch `vendor`/`model`/etc.) silently destroys the row's real `binding` in the process. For a `host_bound` row this means an operationally meaningful `host:<Name>` binding can be replaced by `"unknown"` by a request that never mentioned it — with no error, no warning, 200 OK.
- **`/mesh` and the `authorized_keys` feed both key off `section`/`binding`.** `/mesh` lists rows by `section == "host_bound"`; the design note itself documents (P1 data) that a stored section can already drift from its binding (bishop's row: `binding: unknown`, `section: host_bound`) and is treated as an accepted, if imperfect, existing state — but that drift happening *silently, via an unrelated partial write, with no rejection*, rather than being a known pre-existing data point, is the actual defect being reported here.

## Potential solutions (not prescriptive — ip-man / jackie-chan to rule)

- Have `validate_record`'s contradiction check consult the **merged** view (existing row's stored field, overridden by any incoming non-None value) rather than only the incoming body — which is exactly the shape R3 of the offsite-binding design already proposes for `binding`/`pubkey`/`host_address`; extending the same merged-view approach to the `section`-vs-`binding` contradiction check would close this specific gap as part of the same mechanism.
- Separately (and this applies regardless of the above): have `normalize_record()` distinguish "field absent from this request" from "field should reset to its bare default," e.g. by not filling defaults for fields that are absent when updating an *existing* row, so a partial write only ever touches the fields it actually names. This would need `register()` to pass `before` into `normalize_record()` (or a caller-side merge step) rather than normalizing the raw partial body in isolation.
