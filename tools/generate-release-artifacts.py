#!/usr/bin/env python3
"""Generate auditable local release metadata; never pulls, pushes, or deploys."""
import argparse, hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):
 h=hashlib.sha256(path.read_bytes()).hexdigest(); return {"path":str(path.relative_to(ROOT)).replace('\\\\','/'),"sha256":h}
def tree_sha(relative):
 root=ROOT/relative; h=hashlib.sha256()
 for file in sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts):
  h.update(str(file.relative_to(ROOT)).replace('\\','/').encode()+b'\0'); h.update(file.read_bytes())
 return h.hexdigest()
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
 contexts={name:{'context':'.','dockerfile':dockerfile,'service_source_sha256':tree_sha(path),'dockerfile_sha256':sha(ROOT/dockerfile)['sha256'],'wheelhouse_lock_sha256':sha(ROOT/'wheelhouse.lock.json')['sha256'],'resolved_requirements_sha256':sha(ROOT/'requirements/resolved.txt')['sha256']} for name,path,dockerfile in [('ledger','registrar','registrar/Dockerfile'),('viewer','viewer','viewer/Dockerfile'),('registry','registry','registry/Dockerfile'),('backup','backup','backup/Dockerfile')]}
 compatibility={"ledger_service":"townsquare-ledger-v0","ledger_schema_head":14,"registry_service":"townsquare-registry-v0","registry_schema_head":2,"audit_contract":"registry-ledger-audit-v1"}
 manifest={"schema":2,"commit":a.commit,"images":{"ledger":a.ledger_image,"viewer":a.viewer_image,"registry":a.registry_image,"backup":a.backup_image},"compatibility":compatibility,"build_inputs":contexts,"dependencies":[sha(f) for f in files],"wheelhouse_lock_sha256":sha(ROOT/'wheelhouse.lock.json')['sha256'],"sbom_sha256":sha(ROOT/'sbom.cdx.json')['sha256'],"evidence_status":"GENERATED_PENDING_RUNTIME_EVIDENCE","build":"offline wheelhouse only","sbom":"sbom.cdx.json"}
 (ROOT/'release-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 print('wrote release-manifest.json; generate an SPDX/CycloneDX SBOM from the same offline wheelhouse before release')
if __name__=='__main__': main()
