# -*- coding: utf-8 -*-
# R216 audit: A7 final - one streaming pass, 4 delta calibers, counts + violation stats
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

# reg -> (offset, kind)  kind: 'obj' (object pointer), 'stack' (esp/ebp frame), 'abs' (mov imm)
st = {}
rows = []          # (addr, reg, disp, imm, off, kind)
c7 = 0
va = lo
while va < hi:
    n = min(0x10000, hi - va)
    for off, sz, mn, ops in MD.disasm_lite(blob(va, n), va):
        raw = blob(off, sz)
        if not raw: continue
        if mn == 'mov' and raw[0] == 0xC7 and (raw[1] & 0x38) == 0:
            c7 += 1
            m = RX.match(ops)
            if m:
                d = int(m.group(2), 0) if m.group(2) else 0
                imm = int(m.group(3), 16)
                r = m.group(1)
                o, k = st.get(r, (None, None))
                rows.append((off, r, d, imm, o, k))
        # ---- state ----
        if mn == 'call':
            for x in ('eax', 'ecx', 'edx'): st.pop(x, None)
        elif mn in ('ret', 'int3', 'jmp'):
            st.clear()
        elif mn == 'mov':
            m = re.match(r'^([a-z0-9]{2,3}),\s*(0x[0-9a-f]+)$', ops)
            if m: st[m.group(1)] = (int(m.group(2), 16), 'abs'); continue
            m = re.match(r'^([a-z0-9]{2,3}),\s*\[([a-z0-9]{2,3})(?:\s*([+-])\s*(0x[0-9a-f]+|\d+))?\]$', ops)
            if m:
                d, b = m.group(1), m.group(2)
                k2 = int(m.group(4), 0) * (1 if m.group(3) != '-' else -1) if m.group(4) else 0
                if b in ('esp', 'ebp'):
                    st[d] = (k2, 'obj' if b == 'esp' else 'obj')
                elif b == 'ecx':
                    st[d] = (k2, 'obj')
                elif b in st and st[b][1] != 'stack':
                    st[d] = (k2, 'obj')
                else:
                    st.pop(d, None)
                continue
            m = re.match(r'^([a-z0-9]{2,3}),\s*([a-z0-9]{2,3})$', ops)
            if m:
                s2 = st.get(m.group(2))
                st[m.group(1)] = s2 if s2 else (None, None)
                if s2 is None: st.pop(m.group(1), None)
                continue
            m = re.match(r'^([a-z0-9]{2,3}),', ops)
            if m: st.pop(m.group(1), None)
        elif mn == 'lea':
            m = re.match(r'^([a-z0-9]{2,3}),\s*\[([a-z0-9]{2,3})(?:\s*([+-])\s*(0x[0-9a-f]+|\d+))?\]$', ops)
            if m:
                d, b = m.group(1), m.group(2)
                k2 = int(m.group(4), 0) * (1 if m.group(3) != '-' else -1) if m.group(4) else 0
                if b in ('esp', 'ebp'): st[d] = (k2, 'stack')
                elif b in st and st[b][1] == 'obj': st[d] = (st[b][0] + k2, 'obj')
                else: st.pop(d, None)
                continue
            m = re.match(r'^([a-z0-9]{2,3}),', ops)
            if m: st.pop(m.group(1), None)
        elif mn in ('add', 'sub'):
            m = re.match(r'^([a-z0-9]{2,3}),\s*(0x[0-9a-f]+|\d+)$', ops)
            if m:
                r = m.group(1); v = int(m.group(2), 0) * (1 if mn == 'add' else -1)
                if r in st:
                    o2, k2 = st[r]
                    if o2 is None: st.pop(r, None)
                    else: st[r] = (o2 + v, k2)
                else: st.pop(r, None)
                continue
            m = re.match(r'^([a-z0-9]{2,3}),', ops)
            if m: st.pop(m.group(1), None)
        elif mn == 'xor':
            m = re.match(r'^([a-z0-9]{2,3}),\s*([a-z0-9]{2,3})$', ops)
            if m and m.group(1) == m.group(2): st[m.group(1)] = (0, 'abs')
        elif mn == 'pop':
            if re.match(r'^[a-z0-9]{2,3}$', ops): st.pop(ops, None)
        elif mn in ('inc', 'dec', 'and', 'or', 'shl', 'shr', 'sar', 'sal', 'neg', 'not', 'imul',
                    'mul', 'div', 'idiv', 'xchg', 'adc', 'sbb', 'movzx', 'movsx', 'push', 'cmp', 'test'):
            r = ops.split(',')[0].strip()
            r = re.sub(r'^dword ptr |^byte ptr ', '', r)
            if re.match(r'^[a-z0-9]{2,3}$', r): st.pop(r, None)
    va += n

ne_ = [r for r in rows if r[3] in VSET and r[1] != 'esp']
print("C7/0 sites=%d  parseable=%d  imm-in-VSET=%d  non-esp=%d" % (c7, len(rows), sum(1 for r in rows if r[3] in VSET), len(ne_)))

def ev(label, pred):
    s = [r for r in ne_ if pred(r)]
    eq = ne = 0; diffs = []
    for addr, reg, disp, imm, o, k in s:
        dv = disp + o - VM[imm]
        if dv == 0: eq += 1
        else: ne += 1; diffs.append(dv)
    pos = [d for d in diffs if d > 0]
    print(" %-34s solved=%-4d eq=%-4d ne=%-4d  count<=0=%-3d  min_pos=%s"
          % (label, len(s), eq, ne, sum(1 for d in diffs if d <= 0), min(pos) if pos else '-'))
    return len(s), eq, ne, diffs

print("\n== calibers over the 4195 non-esp sites ==")
ev('C0 any-delta (loose)', lambda r: r[4] is not None)
ev('C1 delta iff base kind=obj', lambda r: r[4] is not None and r[5] == 'obj')
ev('C2 delta=0 (disp vs mdisp)', lambda r: True and False or (r[4] is not None and False))
_, eq0, ne0, d0 = (0, 0, 0, [])
eqz = sum(1 for r in ne_ if r[2] == VM[r[3]])
print(" %-34s n=%-5d eq(=disp==mdisp)=%d ne=%d" % ('C2 delta treated as 0', len(ne_), eqz, len(ne_) - eqz))
cnt = Counter(d for d in [r[2] + (r[4] or 0) - VM[r[3]] for r in ne_ if r[4] is not None and r[5] == 'obj'])
print("\n C1 diff histogram (top 12):", cnt.most_common(12))
neg = [r for r in ne_ if r[4] is not None and r[5] == 'obj' and r[2] + r[4] - VM[r[3]] < 0]
for r in neg[:10]:
    print("   NEG %08x reg=%s disp=%d imm=%08x delta=%d mdisp=%d kind=%s" % (r[0], r[1], r[2], r[3], r[4], VM[r[3]], r[5]))
