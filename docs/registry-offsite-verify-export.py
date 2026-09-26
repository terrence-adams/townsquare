"""
s6 export verification (registry `binding: offsite` fix).

Per ip-man's security ruling Sec.5 (s6, required): the deployed code must be
hashed and copied from the reviewed commit's git BLOBS, never from a Windows
working-tree checkout, because this machine has core.autocrlf=true (jackie's
review, Sec.0) -- a plain checkout silently turns LF into CRLF, which changes
every hash even when the content is identical.

This script is the one automated check on the exported files: it reports
each file's SHA-256 (to compare against `git show <fix-sha>:<path> | sha256sum`,
run separately) and whether it contains any CR byte (0x0D). A clean export
via `git show <rev>:<path> > file` in Git Bash should contain no CR bytes,
because `git show` prints the raw blob and never applies a checkout filter;
PowerShell's `>` redirection is the thing that can introduce corruption here
(it can re-encode a command's output, e.g. to UTF-16), which is exactly why
this whole export must run in Git Bash (ip-man's ruling Sec.5, s6, and
Watch-for (o)).

Usage:
    python registry-offsite-verify-export.py <file> [<file> ...]

Exit code 0 = every file is CR-free (necessary, not sufficient -- still
              compare each printed SHA-256 against the blob hash yourself).
Exit code 1 = at least one file contains a CR byte. Do not copy it to the
              NAS; something upstream of this script (the shell, the editor,
              a stray `git config core.autocrlf` on checkout) touched it.
Exit code 2 = usage / file-read error.
"""
import hashlib
import sys


def main(paths):
    any_cr = False
    for p in paths:
        try:
            data = open(p, "rb").read()
        except OSError as exc:
            print(f"ERROR reading {p}: {exc}")
            return 2
        has_cr = b"\r" in data
        any_cr = any_cr or has_cr
        digest = hashlib.sha256(data).hexdigest()
        print(f"{digest}  {p}  {len(data)} bytes  CR-bytes: {'YES -- STOP' if has_cr else 'none'}")
    return 1 if any_cr else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
