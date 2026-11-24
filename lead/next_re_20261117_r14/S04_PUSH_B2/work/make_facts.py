# -*- coding: utf-8 -*-
"""汇总 18 行四环关键事实，输出 work/facts_final.tsv 供 EVIDENCE/REPORT 引用。只读。"""
import os, csv, json, re
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S04_PUSH_B2"
W = os.path.join(OUT, "work")

rows=[]
with open(os.path.join(W,"b2_entries.tsv"),encoding="utf-8") as fh:
    for r in csv.DictReader(fh,delimiter="\t"): rows.append(r)

cc={}
with open(os.path.join(W,"ctorchain_summary.tsv"),encoding="utf-8") as fh:
    for r in csv.DictReader(fh,delimiter="\t"): cc[r["entry"]]=r

slot=json.load(open(os.path.join(W,"slot_check2.json"),encoding="utf-8"))

out=[]
for r in rows:
    e=r["entry"]
    d=open(os.path.join(W,"dump_%s.txt"%e),encoding="utf-8").read()
    # ①
    m=re.search(r"entry=0x([0-9A-F]+) in_text=(\w+).*?atlas_size=(\d+)",d)
    intext=m.group(2) if m else "?"
    size=m.group(3) if m else r["size"]
    # ③b② sites
    msite=re.search(r"③b② 候选站点数=(\d+)",d)
    n3b2=msite.group(1) if msite else "?"
    # first sites
    sites=re.findall(r"call@0x([0-9A-F]+) -> (\w+)@0x([0-9A-F]+).*?je@0x([0-9A-F]+)|call@0x([0-9A-F]+) -> (\w+)@0x([0-9A-F]+).*?\w+@0x([0-9A-F]+)",d)
    sitelines=[ln.strip() for ln in d.splitlines() if "call@" in ln and "eax_trap_gap" in ln]
    # jump table
    mj=re.search(r"jump-table\(indirect jmp mem\) count=(\d+)",d)
    njt=mj.group(1) if mj else "?"
    nref=slot[e]["n_refs"]
    nslot=slot[e]["n_named_slots"]
    c=cc[e]
    out.append({
        "entry":e,"name":r["name"],"size":size,"intext":intext,
        "dword_refs":nref,"named_slots":nslot,
        "self_vt":c["self_vt_writes"],"n_direct":c["n_direct"],
        "caller_vtwrite":c["caller_with_vtwrite"],"caller_branch":c["caller_branch_eax"],
        "n3b2":n3b2,"njt":njt,
        "sites":" | ".join(sitelines[:4]),
    })

with open(os.path.join(W,"facts_final.tsv"),"w",encoding="utf-8",newline="") as fh:
    keys=["entry","name","size","intext","dword_refs","named_slots","self_vt","n_direct","caller_vtwrite","caller_branch","n3b2","njt","sites"]
    w=csv.DictWriter(fh,fieldnames=keys,delimiter="\t"); w.writeheader(); w.writerows(out)
for o in out:
    print("%s sz=%s refs=%s slots=%s selfvt=%s dir=%s cvtw=%s br=%s 3b2=%s jt=%s"%(
        o["entry"],o["size"],o["dword_refs"],o["named_slots"],o["self_vt"],
        o["n_direct"],o["caller_vtwrite"],o["caller_branch"],o["n3b2"],o["njt"]))
print("wrote facts_final.tsv")
