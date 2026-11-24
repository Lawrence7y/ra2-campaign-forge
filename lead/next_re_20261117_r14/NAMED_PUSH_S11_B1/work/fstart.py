# -*- coding: utf-8 -*-
"""定位安装点所在函数的真实入口：优先 atlas，否则用「回扫 + 线性反汇编必须精确覆盖该点」验证。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *

def candidates(site, back=0x60):
    out = []
    for d in range(0, back):
        va = site - d
        prev = read_va(va - 1, 1)
        if not prev:
            continue
        ins = dis(va, read_va(va, site - va + 6))
        if not ins or ins[0].address != va:
            continue
        # 必须精确落在 site 上
        if not any(i.address == site for i in ins):
            continue
        # 前一条必须是填充/ret（int3/nop/ret）—— 说明 va 是函数边界
        ok = False
        if prev[0] in (0xCC, 0x90):
            ok = True
        elif prev[0] == 0xC3:
            ok = True
        elif prev[0] == 0xC2 and read_va(va - 3, 3)[:1] == b"\xc2":
            ok = True
        if ok:
            out.append(va)
    return out

for lbl, site in [("ROW2 install 004AF5C2", 0x004AF5C2),
                  ("ROW2 install 004AF5E3", 0x004AF5E3),
                  ("ROW2 install 004AF7A3", 0x004AF7A3),
                  ("ROW2 install 004B4D03", 0x004B4D03),
                  ("ROW5/6 install 004B5ADD", 0x004B5ADD),
                  ("ROW5/6 install 004B5B03", 0x004B5B03),
                  ("ROW5/6 install 004B6263", 0x004B6263),
                  ("ROW5/6 install 004B66F3", 0x004B66F3),
                  ("ROW17 install 0054ACC3", 0x0054ACC3),
                  ("ROW17 install 0054AD03", 0x0054AD03),
                  ("ROW17 install 0054B776", 0x0054B776),
                  ("ROW17 install 0054DFA3", 0x0054DFA3)]:
    at = atlas_func_of(site)
    cs = candidates(site)
    print("\n%-30s  atlas=%s  边界候选=%s" % (lbl, hx(at[0]) if at else None, [hx(c) for c in cs[:4]]))
    st = at[0] if at else (cs[-1] if cs else None)
    if st:
        body = dis(st, read_va(st, 0x120))
        n = 0
        for i in body:
            if i.id == 0:
                break
            print("     %s  %-8s %s" % (hx(i.address), i.bytes.hex(), i.mnemonic + " " + i.op_str))
            n += 1
            if i.id == X86_INS_RET:
                nx = read_va(i.address + i.size, 1)
                if nx[:1] in (b"\xcc", b"\x90", b""):
                    break
            if n > 40:
                break
        prof = func_profile_dbg = None
