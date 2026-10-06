#!/usr/bin/env python3
"""NAS-safe verification: accepts public verification material only."""
import argparse,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('request',type=Path);p.add_argument('signature',type=Path);p.add_argument('--public-key',required=True);a=p.parse_args()
subprocess.run(['minisign','-Vm',str(a.request),'-x',str(a.signature),'-p',a.public_key],check=True)
