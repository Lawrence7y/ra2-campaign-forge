"""S13-K1 reusable binary access helpers.
capstone ALWAYS skipdata=True (discipline #2). Function membership by interval
containment using atlas (discipline #14), plus an independent linear-sweep channel.
"""
import struct
import pefile
import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = open(EXE, "rb").read()
SECS = []
for s in pe.sections:
    name = s.Name.decode("ascii", "replace").rstrip("\x00")
    lo = IB + s.VirtualAddress
    hi = lo + max(s.Misc_VirtualSize, s.SizeOfRawData)
    SECS.append((name, lo, hi, s.PointerToRawData, s.PointerToRawData + s.SizeOfRawData))
TEXT = [s for s in SECS if s[0] == ".text"][0]

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True
MD.skipdata = True  # MANDATORY

# atlas: entry -> (size, n_instr, n_callers, n_callees)
ATLAS_FN = {}
for line in open(ATLAS, encoding="utf-8"):
    if line.startswith("entry\t"): continue
    c = line.rstrip("\n").split("\t")
    if len(c) < 2: continue
    try:
        ATLAS_FN[int(c[0], 16)] = (int(c[1]), int(c[2]), int(c[3]), int(c[4]))
    except ValueError:
        pass
ATLAS_SORTED = sorted(ATLAS_FN)

def sec_of(va):
    for n, lo, hi, rl, rh in SECS:
        if lo <= va < hi: return n
    return None

def off_of(va):
    for n, lo, hi, rl, rh in SECS:
        if lo <= va < hi:
            o = rl + (va - lo)
            if o < rh: return o
    return None

def u32(va):
    o = off_of(va)
    if o is None or o + 4 > len(DATA): return None
    return struct.unpack_from("<I", DATA, o)[0]

def u8(va):
    o = off_of(va)
    if o is None: return None
    return DATA[o]

def cstr(va, cap=256):
    o = off_of(va)
    if o is None: return ""
    return DATA[o:o+cap].split(b"\x00")[0].decode("latin1")

def read(va, n):
    o = off_of(va)
    if o is None: return b""
    return DATA[o:o+n]

def fn_at(va):
    """discipline #14: interval containment, NOT entry_at_or_before."""
    for e in ATLAS_SORTED:
        sz = ATLAS_FN[e][0]
        if e <= va < e + sz: return e
    return None

def disasm(va, n=256, skipdata=True):
    """Linear disasm from va, n bytes. skipdata always True."""
    MD.skipdata = skipdata
    out = []
    for insn in MD.disasm(read(va, n), va):
        out.append(insn)
    return out

def disasm_fn(entry, max_bytes=None):
    """Disasm exactly one atlas function [entry, entry+size). No cross-boundary."""
    sz = ATLAS_FN.get(entry, (None,))[0]
    if sz is None:
        return disasm(entry, max_bytes or 256)
    return disasm(entry, min(sz, max_bytes or sz))

def imm_return(va):
    """Decode `mov eax, imm; ret` for WhatAmI/GetSize stubs."""
    for insn in disasm(va, 24)[:4]:
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            dst, src = insn.operands
            if dst.type == capstone.x86.X86_OP_REG and insn.reg_name(dst.reg) == "eax" and src.type == capstone.x86.X86_OP_IMM:
                return src.imm & 0xFFFFFFFF
        if insn.mnemonic.startswith("ret"): break
    return None

def fmt_insn(i):
    return f"{i.address:08X}  {i.bytes.hex(' '):<24} {i.mnemonic} {i.op_str}"
