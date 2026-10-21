"""Independently verify anchor_claims.txt against gamemd.exe bytes.

Reads the claims file, maps each VA through the PE section table to a file
offset, and compares the asserted byte string. Read-only; prints a report.

Run from the repository root:
    python re_atlas/tools/verify_claims.py
"""

import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
CLAIMS = os.path.join(ROOT, "docs", "re", "anchor_claims.txt")

CLAIM_RE = re.compile(r"^(0x[0-9A-Fa-f]{8})\s*=\s*([0-9A-Fa-f ]+?)\s*(?:#\s*(.*))?$")


def load_sections(blob):
    """Return (image_base, [(vaddr, vsize, rawptr, rawsize, name)])."""
    e_lfanew = struct.unpack_from("<I", blob, 0x3C)[0]
    assert blob[e_lfanew:e_lfanew + 4] == b"PE\0\0", "not a PE"
    nsec = struct.unpack_from("<H", blob, e_lfanew + 6)[0]
    opt_size = struct.unpack_from("<H", blob, e_lfanew + 20)[0]
    opt = e_lfanew + 24
    image_base = struct.unpack_from("<I", blob, opt + 28)[0]
    sec_tab = opt + opt_size
    secs = []
    for i in range(nsec):
        off = sec_tab + i * 40
        name = blob[off:off + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", blob, off + 8)
        secs.append((vaddr, vsize, rawptr, rawsize, name))
    return image_base, secs


def va_to_off(image_base, secs, va):
    """VA -> file offset, or (None, reason).

    The BSS tail of .data has no backing bytes, so that case is reported
    separately from 'outside every section' instead of being read as the next
    section's data.
    """
    rva = va - image_base
    for vaddr, vsize, rawptr, rawsize, _name in secs:
        span = max(vsize, rawsize)
        if vaddr <= rva < vaddr + span:
            delta = rva - vaddr
            if delta >= rawsize:
                return None, "in-section-but-beyond-raw"
            return rawptr + delta, None
    return None, "outside-all-sections"


def main():
    for path in (EXE, CLAIMS):
        if not os.path.isfile(path):
            sys.exit(
                f"required input missing:\n  {path}\n"
                "This repository intentionally does not ship gamemd.exe.\n"
                "Place a clean Yuri's Revenge gamemd.exe at ra2youli/gamemd.exe\n"
                "and ensure docs/re/anchor_claims.txt exists, then run again."
            )
    with open(EXE, "rb") as fh:
        blob = fh.read()
    image_base, secs = load_sections(blob)
    print(f"# image_base=0x{image_base:08X}  sections={len(secs)}  exe_bytes={len(blob)}")
    for vaddr, vsize, rawptr, rawsize, name in secs:
        print(f"#   {name:8s} rva=0x{vaddr:08X} vsize=0x{vsize:08X} "
              f"rawptr=0x{rawptr:08X} rawsize=0x{rawsize:08X}")
    print()

    total = ok = bad = unreadable = 0
    bad_rows = []
    with open(CLAIMS, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            m = CLAIM_RE.match(line)
            if not m:
                continue
            total += 1
            va = int(m.group(1), 16)
            want = bytes.fromhex(m.group(2).replace(" ", ""))
            comment = (m.group(3) or "").strip()
            off, why = va_to_off(image_base, secs, va)
            if off is None:
                unreadable += 1
                bad_rows.append((va, "UNREADABLE:" + why, comment))
                continue
            got = blob[off:off + len(want)]
            if got == want:
                ok += 1
            else:
                bad += 1
                bad_rows.append((va, f"MISMATCH want={want.hex(' ')} got={got.hex(' ')}", comment))

    print(f"# RESULT total={total} PASS={ok} FAIL={bad} UNREADABLE={unreadable}")
    for va, why, comment in bad_rows:
        print(f"FAIL 0x{va:08X}  {why}  # {comment[:110]}")
    return 0 if bad == 0 and unreadable == 0 else 1


sys.exit(main())
