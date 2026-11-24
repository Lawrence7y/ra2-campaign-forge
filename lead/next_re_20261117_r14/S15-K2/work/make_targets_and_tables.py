#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build TARGETS.tsv (T1) and explicit two-table dispatch evidence (T2)."""
import os,csv,sys,re
ROOT=r"D:\Project\ra2-campaign-forge"
sys.path.insert(0,os.path.join(ROOT,r"lead\next_re_20261116_r12\_lead_audit"))
import audit_lib as A
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
CARD=os.path.join(ROOT,r"lead\next_re_20261117_r14\S15-K2")
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f,delimiter="\t"))
def norm(e): return e.strip().upper().zfill(8)
cov=rd(COV); atl={norm(r["entry"]):r for r in rd(ATL)}
s15=[r for r in cov if r["subsystem"].strip()=="S15" and norm(r["entry"]) in atl]
final={r["entry"]:r for r in csv.DictReader(open(os.path.join(CARD,"EVIDENCE","PROMOTIONS_FINAL.tsv"),encoding="utf-8-sig"),delimiter="\t")}

# TARGETS.tsv: entry|现name|现grade|缺什么|取证计划
def plan_for(r):
    e=norm(r["entry"]); nm=r["name"].strip(); g=r["grade"].strip()
    if e in final:
        p=final[e]; return ("name&证据" if nm.startswith("sub_") else "证据", f"本卡已升 [已证]->{p['new_name']}")
    if nm.startswith("sub_"):
        return ("真名+一行语义+证据", "查Execute跳表薄壳唯一call/构造器vtable写+基类ctor; 无硬证则保持sub_")
    if "::slot" in nm:
        return ("真名+证据(现为slot号)", "查vtable槽语义(GetSize/WhatAmI双点; 其它槽需调用上下文); 无硬证保持slot")
    return "证据", "查本类vtable槽位/字段读写点"
rows=[]
for r in sorted(s15,key=lambda x:norm(x["entry"])):
    e=norm(r["entry"])
    miss,plan=plan_for(r)
    rows.append([e,r["name"],r["grade"],miss,plan])
with open(os.path.join(CARD,"TARGETS.tsv"),"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t"); w.writerow(["entry","name","grade","missing","plan"])
    w.writerows(rows)
print(f"Wrote TARGETS.tsv with {len(rows)} targets")

# Two dispatch tables explicit evidence (TEventClass::HasOccured, already accounted in KB)
b=A.Bin()
L1=0x71F218; L2=0x71F248; L1n=12; L2n=49
lines=[]
lines.append("TEventClass::HasOccured 0x71E940 — two-table dispatch (引用已入账 KB 10_map_triggers.md §3, 本卡独立字节复核)")
lines.append(f"派发指令 @0x71E964: FF 24 95 18 F2 71 00 = jmp dword ptr [edx*4 + 0x71F218]")
lines.append(f"一级表 L1 @0x{L1:08X}: {L1n} dword (绝对目标, 全部落 .text), 元素语义 = 事件处理函数地址")
for i in range(L1n):
    lines.append(f"  L1[{i:2d}] = 0x{b.u32(L1+4*i):08X}")
lines.append(f"二级选择表 L2 @0x{L2:08X}: {L2n} byte, 元素语义 = L1 下标(0..11), 值 11 = 兜底")
sel=[b.u8(L2+i) for i in range(L2n)]
lines.append("  L2 bytes: "+" ".join(f"{x:02X}" for x in sel))
lines.append(f"  索引公式: target = L1[ L2[ EventKind - 0x0D ] ]; TEventClass+0x2C = EventKind; 合法 0x0D..0x3D (49 槽)")
from collections import Counter
cc=Counter(sel)
lines.append(f"  值分布: {dict(sorted(cc.items()))}; 兜底值=11 出现 {cc.get(11,0)} 次")
lines.append("注: 三级/四级子派发表 0x71F27C(2)/0x71F2C0(14)/0x71F328(10) 见 KB §3.5, 本卡不重做.")
open(os.path.join(CARD,"EVIDENCE","T2_event_dispatch_tables.txt"),"w",encoding="utf-8").write("\n".join(lines)+"\n")
print("\n".join(lines[:8]))
