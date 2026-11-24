#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vt.py — RTTI / vtable 解析 + 槽枚举 (虚表定界从 .rdata 做, 不假定槽号)
COL + 0xC -> TD; TD + 8 = name (§965 正确链)
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import wbase as W

def rtti_name_from_col(col):
    """COL+0xC -> TD; TD+8 内联读出类名字符串 (§990/S17-K3, 非指针)"""
    td = W.rd32(col + 0xC)
    if not td:
        return None, None
    o = W.va2off(td + 8)
    if o is None:
        return td, None
    b = bytearray()
    for i in range(256):
        c = W.DATA[o + i] if o + i < len(W.DATA) else 0
        if c == 0:
            break
        if not (32 <= c < 127):
            break
        b.append(c)
    return td, bytes(b).decode("latin1")

def find_col_for_vtable(vt):
    """vtable[-1] = COL 指针 (即 [vt-4])"""
    col = W.rd32(vt - 4)
    return col

def dump_vtable(vt, nslots=40):
    col = find_col_for_vtable(vt)
    td, name = rtti_name_from_col(col) if col else (None, None)
    print(f"vtable 0x{vt:08X}: COL=0x{col:08X} TD=0x{td:08X} name={name}")
    for i in range(nslots):
        slotva = vt + i * 4
        val = W.rd32(slotva)
        if val is None:
            break
        mark = ""
        if not W.in_text(val):
            mark = "  <-- NOT .text"
        print(f"  slot[{i:2d}] +0x{i*4:03X} @0x{slotva:08X} = 0x{val:08X}{mark}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: vt.py <vtable_hex> [nslots]")
        sys.exit(0)
    vt = int(sys.argv[1], 16)
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    dump_vtable(vt, n)
