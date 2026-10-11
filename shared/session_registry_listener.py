"""Canonical non-secret Session Registry release-listener tuple."""
import hashlib,json

SCHEMA='townsquare.session-registry-listener.v1'
BIND_HOST='0.0.0.0'
BIND_PORT=8793
PUBLIC_URL='http://registry:8793'
READINESS_URL=PUBLIC_URL+'/health/ready'
LOOPBACK_READINESS_URL='http://127.0.0.1:8793/health/ready'
CANONICAL_JSON=json.dumps({'schema':SCHEMA,'bind_host':BIND_HOST,'bind_port':BIND_PORT,'public_url':PUBLIC_URL},sort_keys=True,separators=(',',':'))
SHA256='6822f4d0ec8da1e2c56120c925a8dd6f068f85d6030eab84055a2a0789167b7d'

if hashlib.sha256(CANONICAL_JSON.encode()).hexdigest()!=SHA256:
 raise RuntimeError('packaged Session Registry listener authority invalid')

def environment():
 return {'REGISTRY_SESSION_BIND_HOST':BIND_HOST,'REGISTRY_SESSION_BIND_PORT':str(BIND_PORT),'REGISTRY_SESSION_PUBLIC_URL':PUBLIC_URL,'REGISTRY_SESSION_LISTENER_SHA256':SHA256}
