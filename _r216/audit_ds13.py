# -*- coding: utf-8 -*-
# R216 audit: A7 final caliber - function-scoped ring buffer, backward delta resolution
# Registers track OFFSET FROM OBJECT BASE. At every function entry (after ret/int3/uncond jmp),
# ecx = 0 (thiscall this), stack params via [esp+K] load = 0 (a fresh object base).
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
lo, hi = P.B['.text']['lo'], P.B['.text']['hi_file']
def blob(a, n):
    o = P.r2o(a); return P.RAW[o:o+n]

MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.skipdata = True
RXC7 = re.compile(r'^dword ptr \[([a-z0-9]{2,3})(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\],\s*(0x[0-9a-f]+)$')

RING = []          # list of (addr, mn, ops) for current function
REGS = {}          # current forward state: reg -> offset-from-object-base (int) or None (unknown base)

def reset(entry):
    RING.clear(); REGS.clear()
    if entry: REGS['ecx'] = 0          # thiscall: ecx == this

def resolve(reg):
    return REGS.get(reg)

c7 = 0; nonesp = 0; rows = []
va = lo
while va < hi:
    n = min(0x10000, hi - va)
    for off, sz, mn, ops in MD.disasm_lite(blob(va, n), va):
        raw = blob(off, sz)
        if not raw: continue
        if mn == '.byte': continue
        # ---------- site capture (uses state BEFORE this insn) ----------
        if mn == 'mov' and raw[0] == 0xC7 and (raw[1] & 0x38) == 0:
            c7 += 1
            m = RXC7.match(ops)
            if m:
                imm = int(m.group(3), 16)
                if imm in VSET and m.group(1) != 'esp':
                    nonesp += 1
                    disp = int(m.group(2), 0) if m.group(2) else 0
                    rows.append((off, m.group(1), disp, imm, dict(REGS)))
        # ---------- forward state ----------
        if mn == 'call':
            for x in ('eax', 'ecx', 'edx'): REGS.pop(x, None)
        elif mn in ('ret', 'retf', 'int3'):
            reset(True)
        elif mn == 'jmp':
            reset(True)     # treat fallthrough target as fresh function (approximation)
        elif mn == 'mov':
            m = re.match(r'^([a-z0-9]{2,3}),\s*(0x[0-9a-f]+)$', ops)
            if m: REGS.pop(m.group(1), None); RING.append((off, mn, ops)); continue
            m = re.match(r'^([a-z0-9]{2,3}),\s*\[([a-z0-9]{2,3})(?:\s*([+-])\s*(0x[0-9a-f]+|\d+))?\]$', ops)
            if m:
                d, b = m.group(1), m.group(2)
                k2 = int(m.group(4), 0) * (1 if m.group(3) != '-' else -1) if m.group(4) else 0
                if b == 'esp' or b == 'ebp': REGS[d] = 0          # fresh object base loaded from stack
                elif b in ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi'):
                    REGS.pop(d, None)                             # load through a pointer: base unknown
                else: REGS.pop(d, None)
                RING.append((off, mn, ops)); continue
            m = re.match(r'^([a-z0-9]{2,3}),\s*([a-z0-9]{2,3})$', ops)
            if m:
                s2 = m.group(2)
                if s2 in REGS: REGS[m.group(1)] = REGS[s2]
                else: REGS.pop(m.group(1), None)
                RING.append((off, mn, ops)); continue
            m = re.match(r'^([a-z0-9]{2,3}),', ops)
            if m: REGS.pop(m.group(1), None)
        elif mn == 'lea':
            m = re.match(r'^([a-z0-9]{2,3}),\s*\[([a-z0-9]{2,3})(?:\s*([+-])\s*(0x[0-9a-f]+|\d+))?\]$', ops)
            if m:
                d, b = m.group(1), m.group(2)
                k2 = int(m.group(4), 0) * (1 if m.group(3) != '-' else -1) if m.group(4) else 0
                if b in ('esp', 'ebp'): REGS[d] = k2
                elif b in REGS: REGS[d] = REGS[b] + k2
                else: REGS.pop(d, None)
                RING.append((off, mn, ops)); continue
            m = re.match(r'^([a-z0-9]{2,3}),', ops)
            if m: REGS.pop(m.group(1), None)
        elif mn in ('add', 'sub'):
            m = re.match(r'^([a-z0-9]{2,3}),\s*(0x[0-9a-f]+|\d+)$', ops)
            if m:
                r = m.group(1); v = int(m.group(2), 0) * (1 if mn == 'add' else -1)
                if r in REGS: REGS[r] += v
                else: REGS.pop(r, None)
                RING.append((off, mn, ops)); continue
            m = re.match(r'^([a-z0-9]{2,3}),', ops)
            if m: REGS.pop(m.group(1), None)
        elif mn == 'xor':
            m = re.match(r'^([a-z0-9]{2,3}),\s*([a-z0-9]{2,3})$', ops)
            if m and m.group(1) == m.group(2): REGS.pop(m.group(1), None)
        elif mn == 'pop':
            if re.match(r'^[a-z0-9]{2,3}$', ops): REGS.pop(ops, None)
        elif mn in ('inc', 'dec', 'and', 'or', 'shl', 'shr', 'sar', 'sal', 'neg', 'not', 'imul',
                    'mul', 'div', 'idiv', 'xchg', 'adc', 'sbb', 'movzx', 'movsx', 'cmp', 'test', 'push'):
            r = re.sub(r'^(dword ptr|byte ptr|word ptr) ', '', ops.split(',')[0].strip())
            if re.match(r'^[a-z0-9]{2,3}$', r): REGS.pop(r, None)
    va += n

print("C7/0 total sites = %d ; non-esp sites with imm in view-start set = %d" % (c7, nonesp))
solved = [r for r in rows if r[1] in r[4]]
eq = ne = 0; diffs = []; nps = []
for off, reg, disp, imm, snap in solved:
    dv = disp + snap[reg] - VM[imm]
    if dv == 0: eq += 1
    else:
        ne += 1; diffs.append(dv)
        if dv <= 0: nps.append((off, reg, disp, imm, snap[reg], dv))
print(" delta solved = %d ; unsolved = %d" % (len(solved), len(rows) - len(solved)))
print(" disp+delta==mdisp : %d ; != : %d" % (eq, ne))
if diffs:
    pos = [d for d in diffs if d > 0]
    print(" violation diff: min=%d max=%d  count<=0=%d  min_positive=%s" % (min(diffs), max(diffs), len(nps), min(pos) if pos else '-'))
    print(" hist top:", Counter(diffs).most_common(10))
for x in nps[:12]: print("   NONPOS %08x reg=%s disp=%d imm=%08x delta=%d diff=%d" % x)
print("\ncard anchor: 4195 sites / 2911 solved / 2551 eq / 360 ne / 0 neg")
