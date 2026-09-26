"""
s7 pre-deploy check (registry `binding: offsite` fix).

Per ip-man's security ruling Sec.5 (s7, required) and gsp's review Sec.8 (s7):
imports and runs the ACTUAL reviewed `key_publishable` function -- never a
reimplemented copy of its rule -- against a saved copy of the live
`/registry?retired=0` JSON, and reports every active, keyed row that would
LOSE its key under the new default-deny logic. That list must be empty
before the deploy proceeds; if it is not, STOP (do not restart) and bring
it to Sensei -- it means the deploy would change the live feed beyond what
Done-when (5) expects.

Usage:
    python registry-offsite-s7-precheck.py <schema.py-path> <registry-json-path>

<schema.py-path>      the git-show-exported, hash-verified registry/schema.py
                       staged in runbook Step 3 (s6). Must define
                       key_publishable(row) -> bool.
<registry-json-path>  the runbook Step 4 capture of GET /registry?retired=0
                       (the raw JSON response body, saved to a file).

Exit code 0 = the list is empty (safe to proceed).
Exit code 1 = the list is non-empty (STOP; bring to Sensei).
Exit code 2 = usage / file / import error.
"""
import importlib.util
import json
import sys


def load_key_publishable(schema_path):
    spec = importlib.util.spec_from_file_location("reviewed_schema", schema_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load a module spec from {schema_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, "key_publishable", None)
    if fn is None:
        raise AttributeError(
            f"{schema_path} defines no key_publishable(row) -- "
            "wrong file, or the reviewed diff does not match ip-man's ruling Sec.2.3"
        )
    return fn


def main(schema_path, registry_json_path):
    try:
        key_publishable = load_key_publishable(schema_path)
    except (ImportError, AttributeError, OSError) as exc:
        print(f"S7 PRECHECK ERROR loading {schema_path}: {exc}")
        return 2

    try:
        with open(registry_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"S7 PRECHECK ERROR reading {registry_json_path}: {exc}")
        return 2

    rows = data["agents"] if isinstance(data, dict) and "agents" in data else data

    losers = []
    for row in rows:
        if row.get("status") != "active":
            continue
        pubkey = str(row.get("pubkey", "") or "").strip()
        if not pubkey:
            continue
        if not key_publishable(row):
            losers.append(row.get("agent", "<unknown>"))

    if losers:
        print(f"S7 PRECHECK FAILED: {len(losers)} active keyed row(s) would "
              f"lose their key under the new default-deny rule: {losers}")
        print("STOP. Do not proceed to the backup/copy/restart steps. "
              "Bring this to Sensei before continuing (ip-man ruling Sec.5, s7).")
        return 1

    print(f"S7 PRECHECK PASSED: checked {len(rows)} row(s) from {registry_json_path} "
          f"against key_publishable() from {schema_path}. "
          "No active keyed row loses its key. Safe to proceed.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
