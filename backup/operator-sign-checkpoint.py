#!/usr/bin/env python3
"""Run only in a separate operator environment, never on the NAS container."""
import argparse,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('request',type=Path);p.add_argument('--secret-key',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if not a.request.is_file():raise SystemExit('canonical checkpoint request missing')
subprocess.run(['minisign','-S','-s',a.secret_key,'-m',str(a.request),'-x',str(a.output)],check=True)
print('Signed checkpoint; transfer only request, signature, and public verification material to NAS.')
