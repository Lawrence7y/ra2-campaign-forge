# -*- coding: utf-8 -*-
"""W100 step12: CellClass ctor vtable anchor + full .rdata vtable whitelist build.
Output -> EVIDENCE\\step12_whitelist.txt  (+ EVIDENCE\\vtable_whitelist.txt machine list)
"""
import pefile, capstone, struct, io, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\step12_whitelist.txt"
OUTL = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\vtable_whitelist.txt"

buf = io.StringIO()
class Tee:
    def write(self, s): sys.__stdout__.write(s); buf.write(s)
    def flush(self): pass
sys.stdout = Tee()

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
fh = open(EXE, "rb")
def read(va, n):
    fh.seek(pe.get_offset_from_rva(va - IB)); return fh.read(n)
fh.seek(pe.get_offset_from_rva(0x1000)); text = fh.read(0x3E0000)
fh.seek(pe.get_offset_from_rva(0x3E1000)); rdata = fh.read(0x31000)
TVA, RVA_ = 0x401000, 0x7E1000
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

TEXT_LO, TEXT_HI = 0x401000, 0x401000 + 0x3DF38D
RD_LO, RD_HI = RVA_, RVA_ + 0x30074

def is_text(va): return TEXT_LO <= va < TEXT_HI
def is_rdata(va): return RD_LO <= va < RD_HI
def rd32(buf_, off): return struct.unpack_from("<I", buf_, off)[0]

print("=== 0x47BBF0 (CellClass ctor) head ===")
for ins in md.disasm(read(0x0047BBF0, 0x30), 0x0047BBF0):
    print("0x%08X: %-16s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
print()

# --- WhatAmI thunk map: B8 imm32 C3 within .text ---
thunk = {}
i = 0
n = len(text)
while i < n - 6:
    if text[i] == 0xB8 and text[i+5] == 0xC3:
        imm = rd32(text, i+1)
        if 0 < imm <= 0xFF:
            thunk.setdefault(TVA + i, imm)
    i += 1
print("WhatAmI-style 'mov eax,imm8; ret' thunks in .text: %d" % len(thunk))
thunk_by_target = {t: v for t, v in thunk.items()}
print()

# --- exec-pointer runs in .rdata ---
rd_words = [rd32(rdata, k*4) for k in range(len(rdata)//4)]
def is_exec_ptr(w): return is_text(w)
runs = []  # (start_word_index, length)
k = 0
W = len(rd_words)
while k < W:
    if is_exec_ptr(rd_words[k]):
        j = k
        while j < W and is_exec_ptr(rd_words[j]):
            j += 1
        runs.append((k, j - k))
        k = j
    else:
        k += 1
print("exec-pointer runs in .rdata: %d  (total exec words: %d)" %
      (len(runs), sum(l for _, l in runs)))
long_runs = [r for r in runs if r[1] >= 8]
print("runs with length>=8: %d" % len(long_runs))
print()

def word_va(idx): return RVA_ + idx*4

# --- Set A: slot11 (+0x2C) WhatAmI-thunk anchor (regardless of prev dword) ---
setA = {}
for (rs, rl) in runs:
    # every word in a run could be a vtable start whose +0x2C (slot 11) is a thunk
    for k in range(rs, rs + rl):
        d = rd_words[k]
        s11_off = k + 11
        if s11_off >= W: continue
        if not is_exec_ptr(rd_words[s11_off]): continue
        tgt = rd_words[s11_off]
        if tgt in thunk_by_target:
            N = thunk_by_target[tgt]
            if N <= 0x80:
                setA[d] = N
print("Set A (slot11-WhatAmI anchor vtable starts): %d" % len(setA))
import collections
ns = collections.Counter(setA.values())
print("N distribution: " + ", ".join("N=%d x%d" % (v, c) for v, c in sorted(ns.items())))
missing = [x for x in range(1, 74) if x not in set(setA.values())]
print("N missing in 1..73: %s" % missing)
bigN = {d: v for d, v in setA.items() if v > 0x80}
print("big-N (suspect false positives): %d" % len(bigN))
print()

# --- Set B: structural start: prev word NOT exec ptr, run length>=8 ---
setB = []
for (rs, rl) in long_runs:
    prev_ok = (rs == 0) or (not is_exec_ptr(rd_words[rs-1]))
    if prev_ok:
        setB.append(word_va(rs))
print("Set B (structural run starts, prev-not-exec): %d" % len(setB))
print()

# --- anchors cross-check ---
def slot11_of(d):
    off = (d - RVA_)//4 + 11
    return rd_words[off] if 0 <= off < W else 0

for va, lbl in ((0x007E3EBC, "R09 anchor: WhatAmI()==6 vtable"),
                (0x007EB058, "Lead anchor: Infantry vtable (slot107=0x51BF90, slot11=0x523340 N=15)")):
    off = (va - RVA_)//4
    s11 = rd_words[off + 11]
    s107 = rd_words[off + 107] if off + 107 < W else 0
    print("%s: 0x%08X slot11=0x%08X slot107=0x%08X inSetA=%s" %
          (lbl, va, s11, s107, va in setA))
    if s11 in thunk_by_target:
        print("   slot11 decodes: mov eax,%d; ret" % thunk_by_target[s11])
print()

# --- combined whitelist ---
whitelist = sorted(set(setA.keys()) | set(setB))
print("combined whitelist size: %d" % len(whitelist))
# sample
print("first 20: " + ", ".join("0x%08X" % v for v in whitelist[:20]))
print("0x7EB058 in whitelist: %s ; 0x7E3EBC in whitelist: %s" %
      (0x7EB058 in whitelist, 0x7E3EBC in whitelist))

sys.stdout = sys.__stdout__
with open(OUT, "w", encoding="utf-8") as o:
    o.write(buf.getvalue())
with open(OUTL, "w", encoding="utf-8") as o:
    o.write("# vtable whitelist (VA per line) -- generated by work/step12_whitelist.py\n")
    for v in whitelist:
        o.write("0x%08X %s\n" % (v, setA.get(v, "")))
print("saved -> " + OUT + " , " + OUTL)
