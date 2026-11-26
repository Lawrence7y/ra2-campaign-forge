#!/usr/bin/env python3
# R140-F01-AUDIT : independent (non-author) reimplementation of the RTTI
# three-table counting claims C1..C6.  Pure struct-based PE parsing, no
# capstone, no pefile, no reading of the audited r140*.py scripts.
import struct, hashlib, json, os, collections, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE  = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(ROOT, '_r140', 'audit')
data = open(EXE, 'rb').read()
SHA  = hashlib.sha256(data).hexdigest()

# ---------------- PE headers ----------------
pe = struct.unpack_from('<I', data, 0x3c)[0]
assert data[pe:pe+4] == b'PE\0\0'
nsec     = struct.unpack_from('<H', data, pe+6)[0]
optsz    = struct.unpack_from('<H', data, pe+20)[0]
opt      = pe + 24
magic    = struct.unpack_from('<H', data, opt)[0]
IMAGEBASE= struct.unpack_from('<I', data, opt+28)[0]
sectab   = opt + optsz
SECS = []
for i in range(nsec):
    o = sectab + 40*i
    nm = data[o:o+8].rstrip(b'\0').decode('latin1')
    vs, va, rs, rp = struct.unpack_from('<IIII', data, o+8)
    ch = struct.unpack_from('<I', data, o+36)[0]
    SECS.append(dict(name=nm, vs=vs, rva=va, rs=rs, rp=rp, ch=ch,
                     va_lo=IMAGEBASE+va, va_hi=IMAGEBASE+va+max(vs, rs),
                     raw_lo=rp, raw_hi=rp+rs))

def sec_of_name(pfx):
    for s in SECS:
        if s['name'].startswith(pfx):
            return s
    raise KeyError(pfx)

TEXT  = sec_of_name('.text')
RDATA = sec_of_name('.rdata')
DATA  = sec_of_name('.data')

def raw2va(off):
    for s in SECS:
        if s['raw_lo'] <= off < s['raw_hi']:
            return IMAGEBASE + s['rva'] + (off - s['raw_lo'])
    return None

def va2raw(va):
    for s in SECS:
        if s['va_lo'] <= va < s['va_lo'] + s['rs']:
            return s['raw_lo'] + (va - s['va_lo'])
    return None

def rd32(va):
    o = va2raw(va)
    if o is None or o+4 > len(data):
        return None
    return struct.unpack_from('<I', data, o)[0]

def rd_str(va, maxlen=256):
    o = va2raw(va)
    if o is None:
        return None
    e = o
    while e < len(data) and e-o < maxlen and 0x20 <= data[e] <= 0x7e:
        e += 1
    return data[o:e].decode('latin1')

def in_sec(va, s):
    return s['va_lo'] <= va < s['va_hi']

R = {}

print('='*78)
print('R140-F01-AUDIT  independent recount   exe=%s' % EXE)
print('size=%d  sha256=%s' % (len(data), SHA))
print('ImageBase=0x%08x' % IMAGEBASE)
print('%-10s %-10s %-10s %-10s %-10s %-10s' % ('section','RVA','VS','RAW','RSSIZE','VA'))
for s in SECS:
    print('%-10s 0x%08x 0x%08x 0x%08x 0x%08x 0x%08x' %
          (s['name'], s['rva'], s['vs'], s['rp'], s['rs'], s['va_lo']))
print('CARD CHECK .text  RVA=0x%x VS=0x%x RAW=0x%x -> %s' % (TEXT['rva'], TEXT['vs'], TEXT['rp'],
      'MATCH' if (TEXT['rva']==0x1000 and TEXT['rp']==0x400) else 'DIFF'))
print('CARD CHECK .rdata RVA=0x%x VS=0x%x RAW=0x%x' % (RDATA['rva'], RDATA['vs'], RDATA['rp']))
print('CARD CHECK .data  RVA=0x%x VS=0x%x RAW=0x%x' % (DATA['rva'], DATA['vs'], DATA['rp']))

# ---------------- C1 : TypeDescriptor ----------------
# .?AV / .?AU printable run ending in '@@'; S = string VA; TD = S-8;
# require dword[S-8] in .rdata/.data and dword[S-4]==0.
tds = []            # (td_va, name, kind, s_va)
seen_s = set()
for s in (RDATA, DATA):
    buf = data[s['raw_lo']:s['raw_hi']]
    for tag, kind in ((b'.?AV', 'V'), (b'.?AU', 'U')):
        i = buf.find(tag)
        while i != -1:
            e = i
            while e < len(buf) and e-i < 256 and 0x20 <= buf[e] <= 0x7e:
                e += 1
            st = buf[i:e].decode('latin1')
            if st.endswith('@@') and len(st) >= 8:
                off = s['raw_lo'] + i
                s_va = raw2va(off)
                if s_va is not None and s_va not in seen_s:
                    v8 = rd32(s_va-8)
                    v4 = rd32(s_va-4)
                    if v8 is not None and v4 is not None:
                        if (in_sec(v8, RDATA) or in_sec(v8, DATA)) and v4 == 0:
                            seen_s.add(s_va)
                            tds.append((s_va-8, st, kind, s_va))
            i = buf.find(tag, i+1)

