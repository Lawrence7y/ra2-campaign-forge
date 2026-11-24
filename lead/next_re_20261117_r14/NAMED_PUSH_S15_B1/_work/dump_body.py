# -*- coding: utf-8 -*-
"""逐行正文反汇编（含字节），只看本 entry 自身函数体。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

ENTRIES = ["006E3E30", "006E57A0", "006E6470", "0071F930", "0071FA80",
           "00726860", "007268D0", "00726950", "00727BF0", "00727C80"]

def dump(entry):
    ea = int(entry, 16)
    info = R.ATLAS.get(entry)
    size = info["size"] if info else 0x120
    insns = R.disasm(ea, R.read_va(ea, size))
    print("=" * 78)
    print("== %s  atlas_size=%s  n_decoded=%d" % (entry, size, len(insns)))
    for i in insns:
        if i.id == 0:
            print("   %08X  .byte %-20s (skipdata)" % (i.address, i.bytes.hex()))
            continue
        print("   %08X  %-24s %-30s ; %s" % (i.address, i.bytes.hex(), i.mnemonic + " " + i.op_str, i.op_str))

if __name__ == "__main__":
    for e in (sys.argv[1:] or ENTRIES):
        dump(e)
