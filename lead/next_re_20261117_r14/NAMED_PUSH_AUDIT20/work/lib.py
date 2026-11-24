"""NAMED_PUSH_AUDIT20 audit library (self-written)."""
import struct
import capstone
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGEBASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D


class Bin:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path, fast_load=False)
        self.data = open(path, "rb").read()
        assert self.pe.OPTIONAL_HEADER.ImageBase == IMAGEBASE
        self.secs = []
        for s in self.pe.sections:
            self.secs.append((
                s.Name.rstrip(b"\0").decode("latin1"),
                s.VirtualAddress + IMAGEBASE,
                s.VirtualAddress + IMAGEBASE + max(s.Misc_VirtualSize, s.SizeOfRawData),
                s.PointerToRawData,
                s.SizeOfRawData,
            ))
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        self.md.skipdata = True
        self.md.detail = True

    def off(self, va):
        for name, lo, hi, praw, rawsz in self.secs:
            if lo <= va < hi:
                d = va - lo
                return praw + d if d < rawsz else None
        return None

    def secname(self, va):
        for name, lo, hi, praw, rawsz in self.secs:
            if lo <= va < hi:
                return name
        return None

    def u8(self, va):
        o = self.off(va)
        return None if o is None else self.data[o]

    def u32(self, va):
        o = self.off(va)
        if o is None or o + 4 > len(self.data):
            return None
        return struct.unpack_from("<I", self.data, o)[0]

    def i32(self, va):
        v = self.u32(va)
        return None if v is None else struct.unpack("<i", struct.pack("<I", v))[0]

    def cstr(self, va, maxlen=200):
        o = self.off(va)
        if o is None:
            return None
        e = self.data.find(b"\0", o, o + maxlen)
        if e < 0:
            return None
        return self.data[o:e].decode("latin1")

    def bytes_at(self, va, n):
        o = self.off(va)
        return b"" if o is None else self.data[o:o + n]

    def hexat(self, va, n):
        return self.bytes_at(va, n).hex(" ")

    # ------------- linear sweep -------------
    def sweep(self):
        if getattr(self, "_sw", None):
            return self._sw
        o = self.off(TEXT_LO)
        blob = self.data[o:o + (TEXT_HI - TEXT_LO)]
        instrs = list(self.md.disasm(blob, TEXT_LO))
        by = {i.address: i for i in instrs}
        self._sw = (instrs, by)
        return self._sw

    def addrs(self):
        if getattr(self, "_addrs", None) is None:
            self._addrs = [i.address for i in self.sweep()[0]]
        return self._addrs

    def func(self, va, maxbytes=0x600):
        """Linear disasm from va up to first ret (or maxbytes)."""
        o = self.off(va)
        if o is None:
            return []
        blob = self.data[o:o + maxbytes]
        out = []
        for ins in self.md.disasm(blob, va):
            out.append(ins)
            if ins.mnemonic == "ret":
                break
        return out

    def func_back(self, va):
        """Function start: previous terminator + skip padding, via sweep."""
        import bisect
        addrs = self.addrs()
        i = bisect.bisect_right(addrs, va) - 1
        if i < 0:
            return None
        instrs = self.sweep()[0]
        k = i
        while k >= 0:
            if instrs[k].mnemonic in ("ret", "jmp", "int3", "hlt"):
                break
            k -= 1
        j = k + 1
        while j < len(instrs) and instrs[j].mnemonic in ("nop", "int3", "hlt", "lea") and instrs[j].size == 1:
            j += 1
        return instrs[j].address if j < len(instrs) else None

    def dis(self, va, count=10):
        o = self.off(va)
        if o is None:
            return []
        return [i for i in self.md.disasm(self.data[o:o + 16 * count + 16], va)][:count]

    def instart(self, va):
        """Instruction (sweep) covering va."""
        import bisect
        addrs = self.addrs()
        i = bisect.bisect_right(addrs, va) - 1
        if i < 0:
            return None
        ins = self.sweep()[0][i]
        return ins if ins.address <= va < ins.address + ins.size else None

    # ------------- scans -------------
    def find_dword(self, value, secfilter=None):
        hits = []
        needle = struct.pack("<I", value)
        for name, lo, hi, praw, rawsz in self.secs:
            if secfilter and name != secfilter:
                continue
            blob = self.data[praw:praw + rawsz]
            s = 0
            while True:
                i = blob.find(needle, s)
                if i < 0:
                    break
                hits.append(lo + i)
                s = i + 1
        return hits

    def writers_of_imm(self, value):
        """Instruction sites in .text that encode `value` as an immediate (via sweep boundaries)."""
        res = []
        for va in self.find_dword(value, secfilter=".text"):
            ins = self.instart(va)
            if ins is None:
                res.append({"imm_at": va, "ins": None, "text": "<undecodable>", "bytes": self.hexat(va - 4, 8)})
            else:
                res.append({"imm_at": va, "ins": ins, "ins_va": ins.address,
                            "text": f"{ins.mnemonic} {ins.op_str}", "bytes": ins.bytes.hex(" "),
                            "delta": va - ins.address})
        return res

    def callers_of(self, target):
        """Direct call rel32 sites to target (exhaustive via 0xE8 sweep on instruction boundaries)."""
        out = []
        instrs, _ = self.sweep()
        for ins in instrs:
            if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
                if (ins.operands[0].imm & 0xFFFFFFFF) == target:
                    out.append(ins.address)
        return out

    def callers_of_all(self):
        instrs, _ = self.sweep()
        m = {}
        for ins in instrs:
            if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
                m.setdefault(ins.operands[0].imm & 0xFFFFFFFF, []).append(ins.address)
        return m

    # ------------- RTTI -------------
    def rtti(self, vt):
        col = self.u32(vt - 4)
        info = {"vt": vt, "col": col, "offset": None, "pTD": None, "pCHD": None, "name": None, "notes": []}
        if col is None:
            info["notes"].append("no COL read")
            return info
        info["offset"] = self.u32(col + 4)
        info["pTD"] = self.u32(col + 0xC)
        info["pCHD"] = self.u32(col + 0x10)
        if info["pTD"] and info["pTD"] >= IMAGEBASE:
            info["name"] = self.cstr(info["pTD"] + 8)
            info["td8_u32"] = self.u32(info["pTD"] + 8)
        else:
            info["notes"].append(f"pTD={info['pTD']} not abs VA")
        if info["pCHD"] is not None and info["pCHD"] < IMAGEBASE and info["pCHD"] != 0:
            info["notes"].append(f"pCHD={info['pCHD']:#x} suspicious")
        return info

    def slot_holding(self, vt, entry, n=256):
        res = []
        for i in range(n):
            v = self.u32(vt + 4 * i)
            if v is None:
                break
            if v == entry:
                res.append(i)
        return res

    def vt_dump(self, vt, n=24):
        out = []
        for i in range(n):
            v = self.u32(vt + 4 * i)
            out.append((i, v))
            if v in (None, 0):
                break
        return out

    def push_sites(self, target):
        out = []
        for va in self.find_dword(target, secfilter=".text"):
            o = self.off(va - 1)
            if o is not None and self.data[o] == 0x68:
                out.append(va - 1)
        return sorted(out)


def f(ins):
    return "<none>" if ins is None else f"{ins.address:08X}  {ins.bytes.hex(' '):<20} {ins.mnemonic} {ins.op_str}"


def show(ins_list, indent="  "):
    return "\n".join(indent + f(i) for i in ins_list)


if __name__ == "__main__":
    b = Bin()
    for s in b.secs:
        print(s[0], hex(s[1]), hex(s[2]), hex(s[3]), hex(s[4]))
