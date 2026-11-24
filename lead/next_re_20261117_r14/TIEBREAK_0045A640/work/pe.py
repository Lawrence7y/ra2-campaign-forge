"""Minimal, self-written PE32 reader for gamemd.exe (read-only).

Deliberately does NOT use pefile: everything below is parsed from the raw
file bytes with struct only, so every address used by the other scripts is
traceable to an offset in the on-disk image.

Address model
-------------
VA -> file offset uses the section table.  For the .rdata/.text/data sections
of this binary va - virtualaddress + pointertorawdata works because
sizeofrawdata == virtualsize for the relevant ranges; the helpers below still
check the range and fail loudly instead of silently reading garbage.
"""
import hashlib
import struct
import sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE_DEFAULT = 0x00400000


class PE:
    def __init__(self, path=EXE):
        self.path = path
        with open(path, "rb") as f:
            self.buf = f.read()
        self.sha256 = hashlib.sha256(self.buf).hexdigest().upper()
        self._parse_headers()
        self._parse_sections()

    # ---------- headers ----------
    def _parse_headers(self):
        b = self.buf
        if b[:2] != b"MZ":
            raise SystemExit("not MZ")
        e_lfanew = struct.unpack_from("<I", b, 0x3C)[0]
        if b[e_lfanew:e_lfanew + 4] != b"PE\0\0":
            raise SystemExit("not PE")
        coff = e_lfanew + 4
        (self.machine, self.nsec, self.timestamp, self.psymtab, self.nsyms,
         self.opt_size, self.characteristics) = struct.unpack_from("<HHIIIHH", b, coff)
        opt = coff + 20
        self.opt_magic = struct.unpack_from("<H", b, opt)[0]
        self.image_base = struct.unpack_from("<I", b, opt + 28)[0]
        self.size_of_code = struct.unpack_from("<I", b, opt + 4)[0]
        self.entry_point = struct.unpack_from("<I", b, opt + 16)[0]
        self.nrva = struct.unpack_from("<I", b, opt + 92)[0]
        self.sect_table = opt + self.opt_size

    def _parse_sections(self):
        self.sections = []
        for i in range(self.nsec):
            off = self.sect_table + 40 * i
            name = self.buf[off:off + 8].rstrip(b"\0").decode("latin1")
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", self.buf, off + 8)
            chars = struct.unpack_from("<I", self.buf, off + 36)[0]
            self.sections.append(dict(name=name, vsize=vsize, vaddr=vaddr,
                                      rawsize=rawsize, rawptr=rawptr, chars=chars))

    # ---------- conversion ----------
    #  section table holds RVA; every VA handed in here is image_base + RVA.
    def sec_of(self, va):
        rva = va - self.image_base
        for s in self.sections:
            if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rawsize"]):
                return s
        return None

    def in_raw(self, va, n=1):
        """True iff [va, va+n) is present in on-disk bytes (vs zero-filled tail)."""
        s = self.sec_of(va)
        if s is None:
            return False
        d = (va - self.image_base) - s["vaddr"]
        return d + n <= s["rawsize"]

    def off(self, va, n=1):
        s = self.sec_of(va)
        if s is None:
            raise SystemExit(f"VA {va:#x} not in any section")
        d = (va - self.image_base) - s["vaddr"]
        if d + n > s["rawsize"]:
            raise SystemExit(f"VA {va:#x}+{n} beyond raw data of {s['name']} "
                             f"(rawsize {s['rawsize']:#x}, delta {d:#x})")
        return s["rawptr"] + d

    def u8(self, va):
        return self.buf[self.off(va, 1)]

    def u16(self, va):
        return struct.unpack_from("<H", self.buf, self.off(va, 2))[0]

    def u32(self, va):
        return struct.unpack_from("<I", self.buf, self.off(va, 4))[0]

    def i32(self, va):
        return struct.unpack_from("<i", self.buf, self.off(va, 4))[0]

    def bytes_at(self, va, n):
        return self.buf[self.off(va, n):self.off(va, n) + n]

    def hexdump(self, va, n, base_va=None):
        base_va = va if base_va is None else base_va
        out = []
        data = self.bytes_at(va, n)
        for i in range(0, len(data), 16):
            chunk = data[i:i + 16]
            hx = " ".join(f"{c:02X}" for c in chunk)
            asc = "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)
            out.append(f"{va + i:08X}  {hx:<47}  {asc}")
        return "\n".join(out)

    def cstr(self, va, maxlen=120):
        s = self.sec_of(va)
        if s is None:
            return None
        start = self.off(va, 1)
        out = bytearray()
        for i in range(maxlen):
            if start + i >= len(self.buf):
                break
            c = self.buf[start + i]
            if c == 0:
                break
            out.append(c)
        return out.decode("latin1")

    # ---------- rtti ----------
    def rtti_of_vtable(self, vt_va):
        """[vt-4]=COL, [COL+0xC]=TD, TD+8 = inline name string (R14_COMMON §8.2 技术⑦)."""
        res = {"vt": vt_va}
        try:
            col = self.u32(vt_va - 4)
            res["col"] = col
            if self.sec_of(col) is None:
                res["error"] = "COL not in image"
                return res
            td = self.u32(col + 0xC)
            res["td"] = td
            if self.sec_of(td) is None:
                res["error"] = "TD not in image"
                return res
            name = self.cstr(td + 8)
            res["name"] = name
            if not (name and (name.startswith(".?AV") or name.startswith(".?AU"))):
                res["error"] = f"TD+8 not a mangled name: {name!r}"
        except SystemExit as e:
            res["error"] = str(e)
        return res

    def summary(self):
        L = [f"path        {self.path}",
             f"sha256      {self.sha256}",
             f"image_base  {self.image_base:#010x}",
             f"entry       {self.image_base + self.entry_point:#010x}",
             f"sections    {self.nsec}"]
        for s in self.sections:
            L.append(f"  {s['name']:<8} va {self.image_base + s['vaddr']:#010x} "
                     f"vsize {s['vsize']:#09x} raw {s['rawsize']:#09x} @{s['rawptr']:#09x}")
        return "\n".join(L)


def open_pe(expect_prefix="73201CC0", expect_suffix="F67476"):
    p = PE()
    if not (p.sha256.startswith(expect_prefix) and p.sha256.endswith(expect_suffix)):
        raise SystemExit(f"SHA-256 mismatch: {p.sha256}")
    return p


if __name__ == "__main__":
    p = open_pe()
    print(p.summary())
    print("stdout-encoding", sys.stdout.encoding)
