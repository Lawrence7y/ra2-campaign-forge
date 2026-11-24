"""W152 core: PE access + capstone disassembly + function boundary attribution.

All analysis is static/read-only over the on-disk gamemd.exe.
ImageBase 0x400000 (R2_COMMON §0).  Function boundaries come from
W130_atlas\\function_atlas.tsv (12,916 Ghidra-enumerated functions), so every
instruction we attribute lives inside a boundary Ghidra established -- we never
trust a linear sweep across a `ret`.
"""
import bisect
import struct
import capstone
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

_pe = pefile.PE(EXE, fast_load=True)
IB = _pe.OPTIONAL_HEADER.ImageBase
_secs = []
for s in _pe.sections:
    _secs.append((s.VirtualAddress + IB, s.Misc_VirtualSize,
                  s.PointerToRawData, s.SizeOfRawData, s.Name.rstrip(b'\0').decode()))
_blob = open(EXE, 'rb').read()


def sec_of(va):
    for vstart, vsize, praw, rsize, name in _secs:
        if vstart <= va < vstart + max(vsize, rsize):
            return name, vstart, praw, rsize
    return None, None, None, None


def read(va, n):
    name, vstart, praw, rsize = sec_of(va)
    if name is None:
        raise ValueError("VA %08x outside sections" % va)
    off = praw + (va - vstart)
    return _blob[off:off + n]


def u32(va):
    return struct.unpack('<I', read(va, 4))[0]


def u16(va):
    return struct.unpack('<H', read(va, 2))[0]


def u8(va):
    return read(va, 1)[0]


def code(va, n):
    """Executable bytes for disassembly (zero-padded if past section end)."""
    name, vstart, praw, rsize = sec_of(va)
    b = read(va, n)
    if len(b) < n:
        b = b + b'\x90' * (n - len(b))
    return b


# ---- function boundaries -------------------------------------------------
ENTRIES = []
FUNC = {}
with open(ATLAS, encoding='utf-8', errors='replace') as f:
    f.readline()
    for line in f:
        p = line.rstrip('\n').split('\t')
        if len(p) < 4:
            continue
        try:
            e = int(p[0], 16)
            size = int(p[1])
        except ValueError:
            continue
        ENTRIES.append(e)
        FUNC[e] = (size, p)
ENTRIES.sort()

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True


def owning_fn(va):
    """Entry of the atlas function whose [entry, entry+size) covers va."""
    i = bisect.bisect_right(ENTRIES, va) - 1
    if i < 0:
        return None
    e = ENTRIES[i]
    size = FUNC[e][0]
    if e <= va < e + size:
        return e
    return None


def fn_size(e):
    return FUNC[e][0] if e in FUNC else None


def disas_range(va, n, base=None):
    """Disassemble exactly n bytes starting at va; returns list of (addr,size,text,insn)."""
    out = []
    start = va
    for insn in MD.disasm(code(va, n), va):
        out.append(insn)
        if insn.address + insn.size - start >= n:
            break
    return out


def disas_fn(entry, cap=4000):
    """Whole function decoded from its Ghidra entry, capped by atlas size."""
    size = fn_size(entry)
    if size is None:
        return []
    return disas_range(entry, min(size, cap))


def fn_label(e):
    if e is None:
        return "?"
    s = fn_size(e)
    return "%08X(size=%s)" % (e, s if s is not None else "?")


def fmt(insn):
    return "%08X  %-28s %s %s" % (insn.address,
                                  insn.bytes.hex(),
                                  insn.mnemonic, insn.op_str)
