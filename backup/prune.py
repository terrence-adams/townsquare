#!/usr/bin/env python3
"""Retention helper: defaults to dry-run and accepts only timestamp backup children."""
import argparse, shutil
from datetime import datetime,timezone,timedelta
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument("root"); p.add_argument("--keep-days",type=int,required=True); p.add_argument("--apply",action="store_true"); a=p.parse_args()
root=Path(a.root).resolve()
if not root.is_dir() or a.keep_days<1: raise SystemExit("valid backup root and positive retention required")
cut=datetime.now(timezone.utc)-timedelta(days=a.keep_days)
for child in root.iterdir():
 if not child.is_dir() or not (child/'manifest.json').is_file(): continue
 try: when=datetime.strptime(child.name,"%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
 except ValueError: continue
 if when<cut:
  print(("delete" if a.apply else "would delete"),child)
  if a.apply: shutil.rmtree(child)
