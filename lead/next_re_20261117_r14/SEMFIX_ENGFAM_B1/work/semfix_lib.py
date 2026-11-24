"""SEMFIX-ENGFAM: self-contained PE/VA/disassembly helpers.

Read-only on D:\\Project\\ra2-campaign-forge\\ra2youli\\gamemd.exe.
All evidence produced by this directory is derived from these helpers, not
transcribed from the reference audits.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import capstone
import pefile

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
COVERAGE = Path(
    r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
)


class Bin:
    def __init__(self, path: Path = EXE):
        self.path = path
        self.buf = path.read_bytes()
        self.sha256 = hashlib.sha256(self.buf).hexdigest().upper()
        if self.sha256 != EXPECT_SHA:
            raise SystemExit(f"SHA-256 mismatch: {self.sha256}")
        self.pe = pefile.PE(str(path), fast_load=False)
        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase
        self.entry = self.image_base + self.pe.OPTIONAL_HEADER.AddressOfEntryPoint
        self.sections = []
        for s in self.pe.sections:
            start = self.image_base + s.VirtualAddress
            vend = start + max(s.Misc_VirtualSize, s.SizeOfRawData)
            self.sections.append(
                {
                    "name": s.Name.rstrip(b"\0").decode("latin1"),
                    "rva": s.VirtualAddress,
                    "vstart": start,
                    "vsize": s.Misc_VirtualSize,
                    "raw_size": s.SizeOfRawData,
                    "raw_ptr": s.PointerToRawData,
                    "vend": vend,
                }
            )
        t = self.section(".text")
        self.text_start = t["vstart"]
        self.text_end = t["vstart"] + t["vsize"]

    def section(self, name: str) -> dict:
        for s in self.sections:
            if s["name"] == name:
                return s
        raise SystemExit(f"section {name} not found")

    def sec_of(self, va: int) -> dict | None:
        for s in self.sections:
            if s["vstart"] <= va < s["vend"]:
                return s
        return None

    def is_bss_va(self, va: int) -> bool:
        s = self.sec_of(va)
        return bool(s and s["raw_size"] == 0 and s["vsize"] > 0)

    def in_text(self, va: int, n: int = 1) -> bool:
        return self.text_start <= va and va + n <= self.text_end

    def data(self, va: int, n: int) -> bytes:
        d = self.pe.get_data(va - self.image_base, n)
        if len(d) != n:
            raise SystemExit(f"short read at {va:#010x}: want {n}, got {len(d)}")
        return d

    def u32(self, va: int) -> int:
        return int.from_bytes(self.data(va, 4), "little")

    def i32(self, va: int) -> int:
        return int.from_bytes(self.data(va, 4), "little", signed=True)

    def cstr(self, va: int, maxlen: int = 256) -> str:
        out = bytearray()
        for off in range(0, maxlen, 64):
            chunk = self.data(va + off, min(64, maxlen - off))
            if b"\0" in chunk:
                out += chunk.split(b"\0", 1)[0]
                break
            out += chunk
        try:
            return out.decode("latin1")
        except UnicodeDecodeError:
            return ""

    def text_bytes(self) -> bytes:
        return self.data(self.text_start, self.text_end - self.text_start)

    def rtti(self, vt_va: int) -> dict:
        col = self.u32(vt_va - 4)
        td = self.u32(col + 0x0C)
        name_va = td + 8
        return {
            "vt": vt_va,
            "col": col,
            "td": td,
            "name_va": name_va,
            "name": self.cstr(name_va),
            "col_bytes": self.data(col, 16).hex().upper(),
            "td_bytes": self.data(td, 24).hex().upper(),
        }

    def disasm(self, start: int, size: int):
        return list(md().disasm(self.data(start, size), start))


def md() -> capstone.Cs:
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = True
    return m


def hx(va: int) -> str:
    return f"{va:08X}"


def hbytes(b: bytes) -> str:
    return " ".join(f"{x:02X}" for x in b)


def load_target_rows() -> list[list[str]]:
    """Same semantic filter as the PowerShell command quoted in REPORT.md."""
    import re

    rows = []
    for line in COVERAGE.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) < 6:
            continue
        if re.search(r"unproven|unverified|not proven", p[3], re.I):
            rows.append(p)
    return rows
