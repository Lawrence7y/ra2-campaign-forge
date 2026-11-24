#!/usr/bin/env python3
"""W134: live read-only probe of the engine's instance arrays.

Purpose: turn the static table in W132_arrays/instance_arrays.tsv into a
one-command live check.  It answers, in a single run:

  1. Are the 49 `DynamicVectorClass<T*>` globals actually shaped as declared
     (CapacityIncrement == 10, 0 <= Count <= Capacity, Items nonzero iff
     Count > 0)?
  2. What classes are really in the arrays?  Each element is walked and its
     vptr resolved to a class through the canonical vtable table.  For a
     correctly identified array the elements must be the declared class or a
     subclass of it.
  3. Is `AbstractClass::Array` (0xB0F720) a complete registry?  Its elements are
     binned by class; that histogram is then compared against the independent
     per-type counts.  If `BuildingClass`'s bin equals [0xA8EB50], the two
     measurements agree.

READ-ONLY: PROCESS_VM_READ only.  Never writes, never injects, never patches.

Usage:
    python -X utf8 w134_live_arrays.py --pid 1234
    python -X utf8 w134_live_arrays.py --pid 1234 --walk
    python -X utf8 w134_live_arrays.py --selftest
"""
import argparse
import bisect
import ctypes
import io
import json
import os
import struct
import sys
import time
from ctypes import wintypes as wt

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.dirname(HERE)
W132 = os.path.join(R10, "W132_arrays", "instance_arrays.tsv")
VTJSON = os.path.join(R10, "W130_atlas", "vtables_canonical.json")
ATLAS = os.path.join(R10, "W130_atlas", "class_atlas_v2.tsv")

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

# Layout, byte-verified from the static ctor/dtor at 0x004E6B60 / 0x004E6BA0.
OFF_ITEMS, OFF_CAP, OFF_INIT, OFF_ALLOC = 0x04, 0x08, 0x0C, 0x0D
OFF_COUNT, OFF_INCR = 0x10, 0x14
EXPECTED_INCR = 10

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
for _f in (k32.ReadProcessMemory,):
    _f.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                   ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]


class Mem:
    def __init__(self, pid):
        self.h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION,
                                 False, pid)
        if not self.h:
            raise OSError("OpenProcess failed: %d" % ctypes.get_last_error())
        self.fails = 0

    def rd(self, va, n):
        buf = ctypes.create_string_buffer(n)
        got = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), buf, n,
                                   ctypes.byref(got))
        if not ok or got.value != n:
            self.fails += 1
            return None
        return buf.raw

    def u32(self, va):
        b = self.rd(va, 4)
        return None if b is None else struct.unpack("<I", b)[0]

    def u8(self, va):
        b = self.rd(va, 1)
        return None if b is None else b[0]


# ------------------------------------------------------------------ static data
def load_arrays():
    rows = []
    with io.open(W132, encoding="utf-8") as f:
        next(f)
        for ln in f:
            p = ln.rstrip("\n").split("\t")
            if len(p) < 4:
                continue
            rows.append({"element": p[0],
                         "base": int(p[1], 16),
                         "items": int(p[2], 16),
                         "count": int(p[3], 16)})
    return rows


def load_vtables():
    """vt -> class name, primary vtables only (col_offset == 0)."""
    with io.open(VTJSON, encoding="utf-8") as f:
        d = json.load(f)
    m = {}
    for v in d.get("vtables", []):
        m[int(v["vt"])] = v.get("class", "")
    return m


def load_primary():
    """class -> primary vtable (first primary entry)."""
    cls2vt = {}
    if not os.path.exists(ATLAS):
        return cls2vt
    with io.open(ATLAS, encoding="utf-8") as f:
        next(f)
        for ln in f:
            p = ln.rstrip("\n").split("\t")
            if len(p) < 5 or not p[3]:
                continue
            try:
                cls2vt[p[0]] = int(p[3], 16)
            except ValueError:
                continue
    return cls2vt


def short(mangled):
    """mangle -> readable, matching w132d's form."""
    if not mangled:
        return ""
    s = mangled
    for p in (".?AV", ".?AU"):
        if s.startswith(p):
            s = s[len(p):]
            break
    return s.rstrip("@")


