#!/usr/bin/env python3
"""R107: one full linear sweep of .text with capstone disasm_lite (no detail), building
- start bitmap (bytearray, 1 byte per .text byte)
- terminator bitmap (ret / jmp / unconditional-int3 padding boundaries)

Run: python3 _r107/_exec/sweep.py   -> writes _r107/_exec/sweep_cache.bin (bitmaps) + prints stats
Load via r107_lib.load_sweep()
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r107_lib import DATA, TEXT, TEXT_VA, TEXT_END, va2off, off2va, IMAGEBASE

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

SIZE = TEXT_END - TEXT_VA
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sweep_cache.bin')


def sweep():
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    starts = bytearray(SIZE)
    terms = bytearray(SIZE)
    base_off = va2off(TEXT_VA)
    end = base_off + SIZE
    off = base_off
    n = 0
    while off < end:
        chunk = DATA[off:off + 0x10000]
        cstart = off
        last_end = None
        for a, sz, mn, op in md.disasm_lite(chunk, off2va(cstart)):
            idx = a - TEXT_VA
            starts[idx] = 1
            n += 1
            if mn in ('ret', 'retn', 'jmp', 'int3', 'iretd', 'hlt'):
                terms[idx] = 1
            last_end = va2off(a) + sz
        if last_end is None:
            off = cstart + 0x10000  # chunk had zero decodable bytes; force progress
        else:
            off = last_end
    return starts, terms, n


if __name__ == '__main__':
    starts, terms, n = sweep()
    with open(CACHE, 'wb') as f:
        f.write(SIZE.to_bytes(4, 'little'))
        f.write(bytes(starts))
        f.write(bytes(terms))
    print('text %08x..%08x size=%d insns=%d cache=%s' % (TEXT_VA, TEXT_END, SIZE, n, CACHE))
    print('start bytes set=%d' % sum(starts))
