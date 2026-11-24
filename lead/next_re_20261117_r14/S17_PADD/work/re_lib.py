"""
S17-PADD reusable reverse-engineering library.
System Python 3.12 + capstone 5.0.7 (skipdata=True) + pefile 2024.8.26.
Target ra2youli\\gamemd.exe SHA-256 73201CC0...F67476, ImageBase 0x400000.
Read-only on the target binary.
"""
import os
import struct
import hashlib

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
EXPECTED_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
IMAGE_BASE = 0x400000

_sha = hashlib.sha256(open(EXE, "rb").read()).hexdigest().upper()
assert _sha == EXPECTED_SHA, ("SHA mismatch", _sha)

PE = pefile.PE(EXE, fast_load=False)

# Build VA->offset mapper over all sections (raw data only).
_SECTIONS = []
for s in PE.sections:
    name = s.Name.rstrip(b"\x00").decode("latin-1")
    va = IMAGE_BASE + s.VirtualAddress
    vsize = s.Misc_VirtualSize
    rsize = s.SizeOfRawData
    praw = s.PointerToRawData
    _SECTIONS.append((name, va, vsize, rsize, praw))

TEXT = None  # (va, size_bytes_of_raw, praw)
for name, va, vsize, rsize, praw in _SECTIONS:
    if name == ".text":
        TEXT = (va, rsize, praw)
assert TEXT is not None, "no .text"

DATA = open(EXE, "rb").read()


def va_to_off(va):
    # Only map bytes that actually exist on disk (raw data), not BSS tail.
    for name, sva, vsize, rsize, praw in _SECTIONS:
        if rsize == 0:
            continue
        if sva <= va < sva + rsize:
            off = praw + (va - sva)
            if 0 <= off < len(DATA):
                return off
    return None


def read_bytes(va, n):
    off = va_to_off(va)
    if off is None:
        return None
    return DATA[off:off + n]


def read_u32(va):
    b = read_bytes(va, 4)
    if b is None or len(b) < 4:
        return None
    return struct.unpack("<I", b)[0]


def read_cstr(va, maxn=128):
    off = va_to_off(va)
    if off is None:
        return None
    end = DATA.find(b"\x00", off, off + maxn)
    if end < 0:
        end = off + maxn
    return DATA[off:end].decode("latin-1", "replace")


MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True


def disasm(va, nbytes):
    """Return list of (addr, mnemonic, op_str, size, bytes_hex)."""
    b = read_bytes(va, nbytes)
    if b is None:
        return []
    out = []
    for ins in MD.disasm(b, va):
        out.append((ins.address, ins.mnemonic, ins.op_str, ins.size,
                    b[ins.address - va:ins.address - va + ins.size].hex()))
    return out


def disasm_until_ret(va, maxbytes=2048):
    ins = disasm(va, maxbytes)
    # stop after first ret (inclusive)
    out = []
    for x in ins:
        out.append(x)
        if x[1].startswith("ret") or x[1] == "jmp":
            break
    return out


def sweep_e8(start=None, end=None):
    """Yield (site_va, target_va) for every E8 whose computed target is inside .text.
    start/end default to whole .text raw range. Uses instruction boundary via capstone,
    with raw-byte fallback so skipdata does not hide call sites."""
    tv, tsize, tp = TEXT
    if start is None:
        start = tv
    if end is None:
        end = tv + tsize
    off0 = va_to_off(start)
    off1 = va_to_off(end)
    if off0 is None or off1 is None:
        return
    blob = DATA[off0:off1]
    # Instruction-boundary sweep (dropdown aware: we just scan bytes and validate boundary
    # separately with a capstone pass over the region when needed).
    for i, byte in enumerate(blob):
        if byte != 0xE8:
            continue
        site = start + i
        if i + 5 > len(blob):
            break
        rel = struct.unpack("<i", blob[i + 1:i + 5])[0]
        target = site + 5 + rel
        if tv <= target < tv + tsize:
            yield (site, target)


def sweep_e8_boundary(start=None, end=None):
    """E8 sites that lie on a real capstone instruction boundary."""
    tv, tsize, tp = TEXT
    if start is None:
        start = tv
    if end is None:
        end = tv + tsize
    raw = dict(sweep_e8(start, end))
    b = read_bytes(start, end - start)
    if b is None:
        return []
    out = []
    for ins in MD.disasm(b, start):
        if ins.mnemonic == "call" and ins.size == 5 and ins.address in raw:
            out.append((ins.address, raw[ins.address]))
    return out


def rtti_col_td(name_contains=None, td_va=None, col_va=None):
    """Read RTTI chain COL+0xC -> TD -> TD+8 inline name.
    Given col_va: return (td, name). Given td_va: return name.
    name_contains: scan all COL-like dwords in .rdata pointing to TD whose name matches.
    """
    if td_va is not None:
        return read_cstr(td_va + 8)
    if col_va is not None:
        td = read_u32(col_va + 0xC)
        if td is None:
            return (None, None)
        return (td, read_cstr(td + 8))
    return (None, None)


def holder_scan(entry_va):
    """Scan all mapped dwords equal to entry_va; return list of VAs."""
    hits = []
    for name, sva, vsize, rsize, praw in _SECTIONS:
        if name not in (".rdata", ".data"):
            continue
        off = praw
        end = praw + rsize
        needle = struct.pack("<I", entry_va)
        pos = DATA.find(needle, off, end)
        while pos >= 0:
            hits.append(sva + (pos - praw))
            pos = DATA.find(needle, pos + 1, end)
    return hits


if __name__ == "__main__":
    print("SHA", _sha)
    print(".text", hex(TEXT[0]), "rawsize", TEXT[1], "end", hex(TEXT[0] + TEXT[1]))
    for s in _SECTIONS:
        print(s[0], hex(s[1]), hex(s[2]), "raw", hex(s[3]))
