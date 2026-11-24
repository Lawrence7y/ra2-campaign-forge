from __future__ import annotations
import hashlib, struct
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA, CS_OPT_ON

ROOT = Path(r"D:\Project\ra2-campaign-forge")
GAME = ROOT / "ra2youli" / "gamemd.exe"
COVER = ROOT / "lead" / "next_re_20261117_r14" / "COVERAGE" / "coverage.tsv"
BASE = ROOT / "lead" / "next_re_20261117_r14" / "S10_K7"
EV = BASE / "EVIDENCE"

class Image:
    def __init__(self, path=GAME):
        self.path=Path(path)
        self.data=self.path.read_bytes()
        self.pe=pefile.PE(data=self.data, fast_load=True)
        self.imagebase=self.pe.OPTIONAL_HEADER.ImageBase
        self.sections=[]
        for s in self.pe.sections:
            self.sections.append((s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData,s.Name.rstrip(b"\x00").decode("latin1")))
        self.cs=Cs(CS_ARCH_X86, CS_MODE_32)
        self.cs.detail=True
        self.cs.skipdata=True

    def off(self, va):
        rva=va-self.imagebase
        for vsize,rawsize,ptr,name in [(a,b,c,e) for a,b,c,d,e in self.sections]:
            r=rawsize if rawsize else vsize
            if vsize<=rva<vsize+max(0,0x1000-(vsize%0x1000 or 0x1000)):
                pass
        for vaddr,vsize,ptr,rawsize,name in self.sections:
            if vaddr <= rva < vaddr+max(vsize,rawsize):
                o=ptr+(rva-vaddr)
                if 0<=o<len(self.data): return o
        raise ValueError(f"unmapped VA {va:#x} RVA {rva:#x}")

    def read(self, va, n):
        o=self.off(va); return self.data[o:o+n]

    def u8(self,va): return self.read(va,1)[0]
    def u16(self,va): return struct.unpack("<H",self.read(va,2))[0]
    def u32(self,va): return struct.unpack("<I",self.read(va,4))[0]
    def i32(self,va): return struct.unpack("<i",self.read(va,4))[0]
    def cstr(self, va, n=256):
        b=self.read(va,n); return b.split(b"\x00",1)[0].decode("latin1")

    def disasm(self, va, n=0x200, maxins=80, stop_ret=True):
        out=[]
        for ins in self.cs.disasm(self.read(va,n),va):
            out.append(ins)
            if len(out)>=maxins: break
            if stop_ret and (ins.mnemonic.startswith("ret") or ins.mnemonic=="jmp"): break
        return out

    def fmt(self, ins):
        return f"{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic:<8} {ins.op_str}"

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest().upper()
