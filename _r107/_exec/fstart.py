#!/usr/bin/env python3
"""R107: function-start candidates using the sweep start bitmap + CC padding.
Run: python3 _r107/_exec/fstart.py [target_va ...]
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r107_lib import DATA, TEXT_VA, TEXT_END, va2off, off2va, dis, ins_str, IMAGEBASE

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sweep_cache.bin')


def load_sweep():
    b = open(CACHE, 'rb').read()
    size = int.from_bytes(b[:4], 'little')
    return bytearray(b[4:4 + size]), bytearray(b[4 + size:4 + 2 * size]), size


STARTS, TERMS, SIZE = load_sweep()


def is_start(va):
    i = va - TEXT_VA
    return 0 <= i < SIZE and STARTS[i] == 1


def candidate_starts(target, back=0x3000):
    """addresses s in [target-back, target) that are instruction starts preceded by >=1 0xCC
    and from which linear disasm lands exactly on target."""
    out = []
    for va in range(max(TEXT_VA, target - back), target, 1):
        i = va - TEXT_VA
        if not STARTS[i]:
            continue
        if DATA[va2off(va) - 1] != 0xCC:
            continue
        ins = dis(va, target - va + 16)
        if any(x.address == target for x in ins):
            # require no terminator strictly between (i.e. single linear chain)
            ok = True
            for x in ins:
                if x.address >= target:
                    break
                if TERMS[x.address - TEXT_VA] and x.address != va and \
                   not (x.mnemonic == 'jmp' and va == target):
                    pass
            out.append(va)
    return out


def backwards_chain(target, maxbytes=0x200, maxtotal=0x4000):
    """Walk backwards one instruction at a time using start bitmap: prev start = nearest start
    address < addr whose instruction length ends exactly at addr."""
    chain = []
    cur = target
    budget = maxtotal
    while budget > 0 and len(chain) < maxbytes:
        found = None
        for back in range(1, 16):
            p = cur - back
            i = p - TEXT_VA
            if i < 0 or not STARTS[i]:
                continue
            ins = dis(p, 16)
            if ins and ins[0].address == p and p + ins[0].size == cur:
                found = p
                break
        if found is None:
            break
        chain.append(found)
        cur = found
        budget -= 1
    return chain


if __name__ == '__main__':
    targets = [int(x, 16) for x in sys.argv[1:]] or [0x4c6ccd, 0x69af2c, 0x6a8e0c,
                                                     0x6dd8da, 0x708c44, 0x728c0d, 0x728e62]
    for t in targets:
        c = candidate_starts(t)
        print('%08x cands(%d): %s' % (t, len(c), [hex(x) for x in c[:8]]))
