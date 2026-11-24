"""Self-written common module for S03_C6 RE analysis.
Do NOT import from any other card's work/ directory.
Loads gamemd.exe read-only (SHA verified), maps RVA<->file offset, u32/byte reads, capstone disasm.
"""
import hashlib, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

def sha256(path=EXE):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

_pe = None
_data = None
def get_pe():
    global _pe, _data
    if _pe is None:
        _pe = pefile.PE(EXE, fast_load=True)
        with open(EXE, "rb") as f:
            _data = f.read()
    return _pe

def rva2off(rva):
    pe = get_pe()
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None

def va2off(va):
    return rva2off(va - IMAGE_BASE)

def read_bytes(va, n):
    get_pe()
    off = va2off(va)
    if off is None:
        return None
    return _data[off:off+n]

def u32(va):
    b = read_bytes(va, 4)
    if b is None or len(b) < 4:
        return None
    return struct.unpack("<I", b)[0]

def u16(va):
    b = read_bytes(va, 2)
    if b is None or len(b) < 2:
        return None
    return struct.unpack("<H", b)[0]

def u8(va):
    b = read_bytes(va, 1)
    if b is None:
        return None
    return b[0]

def cstr(va, maxn=200):
    get_pe()
    off = va2off(va)
    if off is None:
        return None
    end = _data.find(b"\x00", off, off+maxn)
    if end < 0:
        end = off+maxn
    return _data[off:end].decode("latin-1", "replace")

def text_section():
    pe = get_pe()
    for s in pe.sections:
        if b".text" in s.Name:
            return s
    return None

MD = None
def md():
    global MD
    if MD is None:
        MD = Cs(CS_ARCH_X86, CS_MODE_32)
        MD.detail = True
        MD.skipdata = True
    return MD

def disasm_va(start_va, max_bytes=8192):
    get_pe()
    off = va2off(start_va)
    if off is None:
        return
    for insn in md().disasm(_data[off:off+max_bytes], start_va):
        yield insn

if __name__ == "__main__":
    print("sha256:", sha256())
    print("match:", sha256().upper() == EXPECT_SHA)
    s = text_section()
    print(".text VA=%08X VSize=%d RawSize=%d RawPtr=%d" % (
        IMAGE_BASE + s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData))
