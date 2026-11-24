#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W154 probe: live verification of instance-array semantics (read-only).

The ledger (§859/§867/§868/§874) names 140 instance arrays and states that
`AbstractClass::Array` is NOT a complete registry, but marks that as
"身份已证，完整性未证" — it was never checked against a live process.

This probe checks it while the game is actually running:

 1. Walk `AbstractClass::Array` (base 0xB0F720): Items=[+4], Capacity=[+8], Count=[+0x10]
    and name EVERY object by its vtable -> class (vtables_canonical.json).
 2. Walk each per-type array the same way and recount; compare walked count to the
    stored Count field (verifies the DynamicVectorClass layout claims).
 3. Membership: is every object of the per-type arrays present in AbstractClass::Array?

Everything is read-only; nothing is written to the target process.
"""
import ctypes
import json
import os
import struct
import subprocess
import sys
from collections import Counter
from ctypes import wintypes as wt

ROOT = r"D:\Project\ra2-campaign-forge"
VT_JSON = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json")

ARRAYS = {
    # base = the DynamicVectorClass object itself (vtable sits AT the base; layout is
    # 0x18 bytes: +0 vtable, +4 Items, +8 Capacity, +0xC flags, +0x10 Count, +0x14 Incr)
    "AbstractClass::Array": 0x00B0F720,
    "FootClass::Array": 0x008B3DC0,
    "UnitClass::Array": 0x008B4108,      # vtable here; Items = 0x008B410C; Count = 0x008B4118
    "InfantryClass::Array": 0x00A83DE8,
    "AircraftClass::Array": 0x00A8E390,
    "BuildingClass::Array": 0x00A8EB40,
    "TechnoClass::Array": 0x00A8EC78,
    "BulletClass::Array": 0x00A8ED40,    # vtable here; Count = 0x00A8ED50
    "AnimClass::Array": 0x00A8E9A8,
}
WHATAMI_OFF = 0x2C

k32 = ctypes.windll.kernel32
k32.OpenProcess.restype = wt.HANDLE
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]


def clean(name):
    n = name
    if n.startswith(".?AV"):
        n = n[4:]
    if n.endswith("@@"):
        n = n[:-2]
    n = n.replace("?$", "").replace("@", "").replace("PAV", "").replace("US", "")
    return n


def main():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process gamemd -ErrorAction SilentlyContinue).Id"],
                         capture_output=True, text=True).stdout.split()
    if not out:
        print("gamemd not running")
        return 2
    pid = int(out[0])
    h = k32.OpenProcess(0x1000 | 0x10, False, pid)

    cache = {}

    def rd(va, n=4):
        if n == 4 and va in cache:
            return cache[va]
        b = ctypes.create_string_buffer(n)
        g = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(h, ctypes.c_void_p(va), b, n, ctypes.byref(g))
        if not ok or g.value != n:
            return None
        if n == 4:
            v = struct.unpack("<I", b.raw)[0]
            cache[va] = v
            return v
        return b.raw

    vt2class = {}
    with open(VT_JSON, encoding="utf-8") as f:
        for e in json.load(f)["vtables"]:
            vt2class[e["vt"]] = (clean(e["class"]), e["col_offset"])

    def rdb(va, n):
        """byte read, never cached (n may be 4, which the u32 cache would shadow)"""
        b = ctypes.create_string_buffer(n)
        g = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(h, ctypes.c_void_p(va), b, n, ctypes.byref(g))
        return b.raw[:g.value] if ok else None

    def array(base):
        items, cap, cnt = rd(base + 4), rd(base + 8), rd(base + 0x10)
        return items, cap, cnt

    print("=== container layout + count cross-check ===")
    walked = {}
    for name, base in ARRAYS.items():
        items, cap, cnt = array(base)
        ptrs = []
        if items and cnt is not None and 0 < cnt <= 5000:
            raw = rdb(items, min(cnt, 5000) * 4)
            if raw:
                ptrs = list(struct.unpack("<%dI" % (len(raw) // 4), raw))
                ptrs = [p for p in ptrs if p]
        walked[name] = ptrs
        print("%-24s base=0x%08X Items=0x%08X Cap=%-6s Count=%-5s walked=%d %s"
              % (name, base, items or 0, cap, cnt, len(ptrs),
                 "OK" if cnt == len(ptrs) else "MISMATCH"))

    print("\n=== type census inside AbstractClass::Array (by vtable) ===")
    census = Counter()
    unknown = 0
    abs_ptrs = walked["AbstractClass::Array"]
    abs_set = set(abs_ptrs)
    for p in abs_ptrs:
        vt = rd(p)
        cls_off = vt2class.get(vt)
        if cls_off:
            census[cls_off[0]] += 1
        else:
            unknown += 1
    for cls, n in census.most_common(40):
        print("  %-32s %d" % (cls, n))
    print("  (unmapped vtable: %d of %d)" % (unknown, len(abs_ptrs)))

    print("\n=== membership: per-type array objects inside AbstractClass::Array ===")
    for name in ("FootClass::Array", "UnitClass::Array", "InfantryClass::Array",
                 "BuildingClass::Array", "TechnoClass::Array", "AnimClass::Array",
                 "BulletClass::Array"):
        ptrs = walked[name]
        inside = sum(1 for p in ptrs if p in abs_set)
        print("  %-24s objects=%-4d in abstract=%-4d  missing=%d"
              % (name, len(ptrs), inside, len(ptrs) - inside))
        if ptrs and inside != len(ptrs):
            for p in ptrs:
                if p not in abs_set:
                    vt = rd(p)
                    print("      MISSING obj=0x%08X vt=0x%08X class=%s"
                          % (p, vt or 0, vt2class.get(vt, ("?",))[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
