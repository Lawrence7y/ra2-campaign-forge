"""独立审计工具（异族）。只读 gamemd.exe，自建 PE 映射 + capstone(skipdata=True)。"""
import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000

class Img:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path, fast_load=True)
        self.pe.parse_data_directories()
        self.size = self.pe.OPTIONAL_HEADER.SizeOfImage
        self.buf = bytearray(self.size)
        self.secs = []
        for s in self.pe.sections:
            va = s.VirtualAddress
            raw = s.PointerToRawData
            sz = s.SizeOfRawData
            vsz = s.Misc_VirtualSize
            data = s.get_data() if sz else b""
            self.buf[va:va+len(data)] = data
            self.secs.append((s.Name.rstrip(b"\0").decode(errors="replace"), IB+va, IB+va+vsz, IB+va+len(data)))
        self.md = Cs(CS_ARCH_X86, CS_MODE_32)
        self.md.detail = False
        self.md.skipdata = True

    def sec_of(self, va):
        for n, a, b, c in self.secs:
            if a <= va < max(b, c):
                return n
        return None

    def rd(self, va, n):
        o = va - IB
        if o < 0 or o+n > self.size:
            return b""
        return bytes(self.buf[o:o+n])

    def u32(self, va):
        b = self.rd(va, 4)
        return struct.unpack("<I", b)[0] if len(b) == 4 else None

    def i32(self, va):
        b = self.rd(va, 4)
        return struct.unpack("<i", b)[0] if len(b) == 4 else None

    def u16(self, va):
        b = self.rd(va, 2)
        return struct.unpack("<H", b)[0] if len(b) == 2 else None

    def cstr(self, va, maxn=256):
        o = va - IB
        if o < 0 or o >= self.size:
            return None
        e = self.buf.find(b"\0", o, min(o+maxn, self.size))
        if e < 0:
            return None
        return bytes(self.buf[o:e]).decode("latin1")

    def dis(self, va, count=200, stop_ret=True):
        code = self.rd(va, 16*count)
        out = []
        for i in self.md.disasm(code, va):
            out.append(i)
            if len(out) >= count:
                break
            if stop_ret and i.mnemonic in ("ret", "retn") :
                j = i.address + i.size
                # 允许 ret imm
                if self.rd(j,1) in (b"\xc3",) or True:
                    pass
                # 继续两三条以便看清 ret 后 padding? 不。直接停
                break
        return out

    def hexb(self, va, n):
        return " ".join(f"{b:02x}" for b in self.rd(va, n))

def fmt(ins):
    return f"{ins.address:08X}  {ins.bytes.hex():<24} {ins.mnemonic:<8} {ins.op_str}"
