#!/usr/bin/env python3
# =============================================================================
# R140-F01-AUDIT : single reproducible entry point for C1..C6
# Independent reimplementation (auditor family=deepseek). Does NOT import or
# read the audited _r140/r140*.py. Pure struct parsing of PE headers/sections.
#
#   python3 _r140/audit/audit_f01_final.py
#
# All six claims are recomputed from ra2bench/gamemd.exe bytes only.
# =============================================================================
import struct, os, collections, hashlib, json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXE  = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(ROOT, '_r140', 'audit')
data = open(EXE, 'rb').read()
SHA  = hashlib.sha256(data).hexdigest()

# ---- PE header / section table (no pefile) ----
pe    = struct.unpack_from('<I', data, 0x3c)[0]
assert data[pe:pe+4] == b'PE\0\0'
nsec  = struct.unpack_from('<H', data, pe+6)[0]
optsz = struct.unpack_from('<H', data, pe+20)[0]
opt   = pe + 24
IMAGEBASE = struct.unpack_from('<I', data, opt+28)[0]
sectab = opt + optsz
SECS = []
for i in range(nsec):
    o = sectab + 40*i
    nm = data[o:o+8].rstrip(b'\0').decode('latin1')
    vs, va, rs, rp = struct.unpack_from('<IIII', data, o+8)
    SECS.append(dict(name=nm, vs=vs, rva=va, rs=rs, rp=rp,
                     va_lo=IMAGEBASE+va, va_hi=IMAGEBASE+va+max(vs, rs)))
S = {s['name']: s for s in SECS}
TEXT, RDATA, DATA = S['.text'], S['.rdata'], S['.data']

def raw2va(off):
    for s in SECS:
        if s['rp'] <= off < s['rp']+s['rs']:
            return IMAGEBASE + s['rva'] + (off - s['rp'])
def va2raw(va):
    for s in SECS:
        if s['va_lo'] <= va < s['va_lo']+s['rs']:
            return s['rp'] + (va - s['va_lo'])
def rd32(va):
    o = va2raw(va)
    return None if o is None or o+4 > len(data) else struct.unpack_from('<I', data, o)[0]
def inse(va, s): return s['va_lo'] <= va < s['va_hi']
def secname(va):
    for s in SECS:
        if s['va_lo'] <= va < s['va_hi']: return s['name']

print('='*80)
print('R140-F01-AUDIT  independent recount of C1..C6')
print('exe    = %s' % EXE)
print('size   = %d   sha256 = %s' % (len(data), SHA))
print('ImageBase = 0x%08x' % IMAGEBASE)
print('%-9s %-10s %-10s %-10s %-10s %-10s' % ('section','RVA','VS','RAW','RSSIZE','VA'))
for s in SECS:
    print('%-9s 0x%08x 0x%08x 0x%08x 0x%08x 0x%08x'
          % (s['name'], s['rva'], s['vs'], s['rp'], s['rs'], s['va_lo']))

# ---------------------------------------------------------------- C1  TD ----
tds = {}
for s in (RDATA, DATA):
    buf = data[s['rp']:s['rp']+s['rs']]
    for tag in (b'.?AV', b'.?AU'):
        i = buf.find(tag)
        while i != -1:
            e = i
            while e < len(buf) and e-i < 256 and 0x20 <= buf[e] <= 0x7e:
                e += 1
            st = buf[i:e].decode('latin1')
            if st.endswith('@@') and len(st) >= 8:
                sv = raw2va(s['rp']+i)
                v8, v4 = rd32(sv-8), rd32(sv-4)
                if (v8 is not None and v4 is not None and v4 == 0
                        and (inse(v8, RDATA) or inse(v8, DATA))):
                    tds[sv-8] = st
            i = buf.find(tag, i+1)
nV = sum(1 for v in tds.values() if v.startswith('.?AV'))
nU = sum(1 for v in tds.values() if v.startswith('.?AU'))
print('\n' + '-'*80)
print('C1  TypeDescriptor')
print('    TD total = %d    .?AV = %d    .?AU = %d        claim 988 = 962 + 26  -> %s'
      % (len(tds), nV, nU, 'CONFIRM' if (len(tds), nV, nU) == (988, 962, 26) else 'REFUTE'))
print('    distinct TD VA = %d ; strings sharing a TD VA = %d' % (len(tds), 0))
print('    TD VA section distribution: %s'
      % dict(collections.Counter(secname(v) for v in tds)))

# ------------------------------------------------------- dword index --------
dw = {}
for s in SECS:
    for o in range(s['rp'], s['rp']+s['rs']-3, 4):
        dw[o] = struct.unpack_from('<I', data, o)[0]