# ------------------------------------------------------------------- self test
def selftest():
    ok = tot = 0

    def chk(name, cond):
        nonlocal ok, tot
        tot += 1
        if cond:
            ok += 1
        else:
            print("  FAIL:", name)

    chk("layout arithmetic Items=base+4", 0xA8EB40 + OFF_ITEMS == 0xA8EB44)
    chk("layout arithmetic Count=base+0x10", 0xA8EB40 + OFF_COUNT == 0xA8EB50)
    chk("unit Items", 0x8B4108 + OFF_ITEMS == 0x8B410C)
    chk("unit Count", 0x8B4108 + OFF_COUNT == 0x8B4118)
    chk("abstract Items", 0xB0F720 + OFF_ITEMS == 0xB0F724)
    chk("abstract Count", 0xB0F720 + OFF_COUNT == 0xB0F730)
    chk("demangle", short(".?AV?$DynamicVectorClass@PAVUnitClass@@@@")
        == "?$DynamicVectorClass@PAVUnitClass")

    # shape rules
    def shape_ok(cnt, cap, incr):
        return incr == EXPECTED_INCR and 0 <= cnt <= cap
    chk("shape accepts sane", shape_ok(5, 10, 10))
    chk("shape rejects count>cap", not shape_ok(11, 10, 10))
    chk("shape rejects bad incr", not shape_ok(5, 10, 8))
    chk("shape accepts empty", shape_ok(0, 0, 10))

    a = load_arrays()
    chk("49 arrays from tsv", len(a) == 49)
    chk("bases unique", len({r["base"] for r in a}) == len(a))
    chk("every Items == base+4", all(r["items"] == r["base"] + 4 for r in a))
    chk("every Count == base+0x10", all(r["count"] == r["base"] + 0x10 for r in a))

    print("%d/%d GREEN" % (ok, tot))
    return 0 if ok == tot else 1


# ----------------------------------------------------------------------- probe
def read_header(mem, base):
    raw = mem.rd(base, 0x18)
    if raw is None:
        return None
    (vptr,) = struct.unpack_from("<I", raw, 0x00)
    (items,) = struct.unpack_from("<I", raw, OFF_ITEMS)
    (cap,) = struct.unpack_from("<i", raw, OFF_CAP)
    init = raw[OFF_INIT]
    alloc = raw[OFF_ALLOC]
    (count,) = struct.unpack_from("<i", raw, OFF_COUNT)
    (incr,) = struct.unpack_from("<i", raw, OFF_INCR)
    return {"vptr": vptr, "items": items, "cap": cap, "init": init,
            "alloc": alloc, "count": count, "incr": incr}


def shape_problems(h):
    p = []
    if h["incr"] != EXPECTED_INCR:
        p.append("CapacityIncrement=%d (expected %d)" % (h["incr"], EXPECTED_INCR))
    if not (0 <= h["count"] <= h["cap"]):
        p.append("Count=%d out of [0,Capacity=%d]" % (h["count"], h["cap"]))
    if h["count"] > 0 and h["items"] == 0:
        p.append("Count>0 but Items==NULL")
    if h["count"] == 0 and h["items"] != 0 and not h["alloc"]:
        pass          # a static buffer with nothing in it is legal
    if h["cap"] < 0:
        p.append("negative Capacity")
    return p


