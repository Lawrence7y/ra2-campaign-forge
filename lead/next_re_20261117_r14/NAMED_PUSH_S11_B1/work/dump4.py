# -*- coding: utf-8 -*-
"""按地址 dumping：entry 体 / 构造器 / 析构器 / 被调，全量指令 + 机器码。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *

def dump(va, cap, label, stop_at_pad=True):
    print("\n########## %s  %s ##########" % (label, hx(va)))
    ins = dis(va, read_va(va, cap))
    n = 0
    for i in ins:
        if i.id == 0:
            print("   %s  <skipdata %s>" % (hx(i.address), i.bytes.hex()))
            break
        print("   %s  %-8s %-40s %s" % (hx(i.address), i.bytes.hex(), i.mnemonic + " " + i.op_str, ""))
        n += 1
        if i.id == X86_INS_RET:
            nxt = read_va(i.address + i.size, 2)
            if nxt[:1] in (b"\xcc", b"\x90", b""):
                break
    print("   [%d insn]" % n)

TARGETS = [
    ("ROW2 entry QI", 0x004AF720, 260),
    ("ROW2 ctor", 0x004AF57F, 160),
    ("ROW2 ctor2", 0x004AF5E0, 120),
    ("ROW2 other", 0x004AF780, 140),
    ("ROW2 dtor(排除)", 0x004B4D00, 120),
    ("ROW5 entry", 0x004B62C0, 320),
    ("ROW5 ctor", 0x004B5AB0, 160),
    ("ROW6 entry QI", 0x004B6470, 260),
    ("ROW17 entry QI", 0x0054DC60, 260),
    ("ROW17 ctor", 0x0054ACA8, 120),
    ("被调 baseQI 0055A9B0", 0x0055A9B0, 340),
    ("被调 0055AA60", 0x0055AA60, 340),
]
for lbl, va, cap in TARGETS:
    dump(va, cap, lbl)

