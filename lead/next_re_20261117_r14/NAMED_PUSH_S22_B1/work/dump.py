# -*- coding: utf-8 -*-
"""逐行/指定地址反汇编转储。用法: python dump.py 006BF810 0069C9C0 007C8E17 ..."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

def dump(ea, size=None):
    if size is None:
        size = R.ATLAS.get(R.hx(ea), {}).get("size") or 256
    print("=" * 78)
    print("FUNC %s  size=%d" % (R.hx(ea), size))
    for ins in R.disasm_body(ea, size):
        if ins.id == 0:
            print("  %08X  db %02x   <skipdata>" % (ins.address, ins.bytes[0])); continue
        print("  %08X  %-22s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic + " " + ins.op_str))

if __name__ == "__main__":
    for a in sys.argv[1:]:
        dump(int(a, 16))
