# -*- coding: utf-8 -*-
# R216 audit (deepseek): A6 fixed (slot0 = dw(view_start)) + A7 law W
import sys, struct, json, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CsError

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MDskip = Cs(CS_ARCH_X86, CS_MODE_32); MDskip.skipdata = True

D = json.load(open('/home/t628/projects/ra2-campaign-forge/_r216/audit_ds_views.json'))
VIEWS = {int(k, 16): v for k, v in D['views'].items()}
COLA = {int(k, 16): v for k, v in D['cola'].items()}
UNIQ = {int(k, 16): v for k, v in D['preamble2view'].items()}
VM = {st: COLA[c][0] for c, st in UNIQ.items()}
def blob(va, n):
    o = P.r2o(va); return P.RAW[o:o+n]

print("== A6 law U (slot0 = first slot value) ==")
nz = [st for st in VM if VM[st] != 0]
cand = 0; ok = 0; bad = []; nonshape = []
for st in sorted(nz):
    m = VM[st]; sl = VIEWS[st]
    if not sl: nonshape.append((st, m, 'empty')); continue
    s0 = sl[0]
    ins = list(MD.disasm_lite(blob(s0, 16), s0))
    if len(ins) < 2: nonshape.append((st, m, 'short')); continue
    a0, a1 = ins[0], ins[1]
    mm = re.match(r'^(sub|add)\s+dword ptr \[esp \+ 4\],\s*(0x[0-9a-f]+|\d+)$', '%s %s' % (a0[2], a0[3]))
    if not mm: nonshape.append((st, m, '%s %s' % (a0[2], a0[3]))); continue
    op = mm.group(1); N = int(mm.group(2), 0)
    if op == 'add': N = -N
    if a1[2] != 'jmp': nonshape.append((st, m, '%s %s' % (a1[2], a1[3]))); continue
    tgt = int(a1[3], 16)
    if tgt not in VM: nonshape.append((st, m, 'jmp-out %08x' % tgt)); continue
    cand += 1
    want = m - VM[tgt]
    if N == want: ok += 1
    else: bad.append((st, m, s0, tgt, VM[tgt], N, want))
print(" mdisp!=0 views=%d ; adjustor-shaped=%d ; N==mdisp-t.mdisp=%d ; counterexamples=%d ; non-shaped=%d"
      % (len(nz), cand, ok, len(bad), len(nonshape)))
for b in bad[:8]: print("   BAD self=%08x m=%d slot0=%08x tgt=%08x tm=%d N=%d want=%d" % b)
for b in nonshape[:8]: print("   NONSHAPE self=%08x m=%d : %s" % b)
print(" A6:", "PASS" if (len(nz) == 260 and cand == 101 and ok == 101 and not bad) else "FAIL")

# ---------------- A7 law W ----------------
VSET = set(VIEWS.keys())
text = P.B['.text']
CH = 0x10000
lo, hi = text['lo'], text['hi_file']

def regname(s): return s.strip()

class St:
    def __init__(self):
        self.d = {}
    def clear(self): self.d.clear()
    def define(self, r, v=0): self.d[r] = v
    def get(self, r): return self.d.get(r)

S = St()
c7 = 0; imm_hit = 0; solved = 0; eq = 0; ne = 0; diffs = []; unsolved = 0
idx_sites = 0
va = lo
prev_end = lo
while va < hi:
    n = min(CH, hi - va)
    for off, sz, mn, ops in MDskip.disasm_lite(blob(va, n), va):
        if off < prev_end: continue
        prev_end = off + sz
        raw = blob(off, sz)
        # ---- state updates (before checking the site, since site's own base is read)
        if mn == 'call':
            for r in ('eax', 'ecx', 'edx'): S.d.pop(r, None)
        elif mn == 'ret':
            S.clear()
        if mn == 'mov' and raw and raw[0] in (0x88, 0x89, 0x8a, 0x8b, 0xb8, 0xb9, 0xba, 0xbb, 0xbe, 0xbf, 0x68):
            m = re.match(r'^([a-z0-9]{2,3}),\s*(.+)$', ops)
            if m and '[' not in m.group(1) and 'ptr' not in m.group(1):
                S.define(m.group(1), 0)
        elif mn == 'lea':
            m = re.match(r'^([a-z0-9]{2,3}),\s*\[([a-z0-9]{2,3})(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]$', ops)
            if m:
                d, s2, k = m.group(1), m.group(2), m.group(3)
                base = S.get(s2) if s2 in S.d else (0 if s2 == s2 else None)
                if s2 in S.d or s2 in ('eax','ebx','ecx','edx','esi','edi','ebp','esp'):
                    v = (S.get(s2) or 0) + (int(k, 0) if k else 0)
                    S.define(d, v)
        elif mn in ('add', 'sub'):
            m = re.match(r'^([a-z0-9]{2,3}),\s*(0x[0-9a-f]+|\d+)$', ops)
            if m and m.group(1) in S.d:
                v = int(m.group(2), 0)
                S.d[m.group(1)] = S.d[m.group(1)] + v if mn == 'add' else S.d[m.group(1)] - v
            elif m:
                S.d.pop(m.group(1), None)
        elif mn in ('xor',):
            m = re.match(r'^([a-z0-9]{2,3}),\s*([a-z0-9]{2,3})$', ops)
            if m and m.group(1) == m.group(2): S.define(m.group(1), 0)
        elif mn in ('pop',):
            if re.match(r'^[a-z0-9]{2,3}$', ops): S.define(ops, 0)
        # ---- C7 site
        if mn == 'mov' and len(raw) >= 2 and raw[0] == 0xC7 and (raw[1] & 0x38) == 0:
            c7 += 1
            m = re.match(r'^dword ptr \[([a-z0-9]{2,3})(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\],\s*(0x[0-9a-f]+)$', ops)
            if 'dword ptr [' in ops and ',' in ops and '*' in ops:
                idx_sites += 1; continue
            if not m: continue
            r = m.group(1); disp = int(m.group(2), 0) if m.group(2) else 0
            imm = int(m.group(3), 16)
            if imm not in VSET: continue
            imm_hit += 1
            if r not in S.d:
                unsolved += 1; continue
            solved += 1
            delta = S.d[r]
            diff = disp + delta - VM[imm]
            if diff == 0: eq += 1
            else: ne += 1; diffs.append(diff)
    va += n

print("\n== A7 law W ==")
print(" C7/0 dword-imm stores in .text = %d" % c7)
print("   (indexed-address ones skipped: %d)" % idx_sites)
print(" imm in view-start set = %d" % imm_hit)
print(" delta solved = %d ; unsolved = %d" % (solved, unsolved))
print(" disp+delta==mdisp : %d ; != : %d" % (eq, ne))
if diffs:
    print(" violation diff min=%d max=%d ; count<=0 = %d ; hist(<=0 present?)" % (min(diffs), max(diffs), sum(1 for x in diffs if x <= 0)))
