# -*- coding: utf-8 -*-
"""a-S05-KPROVED3 独立审计 · 自写基座（不 import 任何对应卡 work 代码）
只做：PE 装载 / VA<->文件偏移 / 按 VA 取字节 / 段范围 / RTTI 链校验。
"""
import hashlib
import struct

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"


class PE:
    def __init__(self, path=EXE):
        with open(path, "rb") as f:
            self.buf = f.read()
        self.sha = hashlib.sha256(self.buf).hexdigest().upper()
        self.size = len(self.buf)
        if self.sha != EXPECT_SHA:
            raise SystemExit("SHA-256 mismatch: %s" % self.sha)
        pe_off = struct.unpack_from("<I", self.buf, 0x3C)[0]
        if self.buf[pe_off:pe_off + 4] != b"PE\0\0":
            raise SystemExit("not PE")
        coff = pe_off + 4
        nsec = struct.unpack_from("<H", self.buf, coff + 2)[0]
        optsz = struct.unpack_from("<H", self.buf, coff + 16)[0]
        opt = coff + 20
        magic = struct.unpack_from("<H", self.buf, opt)[0]
        if magic != 0x10B:
            raise SystemExit("not PE32")
        self.image_base = struct.unpack_from("<I", self.buf, opt + 28)[0]
        self.entry_rva = struct.unpack_from("<I", self.buf, opt + 16)[0]
        self.size_of_image = struct.unpack_from("<I", self.buf, opt + 56)[0]
        self.nsec = nsec
        self.secs = []
        so = opt + optsz
        for i in range(nsec):
            b = so + i * 40
            name = self.buf[b:b + 8].rstrip(b"\0").decode("latin1")
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", self.buf, b + 8)
            chars = struct.unpack_from("<I", self.buf, b + 36)[0]
            self.secs.append(dict(name=name, va=self.image_base + vaddr,
                                  vsize=vsize, rawptr=rawptr, rawsize=rawsize,
                                  chars=chars))

    def sec_of(self, va):
        for s in self.secs:
            if s["va"] <= va < s["va"] + max(s["vsize"], s["rawsize"]):
                return s
        return None

    def off(self, va):
        for s in self.secs:
            if s["va"] <= va < s["va"] + max(s["vsize"], s["rawsize"]):
                d = va - s["va"]
                if d >= s["rawsize"]:
                    return None
                return s["rawptr"] + d
        return None

    def u32(self, va):
        o = self.off(va)
        if o is None or o + 4 > self.size:
            return None
        return struct.unpack_from("<I", self.buf, o)[0]

    def u16(self, va):
        o = self.off(va)
        if o is None or o + 2 > self.size:
            return None
        return struct.unpack_from("<H", self.buf, o)[0]

    def u8(self, va):
        o = self.off(va)
        if o is None:
            return None
        return self.buf[o]

    def bytes_at(self, va, n):
        o = self.off(va)
        if o is None:
            return b""
        return self.buf[o:o + n]

    def cstr(self, va, maxn=512):
        o = self.off(va)
        if o is None:
            return None
        e = self.buf.find(b"\0", o, o + maxn)
        if e < 0:
            e = o + maxn
        try:
            return self.buf[o:e].decode("ascii")
        except UnicodeDecodeError:
            return None

    def is_code(self, va):
        t = self.text
        return t[0] <= va < t[1]

    def is_data(self, va):
        r = self.rdata
        return r[0] <= va < r[1]

    def is_mapped(self, va):
        """任意已映射且可读的段（RTTI 的 TypeDescriptor 落在 .data，不是 .rdata）"""
        return self.off(va) is not None


def load():
    pe = PE()
    for s in pe.secs:
        if s["name"] == ".text":
            pe.text = (s["va"], s["va"] + s["vsize"])
        elif s["name"] == ".rdata":
            pe.rdata = (s["va"], s["va"] + s["vsize"])
    # 全部「非可执行但已映射」的段，供 .rdata 类扫描
    pe.data_ranges = [(s["va"], s["va"] + min(s["vsize"], s["rawsize"]))
                      for s in pe.secs if not (s["chars"] & 0x20000000)]
    return pe


def rtti_of_table(pe, vt):
    """[vt-4]=COL -> [COL+0xC]=TD -> TD+8 内联名串。fail-closed：任一步不成立返回 None。
    实测本镜像 COL 布局：+0 signature=0 / +4 offset / +8 cdOffset / +0xC pTD / +0x10 pCD；
    TD 落在 .data（可写段），TD+0 是 type_info vftable 指针，TD+8 才是内联名串。"""
    col = pe.u32(vt - 4)
    if col is None or not pe.is_data(col):
        return None
    if pe.u32(col) != 0:
        return None
    td = pe.u32(col + 0xC)
    if td is None or not pe.is_mapped(td):
        return None
    nm = pe.cstr(td + 8, 256)
    if nm is None or not (nm.startswith(".?AV") or nm.startswith(".?AU")):
        return None
    return dict(col=col, td=td, name=nm)


if __name__ == "__main__":
    pe = load()
    print("sha", pe.sha)
    print("base", hex(pe.image_base), "size", pe.size)
    for s in pe.secs:
        print("%-9s va=%08X vsize=%8X raw=%8X" % (s["name"], s["va"], s["vsize"], s["rawsize"]))
    print("text", [hex(x) for x in pe.text])
    print("rdata", [hex(x) for x in pe.rdata])
