"""S20-K1 shared helpers. Byte-level, read-only against gamemd.exe.

Key conventions:
- All addresses are VA (ImageBase 0x400000).
- FileOffset = sec.PointerToRawData + (VA - sec.VirtualAddress).
- capstone always skipdata=True (discipline #2).
"""
import struct
import capstone
import pefile
import os

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000
HERE = os.path.dirname(os.path.abspath(__file__))
CARD = os.path.dirname(HERE)
EVID = os.path.join(CARD, "EVIDENCE")


class Bin:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path, fast_load=True)
        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.decode(errors="replace").rstrip("\x00")
            va = self.image_base + s.VirtualAddress
            self.sections.append(dict(
                name=name, va=va, vsize=s.Misc_VirtualSize,
                raw=s.PointerToRawData, rawsize=s.SizeOfRawData,
            ))
        self.by_name = {s["name"]: s for s in self.sections}

    def sec(self, name):
        return self.by_name[name]

    def sec_of(self, va):
        for s in self.sections:
            if s["va"] <= va < s["va"] + s["rawsize"]:
                return s
        return None

    def sec_range(self, name):
        s = self.sec(name)
        return (s["va"], s["va"] + s["rawsize"])

    def read(self, va, n):
        for s in self.sections:
            if s["va"] <= va and va + n <= s["va"] + s["rawsize"]:
                off = s["raw"] + (va - s["va"])
                return self.pe.__data__[off:off + n]
        raise ValueError("VA %08X+%d not in any raw range" % (va, n))

    def u32(self, va):
        return struct.unpack("<I", self.read(va, 4))[0]

    def u16(self, va):
        return struct.unpack("<H", self.read(va, 2))[0]

    def u8(self, va):
        return self.read(va, 1)[0]

    def in_text(self, va):
        lo, hi = self.sec_range(".text")
        return lo <= va < hi

    def in_rdata(self, va):
        lo, hi = self.sec_range(".rdata")
        return lo <= va < hi

    def section_bytes(self, name):
        s = self.sec(name)
        return self.pe.__data__[s["raw"]:s["raw"] + s["rawsize"]]


def md(detail=True, skipdata=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = detail
    m.skipdata = skipdata
    return m


def disasm_window(bin_, start, nbytes, skipdata=True):
    m = md(skipdata=skipdata)
    data = bin_.read(start, nbytes)
    return list(m.disasm(data, start))


def insn_text(insn):
    return "%s %s" % (insn.mnemonic, insn.op_str)


def write_text(name, text):
    path = os.path.join(EVID, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


def write_tsv(name, header, rows):
    path = os.path.join(EVID, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(header + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    return path
