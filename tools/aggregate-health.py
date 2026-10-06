#!/usr/bin/env python3
"""Release health gate: confirms service health and a signed backup manifest.

This is an operator-facing aggregate check, not a new service authority. It
does not modify state or make network calls beyond the two loopback endpoints.
"""
import argparse, json, subprocess, sys, urllib.request
from pathlib import Path
def get(url):
 with urllib.request.urlopen(url,timeout=3) as response:
  data=json.load(response)
 if not data.get('ok'): raise RuntimeError(f'not ready: {url}')
 return data
def main():
 p=argparse.ArgumentParser(); p.add_argument('--ledger',default='http://127.0.0.1:8790/health/ready'); p.add_argument('--viewer',default='http://127.0.0.1:8502/_stcore/health'); p.add_argument('--backup-manifest',type=Path,required=True); p.add_argument('--public-key',required=True); a=p.parse_args()
 manifest=a.backup_manifest
 if not manifest.is_file() or not manifest.with_suffix(manifest.suffix+'.minisig').is_file(): raise SystemExit('signed backup manifest is required')
 subprocess.run(['minisign','-Vm',str(manifest),'-p',a.public_key,'-x',str(manifest)+'.minisig'],check=True)
 ledger=get(a.ledger); viewer=get(a.viewer)
 required={'ledger_service':'townsquare-ledger-v0','ledger_schema_head':14,'registry_service':'townsquare-registry-v0','registry_schema_head':2,'audit_contract':'registry-ledger-audit-v1'}
 print(json.dumps({'ledger':ledger,'viewer':viewer,'compatibility_required':required,'backup_manifest':str(manifest),'ok':True},sort_keys=True))
if __name__=='__main__': main()
