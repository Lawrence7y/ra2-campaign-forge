# -*- coding: utf-8 -*-
# R216 audit (deepseek): A6 (target = some view's slot0) + A7 multi-caliber single pass
import sys, struct, json, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.skipdata = True

D = json.load(open('/home/t628/projects/ra2-campaign-forge/_r216/audit_ds_views.json'))
VIEWS = {int(k, 16): v for k, v in D['views'].items()}
COLA = {int(k, 16): v for k, v in D['cola'].items()}
UNIQ = {int(k, 16): v for k, v in D['preamble2view'].items()}
VM = {st: COLA[c][0] for c, st in UNIQ.items()}
def blob(va, n):
    o = P.r2o(va); return P.RAW[o:o+n]

# ---------- A6: adjustor thunk law ----------
SLOT0 = {}          # slot0 value -> view start
for st, sl in VIEWS.items():
    if sl: SLOT0.setdefault(sl[0], st)
print("== A6 law U ==")
print(" views=%d  mdisp!=0=%d  distinct slot0 values=%d" % (len(VM), sum(1 for v in VM.values() if v), len(SLOT0)))
nz = sorted([st for st in VM if VM[st] != 0])
cand = 0; ok = 0; bad = []; ns = []
for st in nz:
    m = VM[st]; sl = VIEWS[st]
    if not sl: ns.append((st, m, 'empty')); continue
    s0 = sl[0]
    ins = list(MD.disasm_lite(blob(s0, 16), s0))
    if len(ins) < 2: ns.append((st, m, 'short: %08x' % s0)); continue
    mm = re.match(r'^(sub|add)\s+dword ptr \[esp \+ 4\],\s*(0x[0-9a-f]+|\d+)$', '%s %s' % (ins[0][2], ins[0][3]))
    if not mm: ns.append((st, m, '%s %s' % (ins[0][2], ins[0][3]))); continue
    N = int(mm.group(2), 0) * (1 if mm.group(1) == 'sub' else -1)
    if ins[1][2] != 'jmp': ns.append((st, m, 'no-jmp: %s %s' % (ins[1][2], ins[1][3]))); continue
    tgt = int(ins[1][3], 16)
    if tgt not in SLOT0: ns.append((st, m, 'jmp->%08x (not a view slot0)' % tgt)); continue
    cand += 1
    tv = SLOT0[tgt]; want = m - VM[tv]
    if N == want: ok += 1
    else: bad.append((st, m, s0, tgt, VM[tv], N, want))
print(" mdisp!=0 views=%d ; slot0-shaped(sub/add+jmp to a view slot0)=%d ; N==self.mdisp-tgt.mdisp=%d ; counterexamples=%d ; non-shaped=%d"
      % (len(nz), cand, ok, len(bad), len(ns)))
for b in bad[:10]: print("   BAD self=%08x m=%d s0=%08x tgt=%08x tm=%d N=%d want=%d" % b)
for b in ns[:12]: print("   NS  self=%08x m=%-6d : %s" % b)
print(" A6:", "PASS" if (len(nz) == 260 and cand == 101 and ok == 101 and not bad) else "FAIL")

# ---------- A7: linear scan, two delta calibers ----------
texte = P.B['.text']
lo, hi = texte['lo'], texte['hi_file']
SET_START = set(VIEWS.keys())
SET_SLOT = set(x for v in VIEWS.values() for x in v)
SET_COLA = set(COLA.keys())
CAL = {'loose': set(), 'strict': set()}
sites = []   # (addr, mn_raw_c7, reg, disp, imm, dloose, dstrict)  delta None if unsolved

def chunk_iter(a0, n):
    return MD.disasm_lite(blob(a0, n), a0)

for cal in ('loose', 'strict'):
    pass

