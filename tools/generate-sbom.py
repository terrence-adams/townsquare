#!/usr/bin/env python3
"""Generate a nonempty CycloneDX-shaped SBOM from actual local wheel metadata.

Image inspection JSON is required because an SBOM without the built image/base
digest is not release evidence. This tool never contacts a registry.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--wheelhouse',type=Path,required=True);p.add_argument('--image-inspection',type=Path,required=True);a=p.parse_args()
if not a.wheelhouse.is_dir() or not a.image_inspection.is_file():raise SystemExit('local wheelhouse and docker image-inspection JSON are required')
components=[]
for whl in sorted(a.wheelhouse.glob('*.whl')):
 with zipfile.ZipFile(whl) as z:
  metadata=next((n for n in z.namelist() if n.endswith('.dist-info/METADATA')),None)
  if not metadata:raise SystemExit(f'wheel has no metadata: {whl.name}')
  fields=dict(line.split(': ',1) for line in z.read(metadata).decode(errors='replace').splitlines() if ': ' in line)
 components.append({'type':'library','name':fields.get('Name',whl.stem),'version':fields.get('Version','UNKNOWN'),'hashes':[{'alg':'SHA-256','content':hashlib.sha256(whl.read_bytes()).hexdigest()}]})
images=json.loads(a.image_inspection.read_text())
if not components or not images:raise SystemExit('refusing SBOM without wheel components and inspected images')
sbom={'bomFormat':'CycloneDX','specVersion':'1.5','version':1,'metadata':{'component':{'type':'application','name':'townsquare-mvp'},'properties':[{'name':'townsquare.image_inspection_sha256','value':hashlib.sha256(a.image_inspection.read_bytes()).hexdigest()}]},'components':components,'properties':[{'name':'townsquare.evidence_status','value':'GENERATED_FROM_LOCAL_WHEELHOUSE_AND_IMAGE_INSPECTION'}]}
(ROOT/'sbom.cdx.json').write_text(json.dumps(sbom,sort_keys=True,indent=2)+'\n')
