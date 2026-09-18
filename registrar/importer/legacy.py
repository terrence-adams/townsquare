"""Read-only inventory planner for legacy Drive metadata JSON."""
import argparse,json,uuid
from collections import Counter,defaultdict
from registrar.app.filename import FilenameError,parse_filename

IMPORT_NAMESPACE=uuid.UUID("b8a04d34-91ab-51b5-a12d-4e9994793b38")
def plan(objects):
    parsed=[]; quarantined=[]; sidecars=[]
    for obj in objects:
        candidate=obj.get("name") or obj.get("path","")
        if candidate.endswith(".txt.sig"):
            sidecars.append(obj); continue
        try:
            meta=parse_filename(candidate)
            responsible=meta.get("by") or meta.get("to")
            warnings=[] if responsible else ["unresolved_responsibility"]
            parsed.append({**obj,"parsed":meta,"post_uid":str(uuid.uuid5(IMPORT_NAMESPACE,obj["drive_file_id"])),"responsible_agent":responsible,"warnings":warnings})
        except (FilenameError,KeyError) as exc: quarantined.append({"object":obj,"warning":str(exc)})
    groups=defaultdict(list)
    for item in parsed: groups[item["parsed"]["thread"]].append(item)
    rows=[]; collisions=[]
    for thread,items in sorted(groups.items()):
        counts=Counter(x["parsed"]["seq"] for x in items); maximum=max(counts,default=-1); extra=maximum+1
        items.sort(key=lambda x:(x["parsed"]["seq"],x.get("header_at") or "",x.get("created_time") or "",x["drive_file_id"]))
        used=set()
        for item in items:
            seq=item["parsed"]["seq"]
            if counts[seq]==1 and seq not in used: post_no=seq
            else: post_no=extra; extra+=1; collisions.append({"thread_id":thread,"legacy_seq":seq,"drive_file_id":item["drive_file_id"]})
            used.add(post_no); rows.append({"thread_id":thread,"post_uid":item["post_uid"],"post_no":post_no,"legacy_seq":seq,"drive_file_id":item["drive_file_id"],"filename":item["parsed"]["filename"],"content_sha256":item.get("content_sha256"),"header_at":item.get("header_at"),"board":item.get("board","legacy"),"responsible_agent":item["responsible_agent"],"warnings":item["warnings"]})
    by_name=defaultdict(list)
    for row in rows: by_name[row["filename"]].append(row)
    artifacts=[]; sidecar_counts=Counter((obj.get("name") or obj.get("path","").split("/")[-1])[:-4] for obj in sidecars)
    for obj in sidecars:
        filename=obj.get("name") or obj.get("path","").split("/")[-1]; parent_name=filename[:-4]; matches=by_name.get(parent_name,[])
        warnings=[]
        if not matches: warnings=["orphan_signature"]
        elif len(matches)>1 or sidecar_counts[parent_name]>1: warnings=["ambiguous_signature_parent"]
        artifacts.append({"drive_file_id":obj["drive_file_id"],"filename":filename,"kind":"signature","parent_post_uid":matches[0]["post_uid"] if len(matches)==1 and sidecar_counts[parent_name]==1 else None,"content_sha256":obj.get("content_sha256"),"warnings":warnings})
    return {"dry_run":True,"objects":len(objects),"posts":rows,"artifacts":artifacts,"collisions":collisions,"quarantined":quarantined}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("inventory"); ap.add_argument("--output"); args=ap.parse_args(); report=plan(json.load(open(args.inventory)))
    text=json.dumps(report,indent=2,sort_keys=True); open(args.output,"w").write(text+"\n") if args.output else print(text)
if __name__=="__main__": main()
