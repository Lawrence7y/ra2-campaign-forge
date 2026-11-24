# -*- coding: utf-8 -*-
"""对每个 ② 槽的 install host 分类 ctor/dtor：
 - 前 12 条内有没有 call 基类构造（排除 atexit 注册本身）
 - 有没有 call 0x7258d0 / 0x7c8b3d（析构标记）
 - 有没有 Find -1 容器摘链 (cmp eax,-1 / 83 f8 ff)
 - 是否 atexit 注册
 - 写点是否在 entry 体内
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C2
from capstone.x86 import X86_OP_IMM

WORK = os.path.dirname(os.path.abspath(__file__))
REFS = json.load(open(os.path.join(WORK, "refs.json"), encoding="utf-8"))
ROWS = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "b1_rows.json"), encoding="utf-8"))}

DTOR_MARKERS = {0x7258D0, 0x7C8B3D, 0x7C978A}

for e, v in REFS.items():
    ea = int(e,16); esz = int(ROWS[e].get("size") or R.ATLAS.get(e,{}).get("size",0))
    print("\n### %s %s entry=[%08X,%08X)" % (e, v["name"], ea, ea+esz))
    seen = set()
    for s in v.get("slots", []):
        if not s.get("vtable_base"): continue
        for g in s.get("global_writes", []):
            f = g.get("in_func")
            if not f: continue
            fva = int(f[0]) if not isinstance(f[0],str) else int(f[0],16)
            key = (fva, g["write_va"])
            if key in seen: continue
            seen.add(key)
            insns = R.disasm_body(fva, min(f[2], 700))
            early_calls = []   # first 15 insns
            markers = []
            find_ff = 0
            for ins in insns[:60]:
                if ins.id == 0: continue
                if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
                    tgt = ins.operands[0].imm & 0xFFFFFFFF
                    early_calls.append((ins.address, tgt))
                    if tgt in DTOR_MARKERS: markers.append((ins.address, "DTOR_MARK_%08X" % tgt))
                if ins.mnemonic == "cmp" and len(ins.operands)==2 and ins.operands[1].type == 2 \
                   and (ins.operands[1].imm & 0xFFFFFFFF) == 0xFFFFFFFF:
                    find_ff += 1
            atex = bool(C2.is_atexit_registered(fva))
            in_self = ea <= int(g["write_va"],16) < ea+esz
            print("  write@%s host=%08X sz=%d atexit=%s in_self=%s" % (
                g["write_va"], fva, f[2], atex, in_self))
            print("    early_calls(first 15): %s" % (
                ", ".join("%08X->%08X"%(a,t) for a,t in early_calls[:15])))
            if markers: print("    DTOR_MARKERS: %s" % markers)
            if find_ff: print("    cmp_eax,-1 count in first 60: %d" % find_ff)
