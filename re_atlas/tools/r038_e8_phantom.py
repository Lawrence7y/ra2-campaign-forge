# -*- coding: utf-8 -*-
"""R-038: independently reproduce V-001's "560 phantom E8 roots" claim.

C session (xverify V-001) reports that of R-035's 7,279 E8 targets, 560 come
from a 0xE8 byte that is NOT the start of a real `call` instruction -- it is an
operand byte of some other instruction.  If true, LOWER 13,352 is an UPPER
bound, not a lower bound, and D-02's frozen figure is wrong in direction.

This is exactly the "naive byte scan is deceived" trap.  The claim must be
reproduced independently before I change any published number, because the two
readings differ in what they count:

  byte scan   : every 0xE8 byte in .text, take the following rel32
  aligned     : only 0xE8 bytes that capstone says begin a `call` instruction

The test: decode .text linearly with capstone from the section start, collect
every real `call rel32` target; compare with the byte-scan set.  Then, for the
difference, verify each 0xE8 is inside another instruction (not merely at a
different offset due to a desync).

CAVEAT that decides everything: linear sweep from the section start desyncs on
data embedded in .text (documented in fn_walk.py's docstring: "a linear capstone
sweep decodes only ~11% of .text here").  So a naive aligned set is NOT
authoritative either.  The right test is per-address: for each byte-scan target,
re-decode from a known-good boundary and ask whether that 0xE8 starts a call.

Run: python re_atlas/tools/r038_e8_phantom.py
"""

import json
import re
import struct
import sys

import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"

IB = 0x400000
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
TLO, THI = 0x401000, 0x7E1000
SECTIONS = [
    (0x001000, 0x3DF38D, 0x001000, 0x3E0000),
    (0x3E1000, 0x030074, 0x3E1000, 0x031000),
    (0x412000, 0x367BE4, 0x412000, 0x06C000),
]
RAW = open(EXE, "rb").read()


def read_va(va, n):
    rva = va - IB
    for s_rva, _vs, rp, rs in SECTIONS:
        if s_rva <= rva < s_rva + rs:
            o = rp + (rva - s_rva)
            return RAW[o:o + n]
    return b""


TEXT = read_va(TLO, THI - TLO)
NT = len(TEXT)
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True

import hashlib
print(f"sha256 = {hashlib.sha256(RAW).hexdigest()}")
print(f"anchor = {SHA256}")
print(f"match  = {hashlib.sha256(RAW).hexdigest() == SHA256}\n")

# ---------------------------------------------------------------- byte scan
e8_sites = []          # VA of every 0xE8 byte in .text
e8_targets = set()
for m in re.finditer(b"\xe8", TEXT):
    i = m.start()
    if i + 5 > NT:
        continue
    d = struct.unpack_from("<i", TEXT, i + 1)[0]
    t = TLO + i + 5 + d
    if TLO <= t < THI:
        e8_sites.append(TLO + i)
        e8_targets.add(t)

print(f"byte-scan: 0xE8 bytes with in-range target = {len(e8_sites):,}")
print(f"byte-scan: distinct E8 targets            = {len(e8_targets):,}"
      f"   [R-035 reports 7,279]")

# ---------------------------------------------------------------- linear decode
# Decode .text from its start, recording which addresses begin a real `call`.
call_starts = set()
call_targets = set()
insn_start = set()
desync_stops = 0
cur = TLO
while cur < THI:
    off = cur - TLO
    got = None
    for insn in MD.disasm(TEXT[off:off + 16], cur):
        got = insn
        break
    if got is None:
        desync_stops += 1
        cur += 1
        continue
    insn_start.add(got.address)
    if got.mnemonic == "call" and got.operands and \
       got.operands[0].type == capstone.x86.X86_OP_IMM:
        call_starts.add(got.address)
        t = got.operands[0].imm
        if TLO <= t < THI:
            call_targets.add(t)
    cur += got.size

print(f"\nlinear decode from .text start: desync points = {desync_stops:,}")
print(f"  instruction starts recorded = {len(insn_start):,}")
print(f"  real `call rel32` sites     = {len(call_starts):,}")
print(f"  distinct call targets       = {len(call_targets):,}"
      f"   [V-001 reports 6,719]")

# ---------------------------------------------------------------- the difference
phantom = sorted(set(e8_sites) - call_starts)
real = sorted(set(e8_sites) & call_starts)
print(f"\nbyte-scan 0xE8 sites that ARE a real call start : {len(real):,}")
print(f"byte-scan 0xE8 sites that are NOT               : {len(phantom):,}"
      f"   [V-001 reports 560]")

# For each phantom site, confirm the 0xE8 lies inside another instruction.
inside = 0
outside = []
for va in phantom:
    # find the greatest instruction start <= va, then check its extent
    cand = None
    for back in range(1, 16):
        s = va - back
        if s not in insn_start:
            continue
        got = None
        for insn in MD.disasm(read_va(s, 16), s):
            got = insn
            break
        if got is None:
            continue
        if s + got.size > va:
            cand = (s, got)
            break
    if cand is not None:
        inside += 1
    else:
        outside.append(va)

print(f"  ...of those, 0xE8 falls INSIDE another instruction : {inside:,}")
print(f"  ...not attributable to any instruction            : {len(outside):,}")
if outside[:5]:
    print(f"  samples not attributed: {[hex(v) for v in outside[:5]]}")

# ---------------------------------------------------------------- corrected root set
vt = set()
for _k, c in json.load(open(ROOT + r"\re_atlas\evidence\rtti\symbols.json",
                             encoding="utf-8"))["classes"].items():
    for s in c.get("vfuncs") or []:
        try:
            v = int(s, 16)
        except (TypeError, ValueError):
            continue
        if TLO <= v < THI:
            vt.add(v)

PE = 0x7CD80F
lower_bytescan = e8_targets | vt | {PE}
lower_aligned = call_targets | vt | {PE}
print(f"\nLOWER (byte-scan E8)  = {len(lower_bytescan):,}   [R-035: 13,352]")
print(f"LOWER (aligned call)  = {len(lower_aligned):,}   [V-001: 12,792]")
print(f"difference            = {len(lower_bytescan) - len(lower_aligned):,}")

# Are the phantom targets actually distinct addresses that only the phantom
# bytes pointed at?  If a target is ALSO reachable from a real call, removing
# the phantom source does not remove the target.
phantom_targets = set()
for m in re.finditer(b"\xe8", TEXT):
    i = m.start()
    va = TLO + i
    if va not in phantom:
        continue
    if i + 5 > NT:
        continue
    d = struct.unpack_from("<i", TEXT, i + 1)[0]
    t = va + 5 + d
    if TLO <= t < THI:
        phantom_targets.add(t)

only_phantom = phantom_targets - call_targets
print(f"\nphantom sources point at {len(phantom_targets):,} distinct targets")
print(f"  of which ONLY phantom sources reach them: {len(only_phantom):,}")
print(f"  of which a real call also reaches them  : "
      f"{len(phantom_targets) - len(only_phantom):,}")
