#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对 owner=None 的 gap 候选做高置信/低置信分级。可复跑。"""
import os, sys, json, bisect, re
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
WORK  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C02_census\\work")
sys.path.insert(0, os.path.join(ROOT, "lead\\next_re_20261116_r12\\_lead_audit"))
import audit_lib
import capstone

b = audit_lib.Bin()
# 全量 atlas 区间
rows, hdr = audit_lib.load_func_atlas()
starts = [va for va, _ in rows]
sizes  = {va: int(rec["size"]) for va, rec in rows}
def owner(site):
    i = bisect.bisect_right(starts, site) - 1
    if i >= 0 and starts[i] <= site < starts[i] + sizes[starts[i]]:
        return starts[i]
    return None

gaps = json.load(open(os.path.join(WORK, "gaps_raw.json"), encoding="utf-8"))["gaps"]
holes = [g for g in gaps if g["owner"] is None]

# vtable 槽目标集合（全镜像）
vtj = json.load(open(os.path.join(ATLAS, "vtables_v2.json"), encoding="utf-8"))
vt_targets = set()
for v in vtj["vtables"]:
    vt = v["vt"]; n = v.get("slots", 0)
    if n <= 0 or n > 400: continue
    for i in range(n):
        try: vt_targets.add(b.u32(vt + 4*i))
        except Exception: pass

# 函数序言识别：从 target 起前 4 条真指令
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = False; md.skipdata = True
PROLOGUE = re.compile(r"^(push\s+(ebp|ebx|esi|edi|ecx)|mov\s+e[bp][px],\s*esp|sub\s+esp,|and\s+esp,|mov\s+edx,\s*esp|pushf)")

def prologue_ok(va):
    n = 0
    for ins in md.disasm(b.read(va, 24), va):
        if ins.id == 0: return False, ""   # skipdata -> 首字节就不可解码
        if n < 3 and PROLOGUE.match(ins.mnemonic + " " + ins.op_str):
            return True, "%s %s" % (ins.mnemonic, ins.op_str)
        n += 1
        if n >= 4: break
    return False, "(no-prologue-in-4)"

out = []
for g in holes:
    t = g["target"]
    sites = g["sites"]
    site_owners = [(s, owner(s)) for s in sites]
    sites_in_fn = sum(1 for s, o in site_owners if o is not None)
    ok, first = prologue_ok(t)
    out.append(dict(target=t, kind=g["kind"], n_sites=g["n_sites"],
                    is_call_tgt=g["is_call_tgt"], sites_in_fn=sites_in_fn,
                    boundary=g["boundary"], first=first,
                    in_vt=(t in vt_targets),
                    site_owners=site_owners))

json.dump(out, open(os.path.join(WORK, "gap_holes_detail.json"), "w", encoding="utf-8"), indent=1)

# 分级：高置信 = call目标 或 (jmp目标且站点在函数区间内) 或 vtable目标；且 boundary!=False
def grade(x):
    if x["boundary"] is False: return "REJECT-inside-insn"
    if x["in_vt"]: return "high(vt)"
    if x["is_call_tgt"]: return "high(call)"
    if x["sites_in_fn"] >= 1: return "med(jmp-in-fn)"
    return "low(jmp-only-hole)"

from collections import Counter
print("hole candidates:", len(holes))
print("grades:", Counter(grade(x) for x in out))
print("\n--- HIGH/MED detail ---")
for x in out:
    g = grade(x)
    if g.startswith("high") or g.startswith("med"):
        print("%08X %-5s %-14s sites=%d inFn=%d bnd=%s first=[%s] vt=%d" % (
            x["target"], x["kind"], g, x["n_sites"], x["sites_in_fn"],
            x["boundary"], x["first"][:28], x["in_vt"]))
print("\n--- LOW (jmp-only-hole) sample first 20 ---")
lo = [x for x in out if grade(x).startswith("low")]
for x in lo[:20]:
    print("%08X sites=%d n_sites=%d first=[%s]" % (x["target"], x["sites_in_fn"], x["n_sites"], x["first"][:28]))
print("low total", len(lo))
