from __future__ import annotations
import os, sys, struct, bisect, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
COV = os.path.join(ROOT, "lead", "next_re_20261117_r14", "COVERAGE", "coverage.tsv")
OUT = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(OUT)

PE = pefile.PE(EXE, fast_load=True)
BASE = PE.OPTIONAL_HEADER.ImageBase
SEGS = []
for s in PE.sections:
    va = BASE + s.VirtualAddress
    SEGS.append((va, va + max(s.Misc_VirtualSize, s.SizeOfRawData), s.PointerToRawData, s.SizeOfRawData, s.Name.rstrip(b"\x00").decode("latin1")))
SEGS.sort()

def va_off(va):
    for lo, hi, raw, rawsz, name in SEGS:
        if lo <= va < hi:
            d = va - lo
            if d >= rawsz:
                raise ValueError(f"VA {va:#x} in {name} but beyond raw data")
            return raw + d, name
    raise KeyError(f"unmapped VA {va:#x}")

def read(va, n):
    off, name = va_off(va)
    return PE.__data__[off:off+n]

def u32(va):
    return struct.unpack_from("<I", read(va, 4))[0]

def u16(va):
    return struct.unpack_from("<H", read(va, 2))[0]

def cstr(va, maxn=512):
    b = read(va, maxn)
    z = b.find(b"\x00")
    return b[:z if z >= 0 else len(b)]

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True

def dis(va, n=None, stop_ret=False):
    if n is None:
        n = 512
    data = read(va, n)
    out = []
    for i in MD.disasm(data, va):
        out.append(i)
        if stop_ret and (i.mnemonic.startswith("ret") or i.mnemonic in {"jmp"}):
            break
    return out

def fmt(ins):
    return f"{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic} {ins.op_str}".rstrip()

def load_rows(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        lines = [x.rstrip("\r\n") for x in f if x.strip()]
    hdr = lines[0].split("\t")
    return hdr, [dict(zip(hdr, x.split("\t"))) for x in lines[1:]]

def atlas_rows():
    _, rows = load_rows(ATLAS)
    return {int(r["entry"], 16): r for r in rows}

def cov_rows():
    _, rows = load_rows(COV)
    return {int(r["entry"], 16): r for r in rows}

def target_rows():
    path = os.path.join(os.path.dirname(PARENT), "S13_K4", "TARGETS.tsv")
    _, rows = load_rows(path)
    return rows

def s13_set():
    a = atlas_rows(); c = cov_rows()
    return sorted(k for k, v in c.items() if v["subsystem"] == "S13" and k in a)

def sha():
    return hashlib.sha256(open(EXE, "rb").read()).hexdigest().upper()

def find_bytes(pat, segname=".text"):
    out = []
    for lo, hi, raw, rawsz, name in SEGS:
        if segname and name != segname:
            continue
        blob = PE.__data__[raw:raw+rawsz]
        st = 0
        while True:
            p = blob.find(pat, st)
            if p < 0: break
            out.append(lo + p)
            st = p + 1
    return out

if __name__ == "__main__":
    print("sha256", sha())
    print("imagebase", hex(BASE))
    for seg in SEGS: print("segment", *[hex(x) if isinstance(x,int) else x for x in seg[:4]], seg[4])
    addrs = [0x75E3B0, 0x40F510, 0x46C440]
    for va in addrs:
        print("\n===== ", hex(va), " =====")
        print("\n".join(fmt(i) for i in dis(va, 520)))
