#!/usr/bin/env python3
"""R107: dump aligned linear disassembly window before a target VA.
Run: python3 _r107/_exec/dumpwin.py <target_hex> [before_hex] [after_hex]
Picks the earliest instruction-start in the window from which a linear decode lands exactly on target,
so the listing is aligned; prints every instruction with address, bytes, mnemonic.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r107_lib import DATA, TEXT_VA, TEXT_END, va2off, dis, ins_str
from fstart import STARTS, TERMS, SIZE


def aligned_start(target, back):
    lo = max(TEXT_VA, target - back)
    for va in range(lo, target):
        if STARTS[va - TEXT_VA] != 1:
            continue
        ins = dis(va, target - va + 16)
        if any(x.address == target for x in ins):
            return va, ins
    return None, None


def dump(target, back=0x300, fwd=0x40):
    s, ins = aligned_start(target, back)
    if s is None:
        print('no aligned start for %08x' % target)
        return
    print('=== target %08x aligned from %08x ===' % (target, s))
    for x in ins:
        if x.address > target + fwd:
            break
        mark = ''
        if x.address == target:
            mark = '   <== target'
        if TERMS[x.address - TEXT_VA] and x.mnemonic != 'jmp':
            mark += ' [TERM]'
        print(ins_str(x) + mark)


if __name__ == '__main__':
    t = int(sys.argv[1], 16)
    back = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x300
    fwd = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x40
    dump(t, back, fwd)
