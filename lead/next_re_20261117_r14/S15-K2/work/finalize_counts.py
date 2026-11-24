#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate coverage_delta.tsv from PROMOTIONS_STRICT.tsv (37 rows) and compute final S口径 counts."""
import os,csv,re
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
CARD=os.path.join(ROOT,r"lead\next_re_20261117_r14\S15-K2")
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f,delimiter="\t"))
def norm(e): return e.strip().upper().zfill(8)
cov=rd(COV); atl={norm(r["entry"]):r for r in rd(ATL)}
s15=[r for r in cov if r["subsystem"].strip()=="S15" and norm(r["entry"]) in atl]
by={norm(r["entry"]):r for r in s15}
strict=rd(os.path.join(CARD,"EVIDENCE","PROMOTIONS_STRICT.tsv"))
print(f"strict promos={len(strict)}")
# regenerate delta
with open(os.path.join(CARD,"coverage_delta.tsv"),"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t")
    for p in sorted(strict,key=lambda x:x["entry"]):
        r=by[p["entry"]]; nm=p["new_name"]; reason=p["reason"]
        if nm.endswith("::GetSize"):
            sem=f"{nm}: 返回本类对象尺寸常量(B8 imm32 C3); vtable槽12 + RTTI + ctor push大小双点闭合"
        elif nm.endswith("::WhatAmI"):
            m=re.search(r"AbstractType\[(0x[0-9a-f]+)\]=ABS::(\w+)",reason)
            sem=f"{nm}: 返回 AbstractType 类型ID; vtable槽11 + YRpp ABS枚举吻合"+(f" ({m.group(2)})" if m else "")
        else:
            m=re.search(r"actionID=(\d+)=TRIG::(\w+)",reason)
            aid=m.group(1) if m else "?"; atn=m.group(2) if m else "?"
            sem=f"{nm}: TActionClass::Execute 动作ID {aid}(TriggerAction::{atn}) 的实现体; 跳表薄壳唯一call直指"
        w.writerow([p["entry"],"S15",nm,sem,"[已证]",p["evidence_path"]])

# final counts: apply delta to baseline
changes={p["entry"]:p for p in strict}
def is_S_named(n):
    n=(n or "").strip()
    return bool(n) and not n.startswith("sub_") and "::sub_" not in n
def is_L_named(n):
    n=(n or "").strip(); return bool(n) and not n.startswith("sub_")
base_n=len(s15); base_proved=sum(1 for r in s15 if r["grade"].strip()=="[已证]")
base_Snamed=sum(1 for r in s15 if is_S_named(r["name"]))
base_Lnamed=sum(1 for r in s15 if is_L_named(r["name"]))
new_proved=base_proved; new_Snamed=base_Snamed; new_Lnamed=base_Lnamed
for e,p in changes.items():
    r=by[e]
    if r["grade"].strip()!="[已证]": new_proved+=1
    if not is_S_named(r["name"]) and is_S_named(p["new_name"]): new_Snamed+=1
    if not is_L_named(r["name"]) and is_L_named(p["new_name"]): new_Lnamed+=1
# atlas denominator stays 158 (all promoted entries are in atlas)
lines=[]
lines.append(f"BASELINE (atlas S15, disk coverage.tsv): n={base_n}, [已证]={base_proved}, named_L={base_Lnamed}, named_S={base_Snamed}")
lines.append(f"PROMOTIONS applied: {len(changes)} rows")
lines.append(f"  -> [已证]: {base_proved} + {new_proved-base_proved} = {new_proved}/{base_n} = {100*new_proved/base_n:.2f}%")
lines.append(f"  -> named_L: {base_Lnamed} + {new_Lnamed-base_Lnamed} = {new_Lnamed}/{base_n} = {100*new_Lnamed/base_n:.2f}%")
lines.append(f"  -> named_S: {base_Snamed} + {new_Snamed-base_Snamed} = {new_Snamed}/{base_n} = {100*new_Snamed/base_n:.2f}%")
lines.append(f"DoD thresholds: named_S >=90% => need {int(-(-90*base_n//100))} = {-(-90*base_n//100)}; proved >=50% => {-(-50*base_n//100)}")
lines.append(f"GAPS after this card: named_S {-(-90*base_n//100)-new_Snamed} more; proved {max(0,-(-50*base_n//100)-new_proved)} more")
lines.append(f"S15 does NOT meet named>=90% (S口径); {'MEETS' if new_proved>=0.5*base_n else 'does NOT meet'} proved>=50%")
# breakdown
from collections import Counter
cat=Counter()
for p in strict:
    if p["new_name"].endswith("::GetSize"): cat["GetSize"]+=1
    elif p["new_name"].endswith("::WhatAmI"): cat["WhatAmI"]+=1
    else: cat["TActionClass action impl"]+=1
lines.append(f"Promotion breakdown: {dict(cat)}")
open(os.path.join(CARD,"EVIDENCE","FINAL_COUNTS.txt"),"w",encoding="utf-8").write("\n".join(lines)+"\n")
print("\n".join(lines))
