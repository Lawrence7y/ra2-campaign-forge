"""Verify Save_Core 0x67D300 is a LIVE caller (④ witness).

Scans all .text for E8 rel32 -> 0x67D300, then for each direct caller scans one
level up. Emits work/live_chain.txt (from binary bytes only, not from audited txt).
"""
from __future__ import annotations

from pathlib import Path

import capstone

from semfix_lib import Bin, hx, COVERAGE

SAVE_CORE = 0x0067D300


def unit():
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = True
    return m


def scan_e8_to(b: Bin, target: int):
    data = b.text_bytes()
    hits = []
    for i, byte in enumerate(data):
        if byte != 0xE8 or i + 5 > len(data):
            continue
        site = b.text_start + i
        rel = int.from_bytes(data[i + 1:i + 5], "little", signed=True)
        if site + 5 + rel == target:
            ins = next(unit().disasm(data[i:i + 5], site), None)
            if ins and ins.mnemonic == "call":
                hits.append(site)
    return hits


def covering_entry(site: int):
    """nearest coverage entry <= site (function owner guess)."""
    best = None
    for line in COVERAGE.read_text(encoding="utf-8", errors="replace").splitlines():
        p = line.split("\t")
        if len(p) < 3:
            continue
        try:
            a = int(p[0], 16)
        except ValueError:
            continue
        if a <= site and (best is None or a > best[0]):
            best = (a, p[2])
    return best


def main():
    b = Bin()
    lines = []
    lines.append("④ LIVE-CALLER WITNESS for Save_Core 0x67D300 (binary-derived)\n")
    l1 = scan_e8_to(b, SAVE_CORE)
    lines.append(f"Level-1 direct callers of 0x{SAVE_CORE:08X}: {len(l1)}")
    for s in l1:
        owner = covering_entry(s)
        lines.append(f"  call @0x{s:08X} in fn 0x{owner[0]:08X} ({owner[1]})" if owner
                     else f"  call @0x{s:08X}")
    seen = set()
    for s in l1:
        owner = covering_entry(s)
        if not owner:
            continue
        ent = owner[0]
        if ent in seen:
            continue
        seen.add(ent)
        up = scan_e8_to(b, ent)
        lines.append(f"  callers of 0x{ent:08X}: "
                     + (", ".join(hx(x) for x in up) if up else "(none direct)"))
    txt = "\n".join(lines) + "\n"
    out = Path(__file__).resolve().parent / "live_chain.txt"
    out.write_text(txt, encoding="utf-8")
    print(txt)
    print("->", out)


if __name__ == "__main__":
    main()
