#!/usr/bin/env python3
"""Generate auditable local release metadata; never pulls, pushes, or deploys."""
import argparse, hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):
 h=hashlib.sha256(path.read_bytes()).hexdigest(); return {"path":str(path.relative_to(ROOT)).replace('\\\\','/'),"sha256":h}
def main():
 p=argparse.ArgumentParser(); p.add_argument('--ledger-image',required=True); p.add_argument('--viewer-image',required=True); p.add_argument('--registry-image',required=True); p.add_argument('--backup-image',required=True); p.add_argument('--commit',required=True); a=p.parse_args()
 actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 if a.commit != actual: raise SystemExit(f'commit must equal current source SHA: {actual}')
 for image in (a.ledger_image,a.viewer_image,a.registry_image,a.backup_image):
  if '@sha256:' not in image or len(image.rsplit('@sha256:',1)[1])!=64: raise SystemExit('image must be an immutable sha256 digest reference')
 wheelhouse=json.loads((ROOT/'wheelhouse.lock.json').read_text())
 sbom=json.loads((ROOT/'sbom.cdx.json').read_text())
 if not wheelhouse.get('wheels') or not sbom.get('components'): raise SystemExit('refuse release manifest: wheelhouse lock and SBOM must be populated from a real offline build')
 files=[ROOT/'registrar/requirements.txt',ROOT/'viewer/requirements.txt',ROOT/'compose.yml',ROOT/'compose.nas.yml',ROOT/'wheelhouse.lock.json']
 manifest={"schema":1,"commit":a.commit,"images":{"ledger":a.ledger_image,"viewer":a.viewer_image,"registry":a.registry_image,"backup":a.backup_image},"dependencies":[sha(f) for f in files],"build":"offline wheelhouse only","sbom":"sbom.cdx.json"}
 (ROOT/'release-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 print('wrote release-manifest.json; generate an SPDX/CycloneDX SBOM from the same offline wheelhouse before release')
if __name__=='__main__': main()
