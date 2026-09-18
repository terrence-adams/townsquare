import hashlib,hmac,time
from .service import Forbidden,Invalid,canonical,now

def sign(evidence,key_id,key,nonce,timestamp=None):
    timestamp=int(timestamp or time.time()); message=canonical({"evidence":evidence,"key_id":key_id,"nonce":nonce,"timestamp":timestamp}).encode()
    return {"key_id":key_id,"nonce":nonce,"timestamp":timestamp,"signature":hmac.new(key,message,hashlib.sha256).hexdigest()}

def verify(db,evidence,attestation,expected_key_id,key,max_age=300):
    if not isinstance(attestation,dict) or attestation.get("key_id")!=expected_key_id: raise Forbidden("verifier attestation required")
    nonce=attestation.get("nonce",""); timestamp=attestation.get("timestamp")
    if not isinstance(timestamp,int) or abs(int(time.time())-timestamp)>max_age or len(nonce)<16: raise Forbidden("stale or invalid verifier attestation")
    expected=sign(evidence,expected_key_id,key,nonce,timestamp)["signature"]
    if not hmac.compare_digest(expected,str(attestation.get("signature",""))): raise Forbidden("invalid verifier attestation")
    try: db.execute("INSERT INTO verifier_nonces VALUES (?,?,?)",(expected_key_id,nonce,now()))
    except Exception as exc: raise Forbidden("replayed verifier attestation") from exc
