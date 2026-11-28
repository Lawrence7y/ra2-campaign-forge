# -*- coding: utf-8 -*-
# R216 audit: A7 one-pass capstone(skipdata), space-tolerant, full per-site record + subset analysis
import sys, json, re, pickle
from collections import Counter, defaultdict
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

D = json.load(open('/home/t628/projects/ra2-campaign-forge/_r216/audit_ds_views.json'))
VIEWS = {int(k, 16): v for k, v in D['views'].items()}
COLA = {int(k, 16): v for k, v in D['cola'].items()}
UNIQ = {int(k, 16): v for k, v in D['preamble2view'].items()}
VM = {st: COLA[c][0] for c, st in UNIQ.items()}
VSET = set(VIEWS)
texte = P.B['.text']; lo, hi = texte['lo'], texte['hi_file']
def blob(a, n):
    o = P.r2o(a); return P.RAW[o:o+n]

MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.skipdata = True
RX = re.compile(r'^dword ptr \[([a-z0-9]{2,3})(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\],\s*(0x[0-9a-f]+)$')

# record every C7 site: (addr, reg, disp, imm, delta_loose)
REC = []
dl = {}
cur_fn = None
va = lo
c7_all = 0
while va < hi:
    n = min(0x10000, hi - va)
    for off, sz, mn, ops in MD.disasm_lite(blob(va, n), va):
        if off != va and False: pass
        raw = blob(off, sz)
        if not raw: continue
        # --- site capture
        if mn == 'mov' and raw[0] == 0xC7 and (raw[1] & 0x38) == 0:
            c7_all += 1
            m = RX.match(ops)
            if m:
                imm = int(m.group(3), 16)
                REC.append((off, m.group(1), int(m.group(2), 0) if m.group(2) else 0, imm, dl.get(m.group(1))))
        # --- state
        if mn == 'call':
            for r in ('eax', 'ecx', 'edx'): dl.pop(r, None)
        elif mn in ('ret', 'int3', 'jmp'):
            dl.clear()
        elif mn == 'mov':
            mm = re.match(r'^([a-z0-9]{2,3}),\s*(0x[0-9a-f]+)$', ops)
            if mm: dl[mm.group(1)] = int(mm.group(2), 16)
            else:
                mm = re.match(r'^([a-z0-9]{2,3}),', ops)
                if mm:
                    if mm.group(1) not in ('dword', 'byte'): dl[mm.group(1)] = 0
        elif mn == 'lea':
            mm = re.match(r'^([a-z0-9]{2,3}),\s*\[([a-z0-9]{2,3})(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]$', ops)
            if mm:
                d, s2 = mm.group(1), mm.group(2)
                k = int(mm.group(3), 0) if mm.group(3) else 0
                if s2 in dl: dl[d] = dl[s2] + k
                elif s2 in ('esp', 'ebp'): dl[d] = k
                else: dl.pop(d, None)
            else:
                mm = re.match(r'^([a-z0-9]{2,3}),', ops)
                if mm: dl[mm.group(1)] = 0
        elif mn in ('add', 'sub'):
            mm = re.match(r'^([a-z0-9]{2,3}),\s*(0x[0-9a-f]+|\d+)$', ops)
            if mm:
                r = mm.group(1); v = int(mm.group(2), 0) * (1 if mn == 'add' else -1)
                if r in dl: dl[r] += v
                else: dl.pop(r, None)
            else:
                mm = re.match(r'^([a-z0-9]{2,3}),', ops)
                if mm: dl.pop(mm.group(1), None)
        elif mn == 'xor':
            mm = re.match(r'^([a-z0-9]{2,3}),\s*([a-z0-9]{2,3})$', ops)
            if mm and mm.group(1) == mm.group(2): dl[mm.group(1)] = 0
        elif mn == 'pop':
            if re.match(r'^[a-z0-9]{2,3}$', ops): dl[ops] = 0
        elif mn in ('inc', 'dec', 'and', 'or', 'shl', 'shr', 'movzx', 'movsx', 'neg', 'not', 'imul'):
            r = ops.split(',')[0].strip()
            if re.match(r'^[a-z0-9]{2,3}$', r): dl.pop(r, None)
    va += n

pickle.dump(REC, open('/home/t628/projects/ra2-campaign-forge/_r216/audit_ds_sites.pkl', 'wb'))
print("C7/0 sites=%d ; parseable=[reg+disp],imm32 = %d" % (c7_all, len(REC)))
targets = [r for r in REC if r[3] in VSET]
print("imm in VSET: %d" % len(targets))
print(" by reg:", dict(Counter(r[1] for r in targets)))
non_esp = [r for r in targets if r[1] != 'esp']
print("non-esp: %d   (card anchor 4195)" % len(non_esp))

def score(rows, label):
    s = [r for r in rows if r[4] is not None]
    eq = ne = 0; diffs = []; nps = []
    for a, reg, disp, imm, d in s:
        dv = disp + d - VM[imm]
        if dv == 0: eq += 1
        else:
            ne += 1; diffs.append(dv)
            if dv <= 0: nps.append((a, reg, disp, imm, d, dv))
    print(" %-28s solved=%d unsolved=%d eq=%d ne=%d min=%s max=%s count<=0=%d"
          % (label, len(s), len(rows) - len(s), eq, ne, min(diffs) if diffs else '-', max(diffs) if diffs else '-', len(nps)))
    return eq, ne, diffs, nps

print("\n== delta caliber: dl (loose) ==")
score(targets, 'all (incl esp)')
eq, ne, diffs, nps = score(non_esp, 'non-esp')
print(" diff hist top:", Counter(diffs).most_common(10))
print(" nonpositive samples:")
for x in nps[:10]: print("   %08x reg=%s disp=%d imm=%08x delta=%d diff=%d" % x)
