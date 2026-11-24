#!/usr/bin/env python3
"""W120: read-only 8-slot probe for the multi-cell building occupancy question.

Answers (one run): when a 2x2 BuildingClass is destroyed, are ALL of its
footprint cells detached from the cell chains, or only some, or none?

Facts this relies on (all established in the ledger, see GOAL_THREE_TARGETS):
  0x0087F924  DWORD  -> cell table base ; cell = table[Y*512 + X] ; stride 0x148
  CellClass   +0xE4 chain A head, +0xE8 chain B head
  chain node  +0x00 vptr, +0x30 next          (node IS the game object)
  0x007E3EBC  BuildingClass primary vtable (COL offset==0, WhatAmI==6)

READ-ONLY: PROCESS_VM_READ only. Never writes, never debugs, never patches.
"""
import argparse, ctypes, struct, sys, time
from ctypes import wintypes as wt

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
TABLE_GLOBAL = 0x0087F924
ROWS = COLS = 512
CELL_A, CELL_B, NODE_NEXT = 0xE4, 0xE8, 0x30
BC_VT = 0x007E3EBC

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE


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


def image_name(pid):
    # best effort, read-only; returns lowercased exe basename or None
    import subprocess
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "PID eq %d" % pid, "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=15).stdout
        first = out.strip().splitlines()[0]
        return first.split(",")[0].strip('"').lower()
    except Exception:
        return None


def table_base(mem, wait_s=180):
    t0 = time.time()
    while time.time() - t0 < wait_s:
        t = mem.u32(TABLE_GLOBAL)
        if t and t > 0x10000:
            return t
        time.sleep(0.3)
    return None


def scan_building_heads(mem, tbl, cap=None):
    """return list of (cell_ptr, headA, headB) for cells whose chain A/B head is a BuildingClass"""
    blob = mem.rd(tbl, ROWS * COLS * 4)
    if blob is None:
        return None
    entries = struct.unpack_from("<%dI" % (ROWS * COLS), blob, 0)
    out = []
    vt_cache = {}
    seen = set()
    for idx, cell in enumerate(entries):
        if not cell or cell in seen:
            continue
        seen.add(cell)
        raw = mem.rd(cell + CELL_A, 8)          # both heads in one read
        if raw is None:
            continue
        ha, hb = struct.unpack("<II", raw)
        for off, h in ((CELL_A, ha), (CELL_B, hb)):
            if not h or h < 0x10000:
                continue
            v = vt_cache.get(h)
            if v is None:
                v = mem.u32(h)
                vt_cache[h] = v
            if v == BC_VT:
                out.append((idx, cell, off, h))
        if cap and len(out) > cap:
            break
    return out


