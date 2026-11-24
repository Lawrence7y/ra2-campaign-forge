# -*- coding: utf-8 -*-
"""导出 EVIDENCE\merge_records.txt：9 张 A 类卡的每一行在 MERGE_LOG 里的登记（含依据）。"""
import os, re

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT  = os.path.join(ROOT,"RECON_UNMERGED","EVIDENCE")
ENTRY_RE = re.compile(r"^[0-9A-Fa-f]{8}$")
CARDS = ["S09_KPROVED2","S10_K11","S10_K14","SEMFIX_6","SEMFIX_REST","SEMFIX_S10",
         "SEMFIX_SLOTS","SEMFIX_SLOTS2","SEMFIX_SLOTS3"]

def de(card):
    out=[]
    for l in open(os.path.join(ROOT,card,"coverage_delta.tsv"),encoding="utf-8",errors="replace"):
        c0=l.split("\t")[0].strip()
        if ENTRY_RE.match(c0): out.append(c0.upper())
    return out

idx={}
for m in range(1,50):
    p=os.path.join(ROOT,"M%d"%m,"MERGE_LOG.tsv")
    if not os.path.exists(p): continue
    lines=[l for l in open(p,encoding="utf-8",errors="replace").read().split("\n") if l.strip()]
    hdr=lines[0].split("\t")
    for l in lines[1:]:
        pp=l.split("\t")
        if not pp or not ENTRY_RE.match(pp[0].strip()): continue
        r=dict(zip(hdr,pp))
        idx.setdefault(pp[0].strip().upper(),[]).append(("M%d"%m,hdr,r))

o=["# 9 张 A 类卡的逐行并表登记（来源：各 M 卡 MERGE_LOG.tsv，未改动任何文件）",""]
for c in CARDS:
    o.append("="*70)
    o.append("## %s  (delta %d 行)"%(c,len(de(c))))
    for e in de(c):
        recs=idx.get(e,[])
        if not recs:
            o.append("  %s  -> 无 MERGE_LOG 记录（该行未由本卡并入 / 或并入记录在 M 卡 <22 的 _hygiene 报告内）"%e)
            continue
        o.append("  %s"%e)
        for m,hdr,r in recs:
            key=[k for k in ("evidence_or_basis","source_card","reason","col_changed","old_value","new_value","action","note") if k in r]
            o.append("     %-4s "%m + " | ".join("%s=%s"%(k,str(r[k])[:110]) for k in key))
open(os.path.join(OUT,"merge_records.txt"),"w",encoding="utf-8",newline="\n").write("\n".join(o)+"\n")
print("wrote merge_records.txt")
