# -*- coding: utf-8 -*-
# R216 audit: A7 - 8 more delta combos in one sweep, hunting the 2911/2551/360 split
import sys, json, re
from collections import Counter
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
RXMV = re.compile(r'^([a-z0-9]{2,3}),\s*(.+)$')
RXLD = re.compile(r'^\[([a-z0-9]{2,3})(?:\s*([+-])\s*(0x[0-9a-f]+|\d+))?\]$')

# combos: inherit_ptr (bool), argload_zero (bool), jres(bool), ccall(bool), this_is_0(bool)
COMBOS = [
    ('E1 inherit jres ccall', True, True, True, True),
    ('E2 inherit nojres ccall', True, True, False, True),
    ('E3 inherit jres nocall', True, True, True, False),
    ('E4 noinherit jres ccall', False, True, True, True),
    ('E5 inherit noargload', True, False, True, True),
    ('E6 inherit jres ccall no-ecx0', True, True, True, True),
]
S = {i: {} for i in range(len(COMBOS))}
R = {i: {'sol': 0, 'eq': 0, 'ne': 0, 'd': []} for i in range(len(COMBOS))}
c7 = 0; nonesp = 0
va = lo
while va < hi:
    n = min(0x10000, hi - va)
    for off, sz, mn, ops in MD.disasm_lite(blob(va, n), va):
        raw = blob(off, sz)
        if not raw: continue
        if mn == 'mov' and raw[0] == 0xC7 and (raw[1] & 0x38) == 0:
            c7 += 1
            m = RXC7.match(ops)
            if m:
                imm = int(m.group(3), 16)
                if imm in VSET and m.group(1) != 'esp':
                    nonesp += 1
                    reg = m.group(1); disp = int(m.group(2), 0) if m.group(2) else 0; md = VM[imm]
                    for i in S:
                        st = S[i]
                        if reg in st:
                            dv = disp + st[reg] - md
                            R[i]['sol'] += 1
                            if dv == 0: R[i]['eq'] += 1
                            else: R[i]['ne'] += 1; R[i]['d'].append(dv)
        for i, (lab, inh, argo, jres, ccall) in enumerate(COMBOS):
            st = S[i]
            if mn == 'call':
                if ccall:
                    for x in ('eax', 'ecx', 'edx'): st.pop(x, None)
            elif mn in ('ret', 'retf', 'int3'):
                st.clear(); st['ecx'] = 0
            elif mn == 'jmp':
                if jres: st.clear(); st['ecx'] = 0
            elif mn == 'mov':
                m = RXMV.match(ops)
                if not m: continue
                d, src = m.group(1), m.group(2).strip()
                if re.match(r'^0x[0-9a-f]+$', src): st.pop(d, None); continue
                l = RXLD.match(src)
                if l:
                    b = l.group(1)
                    k2 = int(l.group(3), 0) * (1 if l.group(2) != '-' else -1) if l.group(3) else 0
                    if b in ('esp', 'ebp'):
                        st[d] = k2 if argo else 0
                    elif inh and b in st:
                        st[d] = st[b] + k2
                    elif inh:
                        st[d] = 0
                    else:
                        st.pop(d, None)
                    continue
                if re.match(r'^[a-z0-9]{2,3}$', src):
                    if src in st: st[d] = st[src]
                    else: st.pop(d, None)
                    continue
                st.pop(d, None)
            elif mn == 'lea':
                m = RXMV.match(ops)
                if not m: continue
                d, src = m.group(1), m.group(2).strip()
                l = RXLD.match(src)
                if l:
                    b = l.group(1)
                    k2 = int(l.group(3), 0) * (1 if l.group(2) != '-' else -1) if l.group(3) else 0
                    if b in ('esp', 'ebp'): st[d] = k2
                    elif b in st: st[d] = st[b] + k2
                    else: st.pop(d, None)
                    continue
                st.pop(d, None)
            elif mn in ('add', 'sub'):
                m = re.match(r'^([a-z0-9]{2,3}),\s*(0x[0-9a-f]+|\d+)$', ops)
                if m:
                    r2 = m.group(1); v = int(m.group(2), 0) * (1 if mn == 'add' else -1)
                    if r2 in st: st[r2] += v
                    else: st.pop(r2, None)
                    continue
                r2 = re.sub(r'^(dword ptr|byte ptr) ', '', ops.split(',')[0].strip())
                st.pop(r2, None)
            elif mn == 'xor':
                m = re.match(r'^([a-z0-9]{2,3}),\s*([a-z0-9]{2,3})$', ops)
                if m and m.group(1) == m.group(2): st[m.group(1)] = 0
            elif mn == 'pop':
                if re.match(r'^[a-z0-9]{2,3}$', ops): st.pop(ops, None)
            elif mn in ('inc', 'dec', 'and', 'or', 'shl', 'shr', 'sar', 'sal', 'neg', 'not', 'imul',
                        'mul', 'div', 'idiv', 'xchg', 'adc', 'sbb', 'movzx', 'movsx', 'cmp', 'test', 'push'):
                r2 = re.sub(r'^(dword ptr|byte ptr|word ptr) ', '', ops.split(',')[0].strip())
                if re.match(r'^[a-z0-9]{2,3}$', r2): st.pop(r2, None)
    va += n

print("C7/0=%d  non-esp+imm-in-VSET=%d" % (c7, nonesp))
for i, (lab, *_rest) in enumerate(COMBOS):
    r = R[i]; pos = [x for x in r['d'] if x > 0]
    print(" %-28s sol=%-4d eq=%-4d ne=%-4d neg=%-3d minpos=%s" % (lab, r['sol'], r['eq'], r['ne'], sum(1 for x in r['d'] if x <= 0), min(pos) if pos else '-'))
print("card: 4195 / 2911 / 2551 / 360 / neg 0")
