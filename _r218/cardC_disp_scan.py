# -*- coding: utf-8 -*-
"""R218-C: scan .text for indirect call/jmp with [reg+disp] operand, bucket by slot = disp/4.

Hard anti-OOM rules enforced here:
  - .text is walked in <=64KB chunks
  - each chunk is iterated with md.disasm_lite() (tuples only; no Insn detail objects retained)
  - detail=True is never used at all (not needed for lite-level operand strings)
  - chunk boundaries are carried at real instruction ends, so no mid-instruction decode
"""
import sys, os, re, hashlib
from collections import Counter, defaultdict

sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

SEC = P.B['.text']
LO, RAWOFF, RAWSZ = SEC['lo'], SEC['rawptr'], SEC['rawsize']
CHUNK = 0x10000
GPR = {'eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp'}
REG32 = {'eax','ebx','ecx','edx','esi','edi','ebp','esp','eip'}
MEM_RE = re.compile(r'\bptr\s*\[([^\]]+)\]', re.I)
TERM_RE = re.compile(r'([+-]?)\s*([^+-]+)')
SCALE_RE = re.compile(r'^([A-Za-z][A-Za-z0-9]*)\s*\*\s*(\d+)$')
NUM_RE = re.compile(r'^(?:0[xX][0-9a-fA-F]+|[0-9]+)$')

def parse_mem(inner):
    """Return (base, index, scale, disp) from a bracket expression."""
    base = index = None
    scale = 0
    disp = 0
    for sign, term in TERM_RE.findall(inner.strip()):
        term = term.strip()
        if not term:
            continue
        m = SCALE_RE.match(term)
        if m:
            index = m.group(1).lower()
            scale = int(m.group(2))
            continue
        if NUM_RE.match(term):
            v = int(term, 0)
            disp += -v if sign == '-' else v
            continue
        tl = term.lower()
        if tl in REG32:
            base = tl
            continue
        # unknown token: mark as pseudo-index so it is excluded
        index = '?' + tl
    return base, index, scale, disp

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
md.skipdata = True

hits = []            # accepted: (addr, size, mnem, opstr, base, disp)
excl_indexed = []    # call/jmp mem with an index register
excl_other = []      # call/jmp mem without a valid GPR base
total_insns = 0
cur_va, cur_off, remaining = LO, RAWOFF, RAWSZ
nchunks = 0

while remaining > 0:
    n = min(CHUNK, remaining)
    buf = P.RAW[cur_off:cur_off + n]
    last_addr, last_size, covered = None, 0, 0
    nchunks += 1
    # disasm_lite: yields (address, size, mnemonic, op_str) tuples only -- no detail objects
    for addr, size, mnem, opstr in md.disasm_lite(buf, cur_va):
        total_insns += 1
        last_addr, last_size = addr, size
        m = mnem.lower()
        if m not in ('call', 'jmp'):
            continue
        mm = MEM_RE.search(opstr)
        if not mm:
            continue  # direct call/jmp
        base, index, scale, disp = parse_mem(mm.group(1))
        if index is not None and index != '':
            excl_indexed.append((addr, opstr))
            continue
        if base not in GPR:
            excl_other.append((addr, opstr))
            continue
        hits.append((addr, size, mnem, opstr, base, disp))
    if last_addr is None:
        print('WARN: no instruction decoded in chunk at %#x' % cur_va)
        break
    # advance to the end of the last fully-decoded instruction
    adv = (last_addr + last_size) - cur_va
    if adv <= 0:
        adv = n
    cur_va += adv
    cur_off += adv
    remaining -= adv
    del buf

# ---------- (a) ----------
print('=== R218-C disp scan evidence ===')
print('SECTION .text lo=%#x rawptr=%#x rawsize=%#x chunks=%d instructions=%d' %
      (LO, RAWOFF, RAWSZ, nchunks, total_insns))
print('coverage: va_end=%#x (expect %#x), remaining=%d' % (cur_va, LO + RAWSZ, remaining))
print('(a) total accepted indirect call/jmp [reg+disp] hits = %d' % len(hits))

