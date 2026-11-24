# -*- coding: utf-8 -*-
"""W100 work script 1: PE layout + disasm of 0x47C520 family / 0x51BF90 + call-site search.
READ-ONLY on the exe. Output -> EVIDENCE\\step1_disasm.txt
"""
import pefile, capstone, sys, struct

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\step1_disasm.txt"

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
print("ImageBase: 0x%08X" % IB)
print("Sections:")
secs = []
for s in pe.sections:
    name = s.Name.rstrip(b"\0").decode("ascii", "replace")
    va = IB + s.VirtualAddress
    secs.append((name, va, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData,
                 s.Characteristics))
    print("  %-8s VA=0x%08X VSize=0x%X RawPtr=0x%X RawSize=0x%X Char=0x%08X" %
          (name, va, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData,
           s.Characteristics))

def sec_of(va):
    for name, sva, vsz, rdp, rsz, ch in secs:
        if sva <= va < sva + max(vsz, 1):
            return name
    return None

def read(va, n):
    off = pe.get_offset_from_rva(va - IB)
    with open(EXE, "rb") as f:
        f.seek(off)
        return f.read(n)

def disasm(va, n, label=""):
    code = read(va, n)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False
    lines = ["--- %s (0x%08X, %d bytes) ---" % (label, va, n)]
    for ins in md.disasm(code, va):
        lines.append("0x%08X: %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    return "\n".join(lines)

print()
print(disasm(0x0047C4D0, 0xB0, "sibling 0x47C4D0 (per R09_COMMON: ret 8, wanted-id 0x24)"))
print()
print(disasm(0x0047C520, 0x40, "crash family 0x47C520-0x47C54E"))
print()
print(disasm(0x0051BF90, 0x130, "0x51BF90 InfantryClass::IsCellOccupied (head)"))

# --- find E8 rel32 call sites targeting a given VA ---
text = [s for s in secs if s[0] == ".text"][0]
tname, tva, tvsz, trdp, trsz, tch = text
blob = read(tva, trsz)

def find_calls(target):
    hits = []
    for i in range(len(blob) - 5):
        if blob[i] == 0xE8:
            rel = struct.unpack_from("<i", blob, i + 1)[0]
            if tva + i + 5 + rel == target:
                hits.append(tva + i)
    return hits

for tgt in (0x0047C520, 0x0051BF90):
    hits = find_calls(tgt)
    print("\ncall E8 rel32 sites targeting 0x%08X: %d hits" % (tgt, len(hits)))
    for h in hits:
        print("  call-site 0x%08X" % h)
