#!/usr/bin/env python3
# Build direct-call candidate table for S21 atlas∩coverage rows. Read-only on coverage/atlas/exe.
# Writes only under S21_DIRECT.
import os,sys,io,json,collections,bisect
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
ROOT=r"D:\Project\ra2-campaign-forge"
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S21_DIRECT")
WK=os.path.join(OUT,"work"); EV=os.path.join(OUT,"EVIDENCE")
COV=os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE","coverage.tsv")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
def norm(a): return a.upper().replace("0X","")

def load_atlas():
    al={}
    for l in open(ATLAS,encoding="utf-8").read().splitlines()[1:]:
        if not l.strip():continue
        f=l.split("\t"); al[norm(f[0])]=dict(size=int(f[1]),n_instr=int(f[2]),n_callers=int(f[3]))
    return al

def load_s21(al):
    lines=open(COV,encoding="utf-8").read().splitlines()
    rows=[]
    for l in lines[1:]:
        if not l.strip():continue
        f=l.split("\t")
        if len(f)<8:continue
        if f[1]!="S21":continue
        a=norm(f[0])
        if a not in al:continue   # atlas∩coverage convention (=129)
        rows.append(dict(entry=a,name=f[2],sem=f[3],grade=f[4],ev=f[5],nsrc=f[6],conflict=f[7],atlas=al[a]))
    return rows

def main():
    al=load_atlas()
    rows=load_s21(al)
    print("S21 atlas∩ rows:",len(rows),
          "grade:",dict(collections.Counter(r["grade"] for r in rows)))
    # direct call sites by target
    bytarget=collections.defaultdict(list)
    n=0
    for l in open(os.path.join(WK,"all_direct_call_sites.tsv"),encoding="utf-8").read().splitlines()[1:]:
        f=l.split("\t"); bytarget[f[2]].append((f[0],int(f[1]),int(f[3]))); n+=1
    print("direct call sites indexed:",n)
    # atlas intervals sorted for caller-owner lookup
    intervals=sorted((int(a,16), int(a,16)+d["size"]) for a,d in al.items())
    starts=[x[0] for x in intervals]
    def owner_of(addr):
        i=bisect.bisect_right(starts,addr)-1
        if i>=0 and intervals[i][0]<=addr<intervals[i][1]:
            return intervals[i][0],intervals[i][1]
        return None
    def caller_contains_entry(site, entry_int):
        own=owner_of(site)
        if own:
            return own[0]<=entry_int<own[1]
        # caller not in atlas: cannot prove body; only exact site==entry flagged self-loop
        return entry_int==site
    cand={}
    for r in rows:
        a=norm(r["entry"]); en=int(a,16)
        sites=bytarget.get(a,[])
        accepted=[]; rejected_self=[]
        for site,size,rel in sites:
            si=int(site,16)
            own=owner_of(si)
            own_hex=f"{own[0]:08X}" if own else ""
            if caller_contains_entry(si,en):
                rejected_self.append(dict(site=site,size=size,rel=rel,owner=own_hex))
            else:
                accepted.append(dict(site=site,size=size,rel=rel,owner=own_hex))
        cand[a]=dict(accepted=accepted,rejected_self=rejected_self)
    hit_rows=[r for r in rows if cand[norm(r["entry"])]["accepted"]]
    print("rows with >=1 accepted direct caller:",len(hit_rows),
          "by grade:",dict(collections.Counter(r["grade"] for r in hit_rows)))
    out=dict(s21=[{k:r[k] for k in ("entry","name","sem","grade","ev","nsrc","conflict")} | {"atlas":r["atlas"]} for r in rows],
             candidates=cand)
    json.dump(out,open(os.path.join(WK,"s21_candidates.json"),"w",encoding="utf-8"),indent=2,ensure_ascii=False)
    with open(os.path.join(WK,"s21_direct_hits.tsv"),"w",encoding="utf-8",newline="\n") as f:
        f.write("entry\tgrade\tname\tn_accepted\tn_self\tsites\n")
        for r in rows:
            a=norm(r["entry"]); c=cand[a]
            sites=";".join(x["site"] for x in c["accepted"])
            f.write(f"{a}\t{r['grade']}\t{r['name']}\t{len(c['accepted'])}\t{len(c['rejected_self'])}\t{sites}\n")
    print("wrote s21_candidates.json / s21_direct_hits.tsv")
    # list non-proved rows with hits
    print("\nNon-proved rows with accepted direct callers:")
    for r in hit_rows:
        if r["grade"]!="[已证]":
            c=cand[norm(r["entry"])]
            print("  ",r["entry"],r["grade"],r["name"],
                  "accepted",len(c["accepted"]),"self",len(c["rejected_self"]),
                  "sites",[x["site"] for x in c["accepted"][:6]])

if __name__=="__main__":main()
