"""
S17-F1 reusable PE/capstone harness.
ImageBase 0x400000. Read-only on gamemd.exe.
capstone skipdata=True is MANDATORY (R14_COMMON §6 discipline #2).
boundary_check: when max_bytes exceeded -> 'unknown', NEVER False (discipline #3).
"""
import sys, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000

_pe = pefile.PE(EXE, fast_load=True)
_pe.parse_data_directories()

def sections():
    out = []
    for s in _pe.sections:
        name = s.Name.rstrip(b'\x00').decode('latin1')
        out.append((name, s.VirtualAddress + IB, s.Misc_VirtualSize,
                    s.PointerToRawData, s.SizeOfRawData, s.Characteristics))
    return out

def va2off(va):
    """VA -> file offset. General rule from E-W3-01 erratum."""
    for name, va_base, vsize, praw, rawsize, ch in sections():
        if va_base <= va < va_base + max(vsize, rawsize):
            d = va - va_base
            if d < rawsize:
                return praw + d
    # fall back for BSS-like / no raw data
    return None

def read(va, n):
    off = va2off(va)
    if off is None:
        return None
    with open(EXE, 'rb') as f:
        f.seek(off)
        return f.read(n)

def u32(va):
    b = read(va, 4)
    return None if b is None or len(b) < 4 else struct.unpack('<I', b)[0]

def iat_name(va):
    """Resolve a VA inside .idata to the imported symbol name via pefile."""
    for entry in _pe.DIRECTORY_ENTRY_IMPORT:
        dll = entry.dll.decode('latin1') if isinstance(entry.dll, bytes) else entry.dll
        for imp in entry.imports:
            if imp.address and imp.address == va and imp.name:
                return f"{dll}!{imp.name.decode('latin1')}"
    return None

_md = Cs(CS_ARCH_X86, CS_MODE_32)
_md.detail = True
_md.skipdata = True

def disasm(va, nbytes):
    b = read(va, nbytes)
    if b is None:
        return []
    return list(_md.disasm(b, va))

def disasm_insns(va, count):
    """Disassemble exactly `count` instructions from va (skipdata=True)."""
    b = read(va, count * 16 + 64)
    if b is None:
        return []
    out = []
    for ins in _md.disasm(b, va):
        out.append(ins)
        if len(out) >= count:
            break
    return out

def boundary_check(va, expected_hex, max_bytes=16):
    """Check that expected bytes appear at an instruction boundary within max_bytes
    from va. Returns True/False/'unknown'. If disassembly cannot reach va+max_bytes
    (i.e. capstone would bail), returns 'unknown' instead of False."""
    b = read(va, max_bytes + len(expected_hex)//2 + 8)
    if b is None:
        return 'unknown'
    insns = []
    cur = 0
    for ins in _md.disasm(b, va):
        insns.append(ins)
        if ins.address + ins.size >= va + max_bytes:
            break
    # if we never reached max_bytes window, it's inconclusive
    covered = max((ins.address + ins.size for ins in insns), default=va)
    if covered < va + max_bytes:
        return 'unknown'
    want = bytes.fromhex(expected_hex.replace(' ', ''))
    for ins in insns:
        ib = read(ins.address, ins.size)
        if ib == want:
            return True
    return False

def scan_rel32_calls(target, start_va=None, end_va=None):
    """Scan .text for E8/E9 rel32 whose destination == target.
    Returns list of (call_site_va, opcode_byte). Independent of atlas."""
    res = []
    for name, va_base, vsize, praw, rawsize, ch in sections():
        if not (ch & 0x20000000):  # IMAGE_SCN_CNT_CODE
            continue
        lo = va_base
        hi = va_base + rawsize
        if start_va is not None:
            lo = max(lo, start_va)
        if end_va is not None:
            hi = min(hi, end_va)
        data = read(lo, hi - lo)
        if data is None:
            continue
        for i in range(len(data) - 4):
            if data[i] in (0xE8, 0xE9):
                rel = struct.unpack('<i', data[i+1:i+5])[0]
                dest = lo + i + 5 + rel
                if dest == target:
                    res.append((lo + i, data[i]))
    return res

def scan_imm32_refs(target, start_va=None, end_va=None):
    """Scan all sections for little-endian dword == target (absolute refs / vtables)."""
    res = []
    for name, va_base, vsize, praw, rawsize, ch in sections():
        lo = va_base
        hi = va_base + rawsize
        if start_va is not None:
            lo = max(lo, start_va)
        if end_va is not None:
            hi = min(hi, end_va)
        data = read(lo, hi - lo)
        if data is None:
            continue
        pat = struct.pack('<I', target)
        pos = 0
        while True:
            j = data.find(pat, pos)
            if j < 0:
                break
            res.append((lo + j, name))
            pos = j + 1
    return res

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'sections':
        for s in sections():
            print(s)
