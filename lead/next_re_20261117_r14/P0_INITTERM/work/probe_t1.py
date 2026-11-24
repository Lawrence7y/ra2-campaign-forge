"""P0-INITTERM T1 probe: locate _initterm call site and decode the dispatcher body.
Read-only on gamemd.exe. capstone skipdata=True mandatory.
"""
import sys, os, hashlib
sys.path.insert(0, r"D:\Project\ra2-campaign-forge")
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
EXPECTED = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

h = hashlib.sha256(open(EXE, "rb").read()).hexdigest().upper()
print("SHA256:", h, "MATCH" if h == EXPECTED else "MISMATCH")
assert h == EXPECTED

pe = pefile.PE(EXE, fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase
print("ImageBase:", hex(IB))
print("Sections:")
for s in pe.sections:
    print("  %-8s VA=%08X VS=%08X RAW=%08X RS=%08X" % (
        s.Name.decode(errors="replace").rstrip("\x00"),
        IB + s.VirtualAddress, s.Misc_VirtualSize,
        s.PointerToRawData, s.SizeOfRawData))

def va2off(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    raise ValueError("VA not mapped: %08X" % va)

data = open(EXE, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True

def dis(va, n, label):
    off = va2off(va)
    buf = data[off:off+n]
    print("\n=== %s @ %08X (%d bytes) ===" % (label, va, n))
    cnt = 0
    for i in md.disasm(buf, va):
        print("  %08X  %-24s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
        cnt += 1
    print("  [instructions:", cnt, "]")

# Around the call site 0x7CBDD3
dis(0x7CBDD0 - 0x20, 0x60, "around 7CBDD3")
# The dispatcher body at 0x7CBED3
dis(0x7CBED3, 0x100, "dispatcher 7CBED3")
