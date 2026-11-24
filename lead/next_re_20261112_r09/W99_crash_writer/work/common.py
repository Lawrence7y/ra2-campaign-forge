# W99 common: PE load + VA<->off + linear disassembly helpers. READ-ONLY on gamemd.exe.
import pefile, capstone, struct, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
PE = pefile.PE(EXE, fast_load=True)
IMAGEBASE = PE.OPTIONAL_HEADER.ImageBase
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True

_secs = []
for s in PE.sections:
    _secs.append((IMAGEBASE + s.VirtualAddress, s.SizeOfRawData, s.Misc_VirtualSize,
                  s.Name.rstrip(b"\x00").decode("ascii", "replace"), s.PointerToRawData))

def secof(va):
    rva = va - IMAGEBASE
    for base, rawsz, virtsz, name, praw in _secs:
        if base <= va < base + max(rawsz, virtsz):
            return name, va - base + praw
    return None, None

def va2off(va):
    name, off = secof(va)
    return off

def read(va, n):
    o = va2off(va)
    if o is None:
        raise ValueError("VA not mapped: 0x%08X" % va)
    with open(EXE, "rb") as f:
        f.seek(o)
        return f.read(n)

def dword(va):
    b = read(va, 4)
    return struct.unpack("<I", b)[0], b

def disas(start_va, end_va):
    """Disassemble [start,end), return list of (va, bytes_hex, mnemonic, op_str, insn)"""
    code = read(start_va, end_va - start_va)
    out = []
    for insn in MD.disasm(code, start_va):
        out.append((insn.address, insn.bytes.hex().upper(), insn.mnemonic, insn.op_str, insn))
    return out

def find_funcs_containing(vas):
    """crude: report section for each va"""
    for va in vas:
        print("0x%08X -> section %s" % (va, secof(va)[0]))

if __name__ == "__main__":
    for base, rawsz, virtsz, name, praw in _secs:
        print("sec %-8s VA=0x%08X raw=0x%X virt=0x%X" % (name, base, rawsz, virtsz))
    print("ImageBase=0x%08X" % IMAGEBASE)
