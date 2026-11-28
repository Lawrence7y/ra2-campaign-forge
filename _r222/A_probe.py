# -*- coding: utf-8 -*-
"""R222-A: ADPCM codec static forensics, one-shot script."""
import sys, struct, hashlib
from collections import Counter
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import *

OUT = []
def w(s=''):
    OUT.append(str(s))

RAW = P.RAW
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.detail = False

LO, HI = 0x7c6000, 0x7c8000
buf = RAW[P.r2o(LO):P.r2o(LO)+(HI-LO)]
insns = list(md.disasm(buf, LO))

w('=== R222-A ADPCM codec forensics (measured) ===')
w('source_sha256 ' + hashlib.sha256(RAW).hexdigest())
w('range 0x%x..0x%x len %d insns %d' % (LO, HI, HI-LO, len(insns)))

# ---------- T1 ----------
w('\n=== T1 prologue hits (55 8b ec) ===')
pat = bytes((0x55, 0x8b, 0xec))
t1 = []
p = 0
while True:
    i = buf.find(pat, p)
    if i < 0: break
    t1.append(LO+i)
    p = i+1
w('count %d' % len(t1))
w('addresses ' + ' '.join(hex(a) for a in t1))

# ---------- helpers ----------
rdw = lambda va: struct.unpack_from('<I', RAW, P.r2o(va))[0]
rdw_s = lambda va: struct.unpack_from('<i', RAW, P.r2o(va))[0]
rdw16 = lambda va: struct.unpack_from('<H', RAW, P.r2o(va))[0]
rdw16s = lambda va: struct.unpack_from('<h', RAW, P.r2o(va))[0]

# ---------- T2 ----------
w('\n=== T2 jump tables ===')
for base, n in ((0x7c7758, 8), (0x7c7778, 4)):
    w('table %s count %d' % (hex(base), n))
    for i in range(n):
        va = rdw(base+4*i)
        w('  [%d] 0x%08x dec %d sec %s' % (i, va, va, P.sec_of(va)))

# ---------- T3 ----------
w('\n=== T3 add eax,[edx*2+0x879b30] ===')
TARGET_TXT = 'eax, dword ptr [edx*2 + 0x879b30]'
t3 = [ins.address for ins in insns if ins.op_str == TARGET_TXT and ins.mnemonic == 'add']
w('count %d' % len(t3))
w('addresses ' + ' '.join(hex(a) for a in t3))
diffs = Counter(t3[i+1]-t3[i] for i in range(len(t3)-1))
w('diff_histogram ' + ' '.join('%d:%d' % (k, v) for k, v in sorted(diffs.items())))

# ---------- T4 ----------
w('\n=== T4 three unrolled bodies isomorphism ===')
BASES = [0x7c7428, 0x7c77f0, 0x7c7bc0]
# measured body ends from T3: next sample-start minus small gap; last body ends at its T3 tail + 0x2d
BODY_ENDS = [0x7c75b2, 0x7c7982, 0x7c7d4a]

def norm_seq(lo, hi):
    seq = []
    for ins in insns:
        if not (lo <= ins.address < hi): continue
        import re
        opt = re.sub(r'0x[0-9a-f]+',
                     lambda m: ('0x%x' % (int(m.group(), 16)-lo))
                     if lo <= int(m.group(), 16) < hi else '0x%s' % ('ABS_' + m.group()[2:]),
                     ins.op_str)
        seq.append((ins.mnemonic, opt))
    return seq

# use measured T3-derived bodies where possible; keep card bases otherwise
w('candidate_bases ' + ' '.join(hex(b) for b in BASES))
seqs = []
for i, b in enumerate(BASES):
    hi = BODY_ENDS[i]
    seq = norm_seq(b, hi)
    seqs.append(seq)
    w('body[%d] 0x%x..0x%x insns %d' % (i, b, hi, len(seq)))

for a in range(3):
    for b in range(a+1, 3):
        sa, sb = seqs[a], seqs[b]
        n = min(len(sa), len(sb))
        same = sum(1 for j in range(n) if sa[j] == sb[j])
        first = next((j for j in range(n) if sa[j] != sb[j]), None)
        if first is None and len(sa) != len(sb):
            first = n
        w('cmp %d-%d same %d/%d first_diff %s' % (
            a, b, same, n, ('none' if first is None else str(first))))
        if first is not None and first < n:
            w('  at %d: body%d=%s body%d=%s' % (
                first, a, sa[first], b, sb[first]))
w('body sample offsets (T3 measured): ' + ' '.join(
    '[%d]%s' % (k, ','.join(hex(x-base) for x in t3 if base <= x < BODY_ENDS[k]))
    for k, base in enumerate(BASES)))

