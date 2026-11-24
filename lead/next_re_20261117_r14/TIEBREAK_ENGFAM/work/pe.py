"""Self-written minimal PE32 reader (struct only) for gamemd.exe -- read only.

Written fresh for TIEBREAK-ENGFAM.  Every VA below is resolved through the
section table of the on-disk image, so each byte cited in the report can be
traced back to a file offset.  pefile is used only as an independent
cross-check of the import directory (see s3).
"""
import hashlib
import struct

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"


class PE:
    def __init__(self, path=EXE):
        self.path = path
        with open(path, "rb") as f:
            self.buf = f.read()
        self.sha256 = hashlib.sha256(self.buf).hexdigest().upper()
        self._headers()
        self._sections()

    def _headers(self):
        b = self.buf
        assert b[:2] == b"MZ"
        e = struct.unpack_from("<I", b, 0x3C)[0]
        assert b[e:e + 4] == b"PE\0\0"
        coff = e + 4
        (self.machine, self.nsec, _ts, _sp, _ns, self.optsz,
         self.chars) = struct.unpack_from("<HHIIIHH", b, coff)
        opt = coff + 20
        self.magic = struct.unpack_from("<H", b, opt)[0]
        self.image_base = struct.unpack_from("<I", b, opt + 28)[0]
        self.entry_rva = struct.unpack_from("<I", b, opt + 16)[0]
        self.sect_tab = opt + self.optsz
        # data directories: RVA/size pairs, 8 entries before any extension
        self.dd = []
        for i in range(16):
            rva, sz = struct.unpack_from("<II", b, opt + 96 + 8 * i)
            self.dd.append((rva, sz))

    def _sections(self):
        self.secs = []
        for i in range(self.nsec):
            o = self.sect_tab + 40 * i
            nm = self.buf[o:o + 8].rstrip(b"\0").decode("latin1")
            vsz, va, rsz, rp = struct.unpack_from("<IIII", self.buf, o + 8)
            ch = struct.unpack_from("<I", self.buf, o + 36)[0]
            self.secs.append(dict(name=nm, vsz=vsz, va=va, rsz=rsz, rp=rp,
                                  chars=ch, vstart=self.image_base + va,
                                  vend=self.image_base + va + max(vsz, rsz)))

    # ---- address model -------------------------------------------------
    def sec(self, va):
        for s in self.secs:
            if s["vstart"] <= va < s["vend"]:
                return s
        return None

    def mapped(self, va, n=1):
        s = self.sec(va)
        if s is None:
            return False
        d = va - s["vstart"]
        return d + n <= s["rsz"]

    def off(self, va, n=1):
        s = self.sec(va)
        if s is None:
            raise SystemExit(f"VA {va:#010x} outside every section")
        d = va - s["vstart"]
        if d + n > s["rsz"]:
            raise SystemExit(f"VA {va:#010x}+{n} past raw of {s['name']}")
        return s["rp"] + d

    def u8(self, va):
        return self.buf[self.off(va, 1)]

    def u16(self, va):
        return struct.unpack_from("<H", self.buf, self.off(va, 2))[0]

    def u32(self, va):
        return struct.unpack_from("<I", self.buf, self.off(va, 4))[0]

    def i32(self, va):
        return struct.unpack_from("<i", self.buf, self.off(va, 4))[0]

    def raw(self, va, n):
        o = self.off(va, n)
        return self.buf[o:o + n]

    def hexdump(self, va, n):
        d = self.raw(va, n)
        out = []
        for i in range(0, len(d), 16):
            c = d[i:i + 16]
            out.append(f"{va + i:08X}  {' '.join(f'{x:02X}' for x in c):<47}  "
                       + "".join(chr(x) if 32 <= x < 127 else "." for x in c))
        return "\n".join(out)

    def cstr(self, va, maxlen=200):
        if self.sec(va) is None:
            return None
        o = self.off(va, 1)
        e = o
        while e < len(self.buf) and self.buf[e] and e - o < maxlen:
            e += 1
        return self.buf[o:e].decode("latin1")

    def text(self):
        for s in self.secs:
            if s["name"] == ".text":
                return s
        raise SystemExit("no .text")

    # ---- RTTI ----------------------------------------------------------
    def rtti(self, vt_va):
        """[vt-4]=COL -> [COL+0xC]=TD -> TD+8 inline mangled name."""
        r = {"vt": vt_va}
        if not self.mapped(vt_va - 4, 4):
            r["err"] = "vt-4 unmapped"
            return r
        col = self.u32(vt_va - 4)
        r["col"] = col
        if self.sec(col) is None:
            r["err"] = f"COL {col:#x} not mapped"
            return r
        td = self.u32(col + 0xC)
        r["td"] = td
        if self.sec(td) is None:
            r["err"] = f"TD {td:#x} not mapped"
            return r
        nm = self.cstr(td + 8)
        r["name"] = nm
        if not (nm and nm[:4] in (".?AV", ".?AU")):
            r["err"] = f"TD+8 not mangled: {nm!r}"
        return r


def open_pe():
    p = PE()
    if p.sha256 != EXPECT:
        raise SystemExit(f"SHA-256 MISMATCH: {p.sha256}")
    return p


if __name__ == "__main__":
    p = open_pe()
    print("sha256", p.sha256, "-> OK, matches card")
    print("image_base", hex(p.image_base), "entry", hex(p.image_base + p.entry_rva))
    for s in p.secs:
        print(f"  {s['name']:<8} {s['vstart']:#010x}..{s['vend']:#010x}")
    t = p.text()
    print("text", hex(t["vstart"]), hex(t["vend"]))
