#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C09 独立字节通道：自写 struct PE + capstone skipdata=True，按**操作码字节**分类
E8(call32)/E9(jmp32)/EB(jmp8) 直接目标（不读 op_str，不用 pefile）。

与 verify_core 通道（pefile + op_str 解析）不同源；与 collect 通道 A（atlas entry+size）不同源。
供 collect.py / gap_full.py 使用。capstone 全程 skipdata=True。
"""
import struct
import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"


class RawPE:
    def __init__(self, path=EXE):
        self.raw = open(path, "rb").read()
        d = self.raw
        peoff = struct.unpack_from("<I", d, 0x3C)[0]
        assert d[peoff:peoff + 4] == b"PE\0\0"
        coff = peoff + 4
        self.nsec = struct.unpack_from("<H", d, coff + 2)[0]
        so = struct.unpack_from("<H", d, coff + 16)[0]
        opt = coff + 20
        self.image_base = struct.unpack_from("<I", d, opt + 28)[0]
        self.sections = []
        st = opt + so
        for i in range(self.nsec):
            o = st + i * 40
            name = d[o:o + 8].rstrip(b"\x00").decode("latin1")
            vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", d, o + 8)
            self.sections.append(dict(name=name, va=self.image_base + va, rva=va,
                                      vsize=vsize, rawsize=rawsize, raw=rawptr))
        self.by = {s["name"]: s for s in self.sections}

    def text_blob(self):
        s = self.by[".text"]
        return s, self.raw[s["raw"]:s["raw"] + s["rawsize"]]

    def read(self, va, n):
        for s in self.sections:
            if s["va"] <= va and va + n <= s["va"] + max(s["rawsize"], s["vsize"]):
                off = s["raw"] + (va - s["va"])
                if off + n > len(self.raw):
                    raise ValueError("EOF")
                return self.raw[off:off + n]
        raise ValueError("va %08X no bytes" % va)

    def u32(self, va):
        return struct.unpack("<I", self.read(va, 4))[0]


def sweep(pe, want_jcc=False):
    """返回 (chans, stats)。chans={call32:{tgt:[site..]}, jmp32:..., jmp8:...}。
    按 insn.bytes 首字节 + rel 位移自算目标（不读 op_str）。capstone skipdata=True。
    """
    sec, data = pe.text_blob()
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.skipdata = True
    md.detail = False
    chans = {"call32": {}, "jmp32": {}, "jmp8": {}}
    if want_jcc:
        chans["jcc32"] = {}
    n = 0
    skipped = 0
    for insn in md.disasm(data, sec["va"]):
        if insn.id == 0:
            skipped += insn.size
            continue
        n += 1
        b = insn.bytes
        if not b:
            continue
        op = b[0]
        tgt = None
        ch = None
        if op == 0xE8 and len(b) == 5:
            tgt = (insn.address + 5 + struct.unpack("<i", b[1:5])[0]) & 0xFFFFFFFF
            ch = "call32"
        elif op == 0xE9 and len(b) == 5:
            tgt = (insn.address + 5 + struct.unpack("<i", b[1:5])[0]) & 0xFFFFFFFF
            ch = "jmp32"
        elif op == 0xEB and len(b) == 2:
            tgt = (insn.address + 2 + struct.unpack("<b", b[1:2])[0]) & 0xFFFFFFFF
            ch = "jmp8"
        elif want_jcc and op == 0x0F and len(b) == 6 and 0x80 <= b[1] <= 0x8F:
            tgt = (insn.address + 6 + struct.unpack("<i", b[2:6])[0]) & 0xFFFFFFFF
            ch = "jcc32"
        if ch is not None:
            chans[ch].setdefault(tgt, []).append(insn.address)
    stats = dict(insns=n, skipped_bytes=skipped, text_bytes=len(data),
                 text_va=sec["va"], text_end=sec["va"] + sec["rawsize"])
    return chans, stats
