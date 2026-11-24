# -*- coding: utf-8 -*-
"""W173 补证：0x5519B0 调用约定；层遍历 callee 0x551B90/0x551B20 是否含 call[+0x1C]；
0x55BAA0 的调用者(this 来源)；[+0x94] 写点按写入值/函数归类明细；层号来源。"""
from __future__ import annotations
import os
import sys
import bisect
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import w173_common as C
import audit_lib

E = C.EVID


def dasm(va, nbytes, title):
    b = C.B()
    m = C.md(True)
    data = b.read(va, nbytes)
    L = ["=" * 88, "%s [0x%08X,0x%08X)" % (title, va, va + nbytes)]
    for ins in m.disasm(data, va):
        L.append("%08X  %-8s %s%s" % (ins.address, ins.mnemonic, ins.op_str,
                                      "   ; .byte" if ins.id == 0 else ""))
    return L


def main():
    L = []
    L.extend(dasm(0x5519B0, 0x100, "0x5519B0 VectorClass<T>::Add full (调用约定)"))
    L.extend(dasm(0x551B90, 0x100, "0x551B90 (callee of layer-iterator 0x4AE6F0)"))
    L.extend(dasm(0x551B20, 0x100, "0x551B20 (callee of layer-iterator 0x4AE720)"))
    C.write_text(os.path.join(E, "w173_conv_detail.txt"), L)

    b = C.B()
    calls, jmps, stat = audit_lib.sweep_calls(b)
    L2 = ["=" * 88, "调用者表(直接 call rel32)"]
    for tgt in (0x5519B0, 0x551B90, 0x551B20, 0x55BAA0, 0x4A9720, 0x4A88C0, 0x4AE6F0, 0x4AE720):
        ss = sorted(calls.get(tgt, []))
        L2.append("target %08X : %d callers -> %s" % (
            tgt, len(ss), ",".join("%08X" % x for x in ss)))
    C.write_text(os.path.join(E, "w173_callers.txt"), L2)

    # [+0x94] 写点明细按分类/函数
    ins = C.text_insns()
    rows = []
    for j, r in enumerate(ins):
        if r["mn"] != "mov" or len(r["ops"]) < 2:
            continue
        d, s = r["ops"][0], r["ops"][1]
        if d["kind"] != "mem" or d["base"] is None or d["disp"] != C.W94_OFF:
            continue
        if d["size"] != 4:   # 只 dword
            continue
        va = r["va"]
        o = C.owner(va, "atlas")
        if s["kind"] == "imm":
            v = s["val"] & 0xFFFFFFFF
            val = "-1" if v == 0xFFFFFFFF else (str(v) if v <= 4 else "0x%X" % v)
        elif s["kind"] == "reg":
            val = "reg:" + s["name"]
        elif s["kind"] == "mem":
            val = "mem:[%s+0x%X]" % (s["base"], s["disp"])
        else:
            val = "?"
        rows.append((va, val, o[0] if o else None, C.fmt(r)))
    L3 = ["=" * 88, "[+0x94] dword 写点按函数归类（共 %d）" % len(rows)]
    byf = defaultdict(list)
    for va, val, f, txt in rows:
        byf[f].append((va, val, txt))
    L3.append("写入值分类: %r" % dict(Counter(x[1].split(":")[0] for x in rows)))
    for f in sorted(byf, key=lambda x: (x is None, x)):
        L3.append("-" * 80)
        L3.append("fn %s : %d 写点" % (("%08X" % f) if f else "NONE", len(byf[f])))
        for va, val, txt in byf[f]:
            L3.append("  %s   [%s]  %s" % (txt.strip(), val, "%08X" % va))
    C.write_text(os.path.join(E, "w173_w94_byfunc.txt"), L3)

    print("补证完成: w173_conv_detail / w173_callers / w173_w94_byfunc")


if __name__ == "__main__":
    main()
