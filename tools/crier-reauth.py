#!/usr/bin/env python3
"""Re-authorize the Crier's Google Drive rclone remote in one command.

Why this exists: the Crier (Docker container `crier` on the NAS) reads the
TownSquare ledger through rclone remote `gdrive`. That remote uses our own
Google OAuth client, and while the client's consent screen is in "Testing"
status Google expires its refresh token after 7 days. The Crier then fails with
`invalid_grant` until someone re-authorizes, and the NAS has no browser.

What this does, run from a machine with a browser (Venom):
  1. Read the remote's client_id / client_secret / scope from the NAS.
  2. Run `rclone authorize` locally, check the consent URL really asks for the
     same client and scope, then open it. You click Allow.
  3. Back up the NAS rclone.conf, write the new token into it.
  4. Prove it from inside the Crier container, then wait for /health to go ok.

Usage:
  python crier-reauth.py            full re-auth
  python crier-reauth.py --check    report Crier health and token age, change nothing
  python crier-reauth.py --dry-run  everything up to the consent click, change nothing

Needs: rclone on PATH here, key-based ssh to the NAS (batman@192.168.2.3).
Stdlib only. Secrets are never printed; the token travels over ssh stdin, not
the command line.
"""
import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime, timezone

DEFAULTS = {
    "host": os.environ.get("CRIER_NAS", "batman@192.168.2.3"),
    "remote": os.environ.get("CRIER_REMOTE", "gdrive"),
    "container": os.environ.get("CRIER_CONTAINER", "crier"),
    "ledger": os.environ.get("CRIER_LEDGER", "gdrive:N3rd0m/TownSquare"),
    "health": os.environ.get("CRIER_HEALTH", "http://192.168.2.3:8787/health"),
    "nas_rclone": os.environ.get("CRIER_NAS_RCLONE", "$HOME/bin/rclone"),
    "nas_conf": os.environ.get("CRIER_NAS_CONF", "$HOME/.config/rclone/rclone.conf"),
}
GOOGLE_EXPIRY_DAYS = 7
WARN_AT_DAYS = 6
CONSENT_TIMEOUT = 300


class Fail(Exception):
    pass


def say(msg=""):
    print(msg, flush=True)


# ---- NAS access -----------------------------------------------------------

def nas(args, cmd, stdin=None, timeout=60):
    """Run a shell command on the NAS. Returns (rc, stdout, stderr)."""
    # Bytes, not text mode: Windows text mode turns "\n" into "\r\n" on stdin,
    # and rclone rejects a token value that carries a "\r".
    p = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", args.host, cmd],
        input=stdin.encode() if stdin is not None else None,
        capture_output=True, timeout=timeout)
    return (p.returncode, p.stdout.decode(errors="replace"),
            p.stderr.decode(errors="replace"))


def nas_ok(args, cmd, stdin=None, timeout=60):
    rc, out, err = nas(args, cmd, stdin, timeout)
    if rc != 0:
        raise Fail(f"NAS command failed (rc={rc}): {(err or out).strip()[-400:]}")
    return out


def read_remote_settings(args):
    """client_id / client_secret / scope of the remote. The token is dropped here."""
    out = nas_ok(args, f'RCLONE_CONFIG="{args.nas_conf}" {args.nas_rclone} config dump')
    remote = json.loads(out).get(args.remote)
    if not remote or remote.get("type") != "drive":
        raise Fail(f"remote '{args.remote}' is not a drive remote on the NAS")
    missing = [k for k in ("client_id", "client_secret") if not remote.get(k)]
    if missing:
        raise Fail(f"remote '{args.remote}' has no own {', '.join(missing)}; "
                   "this script is for a custom OAuth client")
    return {k: remote.get(k, "") for k in ("client_id", "client_secret", "scope")}


# ---- health ---------------------------------------------------------------

def fetch_health(url):
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:  # /health answers 503 while stale
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}


def token_age_days(args):
    rc, out, _ = nas(args, f'cat "$(dirname {args.nas_conf})/{args.remote}.reauth-at" 2>/dev/null')
    if rc != 0 or not out.strip():
        return None
    try:
        then = datetime.fromisoformat(out.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - then).total_seconds() / 86400


