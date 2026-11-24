#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C04 atlas 空洞入口分析（可复跑）。
- 从 gaps_raw.json 取 owner==None 的 rel32(call/jmp) 目标候选。
- 用 capstone(skipdata=True) 详细模式逐条复扫 .text，区分 jmp 操作码：
    E9 = rel32 near jmp, EB = rel8 short jmp。
  audit_lib.sweep_calls 把两者都记成 'jmp'，但卡纪律要求：
  仅由 EB 短跳命中的洞入口不得硬算成 rel32 命中 → 单列 short_jmp_only，写 UNKNOWNS。
- 每条候选：boundary、首指令序言、in_vt、调用站点是否在真函数内 → 置信度分级。
输出 work/gap_detail.json, work/short_jmp_holes.json, EVIDENCE/gap_candidates.tsv。
"""
import os, sys, json, bisect
from collections import Counter, defaultdict
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
CARD  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C04_census")
WORK  = os.path.join(CARD, "work")
EVID  = os.path.join(CARD, "EVIDENCE")
sys.path.insert(0, os.path.join(ROOT, "lead\\next_re_20261116_r12\\_lead_audit"))
import audit_lib
import capstone

gaps = json.load(open(os.path.join(WORK, "gaps_raw.json"), encoding="utf-8"))
lo, hi = int(gaps["lo"], 16), int(gaps["hi"], 16)
holes = [g for g in gaps["gaps"] if g["owner"] is None]
hole_set = set(g["target"] for g in holes)

# --- atlas 函数区间（区间包含用）---
rows, hdr = audit_lib.load_func_atlas()
starts = [va for va, _ in rows]
sizes = {va: int(rec["size"]) for va, rec in rows}
def owner(x):
    i = bisect.bisect_right(starts, x) - 1
    return starts[i] if i >= 0 and starts[i] <= x < starts[i] + sizes[starts[i]] else None

# --- vtable 槽值集合（目标是否是某虚表槽）---
vtj = json.load(open(os.path.join(ATLAS, "vtables_v2.json"), encoding="utf-8"))
b = audit_lib.Bin()
text = b.text
tlo, thi = text["va"], text["va"] + text["rawsize"]
vt_targets = set()
for v in vtj["vtables"]:
    vt = v["vt"]; n = v.get("slots", 0)
    if n <= 0 or n > 400: continue
    for i in range(n):
        try: tgt = b.u32(vt + 4*i)
        except Exception: continue
        if tlo <= tgt < thi: vt_targets.add(tgt)

# --- 详细复扫 .text，区分 E9(rel32) / EB(rel8) jmp，记录每个洞目标的引用指令 ---
m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
m.detail = False; m.skipdata = True
data = b.pe.__data__[text["raw"]:text["raw"] + text["rawsize"]]
# 目标 -> {'call':[sites], 'jmp32':[sites], 'jmp8':[sites], 'opcodes':set()}
refs = defaultdict(lambda: dict(call=[], jmp32=[], jmp8=[], other=[], opcodes=set()))
for insn in m.disasm(data, text["va"]):
    if insn.id == 0: continue
    mn = insn.mnemonic
    if mn in ("call", "jmp") and insn.op_str.startswith("0x"):
        try: tgt = int(insn.op_str, 16)
        except Exception: continue
        if tgt not in hole_set: continue
        op0 = insn.bytes[0] if insn.bytes else None
        if mn == "call":
            if op0 == 0xE8: refs[tgt]["call"].append(insn.address)
            else: refs[tgt]["other"].append(insn.address)
            refs[tgt]["opcodes"].add(insn.bytes.hex()[:8])
        else:  # jmp
            if op0 == 0xE9: refs[tgt]["jmp32"].append(insn.address)
            elif op0 == 0xEB: refs[tgt]["jmp8"].append(insn.address)
            else: refs[tgt]["other"].append(insn.address)
            refs[tgt]["opcodes"].add(insn.bytes.hex()[:8])

# --- 首指令序言（从目标线性反汇编前若干条）---
def first_insns(va, n=3):
    try: d = b.read(va, 24)
    except Exception: return ""
    out = []
    for insn in m.disasm(d, va):
        if insn.id == 0: continue
        out.append("%s %s" % (insn.mnemonic, insn.op_str))
        if len(out) >= n: break
    return " ; ".join(out)

# --- 分级 ---
detail = []
short_jmp_only = []
for g in sorted(holes, key=lambda x: x["target"]):
    t = g["target"]
    r = refs.get(t, dict(call=[], jmp32=[], jmp8=[], other=[], opcodes=set()))
    has_call = len(r["call"]) > 0
    has_jmp32 = len(r["jmp32"]) > 0
    has_jmp8 = len(r["jmp8"]) > 0
    has_rel32 = has_call or has_jmp32
    in_vt = t in vt_targets
    first = first_insns(t)
    # 引用站点是否位于真函数内（区间包含）
    all_sites = r["call"] + r["jmp32"] + r["jmp8"] + r["other"]
    sites_in_fn = sum(1 for s in all_sites if owner(s) is not None)
    # 置信度
    if g["boundary"] is False:
        conf = "reject-inside-insn"
    elif has_call:
        conf = "high(call-rel32)"
    elif has_jmp32:
        conf = "high(jmp32-rel32)"
    elif in_vt:
        conf = "high(vtable-slot)"
    elif has_jmp8 and not has_rel32:
        conf = "SHORT-JMP-ONLY(非rel32)"
        short_jmp_only.append(dict(target=t, first=first, sites=r["jmp8"], opcodes=sorted(r["opcodes"])))
    elif sites_in_fn >= 1:
        conf = "med(jmp-from-fn)"
    else:
        conf = "low(jmp-hole)"
    detail.append(dict(target=t, conf=conf, boundary=g["boundary"],
                       has_call=has_call, has_jmp32=has_jmp32, has_jmp8=has_jmp8,
                       has_rel32=has_rel32, in_vt=in_vt, first=first,
                       sites_in_fn=sites_in_fn, n_sites=len(all_sites),
                       call=r["call"][:8], jmp32=r["jmp32"][:8], jmp8=r["jmp8"][:8],
                       other=r["other"][:8], opcodes=sorted(r["opcodes"])))

json.dump(dict(lo=hex(lo), hi=hex(hi), detail=detail, short_jmp_only=short_jmp_only),
          open(os.path.join(WORK, "gap_detail.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(EVID, "gap_candidates.tsv"), "w", encoding="utf-8") as f:
    f.write("entry\tconf\tboundary\tcall\tjmp32\tjmp8\tin_vt\tfirst_insn\trel32_sites\n")
    for d in detail:
        rel = " ".join("%08X"%x for x in (d["call"]+d["jmp32"])[:6])
        f.write("%08X\t%s\t%s\t%d\t%d\t%d\t%d\t%s\t%s\n" % (
            d["target"], d["conf"], "unknown" if d["boundary"] is None else str(d["boundary"]).lower(),
            int(d["has_call"]), int(d["has_jmp32"]), int(d["has_jmp8"]), int(d["in_vt"]),
            d["first"][:40], rel))

print("holes owner=None:", len(holes))
print("conf:", dict(Counter(d["conf"] for d in detail)))
print("has_rel32:", sum(1 for d in detail if d["has_rel32"]))
print("short_jmp_only:", len(short_jmp_only))
print("0x4824D4 in holes:", 0x4824D4 in hole_set)
