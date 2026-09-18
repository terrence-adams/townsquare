"""One-shot Registrar verifier using only rclone read commands and HTTPS POST."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,tempfile,urllib.request,uuid
from pathlib import Path
from registrar.app.filename import FilenameError,check_header,parse_filename,read_header
from registrar.app.attestation import sign

def _run(command,runner):
    result=runner(command,capture_output=True,timeout=180)
    if result.returncode: raise RuntimeError((result.stderr or b"rclone/ssh-keygen failed").decode(errors="replace") if isinstance(result.stderr,bytes) else result.stderr)
    return result.stdout

def verify(record,remote,allowed_signers,api_base,token,rclone="rclone",runner=subprocess.run,opener=urllib.request.urlopen,attestation_key=b"test-only",key_id="verifier-1"):
    if not api_base.startswith("https://") and opener is urllib.request.urlopen: raise ValueError("verifier API must use HTTPS")
    listing=_run([rclone,"lsjson","--recursive","--files-only",remote],runner)
    if isinstance(listing,bytes): listing=listing.decode()
    objects=json.loads(listing); matches=[o for o in objects if o.get("ID")==record["drive_file_id"] and not o.get("Path","").endswith(".sig")]
    if len(matches)!=1: raise RuntimeError("Drive file ID did not map to exactly one event")
    path=matches[0]["Path"]; filename=Path(path).name
    if sum(1 for o in objects if o.get("Path")==path)!=1: raise RuntimeError("ambiguous Drive event path")
    sidecars=[o for o in objects if o.get("Path")==path+".sig"]
    if len(sidecars)!=1 or not sidecars[0].get("ID"): raise RuntimeError("signature sidecar identity is missing or ambiguous")
    body=_run([rclone,"cat",f"{remote}/{path}"],runner); signature=_run([rclone,"cat",f"{remote}/{path}.sig"],runner)
    if isinstance(body,str): body=body.encode()
    if isinstance(signature,str): signature=signature.encode()
    binding=False; sig_ok=False; reasons=[]
    try:
        parsed=parse_filename(filename)
        with tempfile.TemporaryDirectory() as td:
            body_path=Path(td)/filename; sig_path=Path(td)/(filename+".sig")
            body_path.write_bytes(body); sig_path.write_bytes(signature)
            header=read_header(str(body_path)); check_header(parsed,header); binding=True
            identity=parsed.get("by") or parsed.get("from")
            if not identity: reasons.append("missing signer identity")
            else:
                command=["ssh-keygen","-Y","verify","-f",allowed_signers,"-I",identity,"-n","townsquare","-s",str(sig_path)]
                result=runner(command,input=body,capture_output=True,timeout=30); sig_ok=result.returncode==0
                if not sig_ok: reasons.append("detached signature invalid")
    except (FilenameError,OSError) as exc: reasons.append("binding invalid: "+str(exc))
    digest=hashlib.sha256(body).hexdigest(); canonical_url=f'https://drive.google.com/file/d/{record["drive_file_id"]}/view'
    evidence={"drive_file_id":record["drive_file_id"],"drive_url":canonical_url,"filename":filename,"content_sha256":digest,"header_binding":binding,"signature_valid":sig_ok,"sidecar_drive_file_id":sidecars[0]["ID"],"sidecar_content_sha256":hashlib.sha256(signature).hexdigest(),"evidence":"; ".join(reasons) or "independent rclone metadata, content, header and SSHSIG matched"}
    nonce=uuid.uuid4().hex; envelope={"evidence":evidence,"attestation":sign(evidence,key_id,attestation_key,nonce)}
    request=urllib.request.Request(f'{api_base.rstrip("/")}/v1/verifications/{record["post_uid"]}',data=json.dumps(envelope,separators=(",",":")).encode(),method="POST",headers={"Authorization":"Bearer "+token,"Idempotency-Key":str(uuid.uuid5(uuid.NAMESPACE_URL,record["post_uid"]+":"+digest+":"+filename)),"Content-Type":"application/json"})
    response=opener(request)
    raw=response.read(); return json.loads(raw.decode() if isinstance(raw,bytes) else raw)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("record",help="JSON file containing post_uid and drive_file_id")
    ap.add_argument("--remote",required=True); ap.add_argument("--allowed-signers",required=True); ap.add_argument("--api",required=True); ap.add_argument("--token-file",required=True); ap.add_argument("--attestation-key-file",required=True); ap.add_argument("--key-id",required=True); ap.add_argument("--rclone",default="rclone")
    args=ap.parse_args(); record=json.loads(Path(args.record).read_text()); token=Path(args.token_file).read_text().strip()
    key=Path(args.attestation_key_file).read_bytes().strip(); print(json.dumps(verify(record,args.remote,args.allowed_signers,args.api,token,args.rclone,attestation_key=key,key_id=args.key_id),sort_keys=True))
if __name__=="__main__": main()
