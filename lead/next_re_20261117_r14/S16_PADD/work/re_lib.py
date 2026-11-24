"""Shared PE + capstone helper for S16_PADD (self-written; no import from other cards)."""
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000

_pe = None
def pe():
    global _pe
    if _pe is None:
        _pe = pefile.PE(EXE, fast_load=True)
    return _pe

def va_to_off(va):
    p = pe()
    rva = va - IMAGE_BASE
    for s in p.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None

ALL_BYTES = None
def all_bytes():
    global ALL_BYTES
    if ALL_BYTES is None:
        with open(EXE, "rb") as f:
            ALL_BYTES = f.read()
    return ALL_BYTES

def read_bytes(va, n):
    off = va_to_off(va)
    if off is None:
        return None
    return all_bytes()[off:off+n]

def section_of(va):
    p = pe()
    rva = va - IMAGE_BASE
    for s in p.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.Name.decode(errors="replace").rstrip("\0")
    return None

_md = Cs(CS_ARCH_X86, CS_MODE_32)
_md.detail = True
_md.skipdata = True

def disasm(va, size):
    b = read_bytes(va, size)
    if b is None:
        return []
    return list(_md.disasm(b, va))

def fmt(ins):
    return f"{ins.address:08X}  {ins.bytes.hex():<20s} {ins.mnemonic:<7s} {ins.op_str}"

def dump(va, size):
    return "\n".join(fmt(i) for i in disasm(va, size))

def raw_va_hits(target_va):
    pat = struct.pack("<I", target_va)
    data = all_bytes()
    hits = []
    start = 0
    while True:
        idx = data.find(pat, start)
        if idx < 0: break
        hit_va = None
        for s in pe().sections:
            if s.PointerToRawData <= idx < s.PointerToRawData + s.SizeOfRawData:
                hit_va = IMAGE_BASE + s.VirtualAddress + (idx - s.PointerToRawData)
                break
        hits.append((idx, hit_va))
        start = idx + 1
    return hits

def vtable_holders(entry_va):
    pat = struct.pack("<I", entry_va)
    data = all_bytes()
    hits = []
    for s in pe().sections:
        name = s.Name.decode(errors="replace").rstrip("\0")
        lo = s.PointerToRawData
        hi = lo + s.SizeOfRawData
        start = lo
        while start < hi:
            idx = data.find(pat, start, hi)
            if idx < 0: break
            slot_va = IMAGE_BASE + s.VirtualAddress + (idx - lo)
            hits.append((slot_va, name, idx))
            start = idx + 1
    return hits

def rtti_of_vtable(vt_va):
    b = read_bytes(vt_va - 4, 4)
    if b is None or len(b) < 4: return None
    col = struct.unpack("<I", b)[0]
    b2 = read_bytes(col + 0xC, 4)
    if b2 is None or len(b2) < 4: return None
    td = struct.unpack("<I", b2)[0]
    name_b = read_bytes(td + 8, 128)
    if name_b is None: return None
    name = name_b.split(b"\0")[0].decode("latin-1", errors="replace")
    return {"vt": hex(vt_va), "col": hex(col), "td": hex(td), "name": name}

if __name__ == "__main__":
    import sys
    for arg in sys.argv[1:]:
        parts = arg.split(":")
        va = int(parts[0], 16)
        size = int(parts[1], 16) if len(parts) > 1 else 0x100
        print(f"=== {va:08X} size={size:#x} section={section_of(va)} ===")
        print(dump(va, size))
        print()
