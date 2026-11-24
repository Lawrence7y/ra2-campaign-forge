# -*- coding: utf-8 -*-
"""定点 dump：候选函数体 + 被调函数体（判 ③b② 用）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

def dump(va, n=None, label=""):
    size = R.ATLAS.get(R.hx(va), {}).get("size") if n is None else n
    size = size or 200
    print("=" * 90)
    print("DUMP %s VA=%08X size=%s" % (label, va, size))
    ins = R.disasm(va, R.read_va(va, size))
    for i in ins:
        if i.id == 0:
            print("  %08X: (skipdata) %s" % (i.address, i.bytes.hex()))
        else:
            print("  %08X: %-9s %-34s | %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex()))

# 候选函数
for e, sz in [("00524D70",332),("005F9950",29),("006F3F40",953),("00703860",686)]:
    dump(int(e,16), sz, e)

# 关键被调
for va, lbl, n in [(0x00410320,"callee 0x410320",120),
                   (0x004F7870,"callee 0x4F7870",200),
                   (0x007C8E17,"malloc 0x7C8E17",40)]:
    dump(va, n, lbl)
