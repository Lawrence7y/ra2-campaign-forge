#!/usr/bin/env python3
"""Identify vtable base/slot for selected AI function pointers via RTTI COL chain."""
from __future__ import annotations
import re
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import wbase

OUT = Path(__file__).resolve().parents[1] / "EVIDENCE"
TARGETS = {
    0x4F8440: "HouseClass::Update",
    0x4DA530: "FootClass::AI",
    0x414BB0: "Foot-derived AI wrapper A",
    0x51BAB0: "Foot-derived AI wrapper B",
    0x7360C0: "Foot-derived AI wrapper C",
}
p = wbase.pe()
data = p.__data__

def dword(va):
    try:
        off = wbase.va_to_off(va)
    except ValueError:
        return None
    if off + 4 > len(data):
        return None
    return struct.unpack_from("<I", data, off)[0]

def dword_refs(value):
    pat = struct.pack("<I", value)
    out = []
    for i in range(len(data) - 3):
        if data[i:i+4] == pat:
            try:
                out.append(wbase.off_to_va(i))
            except ValueError:
                pass
    return out

def class_for_vtable(ref_va):
    # scan back for COL pointer at vtable[-1]
    for pva in range(ref_va - 4, max(0, ref_va - 0x800), -4):
        col = dword(pva)
        if col is None:
            continue
        td = dword(col + 0xC)
        if td is None:
            continue
        try:
            s = wbase.read_bytes(td + 8, 128).split(b"\0", 1)[0]
        except Exception:
            continue
        if s.startswith(b".?AV"):
            return pva + 4, s.decode("ascii", "replace")
    return None, None

lines = []
for target, name in TARGETS.items():
    refs = dword_refs(target)
    lines.append(f"\n=== {name} {target:#x} DWORD_REFS={len(refs)} ===")
    for ref in refs:
        base, cls = class_for_vtable(ref)
        slot = (ref - base) // 4 if base else None
        lines.append(f"REF={ref:#x} VTABLE_BASE={base and hex(base)} SLOT={slot} CLASS={cls}")

(OUT / "E14_ai_vtable_slots.txt").write_text("\n".join(lines)+"\n", encoding="utf-8")
print("\n".join(lines))
