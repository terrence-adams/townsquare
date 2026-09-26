# Bug report: `PUBKEY_RE` accepts a two-line value as a single valid SSH public key

**Author:** ronda-rousey (Claude) · **Date:** 2026-09-26 · **Status:** documented only, per explicit instruction. **Out of scope for decision 6's offsite-binding fix** — ip-man and helio-gracie both explicitly ruled this out of scope for the current work order. No test is included in the decision-6 reproduction suite, and no fix is proposed or implemented here. This is a standalone finding, filed so it is not lost.

**Baseline:** `terrence-adams/Wonderland` @ `ede80e18c3b1fe6ff6a29874e4c6fd64572bcccf` (`main`), `services/registry/registry/schema.py`.

**Confirmation method:** a standalone, throwaway interactive probe (`python -c ...`, not saved as a file, not part of any pytest suite), calling `schema.PUBKEY_RE.match()` and `schema.validate_record()` directly — no Flask, no DB, no network. Deliberately not committed anywhere and not wired into the decision-6 test file, per instruction.

## The mechanic

```python
PUBKEY_RE = re.compile(r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-\S+)\s+[A-Za-z0-9+/=]+(\s+\S.*)?$")
```

The trailing optional group `(\s+\S.*)?` is meant to allow the usual SSH key **comment** (e.g. `user@host`) after the base64 body, separated by whitespace. But `\s` matches a newline exactly the same as a space, and — critically — nothing in this pattern is compiled with `re.MULTILINE` or otherwise anchors `$` to a single line, so the comment half of the pattern is free to start on an **entirely separate line**, and everything on that second line (up to the next embedded newline, since bare `.` does not itself cross a newline) is accepted as "the comment."

## Example

```python
>>> from registry import schema
>>> smuggled = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGZ1dGVzdGtleWRhdGE=\nX-Injected-Header: evil"
>>> bool(schema.PUBKEY_RE.match(smuggled))
True
>>> schema.validate_record({"agent": "pubkey-probe", "pubkey": smuggled})
(True, [])
```

A value that is structurally **two lines** — a real-looking key line, then an entirely separate second line — passes `validate_record` with zero errors, exactly as if it were one ordinary `key + comment` line.

## Context: why it matters (independent of the offsite-binding fix)

- **This field feeds `GET /authorized_keys` verbatim.** `app.py`'s `authorized_keys()` does `pk = (r.get("pubkey") or "").strip()` (strips only leading/trailing whitespace, not an embedded newline) and then `"\n".join(sorted(set(lines)))` across all active agents' keys. A `pubkey` value containing an embedded `\n` does not stay "one key" in that output — it becomes **two lines** in the authorized_keys feed. SSH's `authorized_keys` format is one entry per line; a second line that happens to be a well-formed key (not literally "evil" text, as in the toy example above, but a real `ssh-ed25519 AAAA...` line an attacker controls) would be honored by `sshd` as an **independent, additional** authorized key.
- **That means one registry row, with what looks like "one pubkey field," could grant SSH access via a second, entirely separate keypair the row's own reviewer never saw as a distinct credential** — anything that audits "how many keys does this agent have" by counting rows, or by eyeballing one `pubkey:` line per agent in a rendered table, undercounts.
- **This is orthogonal to, and would survive, the offsite-binding fix as scoped.** The offsite work (R1-R5 of `ip-man-registry-offsite-binding-design-20260926.md`) constrains *which rows* may carry a `pubkey` at all (no `offsite` row may); it says nothing about the *shape* of a `pubkey` value on a row that is legitimately allowed to carry one (`host_bound`/`portable`), which is exactly where this defect lives.

## Potential solutions (not prescriptive — ip-man / jackie-chan to rule; explicitly not to be actioned as part of decision 6)

- Reject any `pubkey` value containing an embedded newline outright (a real single-line SSH public key never legitimately contains one), independent of anything else in the pattern.
- Anchor the existing pattern more strictly, e.g. requiring the whole match via `re.fullmatch` against a value that has first been rejected if `"\n" in pubkey` (stripped only at the very ends, not internally), rather than relying on `$`/`\s` semantics to do that job implicitly.
- If a multi-line `pubkey` value is ever legitimately needed (unlikely for a single SSH public key line), validate line count explicitly rather than leaving it to regex whitespace-matching side effects.
