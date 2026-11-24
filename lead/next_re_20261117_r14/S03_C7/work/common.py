#!/usr/bin/env python3
"""S03-C7 shared PE/disasm helpers. Self-written from raw bytes; no cross-card imports.
pefile 2024.8.26 + capstone 5.0.7 (skipdata=True). Read-only on gamemd.exe."""
import pefile, capstone, struct, hashlib

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000
_pe = pefile.PE(EXE)
DATA = _pe.__data__
SHA = hashlib.sha256(DATA).hexdigest().upper()

# section table: (name, va0, va1, raw_ptr, raw_size)
SECTIONS = []
for s in _pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    va0 = IB + s.VirtualAddress
    SECTIONS.append((nm, va0, va0 + s.Misc_VirtualSize,
                     s.PointerToRawData, s.PointerToRawData + s.SizeOfRawData))

SEC = {nm: (va0, va1, rp, re_) for nm, va0, va1, rp, re_ in SECTIONS}
TEXT_VA, TEXT_END, TEXT_RP, TEXT_RE = SEC['.text']
RDATA_VA, RDATA_END, RDATA_RP, RDATA_RE = SEC['.rdata']

def rva2off(rva):
    return _pe.get_offset_from_rva(rva)

def va2off(va):
    return rva2off(va - IB)

def in_text(va):
    return TEXT_VA <= va < TEXT_END

def in_rdata(va):
    return RDATA_VA <= va < RDATA_END

def u8(va):
    return DATA[va2off(va)]

def u16(va):
    return struct.unpack_from('<H', DATA, va2off(va))[0]

def u32(va):
    return struct.unpack_from('<I', DATA, va2off(va))[0]

def i32(va):
    return struct.unpack_from('<i', DATA, va2off(va))[0]

def ru32(va):
    try:
        return struct.unpack_from('<I', DATA, va2off(va))[0]
    except Exception:
        return None

def bytes_at(va, n):
    o = va2off(va)
    return DATA[o:o+n]

def cstr(va, n=128):
    o = va2off(va)
    end = DATA.find(b'\x00', o, o+n)
    if end < 0:
        end = o+n
    return DATA[o:end].decode('latin-1')

_MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
_MD.skipdata = True
_MD.detail = True

def md():
    return _MD

def disasm_range(start_va, end_va):
    off = va2off(start_va)
    for ins in _MD.disasm(DATA[off:off+(end_va-start_va)], start_va):
        yield ins

def disasm_n(start_va, nbytes):
    off = va2off(start_va)
    return list(_MD.disasm(DATA[off:off+nbytes], start_va))

def insn_str(ins):
    return f"{ins.address:08X}: {ins.bytes.hex():<20} {ins.mnemonic} {ins.op_str}".rstrip()

if __name__ == '__main__':
    print(f"SHA256={SHA}")
    print(f"ImageBase={IB:#x} .text=[{TEXT_VA:#x},{TEXT_END:#x}) .rdata=[{RDATA_VA:#x},{RDATA_END:#x})")
