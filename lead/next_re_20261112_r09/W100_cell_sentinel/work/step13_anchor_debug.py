# -*- coding: utf-8 -*-
"""W100 step13: debug whitelist anchors; pure slot11-anchor scan over ALL rdata dwords.
Output -> EVIDENCE\\step13_anchor_debug.txt
"""
import pefile, struct, io, sys, collections

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\step13_anchor_debug.txt"

buf = io.StringIO()
class Tee:
    def write(self, s): sys.__stdout__.write(s); buf.write(s)
    def flush(self): pass
sys.stdout = Tee()

pe = pefile.PE(EXE, fast_load=True)
fh = open(EXE, "rb")
def read(va, n):
    fh.seek(pe.get_offset_from_rva(va - 0x400000)); return fh.read(n)
fh.seek(pe.get_offset_from_rva(0x3E1000)); rdata = fh.read(0x31000)
fh.seek(pe.get_offset_from_rva(0x1000)); text = fh.read(0x3E0000)

RVA_ = 0x7E1000
TEXT_LO, TEXT_HI = 0x401000, 0x401000 + 0x3DF38D
W = len(rdata)//4
rd = struct.unpack_from("<%dI" % W, rdata, 0)
def word_va(i): return RVA_ + i*4
def is_exec(w): return TEXT_LO <= w < TEXT_HI

# thunk map
thunk = {}
i = 0
n = len(text)
while i < n - 6:
    if text[i] == 0xB8 and text[i+5] == 0xC3:
        imm = struct.unpack_from("<i", text, i+1)[0]
        if 0 < imm <= 0xFF:
            thunk[TVA_ := (0x401000 + i)] = imm
    i += 1

def dbg(va):
    off = (va - RVA_)//4
    print("=== 0x%08X (word %d) ===" % (va, off))
    for d in range(-3, 14):
        k = off + d
        v = rd[k] if 0 <= k < W else 0
        mark = ""
        if d == 11 and 0 <= k < W:
            mark = "  <- slot11"
            if is_exec(v) and v in thunk:
                mark += " THUNK N=%d" % thunk[v]
        print("  [%+3d] 0x%08X: 0x%08X %s" % (d, word_va(k) if 0 <= k < W else 0, v, mark))
    prev = rd[off-1] if off >= 1 else 0
    print("  prev word exec? %s" % is_exec(prev))
    print()

dbg(0x007E3EBC)
dbg(0x007EB058)

# pure anchor scan: any dword D anywhere in rdata (as a VALUE? no - as a LOCATION):
# vtable start = a LOCATION whose slot11 target is a WhatAmI thunk. Scan locations k:
#   D = rd[k]; require rd[k+11] exec and in thunk and N<=0x80. Also require rd[k] itself exec (vptr must be a code ptr slot0).
pure = {}
for k in range(W - 11):
    if not is_exec(rd[k]):
        continue
    t = rd[k+11]
    if is_exec(t) and t in thunk:
        N = thunk[t]
        if N <= 0x80:
            pure[word_va(k)] = N
print("pure anchor scan (no run requirement): %d candidate starts" % len(pure))
ns = collections.Counter(pure.values())
print("N distribution: " + ", ".join("N=%d x%d" % (v, c) for v, c in sorted(ns.items())))
missing = [x for x in range(1, 74) if x not in set(pure.values())]
print("N missing in 1..73: %s" % missing)
print("0x7E3EBC in pure: %s ; 0x7EB058 in pure: %s" % (0x7E3EBC in pure, 0x7EB058 in pure))
print()

# restrict: slot0..slot10 ALL exec (a real vtable prefix) — kills data that happens to point at thunks
strict = {}
for k in range(W - 11):
    ok = True
    for j in range(0, 11):
        if not is_exec(rd[k+j]):
            ok = False; break
    if not ok:
        continue
    t = rd[k+11]
    if is_exec(t) and t in thunk and thunk[t] <= 0x80:
        strict[word_va(k)] = thunk[t]
print("strict anchor (slots0..10 all exec + slot11 thunk): %d" % len(strict))
ns = collections.Counter(strict.values())
print("N distribution: " + ", ".join("N=%d x%d" % (v, c) for v, c in sorted(ns.items())))
missing = [x for x in range(1, 74) if x not in set(strict.values())]
print("N missing in 1..73: %s" % missing)
print("0x7E3EBC in strict: %s ; 0x7EB058 in strict: %s" % (0x7E3EBC in strict, 0x7EB058 in strict))
uniq = {}
for va, N in strict.items():
    uniq.setdefault(N, []).append(va)
multi = {N: vas for N, vas in uniq.items() if len(vas) > 1}
print("N shared by >1 candidate: %s" % {N: len(v) for N, v in multi.items()})
print()

# sample strict list
print("strict sample (first 40):")
for va in list(strict)[:40]:
    print("  0x%08X N=%d" % (va, strict[va]))

sys.stdout = sys.__stdout__
open(OUT, "w", encoding="utf-8").write(buf.getvalue())
print("saved -> " + OUT)
