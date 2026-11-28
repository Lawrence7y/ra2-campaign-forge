# -*- coding: utf-8 -*-
# R216 audit: A7 - 4 delta-resolution variants in one sweep over .text
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

CFG = {
    'W1 ptrload=0  jmpreset=1 xor0=1':dict(ptr=0, jres=1, xor0=1),
    'W2 ptrload=0  jmpreset=0 xor0=1':dict(ptr=0, jres=0, xor0=1),
    'W3 ptrload=UNK jmpreset=1 xor0=1':dict(ptr=None, jres=1, xor0=1),
    'W4 ptrload=0  jmpreset=1 xor0=UNK':dict(ptr=0, jres=1, xor0=None),
}
S = {k: {} for k in CFG}
R = {k: {'sol': 0, 'eq': 0, 'ne': 0, 'diffs': []} for k in CFG}
c7 = 0; nonesp = 0
va = lo
while va < hi:
    n = min(0x10000, hi - va)
    for off, sz, mn, ops in MD.disasm_lite(blob(va, n), va):
        raw = blob(off, sz)
        if not raw: continue
        site = None
        if mn == 'mov' and raw[0] == 0xC7 and (raw[1] & 0x38) == 0:
            c7 += 1
            m = RXC7.match(ops)
            if m:
                imm = int(m.group(3), 16)
                if imm in VSET and m.group(1) != 'esp':
                    nonesp += 1
                    site = (m.group(1), int(m.group(2), 0) if m.group(2) else 0, imm)
        if site:
            r, disp, imm = site; md = VM[imm]
            for k in CFG:
                st = S[k]
                if r in st:
                    dv = disp + st[r] - md
                    R[k]['sol'] += 1
                    if dv == 0: R[k]['eq'] += 1
                    else: R[k]['ne'] += 1; R[k]['diffs'].append(dv)
        for k, c in CFG.items():
            st = S[k]
            if mn == 'call':
                for x in ('eax', 'ecx', 'edx'): st.pop(x, None)
            elif mn in ('ret', 'retf', 'int3'):
                st.clear(); st['ecx'] = 0
            elif mn == 'jmp' and c['jres']:
                st.clear(); st['ecx'] = 0
            elif mn == 'mov':
                m = RXMV.match(ops)
                if not m: continue
                d, src = m.group(1), m.group(2).strip()
                if re.match(r'^0x[0-9a-f]+$', src):
                    st.pop(d, None); continue
                ml = RXLD.match(src)
                if ml:
                    b = ml.group(1)
                    k2 = int(ml.group(3), 0) * (1 if ml.group(2) != '-' else -1) if ml.group(3) else 0
                    if b in ('esp', 'ebp'): st[d] = k2
                    elif c['ptr'] is None: st.pop(d, None)
                    else: st[d] = c['ptr']
                    continue
                m2 = re.match(r'^([a-z0-9]{2,3})$', src)
                if m2:
                    if m2.group(1) in st: st[d] = st[m2.group(1)]
                    else: st.pop(d, None)
                    continue
                st.pop(d, None)
            elif mn == 'lea':
                m = RXMV.match(ops)
                if not m: continue
                d, src = m.group(1), m.group(2).strip()
                ml = RXLD.match(src)
                if ml:
                    b = ml.group(1)
                    k2 = int(ml.group(3), 0) * (1 if ml.group(2) != '-' else -1) if ml.group(3) else 0
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
                if m and m.group(1) == m.group(2):
                    if c['xor0'] is None: st.pop(m.group(1), None)
                    else: st[m.group(1)] = 0
            elif mn == 'pop':
                if re.match(r'^[a-z0-9]{2,3}$', ops): st.pop(ops, None)
            elif mn in ('inc', 'dec', 'and', 'or', 'shl', 'shr', 'sar', 'sal', 'neg', 'not', 'imul',
                        'mul', 'div', 'idiv', 'xchg', 'adc', 'sbb', 'movzx', 'movsx', 'cmp', 'test', 'push'):
                r2 = re.sub(r'^(dword ptr|byte ptr|word ptr) ', '', ops.split(',')[0].strip())
                if re.match(r'^[a-z0-9]{2,3}$', r2): st.pop(r2, None)
    va += n

print("C7/0=%d  non-esp+imm-in-VSET=%d" % (c7, nonesp))
for k in CFG:
    r = R[k]; pos = [d for d in r['diffs'] if d > 0]
    print(" %-34s sol=%-4d eq=%-4d ne=%-4d neg=%-3d minpos=%s" % (k, r['sol'], r['eq'], r['ne'], sum(1 for d in r['diffs'] if d <= 0), min(pos) if pos else '-'))
print("card: 4195 / 2911 / 2551 / 360 / neg 0")
