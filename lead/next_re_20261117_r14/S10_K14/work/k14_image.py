from __future__ import annotations
import hashlib, os
from datetime import datetime, timezone, timedelta
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_DETAIL, CS_OPT_SKIPDATA

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATL = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
LOCAL_TZ = timezone(timedelta(hours=8))

def now():
    return datetime.now(LOCAL_TZ).isoformat(timespec="microseconds")

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest().upper()

class Image:
    def __init__(self, path=EXE):
        self.path = path
        self.data = open(path, "rb").read()
        self.pe = pefile.PE(data=self.data, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.md = Cs(CS_ARCH_X86, CS_MODE_32)
        self.md.detail = True
        self.md.skipdata = True

    def off(self, va, size=1):
        rva = va - self.base
        for s in self.pe.sections:
            start = s.VirtualAddress
            end = start + max(s.Misc_VirtualSize, s.SizeOfRawData)
            if start <= rva and rva + size <= end:
                delta = rva - start
                if delta + size > s.SizeOfRawData:
                    raise KeyError(f"VA {va:#x} is virtual-only (BSS)")
                return s.PointerToRawData + delta
        raise KeyError(f"VA {va:#x} not mapped")

    def read(self, va, size):
        o = self.off(va, size)
        return self.data[o:o+size]

    def u8(self, va): return int.from_bytes(self.read(va, 1), "little")
    def u16(self, va): return int.from_bytes(self.read(va, 2), "little")
    def u32(self, va): return int.from_bytes(self.read(va, 4), "little")
    def i32(self, va): return int.from_bytes(self.read(va, 4), "little", signed=True)

    def disasm(self, va, count=200):
        code = self.read(va, max(16, count * 16))
        return list(self.md.disasm(code, va, count=count))

    def disasm_range(self, start, end):
        code = self.read(start, end-start)
        return list(self.md.disasm(code, start))

def operand_text(ins):
    return ins.op_str

def imm_operands(ins):
    out = []
    for op in ins.operands:
        if op.type == capstone.x86.X86_OP_IMM:
            out.append(op.imm)
    return out

# imported lazily to keep simple scripts quiet
import capstone.x86
