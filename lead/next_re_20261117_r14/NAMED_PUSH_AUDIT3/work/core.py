import hashlib, struct, sys, os
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest().upper()

assert sha(EXE) == EXPECT, "SHA mismatch"
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = open(EXE, "rb").read()

SECS = []
for s in pe.sections:
    nm = s.Name.rstrip(b"\x00").decode()
    SECS.append((nm, IB + s.VirtualAddress, s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData))
    print("SEC %-8s VA=%08X vsize=%X raw=%X rawptr=%X" % (nm, IB + s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData))

def sec_of(va):
    for nm, sva, rva, vs, rs, rp in SECS:
        if sva <= va < sva + max(vs, rs):
            return nm
    return None

def read(va, n):
    for nm, sva, rva, vs, rs, rp in SECS:
        if sva <= va < sva + rs:
            off = rp + (va - sva)
            avail = min(n, sva + rs - va)
            return DATA[off:off + avail]
    return b""

def u32(va):
    b = read(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None

TEXT_LO = None
TEXT_HI = None
for nm, sva, rva, vs, rs, rp in SECS:
    if nm == ".text":
        TEXT_LO, TEXT_HI = sva, sva + vs
print("TEXT [%08X, %08X)" % (TEXT_LO, TEXT_HI))

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

def dis(va, n, raw=False):
    code = read(va, n)
    out = []
    for i in md.disasm(code, va):
        out.append(i)
    return out

def fmt(i):
    bs = i.bytes.hex().upper()
    s = "%08X  %-24s %-8s %s" % (i.address, bs, i.mnemonic, i.op_str)
    return s

def dis_lines(lo, hi):
    res = []
    for i in dis(lo, hi - lo):
        if i.address >= hi:
            break
        res.append(fmt(i))
    return res

if __name__ == "__main__":
    print("ok")
