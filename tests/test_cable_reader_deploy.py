#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""VR-20261008-townsquare-183: install/disable/rollback of the canary host reader."""
import fcntl
import importlib.util
import json
import os
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("deploy", ROOT / "tools" / "cable-reader-deploy.py")
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)

LEGACY = b"#Ansible: townsquare poll\n*/5 * * * * /home/u/.local/bin/townsquare-poll >/dev/null 2>&1\n"
FAKE_CRONTAB = """#!/bin/sh
f="$FAKE_CRONTAB_FILE"
if [ "$1" = "-l" ]; then
  [ -f "$f" ] || { echo "no crontab for u" >&2; exit 1; }
  cat "$f"
else
  cat >"$f"
fi
"""


def sh(*args, cwd, check=True):
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True,
                          env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


class Discovery(BaseHTTPRequestHandler):
    hits = 0

    def do_GET(self):
        type(self).hits += 1
        body = b'{"open_work": [], "history": []}'
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class DeployTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.home, self.repo = tmp / "home", tmp / "repo"
        self.home.mkdir()
        self.crontab_file = tmp / "crontab.txt"
        bindir = tmp / "bin"
        bindir.mkdir()
        (bindir / "crontab").write_text(FAKE_CRONTAB)
        (bindir / "crontab").chmod(0o755)
        self._env = {k: os.environ.get(k) for k in ("PATH", "FAKE_CRONTAB_FILE")}
        os.environ["PATH"] = f"{bindir}:{os.environ['PATH']}"
        os.environ["FAKE_CRONTAB_FILE"] = str(self.crontab_file)
        (self.repo / "hostreader").mkdir(parents=True)
        sh("git", "init", "-q", cwd=self.repo)
        self.v1 = self.commit("v1")
        self.v2 = self.commit("v2")

    def tearDown(self):
        for k, v in self._env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self._tmp.cleanup()

    def commit(self, label):
        (self.repo / "hostreader" / "__main__.py").write_text(f"print({label!r})\n")
        sh("git", "add", "-A", cwd=self.repo)
        sh("git", "commit", "-qm", label, cwd=self.repo)
        return sh("git", "rev-parse", "HEAD", cwd=self.repo).stdout.strip()

    def install(self, rev, base="http://127.0.0.1:9"):
        return deploy.install(self.home, self.repo, rev, base)

    def cron(self):
        return self.crontab_file.read_bytes() if self.crontab_file.exists() else b""

    def ours(self):
        return [l for l in self.cron().splitlines() if l.endswith(deploy.MARKER.encode())]

    def test_new_install_without_crontab(self):
        self.install(self.v1)
        p = deploy.paths(self.home)
        self.assertEqual(os.readlink(p["current"]), f"releases/{self.v1[:7]}")
        self.assertEqual((p["current"] / "REVISION").read_text().strip(), self.v1)
        self.assertTrue((p["current"] / "hostreader" / "__main__.py").exists())
        self.assertEqual(len(self.ours()), 1)
        self.assertTrue(self.ours()[0].startswith(b"* * * * * " + str(p["run"]).encode()))
        self.assertEqual(oct(p["state"].stat().st_mode & 0o777), "0o700")
        self.assertFalse((self.home / ".townsquare").exists())

    def test_cron_preserves_legacy_bytes(self):
        self.crontab_file.write_bytes(LEGACY)
        self.install(self.v1)
        self.assertTrue(self.cron().startswith(LEGACY))
        self.install(self.v2)
        self.assertTrue(self.cron().startswith(LEGACY))
        deploy.disable(self.home)
        self.assertEqual(self.cron(), LEGACY)

    def test_legacy_without_trailing_newline_survives(self):
        self.crontab_file.write_bytes(LEGACY.rstrip(b"\n"))
        self.install(self.v1)
        self.assertEqual(self.cron().splitlines()[:2], LEGACY.splitlines())
        self.assertEqual(len(self.ours()), 1)

    def test_repeat_install_is_idempotent(self):
        self.crontab_file.write_bytes(LEGACY)
        self.install(self.v1)
        before = self.cron()
        msg = self.install(self.v1)
        self.assertEqual(self.cron(), before)
        self.assertIn("cron unchanged", msg)
        self.assertFalse(deploy.paths(self.home)["previous"].exists())

    def test_modified_release_is_refused(self):
        self.install(self.v1)
        rel = deploy.paths(self.home)["releases"] / self.v1[:7]
        (rel / "TREE").write_text("0" * 40 + "\n")
        with self.assertRaises(deploy.DeployError):
            self.install(self.v1)

    def test_upgrade_then_rollback_selects_previous(self):
        self.install(self.v1)
        self.install(self.v2)
        p = deploy.paths(self.home)
        self.assertEqual(os.readlink(p["previous"]), f"releases/{self.v1[:7]}")
        deploy.rollback(self.home)
        self.assertEqual(os.readlink(p["current"]), f"releases/{self.v1[:7]}")
        self.assertFalse((p["releases"] / self.v2[:7]).exists())
        self.assertEqual(len(self.ours()), 1)

    def test_rollback_of_only_release_removes_install_and_cron(self):
        self.crontab_file.write_bytes(LEGACY)
        self.install(self.v1)
        state = deploy.paths(self.home)["state"]
        (state / "state.json").write_text("{}")
        deploy.rollback(self.home)
        p = deploy.paths(self.home)
        self.assertFalse(p["current"].is_symlink())
        self.assertFalse(p["releases"].joinpath(self.v1[:7]).exists())
        self.assertEqual(self.cron(), LEGACY)
        self.assertTrue((state / "state.json").exists())  # reader state is kept

    def test_disable_leaves_install(self):
        self.install(self.v1)
        deploy.disable(self.home)
        self.assertEqual(self.ours(), [])
        self.assertTrue(deploy.paths(self.home)["current"].is_symlink())
        self.assertIn("no canary", deploy.disable(self.home))

    def run_sh(self):
        return subprocess.run([str(deploy.paths(self.home)["run"])], capture_output=True, text=True)

    def log(self):
        return (deploy.paths(self.home)["state"] / "reader.log").read_text()

    def test_success_run_is_logged(self):
        srv = HTTPServer(("127.0.0.1", 0), Discovery)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        # the stand-in package is a stub; use the real hostreader instead
        rel = ROOT / "hostreader"
        sh("cp", "-r", str(rel), str(self.repo), cwd=self.repo)
        sh("git", "add", "-A", cwd=self.repo)
        sh("git", "commit", "-qm", "real", cwd=self.repo)
        rev = sh("git", "rev-parse", "HEAD", cwd=self.repo).stdout.strip()
        self.install(rev, f"http://127.0.0.1:{srv.server_address[1]}")
        proc = self.run_sh()
        self.assertEqual(proc.returncode, 0, self.log())
        self.assertRegex(self.log(), r"Z rc=0 client=" + rev)
        self.assertIn("poll ok", self.log())
        self.assertTrue((deploy.paths(self.home)["state"] / "INBOX.txt").exists())
        self.assertFalse((self.home / ".townsquare").exists())

    def test_overlap_is_skipped_not_stacked(self):
        self.install(self.v1)
        state = deploy.paths(self.home)["state"]
        with open(state / "run.lock", "w") as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            proc = self.run_sh()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("SKIPPED", self.log())
        self.assertNotIn("rc=", self.log())
        self.assertEqual(self.run_sh().returncode, 0)  # lock released: runs again
        self.assertIn("rc=", self.log())

    def test_failure_is_observable_and_keeps_last_good_state(self):
        rel_src = ROOT / "hostreader"
        sh("cp", "-r", str(rel_src), str(self.repo), cwd=self.repo)
        sh("git", "add", "-A", cwd=self.repo)
        sh("git", "commit", "-qm", "real", cwd=self.repo)
        rev = sh("git", "rev-parse", "HEAD", cwd=self.repo).stdout.strip()
        state = deploy.paths(self.home)["state"]
        state.mkdir(parents=True)
        good = {"schema": "townsquare-host-reader-state-v1", "last_poll": None,
                "seen_event_ids": ["e1"],
                "items": [{"thread_id": "t1", "event_id": "e1", "addressee": "cable", "state": "OPEN",
                           "kind": "Request", "ledger_seq": 1, "first_seen_at": "x", "detail": "ok (1 events)"}]}
        (state / "state.json").write_text(json.dumps(good))
        self.install(rev, "http://127.0.0.1:9")  # nothing listens on the discard port
        proc = self.run_sh()
        self.assertEqual(proc.returncode, 1)
        self.assertRegex(self.log(), r"rc=1 .*FAILED")
        self.assertIn("UNKNOWN", (state / "INBOX.txt").read_text())
        self.assertEqual(json.loads((state / "state.json").read_text())["items"], good["items"])

    def test_missing_release_is_logged(self):
        self.install(self.v1)
        deploy.paths(self.home)["current"].unlink()
        self.assertEqual(self.run_sh().returncode, 3)
        self.assertIn("FAILED rc=3", self.log())


if __name__ == "__main__":
    unittest.main()
