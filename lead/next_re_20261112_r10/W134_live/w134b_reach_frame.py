#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W134b: which object-array iterators are reachable from the per-frame update?

Context (ledger §880 / this round):
  `0x48CCC0` is the `Conquer.CPP` game loop.  Its inner loop advances frames by
  calling `0x55D360` once per frame.  So `0x55D360` is the per-frame update.
  The real per-frame cost must therefore be reachable from `0x55D360`.

This script builds a caller->callee map from the binary itself (no reliance on
the Ghidra call-edge log, which turned out to be unparseable), then asks:
  which functions that BOTH reference an object-array Count AND contain a loop
  are reachable from `0x55D360`, and at what depth?

Read-only over the file.
"""
import bisect
import io
import os
import struct
from collections import deque

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
OUT = os.path.dirname(os.path.abspath(__file__))

IB = 0x400000
TRO, TRAWSZ = 0x1000, 0x3E0000
FRAME_FN = 0x0055D360
GAME_LOOP = 0x0048CCC0

ARRAYS = {
    0x00A8EAF8: "Trigger", 0x008B3DD0: "Foot", 0x008B4118: "Unit",
    0x00A83DF8: "Infantry", 0x00A8E3A0: "Aircraft", 0x00A8EB50: "Building",
    0x00A8EC88: "Techno", 0x00A80238: "House", 0x00A80218: "ParticleSys",
    0x00B0F730: "Abstract", 0x00A8ED50: "Bullet", 0x00A8E9B8: "Anim",
}

data = open(EXE, "rb").read()

FNS = []
for ln in io.open(ATLAS, encoding="utf-8").read().splitlines()[1:]:
    p = ln.split("\t")
    if len(p) >= 2:
        try:
            FNS.append((int(p[0], 16), int(p[1])))
        except ValueError:
            pass
FNS.sort()
STARTS = [a for a, _ in FNS]
SIZE = dict(FNS)


def owner(va):
    i = bisect.bisect_right(STARTS, va) - 1
    if i < 0:
        return None
    a, s = FNS[i]
    return a if s and a <= va < a + s else None


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
md.skipdata = True

# ---- per-function scan: callees, has-loop, array refs ----
callees = {}
has_loop = set()
array_refs = {}
call_sites = {}

text = bytes(data[TRO:TRO + TRAWSZ])
n_insn = 0
for ins in md.disasm(text, IB + TRO):
    if ins.id == 0:
        continue
    n_insn += 1
    home = owner(ins.address)
    if home is None:
        continue
    if ins.mnemonic == "call" and ins.op_str.startswith("0x"):
        t = int(ins.op_str, 16)
        callees.setdefault(home, set()).add(t)
        call_sites.setdefault(home, []).append((ins.address, t))
    if ins.mnemonic.startswith("j") and ins.op_str.startswith("0x"):
        t = int(ins.op_str, 16)
        if t < ins.address:
            has_loop.add(home)
    for g, nm in ARRAYS.items():
        if ("0x%x" % g) in ins.op_str:
            array_refs.setdefault(home, {})
            array_refs[home][nm] = array_refs[home].get(nm, 0) + 1

print("instructions decoded      : %d" % n_insn)
print("functions with callees    : %d" % len(callees))
print("functions with a loop     : %d" % len(has_loop))
print("functions referencing arr : %d" % len(array_refs))

iterators = {f for f in array_refs if f in has_loop}
print("object-array iterators    : %d" % len(iterators))

# ---- BFS from the per-frame update ----
print("\n=== reachability from the per-frame update 0x%X ===" % FRAME_FN)
print("(%d callees at depth 1)" % len(callees.get(FRAME_FN, ())))

seen = {FRAME_FN: 0}
q = deque([(FRAME_FN, 0)])
MAXD = 4
while q:
    fn, d = q.popleft()
    if d >= MAXD:
        continue
    for t in callees.get(fn, ()):
        if t in seen:
            continue
        seen[t] = d + 1
        q.append((t, d + 1))

print("reachable functions (depth<=%d): %d" % (MAXD, len(seen)))
by_depth = {}
for f, d in seen.items():
    by_depth[d] = by_depth.get(d, 0) + 1
print("by depth:", dict(sorted(by_depth.items())))

reach_iter = sorted((d, f) for f, d in seen.items() if f in iterators)
print("\n=== object-array iterators reachable from the frame update: %d ==="
      % len(reach_iter))
print("%-8s %-10s %-7s %s" % ("depth", "fn", "size", "array Count refs"))
for d, f in reach_iter:
    print("%-8d 0x%06X %-7s %s"
          % (d, f, SIZE.get(f, "?"),
             ", ".join("%s x%d" % (k, v)
                       for k, v in array_refs.get(f, {}).items())))

not_reach = sorted(iterators - {f for _, f in reach_iter})
print("\n=== iterators NOT reachable from the frame update: %d ===" % len(not_reach))
top = sorted(not_reach, key=lambda f: -SIZE.get(f, 0))[:12]
for f in top:
    print("   0x%06X size=%-6s %s"
          % (f, SIZE.get(f, "?"),
             ", ".join("%s x%d" % (k, v) for k, v in array_refs.get(f, {}).items())))

# ---- also: is the game loop itself reachable/called from anywhere? ----
print("\n=== who calls the Conquer.CPP game loop 0x%X ===" % GAME_LOOP)
callers = [(f, sites) for f, sites in call_sites.items()
           if any(t == GAME_LOOP for _, t in sites)]
for f, sites in callers:
    print("   0x%06X size=%-6s at %s"
          % (f, SIZE.get(f, "?"),
             ", ".join("0x%X" % a for a, t in sites if t == GAME_LOOP)))
