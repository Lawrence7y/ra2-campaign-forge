# -*- coding: utf-8 -*-
"""核查 00703860 的 channelA p1/p2；并列出所有行的 ④ witness（构造安装点/派发站点）。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
WORK = os.path.dirname(os.path.abspath(__file__))
data = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}
rtti = json.load(open(os.path.join(WORK, "rtti_map.json"), encoding="utf-8"))
rows = json.load(open(os.path.join(WORK, "b2_rows.json"), encoding="utf-8"))

print("### 00703860 channelA detail")
r = data["00703860"]
print("chA p1=%d p2=%d p3=%d  sites=%d chB=%d" % (r["chA"]["p1"], r["chA"]["p2"], r["chA"]["p3"], len(r["chA_sites"]), len(r["chB"])))

print()
print("### ④ witness per row (clue-matching vtable)")
for row in rows:
    e = row["entry"]
    rm = rtti.get(e)
    rec = data[e]
    if not rm:
        print("%s %-30s NO RTTI" % (e, row["name"]))
        continue
    vt = int(rm["vtable_base"], 16) if isinstance(rm["vtable_base"], str) else int(rm["vtable_base"])
    off = rm["slot_off"]
    # 用 witness_core 找该 vt 的写入站点与 imm load
    w = W.find_vtable_writes(vt)
    globals_ = w["global"]
    regdisp = w["regdisp"]
    immload = w["imm_load"]
    # 派发站点：call dword ptr [reg+off]
    disp = []
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    from capstone.x86 import X86_INS_CALL, X86_OP_MEM, X86_REG_INVALID
    md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
    for ins in md.disasm(R.TEXT_DATA, R.TEXT_VA):
        if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type == X86_OP_MEM:
            m = ins.operands[0].mem
            if m.disp == off and m.base not in (X86_REG_INVALID, 0) and m.index in (X86_REG_INVALID, 0):
                disp.append("%08X" % ins.address)
                if len(disp) >= 5:
                    break
    # atexit check on global writes
    atex = []
    for g in globals_:
        va = g.get("global") if isinstance(g, dict) else None
        f = W.find_containing_atlas_func(g["write_va"]) if isinstance(g, dict) and "write_va" in g else None
        is_at = bool(W.is_atexit_registered(f[0])) if f else False
        atex.append((g.get("write_va"), "atexit" if is_at else "ctor"))
    print("%s %-30s vt=%s off=%d slot=%d globals=%s regdisp=%d immload=%s atexit=%s disp[:5]=%s" % (
        e, row["name"], rm["vtable_base"], off, rm["slotno"],
        [g.get("write_va") if isinstance(g, dict) else g for g in globals_][:6],
        len(regdisp), [ "%08X"%x for x in immload[:4] ], atex[:6], disp))

