"""AUDIT13 core: independent PE reader + disasm helpers. Own implementation."""
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D

_pe = pefile.PE(EXE, fast_load=True)
_SECT = []
for s in _pe.sections:
    va = s.VirtualAddress + BASE
    _SECT.append((va, va + s.Misc_VirtualSize, s.PointerToRawData, s.Misc_VirtualSize,
                  s.Name.rstrip(b"\x00").decode("latin1")))
_IMG = _pe.OPTIONAL_HEADER.SizeOfImage

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True


def read(va, n):
    for lo, hi, raw, vsz, name in _SECT:
        if lo <= va < hi:
            off = raw + (va - lo)
            with open(EXE, "rb") as f:
                f.seek(off)
                d = f.read(min(n, hi - va))
            return d
    raise ValueError("va out of sections: %x" % va)


def u32(va):
    return int.from_bytes(read(va, 4), "little")


def find_sect(va):
    for lo, hi, raw, vsz, name in _SECT:
        if lo <= va < hi:
            return name
    return None


def hexs(va, n=16):
    d = read(va, n)
    return " ".join("%02X" % b for b in d)


def dis(va, count=200, stop_at_ret=True):
    """linear disasm from va; yields insns. Stops after ret/retn followed by padding."""
    out = []
    cur = va
    for ins in md.disasm(read(va, 4000), va):
        if ins.address >= TEXT_HI:
            break
        out.append(ins)
        cur = ins.address + ins.size
        if len(out) >= count:
            break
        if stop_at_ret and ins.mnemonic in ("ret", "retn", "iretd", "jmp") and ins.mnemonic == "ret" or False:
            pass
    return out


def fn(va, count=400):
    """Disassemble a function body: stop after a ret/ret-imm when the next bytes are padding
    (CC / 90 / 00) or the next address starts another known function prologue."""
    out = []
    for ins in md.disasm(read(va, 8000), va):
        if ins.address >= TEXT_HI:
            break
        out.append(ins)
        nxt = ins.address + ins.size
        if len(out) >= count:
            break
        if ins.mnemonic in ("ret", "retn") or (ins.mnemonic == "retf"):
            pad = read(nxt, 3)
            if pad[:1] in (b"\xcc", b"\x90", b"\x00", b"\xc3"):
                break
    return out


def render(insns, indent=0):
    lines = []
    for i in insns:
        b = " ".join("%02X" % x for x in i.bytes)
        lines.append("  %08X  %-24s %-8s %s" % (i.address, b[:24], i.mnemonic, i.op_str))
    return "\n".join(lines)


def vtable(va, maxn=64):
    """read vtable pointers while they land in .text"""
    out = []
    p = va
    for _ in range(maxn):
        t = u32(p)
        if not (TEXT_LO <= t < TEXT_HI):
            break
        out.append(t)
        p += 4
    return out


def _va(x):
    """stored RTTI pointers in this image are absolute VAs; accept both forms."""
    if x == 0:
        return None
    if find_sect(x) is not None:
        return x
    return BASE + x


def col_of(vt):
    """CompleteObjectLocator for a vtable (stored at vt-4)."""
    return _va(u32(vt - 4))


def col_info(vt):
    col = col_of(vt)
    if col is None:
        return None
    sig, off, cdoff, td_p, cd_p, self_p = (
        u32(col), u32(col + 4), u32(col + 8), u32(col + 12), u32(col + 16), u32(col + 20))
    td = _va(td_p)
    cd = _va(cd_p)
    nm = read(td + 8, 200).split(b"\x00")[0].decode("latin1") if td else None
    return dict(col=col, sig=sig, offset=off, cd_offset=cdoff, td=td, name=nm,
                self=_va(self_p), cd=cd)


def imm32_refs(target, lo=TEXT_LO, hi=TEXT_HI):
    """all occurrences of imm32 target in .text (C7-style push/mov/cmp)."""
    hits = []
    t = target.to_bytes(4, "little")
    data = read(lo, hi - lo)
    idx = 0
    while True:
        k = data.find(t, idx)
        if k < 0:
            break
        hits.append(lo + k)
        idx = k + 1
    return hits