tds.sort()
td_va = {t[0]: t for t in tds}
nV = sum(1 for t in tds if t[2] == 'V')
nU = sum(1 for t in tds if t[2] == 'U')
print('\n--- C1 TypeDescriptor ---')
print('TD total=%d   .?AV=%d   .?AU=%d   (claim 988 = 962 + 26)' % (len(tds), nV, nU))
print('distinct TD VA=%d  distinct string VA=%d' % (len(td_va), len(seen_s)))
R['C1'] = dict(total=len(tds), nV=nV, nU=nU)

# ---------------- raw index of dwords ----------------
# map every 4-aligned raw offset -> dword, for whole image
dwords = {}      # raw off -> value
for s in SECS:
    for o in range(s['raw_lo'], s['raw_hi']-3, 4):
        dwords[o] = struct.unpack_from('<I', data, o)[0]

# ---------------- C2 : COL candidates ----------------
# find dwords whose value == some TD VA ; COL = that position - 12
col_hits = collections.defaultdict(list)   # col_va -> td_va it points to
for o, v in dwords.items():
    if v in td_va:
        pos_va = raw2va(o)
        if pos_va is None:
            continue
        col = pos_va - 12
        if dwords.get(va2raw(col), None) == 0 and rd32(col+12) == v:
            col_hits[col].append(v)
cols_all = sorted(col_hits)                 # 1216 candidates
print('\n--- C2 COL structure ---')
print('COL candidates (dword[COL]==0 & dword[COL+12]==TD)  = %d' % len(cols_all))
strict8 = [c for c in cols_all if rd32(c+8) == 0]
print('  of which dword[COL+8]==0 (cdOffset==0)             = %d' % len(strict8))
dup = [c for c in cols_all if len(col_hits[c]) > 1]
print('  COL addr claimed by >1 TD (impossible)             = %d' % len(dup))
# how many distinct COLs point to a TD in .rdata vs .data
R['C2_cand'] = len(cols_all)

# C3 exclusion
dropped = [c for c in cols_all if rd32(c+16) == 0]
kept    = [c for c in cols_all if rd32(c+16) != 0]
print('  dword[COL+16]==0 (null pClassDescriptor) -> drop   = %d' % len(dropped))
print('  structural COL (dword[COL+16]!=0)                  = %d' % len(kept))
R['C2_kept'] = len(kept); R['C2_drop'] = len(dropped)

def col_name(c):
    td = rd32(c+12)
    t = td_va.get(td)
    return t[1] if t else ('<TD 0x%x>' % td)

# ---------------- vtables : dword[vt-4]==COL VA ----------------
vt_of_col = collections.defaultdict(list)   # col_va -> [vt_va]
all_vt = []
for o, v in dwords.items():
    if v in col_hits:
        vt = raw2va(o) + 4
        vt_of_col[v].append(vt)
        all_vt.append((vt, v))
print('\n--- vtables (dword[vt-4]==COL) ---')
print('vtable pointers found = %d   distinct vt = %d' % (len(all_vt), len(set(v for v, _ in all_vt))))

# ---------------- C3 three-condition coincidence (on 1216) ----------------
def nvt(c):
    return len(vt_of_col.get(c, ()))
c3_a = [c for c in cols_all if rd32(c+16) == 0]
c3_b = [c for c in cols_all if rd32(c+4) == c - 0x18]
c3_c = [c for c in cols_all if nvt(c) == 0]
sa, sb, sc = set(c3_a), set(c3_b), set(c3_c)
inter3 = sa & sb & sc
print('\n--- C3 exclusion coincidence (over the %d candidates) ---' % len(cols_all))
print('A: dword[COL+16]==0                    -> %d' % len(sa))
print('B: dword[COL+4]==COL-0x18              -> %d' % len(sb))
print('C: no vtable dword[vt-4]==COL          -> %d' % len(sc))
print('A&B&C intersection                     -> %d' % len(inter3))
print('A only / B only / C only               -> %d / %d / %d' % (len(sa-sb-sc), len(sb-sa-sc), len(sc-sa-sb)))
print('dropped set size=%d ; kept=%d ; sum=%d' % (len(dropped), len(kept), len(dropped)+len(kept)))
for c in sorted(dropped):
    print('  DROP COL 0x%08x  name=%-34s mdisp=0x%08x cdOff=0x%08x pCD=0x%08x vtRefs=%d  '
          'mdisp==COL-0x18:%s' % (c, col_name(c), rd32(c+4), rd32(c+8), rd32(c+16), nvt(c),
                                  'Y' if rd32(c+4) == c-0x18 else 'N'))
R['C3'] = dict(A=len(sa), B=len(sb), C=len(sc), inter=len(inter3),
               dropped=[(c, col_name(c)) for c in sorted(dropped)])

