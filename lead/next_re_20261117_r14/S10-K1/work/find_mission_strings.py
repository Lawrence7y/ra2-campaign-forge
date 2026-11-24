#!/usr/bin/env python3
"""S10-K1 step 1: locate Mission_* strings and their VA/file offsets in gamemd.exe."""
import sys, re
import pefile

EXE = r"ra2youli\gamemd.exe"
pe = pefile.PE(EXE, fast_load=True)
IMAGE_BASE = pe.OPTIONAL_HEADER.ImageBase
print("ImageBase = 0x%X" % IMAGE_BASE)

# Build VA->offset for sections
sections = []
for s in pe.sections:
    name = s.Name.decode(errors='replace').rstrip('\x00')
    va = IMAGE_BASE + s.VirtualAddress
    vsize = s.Misc_VirtualSize
    raw = s.PointerToRawData
    rsize = s.SizeOfRawData
    sections.append((name, va, vsize, raw, rsize))
    print("SECTION %-8s VA=0x%08X..0x%08X vsize=0x%X raw=0x%X rsize=0x%X"
          % (name, va, va+vsize, vsize, raw, rsize))

data = open(EXE, 'rb').read()

def va_to_off(va):
    for name, sva, vsize, raw, rsize in sections:
        if sva <= va < sva + max(vsize, rsize):
            off = raw + (va - sva)
            return off
    return None

def off_to_va(off):
    for name, sva, vsize, raw, rsize in sections:
        if raw <= off < raw + rsize:
            return sva + (off - raw)
    return None

# Search all ASCII strings containing 'Mission'
pat = re.compile(rb'Mission[_A-Za-z0-9]*')
hits = []
for m in pat.finditer(data):
    off = m.start()
    va = off_to_va(off)
    s = m.group().decode('ascii', errors='replace')
    hits.append((va, off, s))
print("\n=== All 'Mission...' ASCII substrings (%d) ===" % len(hits))
for va, off, s in hits:
    # print surrounding null-terminated string
    start = off
    while start > 0 and data[start-1] != 0 and (off-start) < 80:
        start -= 1
    end = off
    while end < len(data) and data[end] != 0 and (end-off) < 80:
        end += 1
    full = data[start:end].decode('ascii', errors='replace')
    print("VA=0x%08X off=0x%X : %r  (full=%r)" % (va if va else 0, off, s, full))
