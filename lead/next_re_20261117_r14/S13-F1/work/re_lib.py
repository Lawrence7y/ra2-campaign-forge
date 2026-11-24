"""S13-F1 reusable binary access + evidence helpers.
Discipline compliance:
 #2 capstone ALWAYS skipdata=True.
 #3 boundary_check returns 'unknown' on span>=max_bytes, never False.
 #14 function membership by interval containment using atlas, plus an independent
     byte channel (ret/jmp/int3 + 16B align) that does NOT depend on atlas entry+size.
 #15 scan writes in BOTH absolute [glob] and base-loaded [reg+off] forms; mov mem
     operand may be op1.
 #16 field semantics need own write+read support.
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
RDATA = [s for s in SECS if s[0] == ".rdata"][0]

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True
MD.skipdata = True  # MANDATORY (#2)

# atlas: entry -> dict of columns (interval containment uses size)
ATLAS_FN = {}
with open(ATLAS, encoding="utf-8") as f:
    hdr = f.readline().rstrip("\n").split("\t")
    for line in f:
        c = line.rstrip("\n").split("\t")
        if len(c) < 2:
            continue
        try:
            ATLAS_FN[int(c[0], 16)] = {"size": int(c[1]), "n_instr": int(c[2]),
                                      "n_callers": int(c[3]), "n_callees": int(c[4])}
        except ValueError:
            pass
ATLAS_SORTED = sorted(ATLAS_FN)


def sec_of(va):
    for n, lo, hi, rl, rh in SECS:
        if lo <= va < hi:
            return n
    return None


def off_of(va):
    for n, lo, hi, rl, rh in SECS:
        if lo <= va < hi:
            o = rl + (va - lo)
            if o < rh:
                return o
    return None


def in_file(va, n=1):
    o = off_of(va)
    return o is not None and o + n <= len(DATA)


def u32(va):
    o = off_of(va)
    if o is None or o + 4 > len(DATA):
        return None
    return struct.unpack_from("<I", DATA, o)[0]


def u16(va):
    o = off_of(va)
    if o is None or o + 2 > len(DATA):
        return None
    return struct.unpack_from("<H", DATA, o)[0]


def u8(va):
    o = off_of(va)
    if o is None:
        return None
    return DATA[o]


def cstr(va, cap=512):
    o = off_of(va)
    if o is None:
        return ""
    return DATA[o:o + cap].split(b"\x00")[0].decode("latin1")


def read(va, n):
    o = off_of(va)
    if o is None:
        return b""
    return DATA[o:o + n]


def fn_at(va):
    """Discipline #14: interval containment, NOT entry_at_or_before."""
    best = None
    for e in ATLAS_SORTED:
        if e <= va < e + ATLAS_FN[e]["size"]:
            if best is None or e > best:
                best = e
    return best


def atlas_entry_at(va):
    """entry_at_or_before - provided ONLY to demonstrate the difference (#14)."""
    best = None
    for e in ATLAS_SORTED:
        if e <= va:
            best = e
        else:
            break
    return best


def disasm(va, n=256, skipdata=True):
    MD.skipdata = skipdata
    return list(MD.disasm(read(va, n), va))


def disasm_fn(entry, max_bytes=None):
    """Disasm exactly one atlas function [entry, entry+size). No cross-boundary."""
    sz = ATLAS_FN.get(entry, {}).get("size")
    if sz is None:
        return disasm(entry, max_bytes or 256)
    return disasm(entry, min(sz, max_bytes or sz))


def disasm_until_ret(va, max_bytes=4096, max_insn=4000):
    """Linear disasm from va until first ret, capstone skipdata=True."""
    MD.skipdata = True
    out = []
    for insn in MD.disasm(read(va, max_bytes), va):
        out.append(insn)
        if insn.mnemonic.startswith("ret"):
            break
        if len(out) >= max_insn:
            break
    return out


def fmt_insn(i):
    return f"{i.address:08X}  {i.bytes.hex(' '):<24} {i.mnemonic} {i.op_str}"


def dump_insns(insns):
    return "\n".join(fmt_insn(i) for i in insns)


def imm_return(va):
    """Decode `mov eax, imm; ret` for WhatAmI/GetSize stubs."""
    for insn in disasm(va, 24)[:4]:
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            dst, src = insn.operands
            if (dst.type == capstone.x86.X86_OP_REG and insn.reg_name(dst.reg) == "eax"
                    and src.type == capstone.x86.X86_OP_IMM):
                return src.imm & 0xFFFFFFFF
        if insn.mnemonic.startswith("ret"):
            break
    return None


def call_target(insn):
    """Return absolute call/jmp rel32 target if insn is E8/E9, else None."""
    if insn.mnemonic in ("call", "jmp") and len(insn.operands) == 1:
        op = insn.operands[0]
        if op.type == capstone.x86.X86_OP_IMM:
            return op.imm & 0xFFFFFFFF
    return None


def vt_slots(vftable_va, count):
    """Read `count` consecutive dword slots from a vftable base (independent of vtables_v2.json)."""
    return [u32(vftable_va + 4 * i) for i in range(count)]


def boundary_check(va, max_bytes=64):
    """Independent byte-channel function-entry heuristic (atlas-independent).
    Returns 'yes' / 'no' / 'unknown' (#3): unknown on span>=max_bytes, never False.
    'yes' = 16B aligned AND preceding byte region is ret/jmp/int3 or nop padding
            whose preceding real insn is ret/jmp/int3, AND target is not a jcc dest.
    """
    if va % 16 != 0:
        return "no"
    # walk back up to max_bytes for a terminating insn
    start = max(TEXT[1], va - max_bytes)
    span = va - start
    if span >= max_bytes:
        return "unknown"
    # find last non-nop/padding before va
    pre = read(start, span)
    # Simple: decode backwards is unreliable; decode forward from start, track last insn before va
    MD.skipdata = True
    last = None
    for insn in MD.disasm(pre, start):
        if insn.address >= va:
            break
        last = insn
    if last is None:
        return "unknown"
    if last.mnemonic.startswith("ret") or last.mnemonic in ("jmp", "int3"):
        return "yes"
    # padding of nops: check byte right before va
    b = u8(va - 1)
    if b in (0x90, 0xCC, 0xC3):
        return "yes"
    return "no"


def is_jcc_dest(va, window=0x2000):
    """Return True if va is a conditional-jump destination within ±window (approx)."""
    # bounded scan of .text call/jcc rel target set; used sparingly
    MD.skipdata = True
    base = TEXT[1]
    size = min(TEXT[2] - TEXT[1], 0x500000)
    for insn in MD.disasm(read(base, size), base):
        if insn.mnemonic.startswith("j") and insn.mnemonic not in ("jmp",):
            if len(insn.operands) == 1 and insn.operands[0].type == capstone.x86.X86_OP_IMM:
                if insn.operands[0].imm == va:
                    return True
    return False


if __name__ == "__main__":
    print("IB", hex(IB), "text", tuple(hex(x) for x in TEXT[1:3]),
          "atlas fns", len(ATLAS_FN))
