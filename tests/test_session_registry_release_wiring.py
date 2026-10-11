"""Docker-independent release wiring checks for the protected Registry listener."""
import hashlib,http.client,json,re,threading,unittest
from pathlib import Path

from shared.session_registry_listener import BIND_PORT,CANONICAL_JSON,LOOPBACK_READINESS_URL,PUBLIC_URL,READINESS_URL,SHA256,environment
from tests.test_session_registry_s1 import load_app

ROOT=Path(__file__).resolve().parents[1]

def release_values():
 values={}
 for line in (ROOT/'deploy'/'release.env.example').read_text(encoding='utf-8').splitlines():
  if line and not line.startswith('#'):
   name,separator,value=line.partition('=')
   if separator:values[name]=value
 return values

def resolve_listener_values(source,values):
 def replace(match):return values[match.group(1)]
 return re.sub(r'\$\{(REGISTRY_SESSION_[A-Z0-9_]+):\?[^}]+\}',replace,source)

class SessionRegistryReleaseWiringTests(unittest.TestCase):
 def test_canonical_tuple_digest_and_release_env_are_exact(self):
  self.assertEqual('6822f4d0ec8da1e2c56120c925a8dd6f068f85d6030eab84055a2a0789167b7d',hashlib.sha256(CANONICAL_JSON.encode()).hexdigest());self.assertEqual(SHA256,hashlib.sha256(CANONICAL_JSON.encode()).hexdigest());self.assertEqual(environment(),{name:release_values()[name] for name in environment()});self.assertEqual({'bind_host':'0.0.0.0','bind_port':8793,'public_url':'http://registry:8793','schema':'townsquare.session-registry-listener.v1'},json.loads(CANONICAL_JSON));self.assertEqual(('0.0.0.0',8793),load_app().session_listener_config(environment()))
 def test_production_compose_resolves_one_tuple_for_listener_peer_and_health(self):
  source=(ROOT/'compose.yml').read_text(encoding='utf-8');resolved=resolve_listener_values(source,environment());registry=resolved.split('\n  registry:\n',1)[1].split('\n  registry-migrate:\n',1)[0];ledger=resolved.split('\n  ledger:\n',1)[1].split('\n  viewer:\n',1)[0]
  for name,value in environment().items():self.assertIn(f'{name}: "{value}"',registry)
  self.assertIn(f'REGISTRY_READINESS_URL: "{READINESS_URL}"',ledger);self.assertIn(LOOPBACK_READINESS_URL,registry);self.assertNotRegex(registry,r'(?m)^\s+ports:');self.assertNotIn(':8789',resolved)
 def test_current_canary_and_registrar_consumers_use_the_same_endpoint(self):
  canary=(ROOT/'canary'/'compose.canary.yml').read_text(encoding='utf-8');validator=(ROOT/'canary'/'validate_compose.py').read_text(encoding='utf-8');registrar=(ROOT/'registrar'/'app'/'main.py').read_text(encoding='utf-8')
  for name,value in environment().items():self.assertIn(f'{name}: {value}' if name!='REGISTRY_SESSION_BIND_PORT' else f'{name}: "{value}"',canary)
  self.assertIn(READINESS_URL,canary);self.assertIn(LOOPBACK_READINESS_URL.replace('/health/ready','/health/internal/ready'),canary);self.assertNotIn(':8789',canary);self.assertNotIn(':8789',validator);self.assertNotIn(':8789',registrar);self.assertIn('SESSION_REGISTRY_READINESS_URL',registrar)
 def test_exact_configured_port_reaches_registry_health_without_docker(self):
  app=load_app();server=app.ThreadingHTTPServer(('127.0.0.1',BIND_PORT),app.Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   connection=http.client.HTTPConnection('127.0.0.1',BIND_PORT,timeout=3);connection.request('GET','/health/live');response=connection.getresponse();raw=response.read();connection.close();self.assertEqual(200,response.status);self.assertEqual({'ok':True},json.loads(raw))
  finally:server.shutdown();server.server_close();thread.join(3)

if __name__=='__main__':unittest.main()
