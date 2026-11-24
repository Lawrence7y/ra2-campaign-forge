# -*- coding: utf-8 -*-
"""probe: learn the true atexit registration shape from the two control ctors."""
import struct
import sys
import os

import pefile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_survey as L

img = open(L.EXE, "rb").read()
pe = pefile.PE(L.EXE, fast_load=True)
secs = [(s.Name.rstrip(b"\x00").decode("latin1"),
         pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress,
         s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData) for s in pe.sections]
TEXT = [s for s in secs if s[0] == ".text"][0]
tstart, tlen, tro = TEXT[1], TEXT[3], TEXT[4]
tbytes = img[tro:tro + tlen]
tend = tstart + tlen


def dump(va, n):
    for nm, sva, vs, rs, ro in secs:
        if sva <= va < sva + rs:
            b = img[ro + (va - sva):ro + (va - sva) + n]
            print("  0x%08X: %s" % (va, b.hex(" ")))
            return


print("ctor 00438550 .. +0x60")
dump(0x00438550, 0x60)
print("ctor 004E6AE0 .. +0x60")
dump(0x004E6AE0, 0x60)

print("\nall call->0x7C978A sites near the control ctors (|d|<0x200):")
for i in range(len(tbytes) - 5):
    if tbytes[i] == 0xE8:
        rel = struct.unpack_from("<i", tbytes, i + 1)[0]
        tgt = tstart + i + 5 + rel
        if tgt == 0x7C978A:
            s = tstart + i
            if abs(s - 0x00438550) < 0x200 or abs(s - 0x004E6AE0) < 0x200:
                ctx = img[tro + (s - tstart) - 12:tro + (s - tstart) + 5]
                print("  call atexit @0x%08X  ctx-before: %s" % (s, ctx.hex(" ")))

print("\ninit-table candidates: dword runs in .data/.rdata all pointing into .text")
for nm, sva, vs, rs, ro in secs:
    if nm not in (".data", ".rdata"):
        continue
    best = []
    i = 0
    n = rs
    while i + 4 <= n:
        v = struct.unpack_from("<I", img, ro + i)[0]
        if tstart <= v < tend:
            j = i
            cnt = 0
            while j + 4 <= n:
                vv = struct.unpack_from("<I", img, ro + j)[0]
                if tstart <= vv < tend:
                    cnt += 1
                    j += 4
                else:
                    break
            if cnt >= 8:
                best.append((cnt, sva + i))
            i = j
        else:
            i += 4
    best.sort(reverse=True)
    print("  %s runs>=8: %d ; top:" % (nm, len(best)), [("0x%08X" % a, c) for c, a in best[:6]])