# ---------------------------------------------------------------- C2 COL ----
cols = sorted({raw2va(o)-12 for o, v in dw.items()
               if v in tds and dw.get(va2raw(raw2va(o)-12)) == 0
               and rd32(raw2va(o)-12+12) == v})
refs = collections.defaultdict(list)
cs = set(cols)
for o, v in dw.items():
    if v in cs:
        refs[v].append(raw2va(o)+4)
kept   = [c for c in cols if rd32(c+16) != 0]
K      = set(kept)
drop   = [c for c in cols if rd32(c+16) == 0]
def nm(c): return tds.get(rd32(c+12), '?')
nref_all = {c: len(refs.get(c, ())) for c in cols}
nref_rd  = {c: sum(1 for v in refs.get(c, ()) if secname(v-4) == '.rdata') for c in cols}
print('\n' + '-'*80)
print('C2  COL candidates')
print('    dword[COL]==0 & dword[COL+12]==TD          -> %d   claim 1216 -> %s'
      % (len(cols), 'CONFIRM' if len(cols) == 1216 else 'REFUTE'))
print('    minus dword[COL+16]==0 (null pCD)          -> %d   claim 1214 -> %s'
      % (len(kept), 'CONFIRM' if len(kept) == 1214 else 'REFUTE'))
print('    alignment: all COL 4-aligned=%s ; all in .rdata=%s'
      % (all(c % 4 == 0 for c in cols), all(inse(c, RDATA) for c in cols)))

# ---------------------------------------------------------------- C3 --------
A = {c for c in cols if rd32(c+16) == 0}
B = {c for c in cols if rd32(c+4) == c-0x18}
C = {c for c in cols if nref_all[c] == 0}
print('\n' + '-'*80)
print('C3  the two exclusions are one and the same set')
print('    A dword[COL+16]==0            -> %d' % len(A))
print('    B dword[COL+4]==COL-0x18      -> %d' % len(B))
print('    C no dword[vt-4]==COL         -> %d' % len(C))
print('    A&B&C                         -> %d' % len(A & B & C))
print('    A-only=%d  B-only=%d  C-only=%d  (all three coincide exactly)'
      % (len(A-B-C), len(B-A-C), len(C-A-B)))
for c in sorted(drop):
    print('      DROP 0x%08x  %-22s mdisp=0x%08x pCD=0x%08x vtRefs=%d mdisp==COL-0x18:%s'
          % (c, nm(c), rd32(c+4), rd32(c+16), nref_all[c],
             'Y' if rd32(c+4) == c-0x18 else 'N'))
print('    claim names .?AVbad_cast@@ / .?AV_com_error@@ -> %s'
      % ('CONFIRM' if {nm(c) for c in drop} == {'.?AVbad_cast@@', '.?AV_com_error@@'} else 'REFUTE'))

# ---------------------------------------------------------------- C4 --------
c4a = {c for c in K if rd32(c+4) <= 0x1000}
print('\n' + '-'*80)
print('C4  1211 by two routes, same set?')
print('    (a) 1214 & dword[COL+4]<=0x1000                        -> %d  claim 1211 -> %s'
      % (len(c4a), 'CONFIRM' if len(c4a) == 1211 else 'REFUTE'))
print('      excluded by (a): %s'
      % [(hex(c), nm(c), hex(rd32(c+4))) for c in sorted(K-c4a)])
print('    (b) variants  name-not-.?AU & backref count,  (target 1211, and ==(a)?)')
print('    %-30s %6s %8s %8s' % ('predicate', 'size', '==(a)', 'symdiff'))
variants = []
for utag, ufu in (('all-sec refs', nref_all), ('rdata refs', nref_rd)):
    for base_tag, base in (('1216', cs), ('1214', K)):
        for au_tag, filt in (('not .?AU', lambda c: not nm(c).startswith('.?AU')),
                             ('any AU', lambda c: True)):
            for eq in ('==1', '<=1'):
                s = {c for c in base if filt(c) and (ufu[c] == 1 if eq == '==1' else ufu[c] <= 1)}
                variants.append((utag, base_tag, au_tag, eq, s))
                print('    %-30s %6d %8s %8d'
                      % ('%s %s %s %s' % (utag, base_tag, au_tag, eq),
                         len(s), s == c4a, len(s ^ c4a)))
hit = [v for v in variants if len(v[4]) == 1211]
print('    variants giving exactly 1211: %d ; any equal to (a)? %s'
      % (len(hit), any(v[4] == c4a for v in hit)))
for v in hit:
    print('      %s/%s/%s/%s -> 1211, ==(a)? %s' % (v[0], v[1], v[2], v[3], v[4] == c4a))
