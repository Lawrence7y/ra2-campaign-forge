# -*- coding: utf-8 -*-
"""R-039 probe: aligned-decode re-verification of the 0x68 push-site classes.

R-038's defect class (naive byte scan inflates counts) could also affect the
0x68 (push imm32) sites behind P9/P10/P11 and r036's 6,277-site population.
This probe compares the byte-scan site list against an aligned linear decode
(+1 resync, same method as r038) and reports the per-class delta plus the
full detail of any non-aligned site.

Run: python re_atlas/tools/r039_push_aligned.py
"""
import re
import struct

import capstone

IB = 0x400000
TLO, THI = 0x401000, 0x7E1000
SEC = [(0x001000, 0x3DF38D, 0x001000, 0x3E0000),
       (0x3E1000, 0x030074, 0x3E1000, 0x031000),
       (0x412000, 0x367BE4, 0x412000, 0x06C000)]
RAW = open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", "rb").read()

import hashlib
print("sha256[:16]:", hashlib.sha256(RAW).hexdigest()[:16],
      "(anchor 73201cc021497c95)")


def rv(va, n):
    r = va - IB
    for s, _v, rp, rs in SEC:
        if s <= r < s + rs:
            return RAW[rp + (r - s):rp + (r - s) + n]
    return b""


TEXT = rv(TLO, THI - TLO)
NT = len(TEXT)
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True
XS = capstone.x86

PATHRE = re.compile(r"[\\/].*\.(cpp|h|c|hpp)$", re.I)
IDENT = re.compile(r"^[A-Za-z_~][A-Za-z0-9_:~<>@$]*$")
FMTSPEC = re.compile(r"%[-+ #0-9.*lhI]*[diouxXeEfgGaAcCsp%]")

starts = {}
for rva, rp, rs in ((0x3E1000, 0x3E1000, 0x031000), (0x412000, 0x412000, 0x06C000)):
    blob = RAW[rp:rp + rs]
    for m in re.finditer(rb"[\x20-\x7E]{4,400}", blob):
        starts[IB + rva + m.start()] = m.group().decode("ascii", "replace")
PREFIX = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_~][A-Za-z0-9_]*)+)")
pref = {va: PREFIX.match(s.rstrip()).group(1) for va, s in starts.items()
        if PREFIX.match(s.rstrip())}


def cls(imm):
    b = rv(imm, 400)
    z = b.find(b"\0")
    if z < 0 or z < 4:
        return None, None
    s = b[:z]
    if any(c < 0x20 or c > 0x7E for c in s):
        return None, None
    t = s.decode("ascii")
    if PATHRE.search(t):
        return "path", t
    if IDENT.match(t):
        return "ident", t
    if FMTSPEC.search(t):
        return "format", t
    return "text", t


bsites = []
for m in re.finditer(rb"\x68", TEXT):
    i = m.start()
    if i + 5 > NT:
        continue
    va = TLO + i
    imm = struct.unpack_from("<I", TEXT, i + 1)[0]
    k, t = cls(imm)
    if k is None and imm in pref:
        k, t = "name", pref[imm]
    if k:
        bsites.append((va, imm, k, t))

tot = {k: sum(1 for x in bsites if x[2] == k)
       for k in ("path", "format", "text", "ident", "name")}
print("byte-scan totals:", tot, "sum", len(bsites))
print("expected (r036): path=1299 format=351 text=939 ident=3688 name=35  sum=6312")

insn = {}
cur = TLO
desync = 0
while cur < THI:
    off = cur - TLO
    g = None
    for ins in MD.disasm(TEXT[off:off + 16], cur):
        g = ins
        break
    if g is None:
        desync += 1
        cur += 1
        continue
    insn[g.address] = (g.mnemonic, g.size,
                       [(o.type, o.imm) for o in g.operands])
    cur += g.size
print(f"decoded: {len(insn):,} instrs, {desync} resync points")

bad = []
for va, imm, k, t in bsites:
    d = insn.get(va)
    if d and d[0] == "push" and any(ot == XS.X86_OP_IMM and oi == imm
                                    for ot, oi in d[2]):
        continue
    bad.append((va, imm, k, t))
print("non-aligned:", len(bad))
for va, imm, k, t in bad:
    print(f"  0x{va:08X} imm=0x{imm:08X} class={k} str={t[:50]!r}")
    for back in range(1, 16):
        p = insn.get(va - back)
        if p and (va - back) + p[1] > va:
            print(f"    covered by insn @0x{va - back:08X} `{p[0]}` "
                  f"size={p[1]} operands={p[2]}")
            break

# aligned per-class totals
okk = {}
for va, imm, k, t in bsites:
    if (va, imm, k, t) in bad:
        continue
    okk[k] = okk.get(k, 0) + 1
print("aligned totals:", {k: okk.get(k, 0) for k in tot},
      "sum", sum(okk.values()))
