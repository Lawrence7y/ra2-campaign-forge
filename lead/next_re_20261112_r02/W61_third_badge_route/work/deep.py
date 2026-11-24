#!/usr/bin/env python3
# W61 deep-dive: IAT resolution, badge-image loader (0x7514d0) disasm,
# .data string dumps, 0x46CC90 / 0x46CCD0 / 0x734e60 disasm.
import sys, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = sys.argv[1] if len(sys.argv) > 1 else r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"
pe = pefile.PE(EXE, fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase
data = open(EXE, "rb").read()

def rva2off(rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None
def va2off(va): return rva2off(va - IB)
def u32(o): return struct.unpack_from("<I", data, o)[0]

# ---- IAT map ----
print("=== IAT RESOLUTION ===")
iat = {}
for entry in pe.DIRECTORY_ENTRY_IMPORT:
    dll = entry.dll.decode("latin1")
    for imp in entry.imports:
        iat[imp.address - IB + IB] = None  # placeholder
        va = imp.address  # already a VA
        nm = imp.name.decode("latin1") if imp.name else "ord_%d" % imp.ordinal
        iat[va] = (dll, nm)
for va in sorted(iat):
    if iat[va]:
        print("  0x%08X  %-14s %s" % (va, iat[va][0], iat[va][1]))

print("\n=== specific IAT slots used by WndProc 0x52EC00 ===")
for va in [0x7e13b0,0x7e13b4,0x7e13b8,0x7e13bc,0x7e13f8,0x7e13fc,
           0x7e1474,0x7e1490,0x7e1498,0x7e149c,0x7e14a0,0x7e14a4,0x7e14a8,0x7e14ac]:
    print("  [0x%08X] = %s" % (va, iat.get(va, "NOT IN IAT (maybe .rdata pointer)")))

# ---- strings ----
print("\n=== STRING DUMPS ===")
def cstr(va, n=120):
    o = va2off(va)
    if o is None: return "<unmapped>"
    b = data[o:o+n].split(b"\x00")[0]
    return repr(b)
for va in [0x825fb8, 0x8263b0, 0x8263c8, 0x8263e0, 0x8263f0, 0x826408,
           0x825c90, 0x825c98, 0x825ca0, 0x826198, 0x8261a8]:
    print("  0x%08X : %s" % (va, cstr(va)))
print("  RAW @0x8263a0..0x826430 : %r" % data[va2off(0x8263a0):va2off(0x8263a0)+0x90])

# ---- disassembler helper ----
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True
def disasm(name, start, length):
    print("\n=== DISASM %s 0x%08X .. 0x%08X ===" % (name, start, start+length))
    o = va2off(start)
    code = data[o:o+length]
    for ins in md.disasm(code, start):
        extra = ""
        # annotate call/jmp targets that resolve to IAT
        print("  0x%08X  %-20s %s%s" % (ins.address, ins.bytes.hex(" "), ins.mnemonic+" "+ins.op_str, extra))
    print("=== END %s ===" % name)

disasm("0x7514d0 badge-image loader?", 0x7514d0, 0x260)
disasm("0x734e60 other-button image loader?", 0x734e60, 0x1C0)
disasm("0x46CC90 Battle::Find/Get by name", 0x46CC90, 0x40)
disasm("0x46CCD0 Battle::Read_INI", 0x46CCD0, 0x320)
disasm("0x750920 sound/transition", 0x750920, 0x60)