def cmd_discover(mem, tbl):
    rows = scan_building_heads(mem, tbl)
    if rows is None:
        print("table unreadable")
        return 2
    print("cells whose chain head is BuildingClass(0x%08X): %d" % (BC_VT, len(rows)))
    groups = {}
    for idx, cell, off, h in rows:
        groups.setdefault((h, off), []).append((idx, cell))
    print("distinct (head, chain) groups: %d" % len(groups))
    print("\n-- groups sharing ONE head across >=2 cells (multi-cell buildings) --")
    n = 0
    for (h, off), cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len(cells) < 2:
            continue
        n += 1
        if n > 12:
            break
        nxt = mem.u32(h + NODE_NEXT)
        coords = ",".join("(%d,%d)" % (i // COLS, i % COLS) for i, _ in cells)
        print("  head=0x%08X chain=%s cells=%d  next=0x%08X  %s"
              % (h, "A" if off == CELL_A else "B", len(cells), nxt or 0, coords))
    print("\ngroups with >=2 cells: %d" % sum(1 for v in groups.values() if len(v) >= 2))
    return 0


def cmd_watch(mem, tbl, head, secs, out):
    """poll the slots that reference `head` plus the node itself"""
    rows = scan_building_heads(mem, tbl)
    if rows is None:
        print("table unreadable")
        return 2
    slots = [(cell, off) for idx, cell, off, h in rows if h == head]
    if len(slots) < 2:
        print("no group with that head (found %d slots); run --discover first" % len(slots))
        return 2
    print("watching head=0x%08X over %d slots + node fields" % (head, len(slots)))
    print("slots: " + ", ".join("0x%08X+0x%02X" % s for s in slots))
    print("baseline: " + " ".join("%02x" % b for b in (mem.rd(head, 0x34) or b"")))
    rec = out and open(out, "w", encoding="utf-8")
    t0 = time.time()
    last = None
    n = 0
    while time.time() - t0 < secs:
        n += 1
        cur = tuple(mem.u32(cell + off) for cell, off in slots)
        vptr = mem.u32(head)
        nxt = mem.u32(head + NODE_NEXT)
        state = (cur, vptr, nxt)
        if state != last:
            t = time.time() - t0
            zeroed = sum(1 for v in cur if not v)
            line = ("t=%7.3fs  scan#%-6d  zeroed=%d/%d  vptr=0x%08X next=0x%08X  heads=%s"
                    % (t, n, zeroed, len(cur), vptr or 0, nxt or 0,
                       ",".join("0x%08X" % (v or 0) for v in cur)))
            print(line)
            sys.stdout.flush()
            if rec:
                rec.write(line + "\n")
                rec.flush()
            last = state
        if mem.fails > 60 and mem.u32(TABLE_GLOBAL) is None:
            print("PROCESS_GONE @ scan#%d" % n)
            break
        time.sleep(0.001)
    print("\n=== done: %d scans in %.1fs ===" % (n, time.time() - t0))
    if rec:
        rec.close()
    return 0


def self_test():
    """no game needed: exercise parsing/bounds logic only"""
    ok = 0
    tot = 0
    # 1 cell index math
    tot += 1
    assert (9 * 512 + 101) == 4709
    ok += 1
    # 2 group-by logic
    rows = [(0, 0xA, CELL_A, 0x1000), (1, 0xB, CELL_A, 0x1000),
            (2, 0xC, CELL_A, 0x2000)]
    g = {}
    for idx, cell, off, h in rows:
        g.setdefault((h, off), []).append((idx, cell))
    tot += 1
    assert len(g[(0x1000, CELL_A)]) == 2 and len(g[(0x2000, CELL_A)]) == 1
    ok += 1
    # 3 zeroed counter
    tot += 1
    assert sum(1 for v in (0, 0, 0x1234, 0) if not v) == 3
    ok += 1
    # 4 chain selector mapping
    tot += 1
    assert ("A" if CELL_A == 0xE4 else "B") == "A" and ("A" if CELL_B == 0xE4 else "B") == "B"
    ok += 1
    tot += 1
    _b = struct.pack("<hhhhhh", 3, 4, 5, 6, 0x7FFF, 0x7FFF)
    assert decode_coord_list(_b) == [(3, 4), (5, 6)]
    ok += 1
    print("%d/%d GREEN" % (ok, tot))
    return 0 if ok == tot else 1


POOL_BASE = 0x00B0E840
POOL_COUNT = 0x00B0E844
POOL_CUR = 0x00B0E850
BC_520 = 0x520


CHAIN_SEL = 0x8C


def cmd_check_8c(mem, tbl):
    """candidate (f): is obj->[+0x8C] (chain selector) consistent with the chain(s) it is actually registered in?"""
    rows = scan_building_heads(mem, tbl)
    if rows is None:
        print("table unreadable")
        return 2
    per = {}
    for idx, cell, off, h in rows:
        d = per.setdefault(h, {"A": 0, "B": 0, "cells": set()})
        d["A" if off == CELL_A else "B"] += 1
        d["cells"].add(idx)
    print("distinct BuildingClass objects: %d" % len(per))
    print("\n%-12s %-6s %-5s %-5s %-6s %s"
          % ("building", "sel8C", "inA", "inB", "cells", "consistency"))
    bad = 0
    for h in sorted(per, key=lambda x: -len(per[x]["cells"])):
        sel = mem.u32(h + CHAIN_SEL)
        d = per[h]
        inA, inB = d["A"], d["B"]
        if sel is None:
            tag = "unreadable"
        elif sel == 0:
            tag = "sel=0(chainA) " + ("OK" if inA and not inB else
                                      ("MISMATCH(currently only in B)" if inB and not inA else
                                       ("exclusively A" if inA and not inB else "see counts")))
        else:
            tag = "sel!=0(chainB) " + ("OK" if inB and not inA else
                                       ("MISMATCH(currently only in A)" if inA and not inB else
                                        "see counts"))
        if "MISMATCH" in tag:
            bad += 1
        print("%-12s %-6s %-5d %-5d %-6d %s"
              % ("0x%08X" % h, "0x%02X" % (sel & 0xFF) if sel is not None else "?",
                 inA, inB, len(d["cells"]), tag))
    print("\n== SUMMARY: selector/registration MISMATCH = %d of %d ==" % (bad, len(per)))
    return 0


WX_FIELD = 0x9C
WY_FIELD = 0xA0


def trunc_div256(v):
    """C signed-division semantics as used by 0x0041BEA0 (cdq/and 0xff/add/sar 8)"""
    if v is None:
        return None
    v &= 0xFFFFFFFF
    if v & 0x80000000:
        v -= 0x100000000
    if v >= 0:
        return v >> 8
    return -((-v) >> 8)


def cmd_verify_anchor(mem, tbl):
    """for each multi-cell BuildingClass: anchor from +0x9C/+0xA0, expand footprint, test each cell head"""
    rows = scan_building_heads(mem, tbl)
    if rows is None:
        print("table unreadable")
        return 2
    objs = {}
    for idx, cell, off, h in rows:
        objs.setdefault(h, []).append(idx)
    # only multi-cell buildings are informative
    multi = [(h, c) for h, c in objs.items() if len(c) >= 2]
    print("multi-cell BuildingClass objects: %d (of %d total)" % (len(multi), len(objs)))
    for h, cells in sorted(multi, key=lambda kv: -len(kv[1])):
        typ = mem.u32(h + 0x520)
        fp = mem.u32((typ or 0) + TYPE_DFC) if typ else None
        coords = []
        if fp and 0x10000 < fp < 0x7FFFFFFF:
            buf = mem.rd(fp, 0x100)
            coords = decode_coord_list(buf) if buf else []
        wx = mem.u32(h + WX_FIELD)
        wy = mem.u32(h + WY_FIELD)
        ax = trunc_div256(wx)
        ay = trunc_div256(wy)
        print("\n  building 0x%08X  cells=%-3d coords=%-3d  wx=%s(0x%08X) wy=%s(0x%08X)"
              % (h, len(cells), len(coords),
                 ax, wx if wx is not None else 0, ay, wy if wy is not None else 0))
        if not coords:
            print("    no coords -> skip")
            continue
        hit = miss = outofrange = 0
        hits, misses = [], []
        for (cx, cy) in coords:
            gx, gy = ax + cx, ay + cy
            idx = gy * COLS + gx
            if idx < 0 or idx >= ROWS * COLS:
                outofrange += 1
                continue
            cellptr = mem.u32(tbl + idx * 4)
            got = mem.u32(cellptr + CELL_A) if cellptr else None
            if got == h:
                hit += 1
                hits.append((gx, gy))
            else:
                miss += 1
                misses.append((gx, gy, got))
        print("    anchor=(%d,%d)  hit=%d miss=%d outofrange=%d  (cells=%d)"
              % (ax, ay, hit, miss, outofrange, len(cells)))
        if misses[:6]:
            print("    miss sample (gx,gy,actualhead)=%s"
                  % ([(gx, gy, "0x%08X" % (v or 0)) for gx, gy, v in misses[:6]]))
        if hit == len(cells) == len(coords):
            print("    -> ANCHOR OK (all coords land on cells still pointing at this object)")
        elif hit == 0:
            print("    -> ANCHOR WRONG (no coord lands on this object)")
        else:
            print("    -> PARTIAL (some coords land elsewhere; see miss sample)")
    return 0


TYPE_DFC = 0xDFC


def cmd_dump_footprint(mem, tbl):
    """for each BuildingClass: type=[+0x520], fp=[type+0xDFC], decode coords, compare with occupied cells"""
    rows = scan_building_heads(mem, tbl)
    if rows is None:
        print("table unreadable")
        return 2
    objs = {}
    for idx, cell, off, h in rows:
        objs.setdefault(h, []).append(idx)
    print("distinct BuildingClass objects: %d" % len(objs))
    print("\n%-12s %-12s %-12s %-6s %-6s %s"
          % ("building", "type", "fp[+0xDFC]", "cells", "coords", "match"))
    nmatch = nmismatch = nempty = 0
    for h in sorted(objs, key=lambda x: -len(objs[x])):
        typ = mem.u32(h + 0x520)
        fp = mem.u32((typ or 0) + TYPE_DFC) if typ else None
        coords = []
        if fp and 0x10000 < fp < 0x7FFFFFFF:
            buf = mem.rd(fp, 0x100)
            coords = decode_coord_list(buf) if buf else []
        cells = len(objs[h])
        if not fp:
            tag = "EMPTY(fp==0) -> zero detach"
            nempty += 1
        elif len(coords) == cells:
            tag = "match"
            nmatch += 1
        else:
            tag = "MISMATCH"
            nmismatch += 1
        print("%-12s %-12s %-12s %-6d %-6d %s"
              % ("0x%08X" % h, "0x%08X" % (typ or 0),
                 "0x%08X" % (fp or 0), cells, len(coords), tag))
        if coords[:8]:
            print("             coords[:8]=%s" % (coords[:8],))
    print("\n== SUMMARY: match=%d  mismatch=%d  fp-null=%d ==" % (nmatch, nmismatch, nempty))
    return 0


def decode_coord_list(buf, limit=64):
    out = []
    if not buf:
        return out
    for i in range(0, min(len(buf), limit * 4), 4):
        if i + 4 > len(buf):
            break
        x, y = struct.unpack_from("<hh", buf, i)
        if x == 0x7FFF and y == 0x7FFF:
            break
        out.append((x, y))
    return out


def cmd_dump_fp(mem, fp):
    print("=== footprint descriptor 0x%08X ===" % fp)
    raw = mem.rd(fp, 0x80)
    if raw is None:
        print("  unreadable")
        return 2
    vptr = struct.unpack_from("<I", raw, 0)[0]
    p60 = struct.unpack_from("<I", raw, 0x60)[0]
    p64 = struct.unpack_from("<I", raw, 0x64)[0]
    print("  vptr  = 0x%08X" % vptr)
    print("  +0x60 = 0x%08X   +0x64 = 0x%08X" % (p60, p64))
    print("  raw[00:40] " + " ".join("%02x" % b for b in raw[:0x40]))
    print("  raw[40:80] " + " ".join("%02x" % b for b in raw[0x40:0x80]))
    a = decode_coord_list(raw[0x60:0x60 + 0x40])
    print("  (a) inline list at fp+0x60 : %d entries %s" % (len(a), a[:16]))
    if 0x10000 < p60 < 0x7FFFFFFF:
        buf = mem.rd(p60, 0x100)
        if buf is not None:
            b = decode_coord_list(buf)
            print("  (b) list at [fp+0x60]=0x%08X : %d entries %s" % (p60, len(b), b[:16]))
        else:
            print("  (b) [fp+0x60]=0x%08X unreadable" % p60)
        inner = mem.u32(p60 + 0x60)
        print("  (c) [[fp+0x60]+0x60] = 0x%08X" % (inner or 0))
        if inner and 0x10000 < inner < 0x7FFFFFFF:
            buf2 = mem.rd(inner, 0x100)
            if buf2 is not None:
                c = decode_coord_list(buf2)
                print("      as list : %d entries %s" % (len(c), c[:16]))
    return 0


def cmd_dump_pool(mem, tbl):
    """list every BuildingClass's +0x520 and detect sharing / sentinels"""
    base = mem.u32(POOL_BASE)
    cnt = mem.u32(POOL_COUNT)
    cur = mem.u32(POOL_CUR)
    print("pool: base=0x%08X count=%d current=0x%08X"
          % (base or 0, cnt if cnt is not None else -1, cur or 0))

    rows = scan_building_heads(mem, tbl)
    if rows is None:
        print("table unreadable")
        return 2
    # unique building objects (a head may be shared by many cells)
    objs = {}
    for idx, cell, off, h in rows:
        objs.setdefault(h, []).append((idx, cell))
    print("distinct BuildingClass objects seen as chain heads: %d" % len(objs))

    seen520 = {}
    problems = []
    for h in sorted(objs):
        v = mem.u32(h + BC_520)
        key = v if v is not None else -1
        seen520.setdefault(key, []).append(h)
        if v is None:
            problems.append((h, None, "unreadable"))
        elif v == 0:
            problems.append((h, 0, "ZERO (degenerate branch B -> empty list)"))
        elif v == 0xFFFFFFFF:
            problems.append((h, v, "0xFFFFFFFF sentinel (degenerate)"))

    print("\n-- +0x520 value histogram --")
    for v, hs in sorted(seen520.items(), key=lambda kv: -len(kv[1])):
        tag = ""
        if v == 0:
            tag = "  <ZERO>"
        elif v == 0xFFFFFFFF:
            tag = "  <SENTINEL -1>"
        elif len(hs) > 1:
            tag = "  <*** SHARED ***>"
        print("  +0x520 = 0x%08X  used by %d building(s)%s" % (v & 0xFFFFFFFF, len(hs), tag))
        if len(hs) > 1:
            for h in hs[:6]:
                print("       building 0x%08X  cells=%d" % (h, len(objs[h])))

    shared = [(v, hs) for v, hs in seen520.items() if len(hs) > 1 and v not in (0, 0xFFFFFFFF)]
    print("\n== VERDICT ==")
    if shared:
        print("  SHARED POOL ENTRY FOUND: %d value(s) used by >1 building" % len(shared))
        print("  -> pool-entry sharing is REAL in this session")
    else:
        print("  no sharing among %d building(s); all +0x520 distinct or degenerate" % len(objs))
    if problems:
        print("  degenerate cases: %d" % len(problems))
        for h, v, why in problems[:10]:
            print("     building 0x%08X  +0x520=%s  %s"
                  % (h, "None" if v is None else "0x%08X" % (v & 0xFFFFFFFF), why))
    else:
        print("  degenerate cases: 0")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", nargs="?", type=int)
    ap.add_argument("--discover", action="store_true")
    ap.add_argument("--dump-pool", action="store_true")
    ap.add_argument("--dump-fp", type=lambda s: int(s, 0), default=None)
    ap.add_argument("--dump-footprint", action="store_true")
    ap.add_argument("--verify-anchor", action="store_true")
    ap.add_argument("--check-8c", action="store_true")
    ap.add_argument("--watch-head", type=lambda s: int(s, 0), default=None)
    ap.add_argument("--secs", type=float, default=120.0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--allow-any-image", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.pid:
        ap.error("pid required unless --self-test")
    name = image_name(a.pid)
    if name and "gamemd" not in name and not a.allow_any_image:
        print("refuse: pid %d image is %r, not gamemd.exe (use --allow-any-image)"
              % (a.pid, name))
        return 3
    mem = Mem(a.pid)
    print("attached pid=%d image=%s (READ-ONLY)" % (a.pid, name))
    tbl = table_base(mem)
    if not tbl:
        print("WAIT_FAIL: [0x%08X] still 0" % TABLE_GLOBAL)
        return 2
    print("table = 0x%08X" % tbl)
    if a.check_8c:
        return cmd_check_8c(mem, tbl)
    if a.verify_anchor:
        return cmd_verify_anchor(mem, tbl)
    if a.dump_footprint:
        return cmd_dump_footprint(mem, tbl)
    if a.dump_fp is not None:
        return cmd_dump_fp(mem, a.dump_fp)
    if a.dump_pool:
        return cmd_dump_pool(mem, tbl)
    if a.watch_head is not None:
        return cmd_watch(mem, tbl, a.watch_head, a.secs, a.out)
    return cmd_discover(mem, tbl)


if __name__ == "__main__":
    sys.exit(main())