def do_check(args):
    code, h = fetch_health(args.health)
    say(f"Crier /health: HTTP {code or 'no answer'}")
    if code == 0:
        say(f"  unreachable: {h.get('error')}")
        say("  UNKNOWN, not 'no work'. Is the NAS up?")
        return 2
    say(f"  ok={h.get('ok')}  last good poll: {h.get('last_poll_ok')}  stale={h.get('stale')}")
    if h.get("last_poll_error"):
        say(f"  last error: {h['last_poll_error'][:200]}")
    age = token_age_days(args)
    if age is None:
        say("  token age: unknown (no marker yet; written after the next re-auth)")
    else:
        left = GOOGLE_EXPIRY_DAYS - age
        say(f"  token age: {age:.1f} days; Google expires it at {GOOGLE_EXPIRY_DAYS} "
            f"({'EXPIRED' if left <= 0 else f'{left:.1f} days left'})")
        if age >= WARN_AT_DAYS:
            say("  -> re-auth due: python crier-reauth.py")
    return 0 if h.get("ok") else 1


# ---- local rclone authorize ----------------------------------------------

def start_authorize(settings):
    rclone = shutil.which("rclone")
    if not rclone:
        raise Fail("rclone not found on PATH on this machine")
    cfg = {k: v for k, v in settings.items() if v}
    # rclone's configmap codec is standard base64 with no padding (RawStdEncoding).
    blob = base64.b64encode(json.dumps(cfg).encode()).decode().rstrip("=")
    proc = subprocess.Popen(
        [rclone, "authorize", "drive", blob, "--auth-no-open-browser"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines, lock = [], threading.Lock()

    def pump():
        for line in proc.stdout:
            with lock:
                lines.append(line.rstrip("\n"))

    threading.Thread(target=pump, daemon=True).start()
    return proc, lines, lock


def wait_for(lines, lock, pattern, timeout, proc=None):
    """Poll captured output for a regex; return the match, else None."""
    end, rx = time.time() + timeout, re.compile(pattern, re.S)
    while time.time() < end:
        with lock:
            m = rx.search("\n".join(lines))
        if m:
            return m
        if proc is not None and proc.poll() is not None:
            time.sleep(0.3)  # let the pump drain
            with lock:
                return rx.search("\n".join(lines))
        time.sleep(0.2)
    return None


def parse_authorize_output(text):
    """Turn what `rclone authorize` printed between its markers into the token dict.

    rclone 1.75 prints, depending on how it was invoked, either the raw token
    JSON (client_id + client_secret form) or a base64 (standard, unpadded) JSON
    map whose "token" entry holds the token (blob form, which we use).
    """
    text = "".join(text.split())
    if not text:
        raise Fail("rclone printed an empty token block")
    if text.startswith("{"):
        obj = json.loads(text)
    else:
        try:
            obj = json.loads(base64.b64decode(text + "=" * (-len(text) % 4)))
        except Exception:
            raise Fail(f"token block is neither JSON nor base64 JSON "
                       f"({len(text)} chars, starts {text[0]!r}); not showing it")
    if isinstance(obj, dict) and "token" in obj:
        obj = obj["token"]
    if isinstance(obj, str):
        obj = json.loads(obj)
    if not isinstance(obj, dict) or not obj.get("access_token"):
        raise Fail("token block decoded but has no access_token")
    return obj


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def google_url_behind(local_url):
    """rclone's local /auth endpoint 302s to Google; read where, without following."""
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        opener.open(local_url, timeout=8)
    except urllib.error.HTTPError as e:
        return e.headers.get("Location", "")
    return ""


def check_consent_url(url, settings):
    """The consent page must ask for our client and our scope, nothing broader."""
    from urllib.parse import parse_qs, urlparse
    q = parse_qs(urlparse(url).query)
    got_client = (q.get("client_id") or [""])[0]
    got_scope = (q.get("scope") or [""])[0]
    if got_client != settings["client_id"]:
        raise Fail(f"consent URL client_id {got_client!r} != the remote's client_id")
    want = settings.get("scope") or "drive"
    if got_scope.rsplit("/", 1)[-1] != want:
        raise Fail(f"consent URL scope {got_scope!r} != the remote's scope {want!r}; "
                   "refusing, a broader grant than the Crier should hold")
    return got_scope


def authorize(settings, dry_run):
    proc, lines, lock = start_authorize(settings)
    try:
        m = wait_for(lines, lock, r"go to the following link:\s*(http\S+)", 20, proc)
        if not m:
            with lock:
                raise Fail("rclone authorize did not offer a link:\n  " + "\n  ".join(lines[-6:]))
        google = google_url_behind(m.group(1))
        scope = check_consent_url(google, settings)
        say(f"Consent page checked: our client, scope {scope.rsplit('/', 1)[-1]}.")
        if dry_run:
            say("Dry run: stopping before the consent click. Nothing was changed.")
            return None
        say("Opening your browser. Sign in as the Google account that owns the "
            "N3rd0m Drive folder and click Allow.")
        say(f"(If no browser opens, paste this: {m.group(1)})")
        webbrowser.open(m.group(1))
        say(f"Waiting up to {CONSENT_TIMEOUT // 60} minutes for you...")
        t = wait_for(lines, lock, r"--->\s*(.*?)\s*<---End paste", CONSENT_TIMEOUT, proc)
        if not t:
            with lock:
                tail = [ln for ln in lines[-4:] if "--->" not in ln][-3:]
            raise Fail("no token received (consent not given, or timed out). "
                       "rclone's last lines: " + " | ".join(tail)[:300])
        token = parse_authorize_output(t.group(1))
        if not token.get("refresh_token"):
            raise Fail("Google returned no refresh_token; revoke the old grant at "
                       "myaccount.google.com/permissions and run again")
        return token
    finally:
        if proc.poll() is None:
            proc.terminate()


# ---- install + verify -----------------------------------------------------

def push_token(args, token):
    """Back up the NAS config, then set the remote's token. Token goes via stdin."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cmd = (
        f'cp -p "{args.nas_conf}" "{args.nas_conf}.bak-{stamp}" && '
        f'IFS= read -r T && RCLONE_CONFIG="{args.nas_conf}" {args.nas_rclone} '
        f'config update {args.remote} token "$T" --non-interactive >/dev/null'
    )
    nas_ok(args, cmd, stdin=json.dumps(token, separators=(",", ":")) + "\n")
    out = nas_ok(args, f'RCLONE_CONFIG="{args.nas_conf}" {args.nas_rclone} config dump')
    stored = json.loads(out).get(args.remote, {}).get("token", "")
    if json.loads(stored or "{}").get("refresh_token") != token["refresh_token"]:
        raise Fail(f"token did not land in {args.nas_conf} "
                   f"(backup is {args.nas_conf}.bak-{stamp})")
    nas_ok(args, f'date -u +%Y-%m-%dT%H:%M:%SZ > "$(dirname {args.nas_conf})/{args.remote}.reauth-at"')
    say(f"Token written. Previous config kept as rclone.conf.bak-{stamp} on the NAS.")


def verify(args, wait):
    say("Checking from inside the Crier container...")
    nas_ok(args, f"docker exec {args.container} rclone lsd {args.ledger}", timeout=90)
    say("  container can list the ledger: OK")
    if not wait:
        return
    say("Waiting for the Crier's next poll to clear /health (polls every 5 min)...")
    end = time.time() + 6 * 60
    while time.time() < end:
        code, h = fetch_health(args.health)
        if code == 200 and h.get("ok"):
            say(f"  /health ok, last good poll {h.get('last_poll_ok')}")
            return
        time.sleep(15)
    raise Fail("auth works but /health is still not ok after 6 min; "
               f"try: ssh {args.host} docker restart {args.container}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="report health and token age only")
    ap.add_argument("--dry-run", action="store_true", help="stop before the consent click")
    ap.add_argument("--no-wait", action="store_true", help="skip waiting for /health after install")
    for k, v in DEFAULTS.items():
        ap.add_argument(f"--{k.replace('_', '-')}", default=v)
    args = ap.parse_args()
    try:
        if args.check:
            return do_check(args)
        say("Reading the remote's settings from the NAS...")
        settings = read_remote_settings(args)
        token = authorize(settings, args.dry_run)
        if token is None:
            return 0
        push_token(args, token)
        verify(args, wait=not args.no_wait)
        say("Done. Google will expire this token in 7 days; "
            "`python crier-reauth.py --check` shows how long is left.")
        return 0
    except Fail as e:
        say(f"FAILED: {e}")
        return 1
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as e:
        say(f"FAILED: {type(e).__name__}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
