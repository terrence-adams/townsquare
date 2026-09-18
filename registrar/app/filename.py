"""Canonical TownSquare filename parser (schema version 1)."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

SCHEMA_VERSION = 1
PID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
NAME_RE = re.compile(r"^(?P<thread>(?P<prefix>TS|BB|SEEK|OFFER|WANT)-(?P<date>\d{8})(?:-(?P<namespace>[a-z][a-z0-9-]*))?-(?P<number>\d{3,}))\.(?P<seq>\d+)-(?P<state>[A-Z]+)(?P<rest>__.*)?\.txt$")
PREFIXED = ("pid", "mode", "to", "from", "by", "for", "impact", "cap", "cat")

class FilenameError(ValueError): pass

def parse_filename(name: str, path: str = "") -> dict:
    name = Path(name).name; m = NAME_RE.fullmatch(name)
    if not m: raise FilenameError("invalid TownSquare filename")
    result = {"parser_version": SCHEMA_VERSION, "thread": m["thread"], "prefix": m["prefix"],
              "date": m["date"], "namespace": m["namespace"], "local_number": int(m["number"]),
              "seq": int(m["seq"]), "state": m["state"], "filename": name, "path": path,
              "priority": None, "slug": None}
    seen = set()
    for token in filter(None, (m["rest"] or "").split("__")):
        if re.fullmatch(r"P[0-3]", token): key, value = "priority", token
        else:
            match = next(((k, token[len(k)+1:]) for k in PREFIXED if token.startswith(k+"-")), None)
            key, value = match if match else ("slug", token)
        if not value: raise FilenameError(f"empty {key} field")
        if key in seen: raise FilenameError(f"duplicate {key} field")
        seen.add(key)
        if key == "pid" and not PID_RE.fullmatch(value): raise FilenameError("noncanonical pid")
        if key == "mode" and value != "break-glass": raise FilenameError("unsupported mode")
        result[key] = value
    return result

def read_header(path: str) -> dict[str,str]:
    out = {}
    for line in Path(path).read_text(errors="replace").splitlines():
        if line.startswith("---"): break
        if ":" in line:
            key,value=line.split(":",1); key=key.strip()
            if key in out: raise FilenameError(f"duplicate header {key}")
            out[key]=value.strip()
    return out

def check_header(parsed: dict, header: dict[str,str]) -> None:
    values={"id":parsed["thread"],"event":str(parsed["seq"]),"state":parsed["state"]}
    for key in ("pid","mode","priority","to","from","by","for","impact","cap","cat"):
        values["post_id" if key=="pid" else key]=parsed.get(key)
    for key,value in values.items():
        actual=header.get(key)
        if value is None and actual not in (None,""): raise FilenameError(f"header-only field {key}")
        if value is not None and actual != value: raise FilenameError(f"field mismatch {key}")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--check"); ap.add_argument("--json"); args=ap.parse_args()
    try:
        path=args.check or args.json; parsed=parse_filename(Path(path).name,path)
        if args.check: check_header(parsed,read_header(path))
        print(json.dumps(parsed,sort_keys=True)); return 0
    except (OSError,FilenameError) as exc: print(f"townsquare filename: {exc}",file=sys.stderr); return 2
if __name__ == "__main__": raise SystemExit(main())
