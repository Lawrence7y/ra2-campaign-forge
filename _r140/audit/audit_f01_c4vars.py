#!/usr/bin/env python3
# R140-F01-AUDIT part 2 : C4 predicate-(b) variant sweep + detail dump.
# Independently rebuilds TD/COL/vtables (short, self-contained).
import struct, os, collections, json

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE  = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(ROOT, '_r140', 'audit')
data = open(EXE, 'rb').read()

pe = struct.unpack_from('<I', data, 0x3c)[0]
nsec = struct.unpack_from('<H', data, pe+6)[0]
optsz = struct.unpack_from('<H', data, pe+20)[0]
opt = pe+24
IMAGEBASE = struct.unpack_from('<I', data, opt+28)[0]
sectab = opt+optsz
SECS = []
for i in range(nsec):
    o = sectab+40*i
    nm = data[o:o+8].rstrip(b'\0').decode('latin1')
    vs, va, rs, rp = struct.unpack_from('<IIII', data, o+8)
    ch = struct.unpack_from('<I', data, o+36)[0]
    SECS.append(dict(name=nm, vs=vs, rva=va, rs=rs, rp=rp, ch=ch,
                     va_lo=IMAGEBASE+va, va_hi=IMAGEBASE+va+max(vs, rs)))
S = {s['name']: s for s in SECS}
TEXT, RDATA, DATA = S['.text'], S['.rdata'], S['.data']

def raw2va(off):
    for s in SECS:
        if s['rp'] <= off < s['rp']+s['rs']:
            return IMAGEBASE+s['rva']+(off-s['rp'])
def va2raw(va):
    for s in SECS:
        if s['va_lo'] <= va < s['va_lo']+s['rs']:
            return s['rp']+(va-s['va_lo'])
def rd32(va):
    o = va2raw(va)
    return None if o is None or o+4 > len(data) else struct.unpack_from('<I', data, o)[0]
def secname(va):
    for s in SECS:
        if s['va_lo'] <= va < s['va_hi']:
            return s['name']
    return None
def in_sec(va, s): return s['va_lo'] <= va < s['va_hi']
def cstr(va, n=256):
    o = va2raw(va)
    if o is None: return None
    e = o
    while e < len(data) and e-o < n and 0x20 <= data[e] <= 0x7e: e += 1
    return data[o:e].decode('latin1')

# TD
tds = {}
for s in (RDATA, DATA):
    buf = data[s['rp']:s['rp']+s['rs']]
    for tag in (b'.?AV', b'.?AU'):
        i = buf.find(tag)
        while i != -1:
            e = i
            while e < len(buf) and e-i < 256 and 0x20 <= buf[e] <= 0x7e: e += 1
            st = buf[i:e].decode('latin1')
            if st.endswith('@@') and len(st) >= 8:
                sv = raw2va(s['rp']+i)
                v8, v4 = rd32(sv-8), rd32(sv-4)
                if v8 is not None and v4 is not None and (in_sec(v8, RDATA) or in_sec(v8, DATA)) and v4 == 0:
                    tds[sv-8] = st
            i = buf.find(tag, i+1)

# dwords
dw = {}
for s in SECS:
    for o in range(s['rp'], s['rp']+s['rs']-3, 4):
        dw[o] = struct.unpack_from('<I', data, o)[0]

cols = []
for o, v in dw.items():
    if v in tds:
        pv = raw2va(o)
        c = pv-12
        if dw.get(va2raw(c)) == 0 and rd32(c+12) == v:
            cols.append(c)
cols = sorted(set(cols))

# vtable refs : (col -> list of (vt_va, section_name, slot_index))
refs = collections.defaultdict(list)
for o, v in dw.items():
    if v in cols:
        pv = raw2va(o)
        refs[v].append((pv+4, secname(pv), 0))

kept = [c for c in cols if rd32(c+16) != 0]
def nm(c): return tds.get(rd32(c+12), '?')

print('='*78)
print('C4 PART 2 : variant sweep of predicate (b)')
print('TD=%d  COL=%d  kept(1214)=%d  distinct TD among kept=%d'
      % (len(tds), len(cols), len(kept), len({rd32(c+12) for c in kept})))
print('AU COLs among 1216 = %d ; among 1214 = %d'
      % (sum(1 for c in cols if nm(c).startswith('.?AU')),
         sum(1 for c in kept if nm(c).startswith('.?AU'))))
print('ref position sections: %s'
      % dict(collections.Counter(s for L in refs.values() for _, s, _ in L)))

