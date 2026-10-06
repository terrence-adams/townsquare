#!/usr/bin/env python3
"""Create a populated wheelhouse lock from locally acquired wheels, offline."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--wheelhouse',type=Path,required=True);p.add_argument('--resolved',type=Path,required=True);a=p.parse_args()
if not a.wheelhouse.is_dir() or not a.resolved.is_file():raise SystemExit('wheelhouse and resolver output required')
rows=[]
for wheel in sorted(a.wheelhouse.glob('*.whl')):
 rows.append({'filename':wheel.name,'sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'source':'approved-wheelhouse'})
if not rows:raise SystemExit('refusing empty wheelhouse')
out={'schema':1,'status':'RESOLVED','resolver_output_sha256':hashlib.sha256(a.resolved.read_bytes()).hexdigest(),'wheels':rows}
(Path(__file__).resolve().parents[1]/'wheelhouse.lock.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