# ---------- T5 ----------
w('\n=== T5 dispatch matrix 0x7c7371..0x7c73d3 ===')
for ins in insns:
    if 0x7c7371 <= ins.address < 0x7c73d3:
        w('  0x%x  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))
w('--- dispatch epilogue/replay from 0x7c75a1 ---')
for ins in insns:
    if 0x7c75a1 <= ins.address < 0x7c75cc:
        w('  0x%x  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))
for ins in insns:
    if ins.address >= 0x7c75cc and ins.address < 0x7c75cc+0x60:
        w('  0x%x  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))

# ---------- T6 ----------
w('\n=== T6 replay dispatch targets ===')
targets = [rdw(0x7c7758+4*i) for i in range(8)]
for i, t in enumerate(targets):
    w('index %d target 0x%x sec %s' % (i, t, P.sec_of(t)))
    sub_edi = None
    sub_esi = 0
    jmp_t = None
    o = P.r2o(t)
    if o is None:
        w('  UNREADABLE')
        continue
    for ins in md.disasm(RAW[o:o+0x90], t):
        if ins.mnemonic == 'sub' and ins.op_str.startswith('edi, '):
            v = ins.op_str[5:]
            if v.startswith('0x'):
                sub_edi = int(v, 16)
            else:
                sub_edi = int(v)
            break
    for ins in md.disasm(RAW[o:o+0x90], t):
        if ins.mnemonic == 'sub' and ins.op_str.startswith('esi, '):
            v = ins.op_str[5:]
            sub_esi = int(v, 16) if v.startswith('0x') else int(v)
            break
    for ins in md.disasm(RAW[o:o+0x90], t):
        if ins.mnemonic == 'jmp' and ins.op_str.startswith('0x'):
            jmp_t = int(ins.op_str, 16)
            break
    w('  sub_edi %s sub_esi %s jmp %s' % (
        ('NONE' if sub_edi is None else str(sub_edi)),
        str(sub_esi), ('NONE' if jmp_t is None else hex(jmp_t))))

# ---------- T7 ----------
w('\n=== T7 inline delta vs table 0x879b30 ===')
step = [rdw16(0x8758e4 + 2*m) for m in range(89)]
tbl = lambda m, n: rdw_s(0x879b30 + 4*(16*m+n))
def inline(s, n, mode='bit'):
    d = (s >> 3) + (s if n & 4 else 0) + ((s >> 1) if n & 2 else 0) + ((s >> 2) if n & 1 else 0)
    neg = bool(n & 8) if mode == 'bit' else (n >= 8)
    return -d if neg else d
for mode in ('bit', 'ge'):
    hit = 0
    first_mis = None
    for m in range(89):
        for n in range(16):
            if inline(step[m], n, mode) == tbl(m, n):
                hit += 1
            elif first_mis is None:
                first_mis = (m, n, inline(step[m], n, mode), tbl(m, n))
    w('%s: hits %d/1424 first_mismatch %s' % (mode, hit, first_mis))
# C2: shifted step base
step2 = [rdw16(0x8758e6 + 2*m) for m in range(89)]
hit2 = sum(1 for m in range(89) for n in range(16) if inline(step2[m], n) == tbl(m, n))
w('C2 shifted step base 0x8758e6 hits %d/1424' % hit2)
# C3 control: read T3 target as 0x87b170 dwords, count matches
hit3 = sum(1 for ins in insns if ins.op_str == 'eax, dword ptr [edx*2 + 0x87b170]' and ins.mnemonic == 'add')
w('C3 T3 with 0x87b170 hits %d' % hit3)

# ---------- T8 ----------
w('\n=== T8 index update vs 0x8758c4 ===')
idx8 = [rdw16s(0x8758c4 + 2*i) for i in range(8)]
w('0x8758c4 words ' + ' '.join(str(v) for v in idx8))
w('0x8758c4 bytes ' + RAW[P.r2o(0x8758c4):P.r2o(0x8758c4)+16].hex())
w('0x8758d4 bytes ' + RAW[P.r2o(0x8758d4):P.r2o(0x8758d4)+16].hex())
w('16B_equal_0x8758c4_vs_0x8758d4 %s' % (
    RAW[P.r2o(0x8758c4):P.r2o(0x8758c4)+16] ==
    RAW[P.r2o(0x8758d4):P.r2o(0x8758d4)+16]))
for ins in insns:
    if 0x7c639b <= ins.address < 0x7c63c3:
        w('  0x%x  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))

# ---------- T9 ----------
w('\n=== T9 absolute-disp references in .text ===')
refaddrs = [0x8758c4, 0x8758d4, 0x8758e4, 0x8759b4, 0x876ff4, 0x877b14,
            0x877c14, 0x879b30, 0x87b170, 0x87bc90, 0x87bd90, 0x7c7758, 0x7c7778]
textsec = P.B['.text']
tstart, tend = textsec['lo'], textsec['hi_file']
tbody = RAW[textsec['rawptr']:textsec['rawptr']+(tend-tstart)]
# scan for 4-byte LE patterns and verify with disasm_lite linear pass
pats = {a: struct.pack('<I', a) for a in refaddrs}
raw_hits = {a: [] for a in refaddrs}
for a, pat in pats.items():
    p = 0
    while True:
        i = tbody.find(pat, p)
        if i < 0: break
        raw_hits[a].append(tstart+i)
        p = i+1
verified = {a: [] for a in refaddrs}
for va, sz, mnem, ops in md.disasm_lite(tbody, tstart):
    o = P.r2o(va)
    ib = RAW[o:o+sz]
    for a, pat in pats.items():
        if pat in ib:
            verified[a].append(va)
for a in refaddrs:
    w('%s count %d first3 %s' % (
        hex(a), len(verified[a]), ','.join(hex(x) for x in verified[a][:3])))

# ---------- T10 explicit summary ----------
w('\n=== T10 anti-controls summary ===')
bit_hit = sum(1 for m in range(89) for n in range(16) if inline(step[m], n, 'bit') == tbl(m, n))
ge_hit = sum(1 for m in range(89) for n in range(16) if inline(step[m], n, 'ge') == tbl(m, n))
w('C1 sign test n&8 vs n>=8 equivalent: %s (%d vs %d of 1424)' % (
    bit_hit == ge_hit, bit_hit, ge_hit))
w('C2 step base 0x8758e6 shifted: %d/1424' % hit2)
w('C3 T3 operand table 0x87b170 instead of 0x879b30: %d hits' % hit3)

open('/home/t628/projects/ra2-campaign-forge/_r222/A_out.txt', 'w').write('\n'.join(OUT)+'\n')
print('\n'.join(OUT))
