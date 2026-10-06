#!/usr/bin/env python3
"""Print or execute the two-phase wheelhouse procedure only after approval."""
import argparse, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; LOCK=ROOT/'requirements/requirements.lock.json'
COMMANDS=[
 "python -m pip install --upgrade pip==24.3.1 pip-tools==7.5.0 cyclonedx-bom==7.1.0",
 "pip-compile --generate-hashes --strip-extras -o requirements/resolved.txt requirements/registrar.in requirements/viewer.in requirements/toolchain.in",
 "python -m pip download --require-hashes --dest wheelhouse -r requirements/resolved.txt",
 "python tools/generate-wheelhouse-lock.py --wheelhouse wheelhouse --resolved requirements/resolved.txt",
]
def main():
 p=argparse.ArgumentParser();p.add_argument('--approved-fetch',action='store_true');p.add_argument('--print-only',action='store_true');a=p.parse_args()
 if not a.approved_fetch:
  print('\n'.join(COMMANDS)); raise SystemExit('refusing download: pass --approved-fetch only after operator approval')
 if a.print_only: print('\n'.join(COMMANDS));return
 raise SystemExit('fetch execution intentionally disabled in this prepared package; execute the printed commands in the approved isolated fetch environment')
if __name__=='__main__':main()
