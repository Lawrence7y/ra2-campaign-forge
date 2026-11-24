# -*- coding: utf-8 -*-
"""转储 entry 完整反汇编（含字节）到 stdout，供逐行精读。用法: python dump.py <entry> [entry...]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

def dump(entry):
    ea = int(entry, 16)
    sz = R.ATLAS.get(R.hx(ea), {}).get("size")
    if not sz:
        nxt = min((int(k,16) for k in R.ATLAS if int(k,16) > ea), default=None)
        sz = (nxt - ea) if nxt else 128
    print("=" * 90)
    print("ENTRY %s  size=%s" % (entry, R.ATLAS.get(R.hx(ea),{}).get('size')))
    insns = R.disasm(ea, R.read_va(ea, sz))
    for i in insns:
        if i.id == 0:
            print("  %08X  db %s" % (i.address, i.bytes.hex()))
        else:
            print("  %08X  %-20s %s" % (i.address, i.bytes.hex(), (i.mnemonic + " " + i.op_str)))

if __name__ == "__main__":
    for a in sys.argv[1:]:
        dump(a)