def run(caliber):
    regs = {}
    out = []
    prev_end = lo
    va = lo
    while va < hi:
        n = min(0x10000, hi - va)
        for off, sz, mn, ops in chunk_iter(va, n):
            if off < prev_end: continue
            prev_end = off + sz
            raw = blob(off, sz)
            # state
            if mn == 'call':
                for r in ('eax', 'ecx', 'edx'): regs.pop(r, None)
            elif mn == 'ret':
                regs.clear()
            if mn == 'mov' and len(raw) >= 2 and raw[0] in (0x88, 0x89, 0x8a, 0x8b, 0xb8, 0xb9, 0xba, 0xbb, 0xbe, 0xbf, 0x68):
                mm = re.match(r'^([a-z0-9]{2,3}),\s*(0x[0-9a-f]+)$', ops)
                if mm: regs[mm.group(1)] = int(mm.group(2), 16)
                else:
                    mm2 = re.match(r'^([a-z0-9]{2,3}),', ops)
                    if mm2: regs.pop(mm2.group(1), None) if caliber == 'strict' else regs.update({mm2.group(1): 0})
            elif mn == 'lea':
                mm = re.match(r'^([a-z0-9]{2,3}),\s*\[([a-z0-9]{2,3})(?:\s*([+-])\s*(0x[0-9a-f]+|\d+))?\]$', ops)
                if mm:
                    d, s2, sg, k = mm.group(1), mm.group(2), mm.group(3), mm.group(4)
                    if s2 in regs:
                        v = regs[s2] + (int(k, 0) * (1 if sg != '-' else -1) if k else 0)
                        regs[d] = v
                    else: regs.pop(d, None)
                else:
                    mm3 = re.match(r'^([a-z0-9]{2,3}),', ops)
                    if mm3: regs.pop(mm3.group(1), None)
            elif mn in ('add', 'sub'):
                mm = re.match(r'^([a-z0-9]{2,3}),\s*(0x[0-9a-f]+|\d+)$', ops)
                if mm:
                    r = mm.group(1); v = int(mm.group(2), 0)
                    if r in regs: regs[r] = regs[r] + v if mn == 'add' else regs[r] - v
                    else: regs.pop(r, None)
                else:
                    mm4 = re.match(r'^([a-z0-9]{2,3}),', ops)
                    if mm4: regs.pop(mm4.group(1), None)
            elif mn == 'xor':
                mm = re.match(r'^([a-z0-9]{2,3}),\s*([a-z0-9]{2,3})$', ops)
                if mm and mm.group(1) == mm.group(2): regs[mm.group(1)] = 0
            elif mn == 'pop':
                if re.match(r'^[a-z0-9]{2,3}$', ops):
                    if caliber == 'loose': regs[ops] = 0
                    else: regs.pop(ops, None)
            # C7 site: mov r/m32, imm32 (mod=00, reg=000)
            if mn == 'mov' and len(raw) >= 2 and raw[0] == 0xC7 and (raw[1] & 0x38) == 0:
                out.append((off, oz := ops, regs.copy(), raw))
        va += n
    return out

print("\n== A7 law W ==")
data = run('strict')
print(" C7/0 sites (mov dword ptr [mem], imm32) in .text = %d" % len(data))
idxskip = 0; pars = 0; hits = {k: 0 for k in ('start', 'slot', 'cola')}
solved = 0; unsolved = 0; eq = 0; ne = 0; diffs = []
per_mdisp = {}
examples = []
for off, ops, regs, raw in data:
    mm = re.match(r'^dword ptr \[([a-z0-9]{2,3})(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\],\s*(0x[0-9a-f]+)$', ops)
    if not mm:
        if '[' in ops and ',' in ops: idxskip += 1
        continue
    pars += 1
    r = mm.group(1); disp = int(mm.group(2), 0) if mm.group(2) else 0; imm = int(mm.group(3), 16)
    inS = imm in SET_START; inL = imm in SET_SLOT; inC = imm in SET_COLA
    if inS: hits['start'] += 1
    if inL: hits['slot'] += 1
    if inC: hits['cola'] += 1
    if not inS: continue
    if r not in regs: unsolved += 1; continue
    solved += 1
    delta = regs[r]; d = disp + delta - VM[imm]
    m = VM[imm]; per_mdisp.setdefault(m, [0, 0])
    if d == 0: eq += 1; per_mdisp[m][0] += 1
    else:
        ne += 1; diffs.append(d); per_mdisp[m][1] += 1
        if d <= 0 and len(examples) < 12: examples.append((off, ops, r, delta, disp, m, d))
print(" parsed as [reg(+disp)], imm32 : %d ; unparsed-with-mem : %d" % (pars, idxskip))
print(" imm==view start: %d ; imm==any slot target: %d ; imm==COLA key: %d" % (hits['start'], hits['slot'], hits['cola']))
print(" delta solved %d / unsolved %d" % (solved, unsolved))
print(" disp+delta==mdisp : %d ; != : %d" % (eq, ne))
if diffs:
    print(" violation: min=%d max=%d  count<=0: %d ; count>0: %d" % (min(diffs), max(diffs), sum(1 for x in diffs if x <= 0), sum(1 for x in diffs if x > 0)))
    print(" top diffs:", sorted(set(diffs))[:15])
for e in examples: print("   nonpos: %08x %-40s reg=%s delta=%d disp=%d mdisp=%d diff=%d" % e)
print(" per-mdisp eq/ne (first 12):", dict(list(sorted(per_mdisp.items()))[:12]))
