#!/usr/bin/env python3
# R140-F01-AUDIT part 3 : deeper C4-(b) sweep (vtable validity thresholds,
# class-level dedupe), corrected C6 set-composition check, C5 exact table.
import struct, os, collections, json

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE  = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(ROOT, '_r140', 'audit')
data = open(EXE, 'rb').read()
pe = struct.unpack_from('<I', data, 0x3c)[0]
nsec = struct.unpack_from('<H', data, pe+6)[0]
optsz = struct.unpack_from('<H', data, pe+20)[0]
opt = pe+24; IMAGEBASE = struct.unpack_from('<I', data, opt+28)[0]
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
def raw2va(o):
    for s in SECS:
        if s['rp'] <= o < s['rp']+s['rs']: return IMAGEBASE+s['rva']+(o-s['rp'])
def va2raw(va):
    for s in SECS:
        if s['va_lo'] <= va < s['va_lo']+s['rs']: return s['rp']+(va-s['va_lo'])
def rd32(va):
    o = va2raw(va)
    return None if o is None or o+4 > len(data) else struct.unpack_from('<I', data, o)[0]
def sn(va):
    for s in SECS:
        if s['va_lo'] <= va < s['va_hi']: return s['name']
def inse(va, s): return s['va_lo'] <= va < s['va_hi']

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
                sv = raw2va(s['rp']+i); v8, v4 = rd32(sv-8), rd32(sv-4)
                if v8 is not None and v4 is not None and (inse(v8, RDATA) or inse(v8, DATA)) and v4 == 0:
                    tds[sv-8] = st
            i = buf.find(tag, i+1)
dw = {}
for s in SECS:
    for o in range(s['rp'], s['rp']+s['rs']-3, 4):
        dw[o] = struct.unpack_from('<I', data, o)[0]
cols = sorted({raw2va(o)-12 for o, v in dw.items()
               if v in tds and dw.get(va2raw(raw2va(o)-12)) == 0 and rd32(raw2va(o)-12+12) == v})
refs = collections.defaultdict(list)
for o, v in dw.items():
    if v in set(cols): refs[v].append(raw2va(o)+4)
kept = [c for c in cols if rd32(c+16) != 0]
K = set(kept)
def nm(c): return tds.get(rd32(c+12), '?')

# vtable validity: count slots into .text within first n
def txtslots(vt, n=64):
    k = 0
    for i in range(n):
        v = rd32(vt+4*i)
        if v is None: break
        if inse(v, TEXT): k += 1
    return k
nref_all = {c: len(refs.get(c, ())) for c in cols}
nref_rd  = {c: sum(1 for v in refs.get(c, ()) if sn(v-4) == '.rdata') for c in cols}
# valid vt = ref position whose dword[vt] is in .text and dword[vt+4] in .text (>=2 slots)
def valid_refs(c, minSlots=1):
    return sum(1 for v in refs.get(c, ()) if txtslots(v, 64) >= minSlots)

A = {c for c in kept if rd32(c+4) <= 0x1000}
print('='*78)
print('PART 3   (a)=%d  kept=%d  cols=%d' % (len(A), len(kept), len(cols)))
print('\n(b) sweep: "name not .?AU" x "backref count" x universe of refs x minSlots')
hdr = '%-26s' % 'predicate'
for ms in (0, 1, 2, 3, 8):
    hdr += ' ms%d' % ms
print(hdr)
rows = []
for uni, fn in (('all refs', nref_all), ('rdata refs', nref_rd)):
    for base_tag, base in (('1216', set(cols)), ('1214', K)):
        for au_tag, filt in (('notAU', lambda c: not nm(c).startswith('.?AU')),
                             ('anyAU', lambda c: True)):
            for eq in ('==1', '<=1'):
                line = '%-26s' % ('%s %s %s %s' % (uni, base_tag, au_tag, eq))
                for ms in (0, 1, 2, 3, 8):
                    if ms == 0:
                        cnt = {c: fn[c] for c in base}
                    else:
                        cnt = {c: valid_refs(c, ms) for c in base}
                    s = {c for c in base if filt(c) and (cnt[c] == 1 if eq == '==1' else cnt[c] <= 1)}
                    line += ' %-6d' % len(s)
                    rows.append((uni, base_tag, au_tag, eq, ms, len(s), s == A))
                print(line)

hits = [r for r in rows if r[5] == 1211]
print('\ncombinations yielding exactly 1211: %d' % len(hits))
for r in hits: print('   ', r, ' equals (a)?', r[6])

# class-level dedupe variants
byclass = collections.defaultdict(list)
for c in kept: byclass[rd32(c+12)].append(c)
cls = len(byclass)
print('\nclass-level (dedupe by TD, base 1214): classes=%d' % cls)
for name, cnt in (('all refs', nref_all), ('rdata refs', nref_rd)):
    for eq in (1, 0):
        n = 0
        for td, v in byclass.items():
            tot = sum(cnt[c] for c in v)
            if (tot == eq):
                n += 1
        print('  class total %s %s %d -> classes %d' % (name, '==' if eq else '<=', eq, n))

# C4-(a) excluded three, full context
print('\n(a) excluded COLs and their single vtable validity:')
for c in sorted(c for c in kept if rd32(c+4) > 0x1000):
    for v in refs.get(c, ()):
        print('  COL 0x%08x %-28s mdisp=0x%08x vt=0x%08x vtSec=%-7s txtslots=%d'
              % (c, nm(c), rd32(c+4), v, sn(v), txtslots(v)))
        print('        slots:', [hex(rd32(v+4*i) or 0) for i in range(6)])

# C5 exact table
print('\nC5 table: #COLs whose best vtable has >= k .text slots in first 64')
for tag, base in (('1216', set(cols)), ('1214', K)):
    mx = {c: max([txtslots(v) for v in refs.get(c, ())], default=-1) for c in base}
    print(' base=%s ' % tag + '  '.join('k%d=%d' % (k, sum(1 for c in base if mx[c] >= k))
                                       for k in range(2, 13)))
    print('        (with -1 for no vtable) same numbers; monotone?',
          all(sum(1 for c in base if mx[c] >= k) >= sum(1 for c in base if mx[c] >= k+1)
              for k in range(2, 12)))

# C6 corrected
low  = {min(v) for v in byclass.values()}
md0  = {c for c in kept if rd32(c+4) == 0}
multi = {td: v for td, v in byclass.items() if len(v) > 1}
mn = {min(v) for v in multi.values()}; mxv = {max(v) for v in multi.values()}
print('\nC6 corrected (base 1214):')
print(' |A|=%d |B|=%d equal=%s sym=%d a-only=%d b-only=%d'
      % (len(low), len(md0), low == md0, len(low ^ md0), len(low-md0), len(md0-low)))
print(' a-only == set of min-VA COLs of multi classes? %s (%d vs %d)'
      % (low-md0 == mn, len(low-md0), len(mn)))
print(' b-only == set of mdisp0 COLs of multi classes == max-VA? %s (%d vs %d)'
      % (md0-low == mxv, len(md0-low), len(mxv)))
print(' multi classes=%d ; mdisp0-not-highest=%d'
      % (len(multi), sum(1 for td, v in multi.items()
                         if max([c for c in v if rd32(c+4) == 0] or [0]) != max(v))))

json.dump({'a': len(A), 'sweep': [[*r[:5], r[5]] for r in rows],
           'hits1211': [r[:5] for r in hits]},
          open(os.path.join(OUT, 'audit_f01_c4deep.json'), 'w'), indent=1, default=str)
print('\n-> audit_f01_c4deep.json')
