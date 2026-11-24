# -*- coding: utf-8 -*-
"""按需 dump：python dump.py ENTRY [ENTRY ...]
输出每个 entry 的：
 - 全函数反汇编（含字节）
 - 每个 ② 槽的 vt 上下文（vt_base-16 .. slot+20 的 dword，标注）
 - 每个 install host 函数前 45 条指令（判 ctor vs dtor）
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2

def dump_func(ea, size, tag, maxi=None):
    print("  ---- %s func @%08X size=%d ----" % (tag, ea, size))
    insns = R.disasm_body(ea, size)
    for i, ins in enumerate(insns):
        if maxi and i >= maxi:
            print("    ... (truncated at %d)" % maxi); break
        print("    %08X  %-24s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

def dump_vt(slot_va, vt_base, col, td, name):
    print("  ---- vt context for slot@%08X ----" % slot_va)
    start = vt_base - 16
    end = slot_va + 20
    col = int(col, 16) if isinstance(col, str) else col
    td = int(td, 16) if isinstance(td, str) else td
    print("    vt_base=%08X col=%08X td=%08X name=%s" % (vt_base, col, td, name))
    va = start
    while va <= end:
        v = C2.u32(va)
        marks = []
        if va == vt_base - 4: marks.append("COLPT")
        if va == vt_base: marks.append("vt[0]")
        if va == slot_va: marks.append("SLOT")
        print("    %08X: %08X %s" % (va, v if v is not None else 0, " ".join(marks)))
        va += 4

import json
WORK = os.path.dirname(os.path.abspath(__file__))
REFS = json.load(open(os.path.join(WORK, "refs.json"), encoding="utf-8"))

for e in sys.argv[1:]:
    ea = int(e, 16)
    size = R.ATLAS.get(e, {}).get("size") or 256
    print("\n################################################################")
    print("### ROW %s  %s  size=%d" % (e, REFS.get(e, {}).get("name", "?"), size))
    print("################################################################")
    dump_func(ea, size, "ENTRY")
    v = REFS.get(e, {})
    for s in v.get("slots", []):
        if s.get("vtable_base"):
            dump_vt(int(s["slot_va"], 16), int(s["vtable_base"],16),
                    s["col"], s["td"], s["rtti_name"])
            for g in s.get("global_writes", []):
                f = g.get("in_func")
                if f:
                    fva = int(f[0]) if not isinstance(f[0], str) else int(f[0],16); fsz = f[2]
                    dump_func(fva, fsz, "INSTALL-HOST write@%s" % g["write_va"], maxi=48)
