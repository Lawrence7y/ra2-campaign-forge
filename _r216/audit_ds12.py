# -*- coding: utf-8 -*-
# R216 audit: A7 - 6 delta calibers in a single sweep, to locate the 2911/2551/360 anchor
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
RX = re.compile(r'^dword ptr \[([a-z0-9]{2,3})(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\],\s*(0x[0-9a-f]+)$')

# variant params: (label, memload_value, call_clear, jmp_clear, ret_clear)
V = [
    ('V1 memload=0  call:clr eax/ecx/edx',  0,    'partial', False, True),
    ('V2 memload=0  call:keep',             0,    None,      False, True),
    ('V3 memload=0  call:clr all',          0,    'all',     False, True),
    ('V4 memload=0  call:clr all jmp:keep', 0,    'all',     False, True),
    ('V5 memload=None call:clr all',        None, 'all',     False, True),
    ('V6 memload=0  call:all ret:clr',      0,    'all',     False, True),
]
S = [{} for _ in V]
RES = [{'solved': 0, 'eq': 0, 'ne': 0, 'neg': 0, 'diffs': []} for _ in V]
c7 = 0; nonesp = 0
va = lo
while va < hi:
    n = min(0x10000, hi - va)
    for off, sz, mn, ops in MD.disasm_lite(blob(va, n), va):
        raw = blob(off, sz)
        if not raw: continue
        if mn == 'mov' and raw[0] == 0xC7 and (raw[1] & 0x38) == 0:
            c7 += 1
            m = RX.match(ops)
            if m and m.group(1) != 'esp':
                imm = int(m.group(3), 16)
                if imm in VSET:
                    nonesp += 1
                    r = m.group(1); disp = int(m.group(2), 0) if m.group(2) else 0
                    md = VM[imm]
                    for i, (lab, ml, cc, jc, rc) in enumerate(V):
                        st = S[i]
                        if r in st:
                            dv = disp + st[r] - md
                            RES[i]['solved'] += 1
                            if dv == 0: RES[i]['eq'] += 1
                            else:
                                RES[i]['ne'] += 1; RES[i]['diffs'].append(dv)
                                if dv < 0: RES[i]['neg'] += 1
        # state
        for i, (lab, ml, cc, jc, rc) in enumerate(V):
            st = S[i]
            if mn == 'call':
                if cc == 'partial':
                    for x in ('eax', 'ecx', 'edx'): st.pop(x, None)
                elif cc == 'all': st.clear()
            elif mn in ('ret', 'int3'):
                if rc: st.clear()
            elif mn == 'jmp':
                if jc: st.clear()
            if mn == 'mov':
                m = re.match(r'^([a-z0-9]{2,3}),\s*(0x[0-9a-f]+)$', ops)
                if m: st[m.group(1)] = int(m.group(2), 16); continue
                m = re.match(r'^([a-z0-9]{2,3}),\s*\[([a-z0-9]{2,3})(?:\s*([+-])\s*(0x[0-9a-f]+|\d+))?\]$', ops)
                if m:
                    k2 = int(m.group(4), 0) * (1 if m.group(3) != '-' else -1) if m.group(4) else 0
                    st[m.group(1)] = 0 if ml is not None else None
                    if ml is None: st.pop(m.group(1), None)
                    continue
                m = re.match(r'^([a-z0-9]{2,3}),', ops)
                if m: st.pop(m.group(1), None)
            elif mn == 'lea':
                m = re.match(r'^([a-z0-9]{2,3}),\s*\[([a-z0-9]{2,3})(?:\s*([+-])\s*(0x[0-9a-f]+|\d+))?\]$', ops)
                if m:
                    d, b = m.group(1), m.group(2)
                    k2 = int(m.group(4), 0) * (1 if m.group(3) != '-' else -1) if m.group(4) else 0
                    if b in ('esp', 'ebp'): st[d] = k2
                    elif b in st: st[d] = st[b] + k2
                    else: st.pop(d, None)
                    continue
                m = re.match(r'^([a-z0-9]{2,3}),', ops)
                if m: st.pop(m.group(1), None)
            elif mn in ('add', 'sub'):
                m = re.match(r'^([a-z0-9]{2,3}),\s*(0x[0-9a-f]+|\d+)$', ops)
                if m:
                    r = m.group(1); v = int(m.group(2), 0) * (1 if mn == 'add' else -1)
                    if r in st and st[r] is not None: st[r] += v
                    else: st.pop(r, None)
                    continue
                m = re.match(r'^([a-z0-9]{2,3}),', ops)
                if m: st.pop(m.group(1), None)
            elif mn == 'xor':
                m = re.match(r'^([a-z0-9]{2,3}),\s*([a-z0-9]{2,3})$', ops)
                if m and m.group(1) == m.group(2): st[m.group(1)] = 0
            elif mn == 'pop':
                if re.match(r'^[a-z0-9]{2,3}$', ops): st.pop(ops, None)
            elif mn in ('inc', 'dec', 'and', 'or', 'shl', 'shr', 'sar', 'sal', 'neg', 'not', 'imul',
                        'mul', 'div', 'idiv', 'xchg', 'adc', 'sbb', 'movzx', 'movsx', 'cmp', 'test'):
                r = re.sub(r'^(dword ptr|byte ptr|word ptr) ', '', ops.split(',')[0].strip())
                if re.match(r'^[a-z0-9]{2,3}$', r): st.pop(r, None)
    va += n

print("C7/0=%d ; non-esp sites with imm in VSET = %d" % (c7, nonesp))
for i, (lab, *_rest) in enumerate(V):
    r = RES[i]
    pos = [d for d in r['diffs'] if d > 0]
    print(" %-38s solved=%-4d eq=%-4d ne=%-4d neg=%-3d min_pos=%s" %
          (lab, r['solved'], r['eq'], r['ne'], r['neg'], min(pos) if pos else '-'))
print("\n target on card: solved=2911 eq=2551 ne=360 min_of_ne=?  neg=0")
