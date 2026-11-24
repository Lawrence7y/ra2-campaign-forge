"""
S06-K1 shared helper: PE mapping + capstone (skipdata=True) disassembler.
All addresses are VA (ImageBase 0x400000). Read-only on the target.
"""
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

PE_PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(PE_PATH, fast_load=True)
pe.parse_data_directories()
IMAGE_BASE = pe.OPTIONAL_HEADER.ImageBase  # 0x400000

SECTIONS = []
for s in pe.sections:
    SECTIONS.append((s.VirtualAddress + IMAGE_BASE,
                     s.Misc_VirtualSize,
                     s.PointerToRawData,
                     s.SizeOfRawData,
                     s.Name.rstrip(b'\0').decode('latin1')))

def section_of(va):
    for v, vs, raw, rs, name in SECTIONS:
        if v <= va < v + max(vs, rs):
            return (v, vs, raw, rs, name)
    return None

def va_to_off(va):
    s = section_of(va)
    if not s:
        return None
    v, vs, raw, rs, name = s
    delta = va - v
    if delta >= rs:  # BSS / virtual-only
        return None
    return raw + delta

def read(va, n):
    off = va_to_off(va)
    if off is None:
        return b''
    return pe.get_data(off, n)

def u8(va):
    b = read(va, 1)
    return b[0] if b else None

def u16(va):
    import struct
    b = read(va, 2)
    return struct.unpack('<H', b)[0] if len(b) == 2 else None

def u32(va):
    import struct
    b = read(va, 4)
    return struct.unpack('<I', b)[0] if len(b) == 4 else None

def i32(va):
    import struct
    b = read(va, 4)
    return struct.unpack('<i', b)[0] if len(b) == 4 else None

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True          # MANDATORY (R14_COMMON §6 #2)
md.detail = True

def disasm(va, nbytes, count=None):
    """Return list of instructions starting at va, skipdata=True."""
    code = read(va, nbytes)
    out = []
    for ins in md.disasm(code, va):
        out.append(ins)
        if count and len(out) >= count:
            break
    return out

def fmt(ins):
    return f"{ins.address:08X}: {ins.bytes.hex():<20} {ins.mnemonic} {ins.op_str}".rstrip()

def find_bytes(pattern, start_va=None, end_va=None, section='.text'):
    """Yield VAs where raw byte pattern occurs in a given section."""
    sec = next((s for s in SECTIONS if s[4] == section), None)
    if not sec:
        return
    v, vs, raw, rs, name = sec
    data = pe.get_data(raw, rs)
    lo, hi = 0, rs
    if start_va is not None:
        lo = max(lo, start_va - v)
    if end_va is not None:
        hi = min(hi, end_va - v)
    idx = data.find(pattern, lo)
    while idx != -1 and idx < hi:
        yield v + idx
        idx = data.find(pattern, idx + 1, hi)

def text_bounds():
    sec = next((s for s in SECTIONS if s[4] == '.text'), None)
    return (sec[0], sec[0] + max(sec[1], sec[3])) if sec else (0, 0)

if __name__ == '__main__':
    print(f"ImageBase={IMAGE_BASE:#x}")
    for v, vs, raw, rs, name in SECTIONS:
        print(f"  {name:8} VA {v:#010x} .. {v+max(vs,rs):#010x} (raw {rs:#x}, virt {vs:#x})")
    print("text bounds:", [hex(x) for x in text_bounds()])
