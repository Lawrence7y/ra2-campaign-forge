"""S06-K3 standalone PE/capstone helper. Read-only on gamemd.exe.
All addresses are VA (ImageBase 0x400000). skipdata=True mandatory (R14_COMMON s6#2).
"""
import pefile, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID

PE_PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(PE_PATH, fast_load=True)
pe.parse_data_directories()
IMAGE_BASE = pe.OPTIONAL_HEADER.ImageBase

SECTIONS = []
for s in pe.sections:
    SECTIONS.append((s.VirtualAddress + IMAGE_BASE, s.Misc_VirtualSize,
                     s.PointerToRawData, s.SizeOfRawData,
                     s.Name.rstrip(b'\0').decode('latin1')))

def section_of(va):
    for v, vs, raw, rs, name in SECTIONS:
        if v <= va < v + max(vs, rs):
            return (v, vs, raw, rs, name)
    return None

def in_text(va):
    s = section_of(va)
    return bool(s) and s[4] == '.text'

def va_to_off(va):
    s = section_of(va)
    if not s:
        return None
    v, vs, raw, rs, name = s
    delta = va - v
    return raw + delta if delta < rs else None

def read(va, n):
    off = va_to_off(va)
    return b'' if off is None else pe.get_data(off, n)

def u8(va):
    b = read(va, 1); return b[0] if b else None

def u16(va):
    b = read(va, 2); return struct.unpack('<H', b)[0] if len(b) == 2 else None

def u32(va):
    b = read(va, 4); return struct.unpack('<I', b)[0] if len(b) == 4 else None

def i32(va):
    b = read(va, 4); return struct.unpack('<i', b)[0] if len(b) == 4 else None

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.detail = True

def disasm(va, nbytes, count=None):
    code = read(va, nbytes)
    out = []
    for ins in md.disasm(code, va):
        out.append(ins)
        if count and len(out) >= count:
            break
    return out

def rn(reg):
    try:
        return md.reg_name(reg)
    except Exception:
        return None

def text_bounds():
    s = next((x for x in SECTIONS if x[4] == '.text'), None)
    return (s[0], s[0] + max(s[1], s[3])) if s else (0, 0)

# atlas entry->size
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
atlas = {}
with open(ATLAS, encoding='utf-8') as f:
    next(f)
    for ln in f:
        q = ln.rstrip('\n').split('\t')
        if len(q) >= 2:
            try:
                atlas[int(q[0], 16)] = int(q[1])
            except Exception:
                pass

def fn_end(entry, cap=0x1000):
    sz = atlas.get(entry, 0)
    return entry + (sz if 0 < sz <= cap else cap)
