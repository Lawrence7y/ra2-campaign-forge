#!/usr/bin/env python3
"""Shared read-only PE/RTTI/disassembly helpers for S10-K5."""
from pathlib import Path
import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

ROOT = Path(r'D:\Project\ra2-campaign-forge')
EXE = ROOT / 'ra2youli' / 'gamemd.exe'
PE = pefile.PE(str(EXE), fast_load=True)

def sections():
    return PE.sections

def va_to_off(va):
    for s in PE.sections:
        b = s.VirtualAddress + PE.OPTIONAL_HEADER.ImageBase
        if b <= va < b + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (va - b)
    raise KeyError(hex(va))

def read(va, n):
    o = va_to_off(va)
    with EXE.open('rb') as f:
        f.seek(o)
        return f.read(n)

def u32(va):
    return struct.unpack('<I', read(va, 4))[0]

def i8(va):
    return struct.unpack('<b', read(va, 1))[0]

def cstr(va, n=512):
    b = read(va, n)
    return b.split(b'\0', 1)[0].decode('latin1')

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.skipdata = True
MD.detail = True

def disasm(va, count=200, stop_ret=True, max_bytes=8192):
    out = []
    for i in MD.disasm(read(va, max_bytes), va):
        out.append(i)
        if len(out) >= count:
            break
        if stop_ret and (i.mnemonic in ('ret', 'retf') or i.mnemonic.startswith('ret ')):
            break
    return out

def fmt_insn(i):
    return f'{i.address:08X}  {i.bytes.hex(" "):<24s}  {i.mnemonic} {i.op_str}'.rstrip()

def fmt_block(va, **kw):
    return '\n'.join(fmt_insn(i) for i in disasm(va, **kw))

def dump_bytes(va, n=128):
    b = read(va, n)
    return '\n'.join(f'{va+j:08X}  ' + ' '.join(f'{x:02X}' for x in b[j:j+16]) for j in range(0, len(b), 16))

def rtti_from_col(col):
    """Return (td_va, name) from a plausible MSVC CompleteObjectLocator."""
    sig = u32(col)
    off, cdoff, td = struct.unpack('<iii', read(col+4, 12))
    if sig not in (0, 1) or abs(off) > 0x10000 or abs(cdoff) > 0x10000:
        return None
    try:
        nm_va = td + 8
        nm = cstr(nm_va, 256)
        if nm.startswith('.?AV') and nm.endswith('@@'):
            return td, nm
    except Exception:
        pass
    return None

def vtable_at(vtobj):
    """For a vftable object pointer address, return COL and RTTI when parseable."""
    try:
        col = u32(vtobj - 4)
    except Exception:
        return None, None
    r = rtti_from_col(col)
    if r:
        return col, r
    return None, None

def find_rdata_dword_refs(value, limit=10000):
    """All addresses in raw-backed sections whose dword == value."""
    hits = []
    for s in PE.sections:
        if not (s.Characteristics & 0x40000040):  # IMAGE_SCN_CNT_INITIALIZED_DATA|MEM_READ
            continue
        base = PE.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        raw = s.PointerToRawData
        n = min(s.SizeOfRawData, s.Misc_VirtualSize or s.SizeOfRawData)
        if n <= 0 or raw <= 0:
            continue
        data = read(base, n)
        for j in range(0, len(data)-3, 4):
            if struct.unpack_from('<I', data, j)[0] == value:
                hits.append(base+j)
                if len(hits) >= limit:
                    return hits
    return hits

def find_vtable_containing(func_va):
    """Find vftable bases whose slot value equals func_va; infer base by scanning back to COL."""
    found = []
    for ref in find_rdata_dword_refs(func_va):
        # Scan backward for a dword at p where p is a plausible COL pointer and p+4..ref are contiguous slots.
        best = None
        for p in range(ref-4, max(0, ref-4*128)-1, -4):
            try:
                col = u32(p)
            except Exception:
                continue
            r = rtti_from_col(col)
            if r:
                best = (p+4, col, r, (ref-(p+4))//4)
                break
        found.append((ref, best))
    return found

def imm32_operands(insns):
    out = []
    for i in insns:
        for op in i.operands:
            if op.type == X86_OP_IMM and 0 <= op.imm <= 0xffffffff:
                out.append((i.address, op.imm, i.mnemonic, i.op_str))
    return out

def section_of(va):
    for s in PE.sections:
        b = PE.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        if b <= va < b + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.Name.decode('latin1').rstrip('\0')
    return '?'