# ---------- (b) ----------
slot_counter = Counter()
disp_counter = Counter()
for addr, size, mnem, opstr, base, disp in hits:
    disp_counter[disp] += 1
    slot_counter[disp // 4] += 1
top30 = sorted(slot_counter.items(), key=lambda kv: (-kv[1], kv[0]))[:30]
print('(b) slot s=disp//4 distribution TOP30 (s, count):')
for s, c in top30:
    print('   s=%d (disp=%#x) count=%d' % (s, s * 4, c))

# ---------- (c) ----------
hi = [h for h in hits if h[5] >= 0x400]
hi_slots = sorted(set(h[5] // 4 for h in hi))
print('(c) s>=256 (disp>=0x400) hit count = %d' % len(hi))
print('    distinct slot values = %d' % len(hi_slots))
for s in hi_slots:
    ds = sorted(set(h[5] for h in hi if h[5] // 4 == s))
    print('    s=%d disps=%s' % (s, ','.join('%#x' % d for d in ds)))

# ---------- (d) ----------
print('(d) s>=256 hit detail (addr | raw8 | disasm_lite):')
for addr, size, mnem, opstr, base, disp in hi:
    off = P.r2o(addr)
    raw8 = P.RAW[off:off + 8].hex() if off is not None else 'NO_OFF'
    print('   %#x | %s | %s %s | base=%s disp=%#x s=%d' %
          (addr, raw8, mnem, opstr, base, disp, disp // 4))

# ---------- (e) ----------
c2c = [h for h in hits if h[5] == 0x2c]
print('(e) disp==0x2c total hits = %d' % len(c2c))
for addr, size, mnem, opstr, base, disp in c2c:
    mark = ''
    if 0x410210 <= addr < 0x410300:
        mark = '  <-- inside 0x410210 function body (candidate)'
    print('   %#x %s %s [base=%s]%s' % (addr, mnem, opstr, base, mark))
in_body = [h[0] for h in c2c if 0x410210 <= h[0] < 0x410300]
print('   0x410210-body disp==0x2c addresses = %s' %
      (', '.join('%#x' % a for a in in_body) if in_body else 'NONE'))

# ---------- (f) ----------
z = sum(1 for h in hits if h[5] == 0)
print('(f) disp==0 hits = %d ; disp==0x2c hits = %d ; ratio = %.2f' %
      (z, len(c2c), (z / len(c2c) if c2c else float('inf'))))

# ---------- (g) ----------
bad_ge400 = [h for h in hits if h[5] >= 0x400 and h[5] % 4 != 0]
all_nonmult = [h for h in hits if h[5] % 4 != 0]
print('(g) disp>=0x400 AND disp%%4!=0 count = %d (must be 0)' % len(bad_ge400))
for addr, size, mnem, opstr, base, disp in bad_ge400:
    print('   BAD %#x %s %s base=%s disp=%#x' % (addr, mnem, opstr, base, disp))

# ---------- (h) ----------
first64 = [h for h in hits if LO <= h[0] < LO + 0x10000]
print('(h) first-64KB (.text %#x..%#x) hits = %d ; full .text hits = %d ; ratio = %.4f' %
      (LO, LO + 0x10000, len(first64), len(hits),
       (len(first64) / len(hits) if hits else 0.0)))

# ---------- anomalies / uncertainty ----------
print('=== anomalies and uncertainty ===')
print('non-multiple-of-4 disp indirect call/jmp (all): count=%d' % len(all_nonmult))
for addr, size, mnem, opstr, base, disp in all_nonmult:
    print('   %#x %s %s base=%s disp=%#x (%%4=%d)' % (addr, mnem, opstr, base, disp, disp % 4))
print('excluded [reg+index*scale+disp] call/jmp count = %d' % len(excl_indexed))
for addr, opstr in excl_indexed[:40]:
    print('   IDX %#x %s' % (addr, opstr))
print('excluded other-mem call/jmp count = %d' % len(excl_other))
for addr, opstr in excl_other[:40]:
    print('   OTH %#x %s' % (addr, opstr))
print('=== end ===')
