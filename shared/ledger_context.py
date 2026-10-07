"""Validation for the governed-content manifest, distinct from R7 release context."""
import hashlib, json
from pathlib import Path

class LedgerContextError(RuntimeError): pass
def _pairs(items):
 result={}
 for key,value in items:
  if key in result: raise ValueError('duplicate governed-context field')
  result[key]=value
 return result
def load_ledger_context(path,expected_sha256,r7_context_path):
 candidate=Path(path); release=Path(r7_context_path)
 if candidate.resolve()==release.resolve(): raise LedgerContextError('governed and release context paths must be distinct')
 if candidate.is_symlink() or not candidate.is_file() or candidate.stat().st_mode & 0o222: raise LedgerContextError('governed context must be a read-only regular file')
 raw=candidate.read_bytes()
 if len(expected_sha256)!=64 or hashlib.sha256(raw).hexdigest()!=expected_sha256: raise LedgerContextError('governed context hash mismatch')
 try: value=json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs)
 except Exception as exc: raise LedgerContextError('governed context is invalid JSON') from exc
 if not isinstance(value,dict) or set(value)!={"id","sha256","governance","required_items","pinned"} or value.get('pinned') is not True or not isinstance(value.get('governance'),list) or not isinstance(value.get('required_items'),list): raise LedgerContextError('governed context has the wrong closed shape')
 return value
