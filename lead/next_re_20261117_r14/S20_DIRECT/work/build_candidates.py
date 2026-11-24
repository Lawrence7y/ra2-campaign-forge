#!/usr/bin/env python3
# Build direct-call candidate table for S20 rows [static] and [unproved].
# Read-only on coverage/atlas/exe. Writes only under S20_DIRECT.
import os,sys,json,struct,collections
import pefile,capstone
ROOT=r"D:\Project\ra2-campaign-forge"
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S20_DIRECT")
WK=os.path.join(OUT,"work"); EV=os.path.join(OUT,"EVIDENCE")
EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
COV=os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE","coverage.tsv")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")

def norm(a): return a.upper().replace("0X","")
def load_s20():
    lines=open(COV,encoding="utf-8").read().splitlines()
    head=lines[0].split(","); idx={n:i for i,n in enumerate(head)}
    rows=[]
    for l in lines[1:]:
        if not l.strip(): continue
        f=l.split("\t")
        if len(f)<len(head): continue
        if f[idx["subsystem"]]!="S20": continue
        rows.append(dict(entry=f[idx["entry"]],name=f[idx["name"]],sem=f[idx["one_line_semantics"]],
                         grade=f[idx["grade"]],ev=f[idx["evidence_path"]],nsrc=f[idx["n_sources"]],conflict=f[idx["conflict"]]))
    al={}
    for l in open(ATLAS,encoding="utf-8").read().splitlines()[1:]:
        if not l.strip():continue
        f=l.split("\t"); al[norm(f[0])]=dict(size=int(f[1]),n_instr=int(f[2]),n_callers=int(f[3]))
    for r in rows:
        a=norm(r["entry"]); r["atlas"]=al.get(a)
    return rows,al

def main():
    rows,al=load_s20()
    print("S20 total rows:",len(rows),"with atlas:",sum(1 for r in rows if r["atlas"]))
    # load direct call sites by target
    bytarget=collections.defaultdict(list)
    for l in open(os.path.join(WK,"all_direct_call_sites.tsv"),encoding="utf-8").read().splitlines()[1:]:
        f=l.split("\t"); bytarget[f[2]].append((f[0],int(f[1]),int(f[3])))
    # non-self-loop: caller interval must not contain entry
    # use atlas intervals for all callers; for missing-atlas callers, use [site, site+size) as minimal (cannot contain entry unless entry==site)
    # Build global address->atlas interval via sorted atlas entries
    intervals=sorted((int(a,16), int(a,16)+d["size"]) for a,d in al.items())
    import bisect
    starts=[x[0] for x in intervals]
    def caller_contains(site,size,entry_int):
        # find atlas entry with largest start <= site
        i=bisect.bisect_right(starts,site)-1
        if i>=0 and intervals[i][0]<=site<intervals[i][1]:
            return intervals[i][0]<=entry_int<intervals[i][1]
        # fallback: caller body unknown; treat only exact site==entry as self-loop suspicion
        return entry_int==site
    cand={}
    for r in rows:
        a=norm(r["entry"])
        sites=bytarget.get(a,[])
        accepted=[]; rejected_self=[]
        for site,size,rel in sites:
            si=int(site,16); en=int(a,16)
            if caller_contains(si,size,en):
                rejected_self.append(dict(site=site,size=size,rel=rel))
            else:
                accepted.append(dict(site=site,size=size,rel=rel))
        cand[a]=dict(accepted=accepted,rejected_self=rejected_self)
    # stats
    hit_rows=[r for r in rows if cand[norm(r["entry"])]["accepted"]]
    stat=collections.Counter(r["grade"] for r in hit_rows)
    print("rows with >=1 accepted direct caller:",len(hit_rows),"by grade:",dict(stat))
    # Save candidate detail json
    out=dict(s20=[{k:r[k] for k in ("entry","name","sem","grade","ev","nsrc","conflict")} | {"atlas":r["atlas"]} for r in rows],
             candidates=cand)
    json.dump(out,open(os.path.join(WK,"s20_candidates.json"),"w",encoding="utf-8"),indent=2)
    # TSV summary: entry grade n_accepted n_self sites
    with open(os.path.join(WK,"s20_direct_hits.tsv"),"w",encoding="utf-8") as f:
        f.write("entry\tgrade\tname\tn_accepted\tn_self\tsites\n")
        for r in rows:
            a=norm(r["entry"]); c=cand[a]
            sites=";".join(x["site"] for x in c["accepted"])
            f.write(f"{a}\t{r['grade']}\t{r['name']}\t{len(c['accepted'])}\t{len(c['rejected_self'])}\t{sites}\n")
    print("wrote",os.path.join(WK,"s20_direct_hits.tsv"))

if __name__=="__main__":main()
