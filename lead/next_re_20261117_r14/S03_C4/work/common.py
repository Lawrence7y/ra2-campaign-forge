#!/usr/bin/env python3
"""S03-C4 shared PE/disasm helpers. Self-written from raw bytes; no imports from other cards' work/.
pefile 2024.8.26 + capstone 5.0.7 (skipdata=True)."""
import pefile, capstone, struct

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000
_pe = pefile.PE(EXE)
DATA = _pe.__data__
TEXT_VA = IB + _pe.sections[0].VirtualAddress
TEXT_VSIZE = _pe.sections[0].Misc_VirtualSize
TEXT_END = TEXT_VA + TEXT_VSIZE

def rva2off(rva):
    return _pe.get_offset_from_rva(rva)

def va2off(va):
    return rva2off(va - IB)

def in_text(va):
    return TEXT_VA <= va < TEXT_END

def u8(va):
    o = va2off(va); return DATA[o]

def u16(va):
    o = va2off(va); return struct.unpack_from('<H', DATA, o)[0]

def u32(va):
    o = va2off(va); return struct.unpack_from('<I', DATA, o)[0]

def i32(va):
    o = va2off(va); return struct.unpack_from('<i', DATA, o)[0]

def bytes_at(va, n):
    o = va2off(va); return DATA[o:o+n]

def cstr(va, n=256):
    o = va2off(va); end = DATA.find(b'\x00', o, o+n)
    if end < 0: end = o+n
    return DATA[o:end].decode('latin-1')

_MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
_MD.skipdata = True
_MD.detail = True

def disasm_range(start_va, end_va):
    """Yield capstone insns across [start,end) with skipdata=True."""
    off = va2off(start_va)
    nbytes = end_va - start_va
    for ins in _MD.disasm(DATA[off:off+nbytes], start_va):
        yield ins

def disasm_n(start_va, nbytes):
    off = va2off(start_va)
    return list(_MD.disasm(DATA[off:off+nbytes], start_va))

def insn_str(ins):
    return f"{ins.address:08X}: {ins.bytes.hex():<20} {ins.mnemonic} {ins.op_str}".rstrip()

if __name__ == '__main__':
    print(f"ImageBase={IB:#x} .text=[{TEXT_VA:#x},{TEXT_END:#x}) vsize={TEXT_VSIZE:#x}")
