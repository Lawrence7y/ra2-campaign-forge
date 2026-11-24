#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add 5 RTTI-confirmed constructor promotions and regenerate final delta/counts."""
import os,csv,struct,re
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
CARD=os.path.join(ROOT,r"lead\next_re_20261117_r14\S15-K2")
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f,delimiter="\t"))
def norm(e): return e.strip().upper().zfill(8)
cov=rd(COV); atl={norm(r["entry"]):r for r in rd(ATL)}
by={norm(r["entry"]):r for r in cov}
import sys
sys.path.insert(0,os.path.join(ROOT,r"lead\next_re_20261116_r12\_lead_audit"))
import audit_lib as A
b=A.Bin()
# (entry, class, vtable, COL) -- vtable[-1]=COL, COL+0xC->TD->name verified earlier
CTORS=[("006E4DE0","TagClass",0x7F44E0,0x80BBA0),
       ("006E4F60","TagClass",0x7F44E0,0x80BBA0),
       ("006E5B60","TagTypeClass",0x7F45C4,0x80BCF0),
       ("00725FA0","TriggerClass",0x7F5858,0x80C968),
       ("00726C80","TriggerTypeClass",0x7F5904,0x80CA20)]
fields=["entry","old_name","new_name","old_grade","new_grade","reason","evidence_path"]
strict=rd(os.path.join(CARD,"EVIDENCE","PROMOTIONS_STRICT.tsv"))
existing={p["entry"] for p in strict}
added=[]
for e,cn,vt,col in CTORS:
    if e in existing: continue
    # verify vtable[-1]==COL and vtable[0]==vt and RTTI name
    assert b.u32(vt-4)==col, (e,hex(b.u32(vt-4)))
    td=b.u32(col+0xC); nm=b.read(td+8,64).split(b"\x00")[0].decode(errors="replace")
    assert nm==f".?AV{cn}@@",(cn,nm)
    r=by[e]
    added.append(dict(entry=e,old_name=r["name"],new_name=f"{cn}::{cn}",old_grade=r["grade"],new_grade="[已证]",
      reason=f"constructor: writes {cn} vtable chain (vtable[0]={vt:#x}, COL={col:#x}->TD->{nm}) to [this] at entry; calls base ctor 0x410170/0x410800; registers in global arrays; ret 4",
      evidence_path="EVIDENCE/T2_constructor_candidates.txt;EVIDENCE/T2_vtable_verify.txt;EVIDENCE/T2_rtti_and_sub_callers.txt"))
promos=strict+added
with open(os.path.join(CARD,"EVIDENCE","PROMOTIONS_FINAL.tsv"),"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields,delimiter="\t"); w.writeheader()
    for p in sorted(promos,key=lambda x:x["entry"]): w.writerow(p)
# regenerate coverage_delta
with open(os.path.join(CARD,"coverage_delta.tsv"),"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t")
    for p in sorted(promos,key=lambda x:x["entry"]):
        nm=p["new_name"]; reason=p["reason"]
        if nm.endswith("::GetSize"):
            sem=f"{nm}: 返回本类对象尺寸常量(B8 imm32 C3); vtable槽12+RTTI+ctor push大小双点闭合"
        elif nm.endswith("::WhatAmI"):
            m=re.search(r"ABS::(\w+)",reason); sem=f"{nm}: 返回 AbstractType 类型ID; vtable槽11+YRpp ABS枚举吻合"+(f" ({m.group(1)})" if m else "")
        elif "constructor:" in reason:
            m=re.search(r"\.(\?AV\w+@@)",reason); sem=f"{nm}: 构造器; 入口写本类vtable链(C7 [this],vt)+调基类ctor+注册全局数组"
        else:
            m=re.search(r"actionID=(\d+)=TRIG::(\w+)",reason); aid=m.group(1) if m else "?"; atn=m.group(2) if m else "?"
            sem=f"{nm}: TActionClass::Execute 动作ID {aid}(TriggerAction::{atn}) 实现体; 跳表薄壳唯一call直指"
        w.writerow([p["entry"],"S15",nm,sem,"[已证]",p["evidence_path"]])
# counts
s15=[r for r in cov if r["subsystem"].strip()=="S15" and norm(r["entry"]) in atl]
chg={p["entry"]:p for p in promos}
def isSn(n):
    n=(n or "").strip(); return bool(n) and not n.startswith("sub_") and "::sub_" not in n
def isLn(n):
    n=(n or "").strip(); return bool(n) and not n.startswith("sub_")
n=len(s15); bp=sum(1 for r in s15 if r["grade"].strip()=="[已证]"); bs=sum(1 for r in s15 if isSn(r["name"])); bl=sum(1 for r in s15 if isLn(r["name"]))
np_=bp; ns=bs; nl=bl
for e,p in chg.items():
    r=by[e]
    if r["grade"].strip()!="[已证]": np_+=1
    if not isSn(r["name"]) and isSn(p["new_name"]): ns+=1
    if not isLn(r["name"]) and isLn(p["new_name"]): nl+=1
lines=[f"BASELINE atlas S15: n={n}, proved={bp}, named_L={bl}, named_S={bs}",
       f"PROMOTIONS: {len(promos)} (action={sum(1 for p in promos if p['new_name'].startswith('TActionClass::') and not p['new_name'].endswith(('GetSize','WhatAmI')))}, GetSize={sum(1 for p in promos if p['new_name'].endswith('::GetSize'))}, WhatAmI={sum(1 for p in promos if p['new_name'].endswith('::WhatAmI'))}, ctor={len(added)})",
       f"FINAL proved={np_}/{n}={100*np_/n:.2f}% (DoD>=50%: {'PASS' if np_>=0.5*n else 'FAIL'})",
       f"FINAL named_L={nl}/{n}={100*nl/n:.2f}% (PANEL口径)",
       f"FINAL named_S={ns}/{n}={100*ns/n:.2f}% (DoD>=90%: {'PASS' if ns>=0.9*n else 'FAIL'}, need {-(-90*n//100)})",
       f"REMAINING gap: named_S {-(-90*n//100)-ns} more rows needed"]
open(os.path.join(CARD,"EVIDENCE","FINAL_COUNTS.txt"),"w",encoding="utf-8").write("\n".join(lines)+"\n")
open(os.path.join(CARD,"EVIDENCE","FINAL_COUNTS.txt"),"a",encoding="utf-8").write("\n".join(promos and [f"{p['entry']}\t{p['new_name']}" for p in sorted(promos,key=lambda x:x['entry'])])+"\n")
print("\n".join(lines))