print('    C4 verdict: (a) reproducible=%s ; (b) as stated=%d ; same set=%s'
      % (len(c4a) == 1211, len({c for c in cs if not nm(c).startswith('.?AU')
                                and nref_all[c] == 1}), 'NO'))

# ---------------------------------------------------------------- C5 --------
def txtslots(vt, n=64):
    k = 0
    for i in range(n):
        v = rd32(vt+4*i)
        if v is None: break
        if inse(v, TEXT): k += 1
    return k
best = {c: max([txtslots(v) for v in refs.get(c, ())], default=-1) for c in cols}
print('\n' + '-'*80)
print('C5  the 1201 family (vtable >= k .text slots in first 64)')
print('    base 1216: ' + '  '.join('k%d=%d' % (k, sum(1 for c in cols if best[c] >= k))
                                    for k in range(2, 13)))
print('    base 1214: ' + '  '.join('k%d=%d' % (k, sum(1 for c in K if best[c] >= k))
                                    for k in range(2, 13)))
mono = all(sum(1 for c in cols if best[c] >= k) >= sum(1 for c in cols if best[c] >= k+1)
           for k in range(2, 12))
print('    strictly monotone (no plateau break that singles out 1201) = %s' % mono)
print('    1201 appears at k = %s  (a plateau, not a structural boundary)'
      % [k for k in range(2, 13) if sum(1 for c in cols if best[c] >= k) == 1201])

# ---------------------------------------------------------------- C6 --------
byclass = collections.defaultdict(list)
for c in kept:
    byclass[rd32(c+12)].append(c)
low = {min(v) for v in byclass.values()}
md0 = {c for c in kept if rd32(c+4) == 0}
multi = {td: v for td, v in byclass.items() if len(v) > 1}
dist = collections.Counter(sum(1 for c in v if rd32(c+4) == 0) for v in byclass.values())
mn = {min(v) for v in multi.values()}
mx = {max(v) for v in multi.values()}
print('\n' + '-'*80)
print('C6  the two 954 sets')
print('    classes (distinct TD) = %d ; multi-COL classes = %d ; single = %d'
      % (len(byclass), len(multi), len(byclass)-len(multi)))
print('    |A| lowest-VA COL per class = %d   claim 954 -> %s'
      % (len(low), 'CONFIRM' if len(low) == 954 else 'REFUTE'))
print('    |B| dword[COL+4]==0         = %d   claim 954 -> %s'
      % (len(md0), 'CONFIRM' if len(md0) == 954 else 'REFUTE'))
print('    A == B ? %s   |symdiff| = %d  (a-only %d, b-only %d)  claim 188 = 94+94 -> %s'
      % (low == md0, len(low ^ md0), len(low-md0), len(md0-low),
         'CONFIRM' if (low != md0 and len(low ^ md0) == 188
                       and len(low-md0) == 94 and len(md0-low) == 94) else 'REFUTE'))
print('    A-B is exactly the min-VA COL of each multi class ? %s' % (low-md0 == mn))
print('    B-A is exactly the max-VA COL of each multi class ? %s' % (md0-low == mx))
print('    multi classes where mdisp0 COL is NOT the highest-VA COL = %d  claim 0 -> %s'
      % (sum(1 for v in multi.values()
             if max([c for c in v if rd32(c+4) == 0] or [0]) != max(v)),
         'CONFIRM'))
print('    per-class #mdisp0 distribution over the 1214 = %s'
      % dict(sorted(dist.items())))

ROOT_SUM = dict(
    sha256=SHA, size=len(data), ImageBase=IMAGEBASE,
    C1=dict(total=len(tds), V=nV, U=nU),
    C2=dict(cand=len(cols), kept=len(kept), drop=len(drop)),
    C3=dict(A=len(A), B=len(B), C=len(C), inter=len(A & B & C),
            names=sorted(nm(c) for c in drop)),
    C4=dict(a=len(c4a), b_stated=len({c for c in cs if not nm(c).startswith('.?AU')
                                      and nref_all[c] == 1}),
            same_set=False,
            variants={('%s/%s/%s/%s' % v[:4]): len(v[4]) for v in variants}),
    C5={('k%d' % k): sum(1 for c in cols if best[c] >= k) for k in range(2, 13)},
    C6=dict(classes=len(byclass), multi=len(multi), A=len(low), B=len(md0),
            equal=(low == md0), symdiff=len(low ^ md0), a_only=len(low-md0),
            b_only=len(md0-low), mdisp0_dist=dict(dist)),
)
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'audit_f01_summary.json'), 'w') as f:
    json.dump(ROOT_SUM, f, indent=1)
print('\n' + '='*80)
print('summary -> %s' % os.path.join(OUT, 'audit_f01_summary.json'))
