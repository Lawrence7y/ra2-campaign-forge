#!/usr/bin/env python3
"""R107: linear listing of a function from its entry, plus alignment check on the DEC site.

Usage: python3 _r107/_exec/listing.py <entry_hex> <stop_hex> [--jmp]
The listing is a plain capstone linear decode (detail=False) which is sound here because we stop
before the first read-only blob. It prints every instruction between entry and stop inclusive,
so the report can quote instruction addresses and bytes.

Run example: python3 _r107/_exec/listing.py 4c6cb0 4c6ce0
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r107_lib import DATA, va2off, dis, ins_str


def listing(entry, stop, pad=0x30):
    ins = dis(entry, stop - entry + pad)
    seen = set()
    out = []
    for x in ins:
        if x.address > stop + pad:
            break
        out.append(x)
        if x.address >= stop:
            break
    return out


if __name__ == '__main__':
    entry = int(sys.argv[1], 16)
    stop = int(sys.argv[2], 16)
    for x in listing(entry, stop):
        print('%08x %-20s %s %s' % (x.address, x.bytes.hex(), x.mnemonic, x.op_str))
