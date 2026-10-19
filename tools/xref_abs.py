#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xref.py - absolute-address cross reference for gamemd.exe (RA2/YR, ImageBase 0x400000).

Scans the whole image for 32-bit little-endian occurrences of a target VA and classifies each hit:
  call  : E8 rel32 resolving to target
  jmp   : E9 rel32 resolving to target
  imm   : the dword appears as a 32-bit immediate/operand right after an opcode byte
  data  : the dword appears inside a data section or not preceded by an opcode

usage:
  python tools/xref.py 0x67D300 [0x67CEF0 ...]
  python tools/xref.py --range 0x67FDF0 0x680F70     # scan a VA range
"""
import struct, sys, argparse, os
sys.stdout.reconfigure(encoding="utf-8")
EXE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ra2youli", "gamemd.exe")
IB = 0x400000

def sections(d):
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    optsz = struct.unpack_from("<H", d, pe + 20)[0]
    off = pe + 24 + optsz
    out = []
    for i in range(nsec):
        o = off + i * 40
        name = d[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
        vs, va, rs, rp = struct.unpack_from("<IIII", d, o + 8)
        out.append(dict(name=name, base=IB + va, vsize=vs, raw=rp, rsize=rs))
    return out

def sec_of(secs, va):
    for s in secs:
        if s["base"] <= va < s["base"] + max(s["vsize"], s["rsize"]):
            return s
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="*", type=lambda x: int(x, 16))
    ap.add_argument("--range", nargs=2, type=lambda x: int(x, 16), default=None)
    ap.add_argument("--exe", default=EXE)
    a = ap.parse_args()
    d = open(a.exe, "rb").read()
    secs = sections(d)
    text = next(s for s in secs if s["name"] == ".text")
    tlo, thi = text["raw"], text["raw"] + text["rsize"]
    targets = list(a.targets)
    if a.range:
        targets = list(range(a.range[0], a.range[1]))
    hits = {t: [] for t in targets}
    tset = set(targets)
    # 1) relative call/jmp
    for o in range(tlo, thi - 5):
        op = d[o]
        if op in (0xE8, 0xE9):
            rel = struct.unpack_from("<i", d, o + 1)[0]
            va = o + 5 + rel + IB
            if va in tset:
                hits[va].append(("call" if op == 0xE8 else "jmp", o + IB))
    # 2) absolute dword occurrences
    for t in targets:
        b = struct.pack("<I", t)
        i = d.find(b)
        while i != -1:
            s = sec_of(secs, i + IB)
            if s and s["name"] == ".text":
                hits[t].append(("imm/text", i + IB))
            else:
                hits[t].append((("data:" + (s["name"] if s else "?")), i + IB))
            i = d.find(b, i + 1)
    for t in targets:
        print("=== 0x%08X  (%d refs)" % (t, len(hits[t])))
        for kind, va in hits[t]:
            print("    %-10s 0x%08X" % (kind, va))

if __name__ == "__main__":
    main()
