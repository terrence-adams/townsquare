"""
Step 9 journal comparison (registry `binding: offsite` fix).

Per Addendum 1 Sec.4 and jackie-chan's U11 (registry-offsite-review):
`/journal?limit=5`'s newest entry must be compared by its `op`, `agent` and
`applied_at` fields, not by raw response bytes -- a container restart drains
the outbox immediately (D3), which can legitimately flip the per-entry
`publishing` field and the envelope's `outbox_pending` /
`publisher.pending` / `publisher.published` fields with zero new
registrations. Those four fields are expected to vary and are NOT checked
here on purpose.

This script does not assume the entries array is sorted in any particular
order (newest-first or newest-last) -- neither has been confirmed against
the live service this session, and guessing wrong would silently compare
the wrong entry. Instead it finds the entry with the maximum `seq` in each
capture (seq is journal.py's own monotonic counter) and compares those two.

Usage:
    python registry-offsite-journal-diff.py <pre-journal.json> <post-journal.json>

Exit code 0 = op/agent/applied_at all match (the newest entry is unchanged).
Exit code 1 = at least one of those fields differs.
Exit code 2 = usage / file / shape error.
"""
import json
import sys


def newest_entry(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    entries = data["entries"] if isinstance(data, dict) and "entries" in data else data
    if not entries:
        raise ValueError(f"{path}: no journal entries found")
    return max(entries, key=lambda e: e.get("seq", -1))


def main(pre_path, post_path):
    try:
        pre = newest_entry(pre_path)
        post = newest_entry(post_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    ok = True
    for field in ("op", "agent", "applied_at"):
        pre_v, post_v = pre.get(field), post.get(field)
        match = pre_v == post_v
        ok = ok and match
        print(f"{field}: pre={pre_v!r} post={post_v!r} {'MATCH' if match else 'MISMATCH -- STOP'}")

    print(f"(pre seq={pre.get('seq')!r}, post seq={post.get('seq')!r}; "
          f"NOT compared: publishing, outbox_pending, publisher.pending/published -- "
          f"expected to vary per D3's automatic outbox drain on restart)")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