# ---------------- C4 : two reproductions of 1211 ----------------
set_1214 = set(kept)
c4a = {c for c in set_1214 if rd32(c+4) <= 0x1000}
# (b) over the 1216 candidates: name not .?AU and exactly one vtable backref
c4b = {c for c in cols_all if not col_name(c).startswith('.?AU') and nvt(c) == 1}
print('\n--- C4 the two 1211 reproductions ---')
print('(a) within %d kept, dword[COL+4]<=0x1000        -> %d' % (len(set_1214), len(c4a)))
print('(b) within %d cand, name!=.?AU & exactly 1 vtable-> %d' % (len(cols_all), len(c4b)))
print('(a)==(b)? %s   |a|= %d  |b|= %d  symdiff=%d' % (c4a == c4b, len(c4a), len(c4b),
      len(c4a ^ c4b)))
print('only in a=%d  only in b=%d' % (len(c4a-c4b), len(c4b-c4a)))
# cross-checks on the same two predicates applied to the other base set
c4a_1216 = {c for c in cols_all if rd32(c+4) <= 0x1000}
c4b_1214 = {c for c in set_1214 if not col_name(c).startswith('.?AU') and nvt(c) == 1}
print('cross: (a) on 1216 -> %d ; (b) on 1214 -> %d' % (len(c4a_1216), len(c4b_1214)))
# also: the two dropped
print('are the C3 dropped pair inside (a)? %s ; inside (b)? %s' %
      ([c in c4a for c in dropped], [c in c4b for c in dropped]))
R['C4'] = dict(a=len(c4a), b=len(c4b), same=c4a == c4b, symdiff=len(c4a ^ c4b),
               a_only=len(c4a-c4b), b_only=len(c4b-c4a))

# ---------------- C5 : vtable .text-slot-count family ----------------
def slots_txt(vt, n=64, textonly=True):
    k = 0
    for i in range(n):
        v = rd32(vt + 4*i)
        if v is None:
            break
        if textonly:
            if in_sec(v, TEXT):
                k += 1
        else:
            if any(in_sec(v, s) for s in SECS if s['ch'] & 0x20000000):
                k += 1
    return k

print('\n--- C5  vtable .text-slot family ---')
for label, base in (('1216', cols_all), ('1214', sorted(set_1214))):
    maxtx = {}
    for c in base:
        vs = vt_of_col.get(c, ())
        maxtx[c] = max([slots_txt(v) for v in vs], default=-1)
    for textonly in (True, False):
        lbl = '.text only' if textonly else 'any exec sec'
        row = []
        for k in range(0, 13):
            if not textonly and k < 2:
                continue
            n = sum(1 for c in base if maxtx[c] >= k) if textonly else \
                sum(1 for c in base if max([slots_txt(v, 64, False) for v in vt_of_col.get(c, ())], default=-1) >= k)
            row.append((k, n))
        print(' base=%s  crit=%-12s  %s' % (label, lbl,
              '  '.join('k%d=%d' % (k, n) for k, n in row if k >= 2)))
    if label == '1216':
        hist = collections.Counter(maxtx.values())
        print('  maxslot histogram (top):', sorted(hist.items())[:12], '...max=', max(hist))
        R['C5'] = {str(k): sum(1 for c in base if maxtx[c] >= k) for k in range(2, 13)}

# ---------------- C6 : 954 sets ----------------
def analyse(base, tag):
    byclass = collections.defaultdict(list)
    for c in base:
        byclass[rd32(c+12)].append(c)
    A = {min(v) for v in byclass.values()}                 # lowest-VA COL per class
    B = {c for c in base if rd32(c+4) == 0}                 # mdisp==0
    multi = {td: v for td, v in byclass.items() if len(v) > 1}
    bad = []
    for td, v in multi.items():
        z = [c for c in v if rd32(c+4) == 0]
        if z and max(z) != max(v):
            bad.append(td)
    print('\n--- C6 954 sets (base=%s, %d COLs) ---' % (tag, len(base)))
    print(' classes(distinct TD)=%d   multi-COL classes=%d   single=%d' %
          (len(byclass), len(multi), len(byclass)-len(multi)))
    print(' |A min-VA-per-class|=%d   |B mdisp==0|=%d   A==B? %s   |A^B|=%d (a-only %d, b-only %d)' %
          (len(A), len(B), A == B, len(A ^ B), len(A-B), len(B-A)))
    print(' multi-COL classes where mdisp==0 is NOT the highest-VA COL: %d' % len(bad))
    extra = sum(len(v)-1 for v in byclass.values())
    print(' extra COLs beyond first per class=%d' % extra)
    return dict(classes=len(byclass), multi=len(multi), A=len(A), B=len(B),
                same=A == B, sym=len(A ^ B), aonly=len(A-B), bonly=len(B-A), bad=len(bad))

R['C6_1214'] = analyse(sorted(set_1214), '1214')
R['C6_1216'] = analyse(cols_all, '1216')

# ---------------- sanity: the two dropped names ----------------
print('\n--- C3 dropped names ---')
print([ (hex(c), col_name(c)) for c in sorted(dropped) ])

json.dump({'sha256': SHA, 'size': len(data), 'R': R},
          open(os.path.join(OUT, 'audit_f01_indep.json'), 'w'), indent=1, default=str)
print('\nJSON -> %s' % os.path.join(OUT, 'audit_f01_indep.json'))
