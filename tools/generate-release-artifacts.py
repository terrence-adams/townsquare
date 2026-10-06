#!/usr/bin/env python3
"""Generate auditable local release metadata; never pulls, pushes, or deploys."""
import argparse, hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):
 h=hashlib.sha256(path.read_bytes()).hexdigest(); return {"path":str(path.relative_to(ROOT)).replace('\\\\','/'),"sha256":h}
def main():
 p=argparse.ArgumentParser(); p.add_argument('--ledger-image',required=True); p.add_argument('--viewer-image',required=True); p.add_argument('--commit',required=True); a=p.parse_args()
 for image in (a.ledger_image,a.viewer_image):
  if '@sha256:' not in image or len(image.rsplit('@sha256:',1)[1])!=64: raise SystemExit('image must be an immutable sha256 digest reference')
 files=[ROOT/'registrar/requirements.txt',ROOT/'viewer/requirements.txt',ROOT/'compose.yml',ROOT/'compose.nas.yml']
 manifest={"schema":1,"commit":a.commit,"images":{"ledger":a.ledger_image,"viewer":a.viewer_image},"dependencies":[sha(f) for f in files],"build":"offline wheelhouse only","sbom":"sbom.cdx.json"}
 (ROOT/'release-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 print('wrote release-manifest.json; generate an SPDX/CycloneDX SBOM from the same offline wheelhouse before release')
if __name__=='__main__': main()
