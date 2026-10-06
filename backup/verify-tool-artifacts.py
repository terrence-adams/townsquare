#!/usr/bin/env python3
"""Offline verifier for staged public age/minisign executables."""
import hashlib,json,sys
from pathlib import Path
directory=Path(sys.argv[1]); lock=json.loads(Path(sys.argv[2]).read_text())
if lock.get('status')!='RESOLVED':raise SystemExit('tool artifact lock is not resolved')
for item in lock.get('artifacts',[]):
 path=directory/item['filename']
 if not path.is_file():raise SystemExit(f'missing staged artifact: {path.name}')
 if hashlib.sha256(path.read_bytes()).hexdigest()!=item.get('sha256'):raise SystemExit(f'hash mismatch: {path.name}')
