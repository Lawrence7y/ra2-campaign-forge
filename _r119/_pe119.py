import struct
PATH = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
BUF = open(PATH, "rb").read()
def u16(o): return struct.unpack_from("<H", BUF, o)[0]
def u32(o): return struct.unpack_from("<I", BUF, o)[0]
class PE:
    def __init__(self):
        self.e_lfanew = u32(0x3c)
        assert BUF[self.e_lfanew:self.e_lfanew+4] == b"PE\0\0"
        coff = self.e_lfanew + 4
        self.machine = u16(coff); self.nsec = u16(coff+2); self.opt_size = u16(coff+16)
        opt = coff + 20
        self.magic = u16(opt); assert self.magic == 0x10b
        self.imagebase = u32(opt+28); self.sizeofimage = u32(opt+56)
        self.numberofrva_sizes = u32(opt+92)
        secoff = opt + self.opt_size
        self.secs = []
        for i in range(self.nsec):
            o = secoff + 40*i
            name = BUF[o:o+8].rstrip(b"\0").decode("latin1")
            vsize, rva, rawsize, raw = struct.unpack_from("<IIII", BUF, o+8)
            self.secs.append(dict(name=name, rva=rva, va=self.imagebase+rva, vsize=vsize,
                                  rawsize=rawsize, raw=raw, chars=u32(o+36)))
    def sec_of_va(self, va):
        for s in self.secs:
            if s["va"] <= va < s["va"] + s["rawsize"]: return s
        return None
    def va2off(self, va):
        s = self.sec_of_va(va); return None if not s else s["raw"] + (va - s["va"])
    def off2va(self, off):
        for s in self.secs:
            if s["raw"] <= off < s["raw"] + s["rawsize"]: return s["va"] + (off - s["raw"])
        return None
    def secname_of_off(self, off):
        for s in self.secs:
            if s["raw"] <= off < s["raw"] + s["rawsize"]: return s["name"]
        return None
    def sec_by_name(self, n):
        for s in self.secs:
            if s["name"] == n: return s
        return None
PE_ = PE()
def cstr(off, maxlen=400):
    e = BUF.find(b"\0", off, off+maxlen)
    return None if e < 0 else BUF[off:e]
