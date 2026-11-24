#!/usr/bin/env python3
# W61: dump UI/PCX string tables + format strings used by 0x734e60.
import sys, struct
import pefile
EXE=sys.argv[1]
data=open(EXE,"rb").read(); pe=pefile.PE(EXE,fast_load=False); IB=pe.OPTIONAL_HEADER.ImageBase
def rva2off(r):
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)
    return None
def va2off(v): return rva2off(v-IB)
def cstr(va,n=160):
    o=va2off(va)
    if o is None: return "<unmapped>"
    return repr(data[o:o+n].split(b"\x00")[0])
print("=== named string constants ===")
for va in [0x81b2ec,0x81b304,0x81b4ac,0x81b4b8,0x81b4d0,0x81b4e8,0x81b500,0x81b514,
           0x845820,0x8457f4,0x8457bc,0x846574,0x817474,0x8241ac,0x8241c8,
           0x82634c,0x8263a8,0x826330,0x826304]:
    print("  0x%08X : %s" % (va, cstr(va)))
print("\n=== raw .rdata UI-name region 0x824080..0x824340 ===")
o=va2off(0x824080)
print(repr(data[o:o+0x2C0]))
print("\n=== raw 0x81B480..0x81B540 ===")
o=va2off(0x81B480)
print(repr(data[o:o+0xC0]))
print("\n=== ALL .PCX / .SHP filename strings in image (VA + text) ===")
import re
pat=re.compile(rb"[ -~]{3,60}\.(?:PCX|SHP|BMP|VQA|BIK)\b", re.I)
seen=set()
for m in pat.finditer(data):
    s=m.group()
    if s in seen: continue
    seen.add(s)
    off=m.start()
    va=None
    for sec in pe.sections:
        if sec.PointerToRawData<=off<sec.PointerToRawData+sec.SizeOfRawData:
            va=IB+sec.VirtualAddress+(off-sec.PointerToRawData); break
    print("  0x%08X %s" % (va or 0, s.decode("latin1")))
print("total: %d" % len(seen))
