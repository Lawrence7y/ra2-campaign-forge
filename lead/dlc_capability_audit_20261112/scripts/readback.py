"""Independent artifact read-back verification for a built ra2forge package.

Run as:  python -I -X utf8 <ABS_PATH_TO_THIS_FILE> <ABS_PACKAGE_DIR>

Deliberately uses ONLY the standard library (hashlib / zlib / struct / re) and
re-implements the plain TS/RA2 MIX index itself. It does NOT import ra2forge,
so it is an independent check of the bytes that actually landed on disk, not a
re-run of the builder's own self-checks.

Checks:
  - list every file in the package (what a "manifest-like" file could be)
  - full sha256 of every artifact, matched against BUILD_REPORT.txt's truncated
    "sha256=<16 hex>" lines
  - parse every *.MAP's [Basic] section (GBK) -> Name / NextScenario / EndOfGame
  - parse BATTLEMD98.INI -> [Battles] index, own section, Scenario, Description,
    absence of official battle-id sections
  - re-open expandmd98.mix, decode its plain index, compute CRC32 of the
    uppercased file names exactly as the tool does, verify the id set and that
    every map's bytes inside the MIX equal the loose *.MAP bytes, and verify
    that no known .INI name is present as an entry id
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
import zlib
from pathlib import Path

OFFICIAL_ID_RE = re.compile(r"^(?:ALL|SOV)\d+$", re.IGNORECASE)
INI_PROBES = ("BATTLEMD98.INI", "BATTLEMD.INI", "RULESmd.INI", "AI.INI")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def crc_hash(name: str) -> int:
    return zlib.crc32(name.upper().encode("ascii", "replace")) & 0xFFFFFFFF


def parse_ini(text: str) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    cur: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            cur = line[1:-1]
            sections.setdefault(cur, {})
            continue
        if cur is not None and "=" in line:
            k, _, v = line.partition("=")
            sections[cur][k.strip()] = v.strip()
    return sections


def basic_section(text: str) -> dict[str, str]:
    """Extract [Basic] key/value pairs only."""
    secs = parse_ini(text)
    return secs.get("Basic", {})


class MixIndex:
    def __init__(self, path: Path):
        self.path = path
        self.raw = path.read_bytes()
        first, flags = struct.unpack_from("<HH", self.raw, 0)
        if first != 0:
            raise ValueError("not a plain TS/RA2 MIX (first word != 0)")
        self.flags = flags
        self.count, self.body_size = struct.unpack_from("<HI", self.raw, 4)
        self.data_start = 10 + self.count * 12
        self.entries = []
        for i in range(self.count):
            hid, off, size = struct.unpack_from("<III", self.raw, 10 + i * 12)
            self.entries.append((hid, off, size))

    def get(self, hid: int) -> bytes | None:
        for eid, off, size in self.entries:
            if eid == hid:
                return self.raw[self.data_start + off: self.data_start + off + size]
        return None


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: readback.py <ABS_PACKAGE_DIR>", file=sys.stderr)
        return 2
    pkg = Path(sys.argv[1])
    if not pkg.is_dir():
        print(f"package dir not found: {pkg}", file=sys.stderr)
        return 2
    print(f"PACKAGE = {pkg}")
    files = sorted(p for p in pkg.iterdir() if p.is_file())
    print(f"\n-- files in package ({len(files)}) --")
    for p in files:
        print(f"  {p.name}\t{p.stat().st_size} bytes\tsha256={sha256_file(p)}")

    manifest_like = [p.name for p in files
                     if re.search(r"manifest|package|meta|checksum|sha|sum", p.name, re.I)]
    print(f"\n-- manifest-like filenames (regex) = {manifest_like or 'NONE'} --")
    for keyword in ("package_id", "version", "target", "build", "depend",
                    "conflict", "hash", "sha256", "content"):
        print(f"  key '{keyword}' present in any filename? "
              f"{any(keyword.lower() in p.name.lower() for p in files)}")

    maps = sorted(p for p in files if p.suffix.upper() == ".MAP")
    battle = pkg / "BATTLEMD98.INI"
    mixpath = pkg / "expandmd98.mix"
    report = pkg / "BUILD_REPORT.txt"

    print(f"\n-- MAP read-back ({len(maps)} maps) --")
    for p in maps:
        basic = basic_section(p.read_bytes().decode("gbk", errors="replace"))
        print(f"  {p.name}: Name={basic.get('Name','<absent>')!r} "
              f"NextScenario={basic.get('NextScenario','<absent>')!r} "
              f"EndOfGame={basic.get('EndOfGame','<absent>')!r} "
              f"Player={basic.get('Player','<absent>')!r}")

    print("\n-- BATTLEMD98.INI read-back --")
    if not battle.is_file():
        print("  MISSING BATTLEMD98.INI")
    else:
        secs = parse_ini(battle.read_bytes().decode("gbk", errors="replace"))
        print(f"  sections = {sorted(secs)}")
        print(f"  [Battles] = {secs.get('Battles', {})}")
        own = [s for s in secs if s != "Battles" and not OFFICIAL_ID_RE.match(s)]
        for s in own:
            print(f"  [{s}] = {secs[s]}")
        official = [s for s in secs if OFFICIAL_ID_RE.match(s)]
        print(f"  official battle-id sections = {official or 'NONE'}")

    print("\n-- expandmd98.mix read-back (independent MIX index decode) --")
    if not mixpath.is_file():
        print("  MISSING expandmd98.mix")
    else:
        mix = MixIndex(mixpath)
        print(f"  flags={mix.flags} count={mix.count} body_size={mix.body_size} "
              f"data_start={mix.data_start}")
        for hid, off, size in mix.entries:
            print(f"  entry id=0x{hid:08X} offset={off} size={size}")
        want_ids = {crc_hash(p.name) for p in maps}
        got_ids = {e[0] for e in mix.entries}
        print(f"  expected map CRCs = {[f'0x{i:08X}' for i in sorted(want_ids)]}")
        print(f"  id set equal? {'YES' if got_ids == want_ids else 'NO'}")
        for p in maps:
            inside = mix.get(crc_hash(p.name))
            loose = p.read_bytes()
            print(f"  {p.name}: bytes in MIX == loose MAP? "
                  f"{'YES' if inside == loose else 'NO'}")
        ini_hits = [(n, crc_hash(n)) for n in INI_PROBES
                    if crc_hash(n) in got_ids]
        print(f"  known .INI names present as entry ids? {ini_hits or 'NONE'}")
        print(f"  INI count in MIX (by probe) = {len(ini_hits)}")

    print("\n-- BUILD_REPORT.txt truncated-hash cross-check --")
    if report.is_file():
        text = report.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("self-checks:") or s.startswith("[PASS]") or "  [PASS]" in s:
                print(f"  {s}")
        for m in re.finditer(r"^\s+(\S+)\s+(\d+) bytes\s+sha256=([0-9a-f]{16})\s*$",
                             text, re.M):
            name, _size, short = m.group(1), m.group(2), m.group(3)
            p = pkg / name
            if p.is_file():
                full = sha256_file(p)
                print(f"  {name}: report={short} actual={full[:16]} "
                      f"{'MATCH' if full.startswith(short) else 'MISMATCH'}")
            else:
                print(f"  {name}: NOT ON DISK")
        print("\n-- BUILD_REPORT.txt full text --")
        print(text)
    else:
        print("  MISSING BUILD_REPORT.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