# predicate (a)
A = {c for c in kept if rd32(c+4) <= 0x1000}
A16 = {c for c in cols if rd32(c+4) <= 0x1000}
print('\n(a) kept & mdisp<=0x1000 -> %d   |  on 1216 -> %d' % (len(A), len(A16)))
hi = [c for c in kept if rd32(c+4) > 0x1000]
print('(a) excluded COLs (%d):' % len(hi))
for c in sorted(hi):
    print('   COL 0x%08x %-38s mdisp=0x%08x vtRefs=%d' % (c, nm(c), rd32(c+4), len(refs.get(c, ()))))

# predicate (b) variants
variants = {}
def addv(tag, s): variants[tag] = s
nref_all = {c: len(refs.get(c, ())) for c in cols}
nref_rd  = {c: sum(1 for _, sn, _ in refs.get(c, ()) if sn == '.rdata') for c in cols}
notAU = {c for c in cols if not nm(c).startswith('.?AU')}
addv('b0 all-sec refs ==1',        {c for c in notAU if nref_all[c] == 1})
addv('b1 .rdata refs ==1',         {c for c in notAU if nref_rd[c] == 1})
addv('b2 all refs==1 (incl AU)',   {c for c in cols if nref_all[c] == 1})
addv('b3 .rdata refs==1 (incl AU)',{c for c in cols if nref_rd[c] == 1})
addv('b4 all refs<=1',             {c for c in notAU if nref_all[c] <= 1})
addv('b5 notAU & allrefs==1 & on1214', {c for c in notAU if nref_all[c] == 1 and c in set(kept)})
print('\n(b) variants (target 1211, equal to (a)?):')
for k in sorted(variants):
    s = variants[k]
    print('  %-32s |set|=%-5d ==(a)? %-5s symdiff=%-3d  a-only=%-3d b-only=%-3d'
          % (k, len(s), s == A, len(s ^ A), len(A-s), len(s-A)))

# detail of the (a) vs b0 symmetric difference
B = variants['b0 all-sec refs ==1'] if 'b0 all-sec refs ==1' in variants else variants['b0 all-sec refs ==1']
B = variants['b0 all-sec refs ==1']
print('\n--- (a) vs (b0) symmetric difference detail ---')
print('a-only (%d):' % len(A-B))
for c in sorted(A-B): print('   COL 0x%08x %-38s mdisp=0x%08x refs=%d' % (c, nm(c), rd32(c+4), nref_all[c]))
print('b-only (%d):' % len(B-A))
for c in sorted(B-A): print('   COL 0x%08x %-38s mdisp=0x%08x refs=%d' % (c, nm(c), rd32(c+4), nref_all[c]))

# how many COLs have multi refs, and are those refs in .data (suspicious) ?
multi = [c for c in cols if nref_all[c] > 1]
print('\nCOLs with >1 backref: %d ; of which all refs in .rdata: %d ; any ref in .data: %d'
      % (len(multi),
         sum(1 for c in multi if all(sn == '.rdata' for _, sn, _ in refs[c])),
         sum(1 for c in multi if any(sn != '.rdata' for _, sn, _ in refs[c]))))

# C6 re-verify on 1214 with class membership cross-tab
byclass = collections.defaultdict(list)
for c in kept: byclass[rd32(c+12)].append(c)
low  = {min(v) for v in byclass.values()}
md0  = {c for c in kept if rd32(c+4) == 0}
print('\n--- C6 re-verify (base 1214) ---')
print('classes=%d |A(minVA)=%d |B(mdisp0)=%d equal=%s sym=%d a-only=%d b-only=%d'
      % (len(byclass), len(low), len(md0), low == md0, len(low ^ md0), len(low-md0), len(md0-low)))
viol = [td for td, v in byclass.items() if len(v) > 1 and max([c for c in v if rd32(c+4) == 0] or [0]) != max(v)]
print('multi-COL classes=%d  mdisp0-not-highestVA=%d' % (sum(1 for v in byclass.values() if len(v) > 1), len(viol)))
print('a-only/b-only are exactly the max/min of each multi class? %s'
      % (low-md0 == {max(v) for v in byclass.values() if len(v) > 1}
         and md0-low == {min(v) for v in byclass.values() if len(v) > 1}))

print('\nvariant table -> audit_f01_c4.json')
json.dump({'|a|': len(A), 'variants': {k: len(v) for k, v in variants.items()},
           'a_minus_b0': [(hex(c), nm(c), rd32(c+4), nref_all[c]) for c in sorted(A-B)],
           'b0_minus_a': [(hex(c), nm(c), rd32(c+4), nref_all[c]) for c in sorted(B-A)]},
          open(os.path.join(OUT, 'audit_f01_c4.json'), 'w'), indent=1, default=str)
