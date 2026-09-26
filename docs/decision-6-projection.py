import json, hashlib, sys, urllib.request

STABLE = ["agent","vendor","model","binding","section","os","shell","role","status","pubkey","host_address"]

def main(out_path):
    with urllib.request.urlopen("http://192.168.2.3:8789/registry", timeout=10) as r:
        data = json.load(r)
    rows = data["agents"] if isinstance(data, dict) and "agents" in data else data
    projected = []
    for row in rows:
        if row.get("agent") == "claude-app":
            continue
        line = "\t".join(str(row.get(f, "")) for f in STABLE)
        projected.append((row.get("agent",""), line))
    projected.sort(key=lambda x: x[0])
    text = "\n".join(line for _, line in projected) + "\n"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(f"rows={len(projected)} sha256={sha} file={out_path}")

if __name__ == "__main__":
    main(sys.argv[1])