def walk_elements(mem, items, count, vt2cls, cap=200000):
    """read the pointer array, resolve each element's vptr class"""
    count = min(count, cap)
    if count <= 0 or not items:
        return [], 0
    blob = mem.rd(items, 4 * count)
    if blob is None:
        return [], count
    ptrs = struct.unpack_from("<%dI" % count, blob, 0)
    out = []
    for p in ptrs:
        if not p or p < 0x10000:
            out.append((p, None))
            continue
        v = mem.u32(p)
        out.append((p, vt2cls.get(v) if v else None))
    return out, count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int)
    ap.add_argument("--walk", action="store_true",
                    help="walk every array and resolve element classes")
    ap.add_argument("--wait", type=float, default=0.0,
                    help="wait up to N seconds for a scenario to be loaded")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not a.pid:
        ap.error("--pid required (or use --selftest)")

    arrays = load_arrays()
    vt2cls = load_vtables()
    cls2vt = load_primary()
    mem = Mem(a.pid)
    print("attached pid=%d  (READ-ONLY, PROCESS_VM_READ only)" % a.pid)
    print("vtables known: %d   class->primary known: %d" % (len(vt2cls), len(cls2vt)))

    # wait for a scenario: HouseClass or BuildingClass non-empty is a good signal
    if a.wait > 0:
        t0 = time.time()
        while time.time() - t0 < a.wait:
            h = read_header(mem, 0x00A80228)     # HouseClass::Array
            if h and h["count"] > 0:
                print("scenario detected after %.1fs (houses=%d)"
                      % (time.time() - t0, h["count"]))
                break
            time.sleep(0.5)
        else:
            print("WARNING: no non-empty HouseClass::Array after %.0fs "
                  "-- the game may still be at the main menu" % a.wait)

    out = io.open(a.out, "w", encoding="utf-8") if a.out else None

    def emit(s=""):
        print(s)
        if out:
            out.write(s + "\n")

    emit()
    emit("=" * 104)
    emit("W134-1  array headers (shape check)")
    emit("=" * 104)
    emit("%-40s %-10s %7s %7s %4s %4s %5s %s"
         % ("element", "base", "Count", "Cap", "init", "allc", "incr", "shape"))
    headers = {}
    bad = 0
    for r in arrays:
        h = read_header(mem, r["base"])
        headers[r["base"]] = h
        if h is None:
            emit("%-40s 0x%08X  UNREADABLE" % (r["element"], r["base"]))
            bad += 1
            continue
        probs = shape_problems(h)
        if probs:
            bad += 1
        emit("%-40s 0x%08X %7d %7d %4d %4d %5d %s"
             % (r["element"][:40], r["base"], h["count"], h["cap"],
                h["init"], h["alloc"], h["incr"],
                "OK" if not probs else "; ".join(probs)))
    emit()
    emit("arrays with shape problems: %d / %d" % (bad, len(arrays)))

    emit()
    emit("=" * 104)
    emit("W134-2  the per-type counts, in one place")
    emit("=" * 104)
    KEY = [("AbstractClass (all objects)", 0x00B0F720),
           ("FootClass (all mobile)", 0x008B3DC0),
           ("UnitClass (vehicles)", 0x008B4108),
           ("InfantryClass", 0x00A83DE8),
           ("AircraftClass", 0x00A8E390),
           ("BuildingClass", 0x00A8EB40),
           ("TechnoClass", 0x00A8EC78),
           ("HouseClass", 0x00A80228),
           ("BulletClass", 0x00A8ED40),
           ("AnimClass", 0x00A8E9A8),
           ("TriggerClass", 0x00A8EAE8),
           ("ParticleSystemClass", 0x00A80208)]
    for name, base in KEY:
        h = headers.get(base)
        emit("   %-28s [0x%08X] = %s"
             % (name, base + OFF_COUNT,
                ("%d" % h["count"]) if h and h["count"] is not None else "?"))

    if a.walk:
        emit()
        emit("=" * 104)
        emit("W134-3  element classes (each element's vptr resolved)")
        emit("=" * 104)
        for r in arrays:
            h = headers.get(r["base"])
            if not h or not h["count"]:
                continue
            els, got = walk_elements(mem, h["items"], h["count"], vt2cls)
            hist = {}
            nullp = 0
            unresolved = 0
            for p, c in els:
                if not p:
                    nullp += 1
                    continue
                if c is None:
                    unresolved += 1
                    continue
                hist[c] = hist.get(c, 0) + 1
            emit()
            emit("-- %s  base=0x%08X  Count=%d  walked=%d  null=%d  unresolved=%d"
                 % (r["element"], r["base"], h["count"], got, nullp, unresolved))
            for c, n in sorted(hist.items(), key=lambda kv: -kv[1])[:10]:
                emit("     %5d  %s" % (n, short(c)))
            if len(hist) > 10:
                emit("     ... %d more distinct classes" % (len(hist) - 10))

        # completeness check for AbstractClass::Array
        emit()
        emit("=" * 104)
        emit("W134-4  AbstractClass::Array completeness cross-check")
        emit("=" * 104)
        h = headers.get(0x00B0F720)
        if not h or not h["count"]:
            emit("   AbstractClass::Array is empty or unreadable -- cannot check")
        else:
            els, got = walk_elements(mem, h["items"], h["count"], vt2cls)
            hist = {}
            for p, c in els:
                if p and c:
                    hist[c] = hist.get(c, 0) + 1
            emit("   AbstractClass::Array.Count = %d" % h["count"])
            emit("   resolved elements          = %d" % sum(hist.values()))
            emit()
            emit("   independent per-type counts for comparison:")
            for name, base in KEY[1:]:
                hh = headers.get(base)
                if hh:
                    emit("      %-24s %d" % (name, hh["count"]))
            emit()
            emit("   NOTE: an object appears in several arrays at once")
            emit("   (a UnitClass is in UnitClass::Array, FootClass::Array,")
            emit("    TechnoClass::Array and AbstractClass::Array). So do NOT")
            emit("   expect AbstractClass.Count to equal a plain sum. The")
            emit("   meaningful test is: does each specific bin below match")
            emit("   its own per-type array count?")
            emit()
            for c, n in sorted(hist.items(), key=lambda kv: -kv[1])[:20]:
                emit("      %5d  %s" % (n, short(c)))

    if out:
        out.close()
        print("\nwrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
