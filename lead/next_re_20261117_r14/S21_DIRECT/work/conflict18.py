#!/usr/bin/env python3
# 18 conflict scan by entry address (report only), single regex alternation.
import os,sys,io,json,re
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")
ROOT=r"D:\Project\ra2-campaign-forge"
EV=os.path.join(ROOT,"lead","next_re_20261117_r14","S21_DIRECT","EVIDENCE")
V=json.load(open(os.path.join(EV,"verify_direct.json"),encoding="utf-8"))["verified"]
entries=[r["entry"] for r in V]
# single combined regex: match any of the 35 addresses (with optional 0x prefix) as hex token
alt="|".join("0?x?"+e.lower() for e in entries)
MASTER=re.compile(r"(?<![0-9a-f])("+alt+r")(?![0-9a-f])",re.I)
addr2e={e.lower():e for e in entries}
roots=[os.path.join(ROOT,"docs","re"),os.path.join(ROOT,"re_atlas","kb"),os.path.join(ROOT,"re_atlas","evidence"),os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE")]
extra=[os.path.join(ROOT,"lead","GOAL_THREE_TARGETS_20261018.md")]
hits18={e:[] for e in entries};scanned=0;errs=0
def scan_lines(lines_iter,src):
    global scanned
    for i,l in enumerate(lines_iter,1):
        low=l.lower()
        for m in MASTER.finditer(low):
            tok=m.group(1).replace("0x","")
            # normalize token to 8 hex by matching known entry
            e=None
            for ee in entries:
                if ee.lower().endswith(tok) or tok.endswith(ee.lower()) or tok==ee.lower():
                    e=ee;break
            if e and len(hits18[e])<8:
                hits18[e].append(src+":"+str(i)+":"+l[:160])
for base in roots:
    if not os.path.isdir(base):continue
    for dp,dn,fn in os.walk(base):
        for n in fn:
            if not n.lower().endswith((".md",".tsv",".txt",".json")):continue
            p=os.path.join(dp,n)
            try:
                txt=open(p,encoding="utf-8",errors="ignore").read().splitlines()
                scanned+=1
            except:errs+=1;continue
            scan_lines(txt,p.replace(ROOT+os.sep,""))
for p in extra:
    if os.path.exists(p):
        try:
            scan_lines(open(p,encoding="utf-8",errors="ignore").read().splitlines(),os.path.basename(p))
            scanned+=1
        except:errs+=1
print("18 scanned files:",scanned,"errs:",errs)
tot=0
for e in entries:
    tot+=len(hits18[e])
    print("  18",e,"hits:",len(hits18[e]))
    for h in hits18[e][:2]:print("      ",h[:150])
print("total 18 hits:",tot)
# merge into baseline_final.json
p=os.path.join(EV,"baseline_final.json")
d=json.load(open(p,encoding="utf-8"))
d["conflicts18"]=hits18;d["scanned_files18"]=scanned
json.dump(d,open(p,"w",encoding="utf-8"),indent=2,ensure_ascii=False)
print("merged 18 into baseline_final.json")