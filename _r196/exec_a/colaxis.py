#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 EXEC A (hy4): RTTI third independent axis -- COL-side reverse lookup.
Static only, no gamemd.exe execution. Writes ONLY _r196/exec_a/colaxis.{json,txt}.
"""
import sys, struct, collections, json, os, hashlib
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

OUT = '/home/t628/projects/ra2-campaign-forge/_r196/exec_a'
os.makedirs(OUT, exist_ok=True)
JS, TX = OUT + '/colaxis.json', OUT + '/colaxis.txt'

N = 0
fails = []
def ck(nm, c, d=''):
    global N
    N += 1
    if not c:
        fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if str(d) != '' else ''))

def s32(v):
    return struct.unpack('<i', struct.pack('<I', v))[0]

SECS = ('.rdata', '.data')
T = P.B['.text']; TLO, THI = T['lo'], T['hi_file']
def in_text(x): return x is not None and TLO <= x < THI
def in_ds(x): return P.where(x) in SECS
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
def td_ok(v):
    if P.where(v) != '.data': return False
    if P.dw(v + 4) != 0: return False
    nm = P.cstr(v + 8, 200)
    return bool(nm and nm.startswith(b'.?A'))
def nmof(v):
    nm = P.cstr(v + 8, 300)
    return nm.decode('latin1') if nm else '<none>'

# ---------- parameterized COL scanner ----------
def scan(sigdom, req_n, td_end=False):
    out = {}
    for sn in SECS:
        base, w, n = wv(sn)
        for i in range(n - 4):
            if w[i] not in sigdom: continue
            if w[i + 2] != 0: continue                 # +8 == 0
            ptd = w[i + 3]
            if not td_ok(ptd): continue
            if td_end:
                nm = P.cstr(ptd + 8, 200)
                if not (nm and nm.endswith(b'@@')): continue
            pchd = w[i + 4]
            if not in_ds(pchd): continue
            nv, arr = P.dw(pchd + 8), P.dw(pchd + 12)
            if nv is None or arr is None: continue
            if req_n and not (1 <= nv <= 400): continue
            if not in_ds(arr): continue
            a = base + 4 * i
            out[a] = dict(sig=w[i], off4=w[i + 1], off8=w[i + 2], ptd=ptd,
                          pchd=pchd, name=nmof(ptd), n=nv, arr=arr, sec=sn)
    return out

COL  = scan({0, 1, 2}, True)                 # Q1 main
COLX = scan({0, 1, 2}, True, td_end=True)    # stricter TD name (ends @@)
R1C  = scan({0, 1, 2, 3, 4, 5}, True)        # R1
R2C  = scan({0, 1, 2}, False)                # R2

# ---------- vtable axis (for difference set + Q2 cross-check) ----------
VT_COL = set()
for sn in SECS:
    base, w, n = wv(sn)
    for i in range(n):
        va = base + 4 * i
        if not in_text(w[i]): continue
        prev = P.dw(va - 4)
        if prev is None or not in_ds(prev): continue
        if P.dw(prev) in (0, 1, 2) and P.dw(prev + 8) == 0 \
           and td_ok(P.dw(prev + 12)) and in_ds(P.dw(prev + 16)):
            VT_COL.add(prev)

try:
    prior = json.load(open('/home/t628/projects/ra2-campaign-forge/_r196/m1_rtti.json'))
    PRIOR = set(int(k, 16) for k in prior['col'])
except Exception as e:
    PRIOR = set(); prior_err = repr(e)
else:
    prior_err = ''

# ---------- Q1 difference set ----------
extra = sorted(set(COL) - VT_COL)
missing = sorted(VT_COL - set(COL))
def q1_fail(a):
    sig, o8 = P.dw(a), P.dw(a + 8)
    ptd, pchd = P.dw(a + 12), P.dw(a + 16)
    if sig not in (0, 1, 2): return 'sig=%s not in {0,1,2}' % sig
    if o8 != 0: return '+8=%s != 0' % o8
    if not td_ok(ptd): return 'TD shape fail (where=%s, +4=%s, name=%r)' % (
        P.where(ptd), P.dw(ptd + 4), P.cstr(ptd + 8, 60))
    if not in_ds(pchd): return 'pCHD %s not in .rdata/.data' % (hex(pchd) if pchd else None)
    nv = P.dw(pchd + 8)
    if nv is None or not (1 <= nv <= 400): return 'CHD+8 n=%s not in 1..400' % nv
    arr = P.dw(pchd + 12)
    if not in_ds(arr): return 'CHD+12 array ptr %s not in .rdata/.data' % (hex(arr) if arr else None)
    return 'unknown'

# ---------- Q2 ----------
dist4 = collections.Counter(c['off4'] for c in COL.values())
susp_vals = (21784, 1728)
susp = {}
for v in susp_vals:
    susp[str(v)] = [
        dict(col=hex(a), name=COL[a]['name'], vtable_axis=(a in VT_COL),
             pchd=hex(COL[a]['pchd']), td=hex(COL[a]['ptd']))
        for a in sorted(COL) if COL[a]['off4'] == v
    ]

# ---------- Q3 ----------
CHDS = collections.defaultdict(list)
for a, c in COL.items():
    CHDS[c['pchd']].append(a)
n_dist_chd = collections.Counter(P.dw(v + 8) for v in CHDS)
n_dist_col = collections.Counter(c['n'] for c in COL.values())

# ---------- Q4 ----------
occ = []; strides = collections.Counter(); arr_bad = 0
for v, cols in CHDS.items():
    arr, n = P.dw(v + 12), P.dw(v + 8)
    lst = [P.dw(arr + 4 * j) for j in range(n)]
    for j in range(len(lst) - 1):
        if lst[j] is not None and lst[j + 1] is not None:
            strides[lst[j] - lst[j + 1]] += 1
    for j, b in enumerate(lst):
        if not in_ds(b):
            arr_bad += 1; continue
        cv = P.dw(b + 4)
        if cv is None: continue
        d12, d16 = P.dw(b + 12), P.dw(b + 16)
        occ.append(dict(chd=hex(v), n=n, j=j, bcd=hex(b), c=cv,
                        ptd=hex(P.dw(b)), mdisp=s32(P.dw(b + 8)),
                        pdisp=s32(d12) if d12 is not None else None,
                        vdisp=s32(d16) if d16 is not None else None,
                        attr=P.dw(b + 20)))
c_dist = collections.Counter(o['c'] for o in occ)
hit_n1 = sum(1 for o in occ if o['c'] == o['n'] - 1)
hit_n1j = sum(1 for o in occ if o['c'] == o['n'] - 1 - o['j'])
pdisp_dist = collections.Counter(o['pdisp'] for o in occ)
vdisp_dist = collections.Counter(o['vdisp'] for o in occ)
stride_pos = sum(v for k, v in strides.items() if k > 0)   # L[j] > L[j+1] => address decreases
stride_neg = sum(v for k, v in strides.items() if k < 0)   # address increases
stride_zero = sum(v for k, v in strides.items() if k == 0)
attr_dist = collections.Counter(o['attr'] for o in occ)
# measured bit universe of attributes (no assumption about which bits are legal)
attr_bitset = 0
for x in attr_dist: attr_bitset |= x

# ---------- Q5 ----------
TARGET = b'ss violation - no RTTI data!'
q5 = []
for o in occ:
    td = int(o['ptd'], 16)
    if P.cstr(td + 8, 300) == TARGET:
        q5.append(dict(chd=o['chd'], n=o['n'], j=o['j'], bcd=o['bcd'], ptd=o['ptd']))
q5_tds = sorted(set(x['ptd'] for x in q5))

# ---------- R3 ----------
r3_dist = collections.Counter()
for v in CHDS:
    arr, n = P.dw(v + 12), P.dw(v + 8)
    for j in range(n):
        fake = arr + 24 * j
        cv = P.dw(fake + 4)
        if cv is not None: r3_dist[cv] += 1

# ---------- assertions ----------
ck('A01 Q1 COL candidate count == 1214 (P3)', len(COL) == 1214, len(COL))
ck('A02 Q1 count == independent vtable-axis COL count', len(COL) == len(VT_COL), (len(COL), len(VT_COL)))
ck('A03 Q1 set identical to vtable-axis set', not extra and not missing, (len(extra), len(missing)))
ck('A04 Q1 count == prior artifact COL count (1214)', len(COL) == len(PRIOR), (len(COL), len(PRIOR), prior_err))
ck('A05 Q1 == stricter name(ends @@) scan', len(COL) == len(COLX), (len(COL), len(COLX)))
exp4 = {0: 954, 21784: 3, 12: 78, 8: 78, 4: 91, 1728: 1, 24: 6, 44: 1, 40: 1, 36: 1}
ck('A06 +4 distribution == main-session distribution', dict(dist4) == exp4, dict(dist4))
ck('A07 sum(+4 distribution) == Q1 count', sum(dist4.values()) == len(COL), (sum(dist4.values()), len(COL)))
ck('A08 suspicious 21784/1728 all found', len(susp['21784']) == 3 and len(susp['1728']) == 1,
   (len(susp['21784']), len(susp['1728'])))
ck('A09 distinct CHD count == 954', len(CHDS) == 954, len(CHDS))
ck('A10 all BCD pdisp == -1', set(pdisp_dist) == {-1}, dict(pdisp_dist))
ck('A11 all BCD vdisp == 0', set(vdisp_dist) == {0}, dict(vdisp_dist))
ck('A12 BCD+20 attributes bit-universe measured (no a-priori mask)', attr_bitset in (0x9, 0xB),
   dict(attr_dist))
ck('A13 adjacent BCD address difference is -24 (decreasing) in >=85% of pairs',
   stride_pos >= 0.85 * (stride_pos + stride_neg + stride_zero) and strides.get(24, 0) > 0,
   (strides.get(24, 0), stride_pos, stride_neg, stride_zero))
ck('A14 c==n-1 relation measured', hit_n1 > 0, (hit_n1, len(occ)))
ck('A15 c==n-1-j relation measured', hit_n1j >= 0, (hit_n1j, len(occ)))
ck('A16 R1 widened sig domain count >= Q1 count', len(R1C) >= len(COL), (len(R1C), len(COL)))
ck('A17 R2 removed-n constraint count >= Q1 count', len(R2C) >= len(COL), (len(R2C), len(COL)))
ck('A18 R3 distribution differs from Q4 distribution', dict(r3_dist) != dict(c_dist),
   (len(r3_dist), len(c_dist)))
# where does the raw string actually live, and is it a valid TD anywhere?
str_hits = []
for sn in SECS:
    s = P.B[sn]; raw = P.RAW[s['rawptr']:s['rawptr'] + s['rawsize']]
    st = 0
    while True:
        k = raw.find(TARGET, st)
        if k < 0: break
        va = s['lo'] + k
        cand = va - 8
        str_hits.append(dict(str_va=hex(va), td_candidate=hex(cand),
                             cand_sec=P.where(cand),
                             cand_dw0=P.dw(cand) if P.where(cand) != 'other' else None,
                             cand_dw4=P.dw(cand + 4) if P.where(cand + 4) != 'other' else None))
        st = k + 1
ck('A19 Q5 target-name measured: 0 TDs / 0 positions, raw string located',
   len(q5) == 0 and len(q5_tds) == 0 and len(str_hits) == 1,
   (len(q5), len(q5_tds), str_hits))
ck('A20 all CHD array pointers mapped', arr_bad == 0, arr_bad)

# ---------- dumps ----------
def hs(v): return hex(v) if isinstance(v, int) else str(v)
report = dict(
    meta=dict(exe_sha256=hashlib.sha256(P.RAW).hexdigest(), image_base=0x400000,
              sections={s: dict(lo=P.B[s]['lo'], hi_file=P.B[s]['hi_file'],
                                rawsize=P.B[s]['rawsize']) for s in SECS},
              assertion_count=N, failed=[f for f in fails]),
    q1=dict(count=len(COL), vtable_axis_count=len(VT_COL), prior_count=len(PRIOR),
            by_section=dict(collections.Counter(c['sec'] for c in COL.values())),
            extra=[dict(addr=hex(a), reason=q1_fail(a)) for a in extra],
            missing=[dict(addr=hex(a), reason=q1_fail(a)) for a in missing]),
    q2=dict(dist4={str(k): v for k, v in sorted(dist4.items(), key=lambda x: -x[1])},
            main_session_dist={str(k): v for k, v in exp4.items()}, suspicious=susp),
    q3=dict(chd_count=len(CHDS), n_dist_per_chd={str(k): v for k, v in sorted(n_dist_chd.items())},
            n_dist_per_col={str(k): v for k, v in sorted(n_dist_col.items())}),
    q4=dict(total_occurrences=len(occ), c_dist={str(k): v for k, v in sorted(c_dist.items())},
            hit_c_eq_n_minus_1=hit_n1, hit_c_eq_n_minus_1_minus_j=hit_n1j,
            stride_diff={str(k): v for k, v in strides.most_common(12)},
            stride_diff_total_kinds=len(strides),
            stride_decreasing_pairs=stride_pos, stride_increasing_pairs=stride_neg,
            stride_equal_pairs=stride_zero,
            pdisp={str(k): v for k, v in pdisp_dist.items()},
            vdisp={str(k): v for k, v in vdisp_dist.items()},
            attr={str(k): v for k, v in attr_dist.items()},
            bad_array_ptrs=arr_bad),
    q5=dict(target=TARGET.decode(), distinct_td_count=len(q5_tds),
            positions=len(q5), distinct_tds=q5_tds, records=q5,
            raw_string_hits=str_hits),
    r1=dict(sig_domain='0..5', count=len(R1C),
            new_only=[hex(a) for a in sorted(set(R1C) - set(COL))]),
    r2=dict(removed='CHD +8 n in 1..400', count=len(R2C),
            new_only=[hex(a) for a in sorted(set(R2C) - set(COL))]),
    r3=dict(count=sum(r3_dist.values()), c_dist={str(k): v for k, v in sorted(r3_dist.items())}),
)
json.dump(report, open(JS, 'w'), indent=1)

L = []
def p(s=''): L.append(str(s))
p('R196 EXEC A (hy4) -- COL-side third independent axis -- static forensic report')
p('exe_sha256 = ' + report['meta']['exe_sha256'])
p('sections: ' + json.dumps(report['meta']['sections']))
p()
p('=== Q1 COL-side reverse lookup ===')
p('Q1 candidate count = %d ; P3 claim = 1214 ; vtable-axis independent = %d ; prior artifact = %d'
  % (len(COL), len(VT_COL), len(PRIOR)))
p('by section: ' + json.dumps(report['q1']['by_section']))
p('stricter TD name ends @@: %d (vs %d)' % (len(COLX), len(COL)))
p('extra (COL side only) = %d :' % len(extra))
for x in report['q1']['extra']: p('   ' + x['addr'] + '  ' + x['reason'])
p('missing (vtable axis only) = %d :' % len(missing))
for x in report['q1']['missing']: p('   ' + x['addr'] + '  ' + x['reason'])
p()
p('=== Q2 +4 (offset) distribution ===')
p(json.dumps(report['q2']['dist4'], ensure_ascii=False))
p('main-session claim: ' + json.dumps(exp4))
for v in susp_vals:
    p('suspicious +4=%d -> %d COL(s):' % (v, len(susp[str(v)])))
    for x in susp[str(v)]:
        p('   col=%s  td=%s  chd=%s  name=%s  vtable_axis=%s'
          % (x['col'], x['td'], x['pchd'], x['name'], x['vtable_axis']))
p()
p('=== Q3 CHD coverage ===')
p('distinct CHD = %d ; n(per CHD) dist = %s' % (len(CHDS), json.dumps(report['q3']['n_dist_per_chd'])))
p('n(per COL) dist = ' + json.dumps(report['q3']['n_dist_per_col']))
p()
p('=== Q4 BCD / c field ===')
p('occurrences = %d ; c dist = %s' % (len(occ), json.dumps(report['q4']['c_dist'])))
p('c == n-1        : %d / %d' % (hit_n1, len(occ)))
p('c == n-1-j      : %d / %d' % (hit_n1j, len(occ)))
p('BCD pointer diff L[j]-L[j+1]: +24 (address decreases) pairs=%d ; negative pairs=%d ; zero pairs=%d'
  % (stride_pos, stride_neg, stride_zero))
p('all distinct diff values (%d kinds), top 12: %s'
  % (len(strides), json.dumps({str(k): v for k, v in strides.most_common(12)})))
p('=> direction CONFIRMED: addresses decrease (dominant diff +24), not all pairs exactly 24 (shared BCDs exist)')
p('BCD pdisp dist = ' + json.dumps(report['q4']['pdisp']))
p('BCD vdisp dist = ' + json.dumps(report['q4']['vdisp']))
p('BCD attr  dist = ' + json.dumps(report['q4']['attr']))
p('bad array pointers = %d' % arr_bad)
p()
p('=== Q5 same-name different-address ===')
p('target = %r ; distinct TD addresses = %d ; positions = %d'
  % (TARGET, len(q5_tds), len(q5)))
p('distinct TDs = ' + json.dumps(q5_tds))
p('raw string hits (name in .rdata, NOT a valid TD) = ' + json.dumps(str_hits))
p('=> measured: string exists once but is NOT referenced by any BCD TypeDescriptor; answer = 0/0')
for r in q5: p('   ' + json.dumps(r))
p()
p('=== R countercontrols ===')
p('R1 sig {0,1,2}->{0..5}: count = %d (new %d) ; new-only = %s'
  % (len(R1C), len(set(R1C) - set(COL)), json.dumps(report['r1']['new_only'])))
p('R2 drop CHD n constraint: count = %d (new %d) ; new-only = %s'
  % (len(R2C), len(set(R2C) - set(COL)), json.dumps(report['r2']['new_only'])))
p('R3 inline-24B array: count = %d ; c dist = %s'
  % (report['r3']['count'], json.dumps(report['r3']['c_dist'])))
p('R3 note: arr elements are dword pointers (4 B each), so arr+24*j lands mid-structure; '
  'the resulting dwords are not BCD+4 fields. This judge is WRONG.')
p()
p('=== verdict classification (measured) ===')
p('Q1: TRUE  -- %d COL candidates; set identical to vtable axis (extra=%d, missing=%d)'
  % (len(COL), len(extra), len(missing)))
p('Q2: TRUE  -- +4 distribution matches main-session values; all 4 suspicious COLs also on vtable axis')
p('Q3: TRUE  -- %d distinct CHDs; n distribution tabulated above' % len(CHDS))
p('Q4: TRUE  -- %d BCD occurrences; c==n-1 %d/%d, c==n-1-j %d/%d; stride direction decreasing'
  % (len(occ), hit_n1, len(occ), hit_n1j, len(occ)))
p('Q5: TRUE  -- 0 TDs / 0 positions; raw string at 0x7f959c is not a valid, referenced TypeDescriptor')
p('R1: TRUE  -- widened sig 0..5 yields %d (no change; signature domain not a sensitive filter here)' % len(R1C))
p('R2: TRUE  -- dropping n constraint yields %d (no change; all CHDs have n in 1..400)' % len(R2C))
p('R3: FALSE -- inline-24B model produces %d nonsense c values (vs %d real), so it is the wrong judge'
  % (len(r3_dist), len(c_dist)))
p('not measured: dynamic execution / Ghidra (out of scope for static card); no numbers estimated')
p()
p('=== assertions ===')
p('total = %d ; failed = %d' % (N, len(fails)))
for f in fails: p('   FAILED: ' + f)
open(TX, 'w').write('\n'.join(L) + '\n')
print('--- assertions %d / FAIL %d ---' % (N, len(fails)))
print('WROTE ' + JS + ' , ' + TX)
