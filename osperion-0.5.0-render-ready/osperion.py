from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from app.service import analyze_text, persist, analyze_image, persist_image
from app.db import search, history, stats, cleanup, create_investigation, list_investigations, list_images
from app.config import set_retention_days

def print_report(r: dict):
    print("\n=== OSPERION Analysis ===")
    print(f"Platform: {r['platform']}")
    print(f"Input SHA-256: {r['input_sha256']}")
    print(f"Artifacts: {r['artifact_count']}")
    print(f"Previous correlations: {r['correlation_count']}")
    print("\nArtifacts:")
    for a in r["artifacts"][:200]:
        print(f"  [{a['confidence']:<8}] {a['type']:<18} {a['value']}")
    if len(r["artifacts"]) > 200: print(f"  ... {len(r['artifacts'])-200} more")
    if r["correlations"]:
        print("\nPreviously observed matches:")
        for m in r["correlations"][:100]:
            scope = f"investigation #{m['investigation_id']}" if m.get("investigation_id") else "global history"
            print(f"  - {m['artifact_type']}: {m['value']} -> evidence #{m['matched_evidence_id']} ({m['matched_filename']}; {scope})")
    print("\nNote: correlations are evidence matches, not proof that accounts belong to the same person.")

def ask_save(report, filename, investigation_id=None, forced=None):
    if forced is True:
        eid = persist(report, filename, investigation_id); print(f"Saved as evidence #{eid}."); return
    if forced is False:
        print("Not saved."); return
    if not sys.stdin.isatty():
        print("Non-interactive CLI: not saved. Use --save to persist."); return
    scope = f"investigation #{investigation_id}" if investigation_id else "local history"
    ans = input(f"\nSave this analysis to {scope}? [y/N]: ").strip().lower()
    if ans in {"y", "yes"}:
        eid = persist(report, filename, investigation_id); print(f"Saved as evidence #{eid}.")
    else: print("Not saved.")

def main():
    p=argparse.ArgumentParser(prog="osperion",description="Local-first evidence correlation tool")
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("analyze",help="analyze inspect/source code")
    a.add_argument("file");a.add_argument("--platform",default="auto");a.add_argument("--investigation",type=int)
    a.add_argument("--save",action="store_true");a.add_argument("--no-save",action="store_true");a.add_argument("--json",action="store_true")
    im=sub.add_parser("image",help="analyze and optionally save a profile/media image")
    imsub=im.add_subparsers(dest="image_cmd",required=True)
    ia=imsub.add_parser("analyze",help="calculate SHA-256/pHash/dHash and compare with saved images")
    ia.add_argument("file");ia.add_argument("--investigation",type=int)
    ia.add_argument("--save",action="store_true");ia.add_argument("--no-save",action="store_true")
    il=imsub.add_parser("list",help="list saved images");il.add_argument("--investigation",type=int,required=True)
    s=sub.add_parser("search",help="search saved artifacts");s.add_argument("query")
    h=sub.add_parser("history",help="show saved evidence");h.add_argument("--investigation",type=int)
    st=sub.add_parser("stats",help="show local database stats");st.add_argument("--investigation",type=int)
    c=sub.add_parser("cleanup",help="remove expired saved history")
    inv=sub.add_parser("investigation",help="manage investigations")
    invsub=inv.add_subparsers(dest="inv_cmd",required=True)
    invsub.add_parser("list",help="list investigations")
    ic=invsub.add_parser("create",help="create an investigation");ic.add_argument("name");ic.add_argument("--description",default="")
    cfg=sub.add_parser("config",help="configure retention");cfg.add_argument("--retention-days",type=int,required=True)
    w=sub.add_parser("web",help="start local web UI");w.add_argument("--host",default="127.0.0.1");w.add_argument("--port",type=int,default=8000)
    args=p.parse_args()
    if args.cmd=="analyze":
        path=Path(args.file)
        if not path.exists(): p.error(f"File not found: {path}")
        report=analyze_text(path.read_text(encoding="utf-8",errors="replace"),path.name,args.platform,args.investigation)
        if args.json: print(json.dumps(report,indent=2,ensure_ascii=False))
        else: print_report(report)
        forced=True if args.save else False if args.no_save else None
        ask_save(report,path.name,args.investigation,forced)
    elif args.cmd=="image":
        if args.image_cmd=="list":
            print(json.dumps(list_images(args.investigation),indent=2,ensure_ascii=False))
        elif args.image_cmd=="analyze":
            path=Path(args.file)
            if not path.exists(): p.error(f"File not found: {path}")
            raw=path.read_bytes()
            try:
                result=analyze_image(raw,args.investigation)
            except ValueError as e:
                p.error(str(e))
            print("\n=== OSPERION Image Analysis ===")
            print(f"File: {path.name}")
            print(f"SHA-256: {result['sha256']}")
            print(f"pHash: {result['phash']}")
            print(f"dHash: {result['dhash']}")
            print(f"Dimensions: {result['width']}x{result['height']}")
            print(f"Previous image matches: {result['match_count']}")
            for m in result["matches"]:
                print(f"  - [{m['match_type']}] {m['label'] or m['filename']} | pHash distance={m['phash_distance']} | investigation #{m['investigation_id']}")
                print(f"    {m['note']}")
            if args.save:
                if args.investigation is None: p.error("--investigation is required with --save")
                iid=persist_image(raw,path.name,"", "unknown",args.investigation); print(f"Saved image asset #{iid}.")
            elif args.no_save:
                print("Not saved.")
            elif sys.stdin.isatty():
                if args.investigation is None:
                    print("No investigation supplied; image was not saved.")
                else:
                    ans=input(f"\nSave this image to investigation #{args.investigation}? [y/N]: ").strip().lower()
                    if ans in {"y","yes"}:
                        iid=persist_image(raw,path.name,"","unknown",args.investigation); print(f"Saved image asset #{iid}.")
                    else: print("Not saved.")
            else:
                print("Non-interactive CLI: not saved. Use --save to persist.")
    elif args.cmd=="search": print(json.dumps(search(args.query),indent=2,ensure_ascii=False))
    elif args.cmd=="history": print(json.dumps(history(100,args.investigation),indent=2,ensure_ascii=False))
    elif args.cmd=="stats": print(json.dumps(stats(args.investigation),indent=2,ensure_ascii=False))
    elif args.cmd=="cleanup": print(f"Removed expired evidence records: {cleanup()}")
    elif args.cmd=="config": print(f"Retention days: {set_retention_days(args.retention_days)}")
    elif args.cmd=="investigation":
        if args.inv_cmd=="list": print(json.dumps(list_investigations(),indent=2,ensure_ascii=False))
        elif args.inv_cmd=="create":
            iid=create_investigation(args.name,args.description);print(f"Created investigation #{iid}: {args.name}")
    elif args.cmd=="web":
        import uvicorn;uvicorn.run("app.api:app",host=args.host,port=args.port)
if __name__=="__main__": main()
