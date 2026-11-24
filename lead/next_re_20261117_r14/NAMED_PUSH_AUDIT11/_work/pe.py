"""Independent PE/disasm helper for NAMED_PUSH_AUDIT11 (異族审计)."""
import hashlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SYNTAX_INTEL

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

with open(EXE, "rb") as f:
    DATA = f.read()
SHA = hashlib.sha256(DATA).hexdigest().upper()
assert SHA == EXPECT_SHA, SHA

PE = pefile.PE(EXE, fast_load=True)
IMAGEBASE = PE.OPTIONAL_HEADER.ImageBase
SECTIONS = []
for s in PE.sections:
    name = s.Name.rstrip(b"\x00").decode()
    SECTIONS.append((name, IMAGEBASE + s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData))

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True


def sec_of(va):
    for name, sva, vsz, rawsz, raw in SECTIONS:
        if sva <= va < sva + max(vsz, rawsz):
            return name, sva, vsz, rawsz, raw
    return None


def off(va):
    s = sec_of(va)
    if not s:
        return None
    name, sva, vsz, rawsz, raw = s
    d = va - sva
    if d >= rawsz:
        return None
    return raw + d


def rd(va, n):
    o = off(va)
    if o is None or o + n > len(DATA):
        return None
    return DATA[o:o + n]


def u32(va):
    b = rd(va, 4)
    return None if b is None else int.from_bytes(b, "little")


def u16(va):
    b = rd(va, 2)
    return None if b is None else int.from_bytes(b, "little")


def hexs(va, n):
    b = rd(va, n)
    return None if b is None else " ".join(f"{x:02x}" for x in b)


def cstr(va, maxlen=256):
    o = off(va)
    if o is None:
        return None
    e = DATA.find(b"\x00", o, o + maxlen)
    if e < 0:
        e = o + maxlen
    try:
        return DATA[o:e].decode("latin-1")
    except Exception:
        return None


def dis(va, maxbytes=400):
    b = rd(va, maxbytes)
    if b is None:
        return []
    return list(MD.disasm(b, va))


def dis_range(va_start, va_end):
    b = rd(va_start, va_end - va_start)
    if b is None:
        return []
    return list(MD.disasm(b, va_start))


def fmt(ins):
    m = ins.mnemonic
    o = ins.op_str
    return f"{ins.address:08X}  {ins.bytes.hex(' '):<24} {m} {o}".rstrip()


def rtti_name(vt_va):
    """vt-4 -> COL -> [COL+0xC] = TD -> TD+8 inline name (or pointer)."""
    out = {}
    col = u32(vt_va - 4)
    out["col"] = col
    if not col:
        return out
    out["col_bytes"] = hexs(vt_va - 4, 16)
    td = u32(col + 0xC)
    out["td"] = td
    if not td:
        return out
    td_bytes = rd(td, 16)
    out["td_bytes"] = hexs(td, 16)
    if td_bytes and td_bytes[0] & 1:  # type descriptor 32-bit pointer? heuristic
        pass
    nm_inline = cstr(td + 8)
    out["name_inline"] = nm_inline
    # also try pointer form (64-bit build style) just in case
    p = u32(td + 8)
    if p:
        out["name_ptr_target"] = cstr(p)
    return out


def rtti_class(vt_va):
    """strict RTTI: [vt-4]=COL -> [COL+0xC]=TD -> TD+8 inline name string"""
    d = {"vt": f"{vt_va:08X}"}
    col = u32(vt_va - 4)
    d["col"] = f"{col:08X}" if col else None
    if not col:
        return d
    s = sec_of(col)
    d["col_sec"] = s[0] if s else None
    td = u32(col + 0xC)
    d["td"] = f"{td:08X}" if td else None
    if not td:
        return d
    s = sec_of(td)
    d["td_sec"] = s[0] if s else None
    nm = cstr(td + 8, 300)
    d["name"] = nm
    d["name_ok"] = bool(nm and nm.startswith(".?A"))
    return d


def direct_callers(target, scan=True):
    """E8 rel32 boundaries over .text."""
    res = []
    if not scan:
        return res
    text = sec_of(0x401000)
    name, sva, vsz, rawsz, raw = text
    start, end = sva, sva + rawsz
    blob = DATA[raw:raw + rawsz]
    for i in range(0, len(blob) - 5):
        if blob[i] == 0xE8:
            va = start + i
            rel = int.from_bytes(blob[i + 1:i + 5], "little", signed=True)
            if (va + 5 + rel) & 0xFFFFFFFF == target:
                res.append(va)
    return res
