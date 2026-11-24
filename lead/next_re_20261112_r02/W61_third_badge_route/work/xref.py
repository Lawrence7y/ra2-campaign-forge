#!/usr/bin/env python3
# W61 xref/string hunt for Q2 (badge art source).
import sys, struct, re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = sys.argv[1]
data = open(EXE, "rb").read()
pe = pefile.PE(EXE, fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase
def rva2off(rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None
def va2off(va): return rva2off(va - IB)
TEXT_OFF = pe.sections[0].PointerToRawData
TEXT_SZ  = pe.sections[0].SizeOfRawData
TEXT_VA  = IB + pe.sections[0].VirtualAddress
text = data[TEXT_OFF:TEXT_OFF+TEXT_SZ]

def find_all(pat):
    out=[]
    i=0
    while True:
        j=text.find(pat,i)
        if j<0: break
        out.append(TEXT_VA+j)
        i=j+1
    return out

print("=== A. custom-message immediates (push imm32 / cmp eax,imm32) in .text ===")
for val in [0x4d3,0x4d4,0x4d5,0x4d6,0x4d7,0x4b2,0x4cd,0x497,0x4d8,0x4ac]:
    b = struct.pack("<I", val)
    pushes = find_all(b"\x68"+b)
    cmps   = find_all(b"\x3d"+b)
    print("  0x%03X : push@%d  cmp_eax@%d" % (val, len(pushes), len(cmps)))
    print("    push VAs: %s" % ", ".join("0x%08X"%v for v in pushes[:20]))
    print("    cmp  VAs: %s" % ", ".join("0x%08X"%v for v in cmps[:20]))

print("\n=== B. SetWindowLongA / RegisterClassA / CallWindowProcA call sites ===")
for name, iatva in [("SetWindowLongA",0x7e1470),("RegisterClassA",0x7e14d8),
                    ("CallWindowProcA",0x7e1488),("CreateWindowExA",0x7e14d4),
                    ("LoadBitmapA",None)]:
    if iatva is None: continue
    pat = b"\xff\x15"+struct.pack("<I", iatva)
    vs = find_all(pat)
    print("  %-18s IAT=0x%08X : %d direct call sites : %s" % (name, iatva, len(vs),
          ", ".join("0x%08X"%v for v in vs[:40])))

print("\n=== C. absolute xrefs to .data campaign-menu globals ===")
for va in [0x825c20,0x825c68,0x825c6c,0x825c70,0x825c74,0x825c78,0x825c7c,
           0xa8f7a0,0xa8f7a8,0xa8f7ad,0xa8f7b0,0xa8eb64,0x8263e0,0x8263f0,0x826408,
           0x8263b0,0x8263c8,0x825c90,0x825c98,0x825ca0]:
    b = struct.pack("<I", va)
    # count raw occurrences in .text (any context)
    allv = find_all(b)
    print("  0x%08X : %d raw occurrences in .text : %s" % (va, len(allv),
          ", ".join("0x%08X"%v for v in allv[:12])))

print("\n=== D. all ASCII strings matching art/menu keywords (VA + text) ===")
# scan whole file for printable runs
kw = re.compile(rb"(?i)(badge|campaign|bootcamp|boot.camp|tutorial|\btut\b|camp|select|emblem|side.?icon|sidebar|cameo|\.shp|\.pcx|\.bmp|stt:|theme|menu)")
seen=set(); results=[]
i=0
while i < len(data)-4:
    if 0x20 <= data[i] < 0x7f:
        j=i
        while j < len(data) and 0x20 <= data[j] < 0x7f: j+=1
        if j-i >= 4:
            s = data[i:j]
            if kw.search(s):
                off = i
                # map to VA if possible
                va = None
                for sec in pe.sections:
                    if sec.PointerToRawData <= off < sec.PointerToRawData+sec.SizeOfRawData:
                        va = IB + sec.VirtualAddress + (off-sec.PointerToRawData); break
                if va is not None and s not in seen:
                    seen.add(s); results.append((va,s))
        i=j
    else:
        i+=1
print("  total unique matching strings: %d" % len(results))
# focus: short, filename-ish / label-ish strings
focus=[(va,s) for va,s in results if len(s)<=48]
for va,s in sorted(focus):
    print("  0x%08X %s" % (va, s.decode("latin1")))
print("\n=== D2. ALL STT: / *Select / *Campaign* strings (unfiltered length) ===")
for va,s in sorted(results):
    t=s.decode("latin1")
    if t.startswith("STT:") or "Campaign" in t or "BootCamp" in t or "Select" in t or "campaign" in t.lower():
        print("  0x%08X %s" % (va,t))
