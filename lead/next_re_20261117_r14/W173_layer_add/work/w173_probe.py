# -*- coding: utf-8 -*-
"""W173 探针：完整反汇编指定函数 + 每个 call[reg+0x1C] 站点的前序窗口（不截断）。"""
from __future__ import annotations
import os
import sys
import bisect

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w173_common as C

E = C.EVID


def dump_range(va, nbytes, title):
    """从 va 线性反汇编 nbytes（skipdata=True），带边界验证的入口提示。"""
    b = C.B()
    m = C.md(True)
    data = b.read(va, nbytes)
    L = ["=" * 90, "%s  [0x%08X, 0x%08X)" % (title, va, va + nbytes)]
    for ins in m.disasm(data, va):
        if ins.id == 0:
            L.append("%08X  .byte %s" % (ins.address, ins.bytes.hex()))
            continue
        L.append("%08X  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
    return L


def main():
    L = []
    funcs = [
        (0x4A88C0, 0x400, "fn 0x4A88C0 (iterates [5]LayerClass: mov esi,0x8A0360)"),
        (0x4A9720, 0x100, "fn 0x4A9720 (direct caller of 0x5519B0)"),
        (0x4A9770, 0x120, "fn 0x4A9770 (RemoveFromLayer)"),
        (0x4AE6F0, 0x80, "fn 0x4AE6F0"),
        (0x4AE720, 0x80, "fn 0x4AE720"),
        (0x55BAA0, 0x100, "fn 0x55BAA0 (direct caller of 0x5519B0)"),
        (0x55D360, 0xA00, "fn 0x55D360 (sort layer[2], mov ecx,0x8A0390 @+0x863)"),
        (0x4824D4, 0x1000, "fn 0x4824D4 (atlas hole; refs 0x8A0394/0x8A03A0)"),
    ]
    for va, n, title in funcs:
        L.extend(dump_range(va, n, title))
        L.append("")
    C.write_text(os.path.join(E, "w173_probe_funcs.txt"), L)

    # 每个 chA 站点：前 24 条 + 站点 + 后 4 条
    ins = C.text_insns()
    v = C.vas()
    sites = []
    for j, r in enumerate(ins):
        if r["mn"] != "call" or not r["ops"]:
            continue
        op = r["ops"][0]
        if op["kind"] == "mem" and op["base"] and (op["disp"] & 0xFFFFFFFF) == C.ADD_SLOT:
            sites.append(j)
    L2 = ["=" * 90,
          "W173 chA 站点逐点前序窗口（每点前24后4；thiscall 看 ecx，vptr 看目标 reg）",
          "站点数: %d" % len(sites)]
    for j in sites:
        r = ins[j]
        oa = C.owner(r["va"], "atlas")
        osy = C.owner(r["va"], "synth")
        L2.append("-" * 90)
        L2.append("SITE %08X %s | atlas=%s synth=%s" % (
            r["va"], C.fmt(r),
            ("%08X" % oa[0]) if oa else "NONE",
            ("%08X" % osy[0]) if osy else "NONE"))
        for k in range(max(0, j - 24), min(len(ins), j + 5)):
            mark = ">>" if k == j else "  "
            L2.append("%s %s" % (mark, C.fmt(ins[k])))
    C.write_text(os.path.join(E, "w173_probe_chA_windows.txt"), L2)
    print("probe funcs + %d chA windows written" % len(sites))


if __name__ == "__main__":
    main()
