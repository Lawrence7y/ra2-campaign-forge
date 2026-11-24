# -*- coding: utf-8 -*-
"""虚表逐槽打印 + 指定函数体完整反汇编。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from core2 import u32, va_in, read_cstr, parse_col, parse_td, find_containing_atlas_func
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True

def vt_slots(vb, limit=64):
    out = []
    for i in range(limit):
        v = u32(vb + 4 * i)
        if v is None or not R.in_text(v):
            break
        out.append(v)
    return out

def vt_report(vb):
    col = u32(vb - 4)
    ci = parse_col(col)
    tdi = parse_td(ci["td"]) if ci else None
    print("=" * 78)
    print("VT %08X  COL=%08X  TD=%08X  NAME=%s" %
          (vb, col or 0, ci["td"] if ci else 0, tdi["name"] if tdi else "?"))
    for i, t in enumerate(vt_slots(vb)):
        f = find_containing_atlas_func(t)
        print("   slot#%-2d (+0x%02X) -> %08X   %s" %
              (i, 4 * i, t, ("func " + f[1] + " size=" + str(f[2])) if f else ""))

def dumpf(va, size=None):
    if size is None:
        info = R.ATLAS.get("%08X" % va)
        size = info["size"] if info else 0x120
    insns = R.disasm(va, R.read_va(va, size))
    print("=" * 78)
    print("== FUNC %08X size=%s" % (va, size))
    for i in insns:
        if i.id == 0:
            print("   %08X  .byte %s" % (i.address, i.bytes.hex())); continue
        print("   %08X  %-22s %s" % (i.address, i.bytes.hex(), i.mnemonic + " " + i.op_str))

if __name__ == "__main__":
    mode = sys.argv[1]
    for a in sys.argv[2:]:
        if mode == "vt":
            vt_report(int(a, 16))
        else:
            dumpf(int(a, 16))
