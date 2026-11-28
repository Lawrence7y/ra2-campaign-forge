#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 exec_a: slots 11/12/13 byte census (static only). One shot, all evidence."""
import sys, struct, collections, json, hashlib, os, subprocess
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

OUT = '/home/t628/projects/ra2-campaign-forge/_r200/exec_a'
os.makedirs(OUT, exist_ok=True)
_orig = sys.stdout
_buf = []
class Tee:
    def write(self, s):
        _orig.write(s); _buf.append(s)
    def flush(self):
        _orig.flush()
sys.stdout = Tee()

N = 0
fails = []
def ck(nm, c, d=''):
    global N
    N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def in_text(x): return x is not None and LO <= x < HI
def hx(x): return hex(x) if x is not None else 'None'

print('=== BASE RECONSTRUCTION (byte reads only) ===')
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], pchd=w[i + 4], name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL:
            VT[base + 4 * i] = P.dw(base + 4 * i - 4)
NS = {}
def nslot(vt):
    if vt in NS: return NS[vt]
    k = 0
    while True:
        t = P.dw(vt + 4 * k)
        if not in_text(t): break
        k += 1
    NS[vt] = k; return k
MAIN = [vt for vt in VT if COL[VT[vt]]['mdisp'] == 0]
ck('B1 COL==1214', len(COL) == 1214, len(COL))
ck('B2 VT==1214', len(VT) == 1214, len(VT))
ck('B3 slot total==14044', sum(nslot(v) for v in VT) == 14044, sum(nslot(v) for v in VT))
ck('B4 MAIN==954', len(MAIN) == 954, len(MAIN))

r199 = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in r199['pairs']]
uniq = list(dict.fromkeys(pairs))
r199_slotmis = {int(k): v for k, v in r199['slotmis'].items()}
ck('B5 pairs==603', len(pairs) == 603, len(pairs))
ck('B6 pairs unique==603', len(uniq) == 603, len(uniq))
ck('B7 MAIN order reproducible', len(set(MAIN)) == 954, len(set(MAIN)))

def dv(vt, k): return P.dw(vt + 4 * k)
def comparable(p, k): return min(nslot(p[0]), nslot(p[1])) > k
def matched(p, k):
    a, b = dv(p[0], k), dv(p[1], k)
    return a is not None and b is not None and a == b

def slot_stats(pl, k):
    den = sum(1 for p in pl if comparable(p, k))
    m = sum(1 for p in pl if comparable(p, k) and matched(p, k))
    return dict(den=den, match=m, mis=den - m,
                rate=round(100.0 * m / den, 2) if den else 0.0)

def triple_states(pl, ks):
    """states per comparable pair, order = ks; returns counter + isomorphism count."""
    c = collections.Counter(); iso = 0; den = 0
    for p in pl:
        if not all(comparable(p, k) for k in ks): continue
        den += 1
        st = ''.join('M' if matched(p, k) else 'X' for k in ks)
        c[st] += 1
        if st in ('MMM', 'XXX'): iso += 1
    return dict(counter=c, iso=iso, den=den,
                ratio=round(100.0 * iso / den, 2) if den else 0.0)

def topn(counter, n=5):
    return [[hx(a), cnt] for a, cnt in counter.most_common(n)]

res = {}
res['B'] = dict(col=len(COL), vt=len(VT), slots=sum(nslot(v) for v in VT),
                main=len(MAIN), pairs=len(pairs), uniq=len(uniq))

print('\n=== Q1 DENOMINATOR / SLOT 11 12 13 ===')
q1 = {}
for k in (11, 12, 13):
    q1[k] = slot_stats(pairs, k)
    s = q1[k]
    print('  slot %-2d den=%-4d match=%-4d mismatch=%-4d match_rate=%.2f%% (mismatch_rate=%.2f%%)'
          % (k, s['den'], s['match'], s['mis'], s['rate'], round(100.0 * s['mis'] / s['den'], 2)))
    ck('Q1 slot%d den/mis matches R199' % k,
       s['den'] == r199_slotmis[k][1] and s['mis'] == r199_slotmis[k][0],
       (s['den'], s['mis'], r199_slotmis[k]))
both14 = sum(1 for p in uniq if nslot(p[0]) >= 14 and nslot(p[1]) >= 14)
print('  unique pairs with n_d>=14 and n_b>=14: %d' % both14)
ck('Q1 both>=14 equals comparable-13 den', both14 == q1[13]['den'], (both14, q1[13]['den']))
ck('Q1 match+mis==den all slots', all(q1[k]['match'] + q1[k]['mis'] == q1[k]['den'] for k in q1))
res['Q1'] = {str(k): v for k, v in q1.items()}
res['Q1']['both_ge_14'] = both14

print('\n=== Q2 TRIPLE STATES (11,12,13) ===')
ORDER = ('MMM', 'MMX', 'MXM', 'MXX', 'XMM', 'XMX', 'XXM', 'XXX')
q2 = triple_states(pairs, (11, 12, 13))
for st in ORDER:
    print('  %s = %d' % (st, q2['counter'][st]))
print('  triple comparable pairs = %d ; isomorphism (MMM+XXX) = %d (%.2f%%)'
      % (q2['den'], q2['iso'], q2['ratio']))
repro = (q2['iso'] == 107)
print('  R199 recorded 107 -> independent value %d ; reproduced = %s' % (q2['iso'], repro))
ck('Q2 eight states sum==den', sum(q2['counter'][st] for st in ORDER) == q2['den'], q2['den'])
ck('Q2 iso == R199 107', repro, q2['iso'])
res['Q2'] = dict(states={st: q2['counter'][st] for st in ORDER}, den=q2['den'],
                 iso=q2['iso'], ratio=q2['ratio'], r199_107_reproduced=repro)

print('\n=== Q3 IMPLEMENTATION ADDRESS DISTRIBUTIONS ===')
q3 = {}
for k in (11, 12, 13):
    match_b = collections.Counter()
    for p in pairs:
        if comparable(p, k) and matched(p, k): match_b[dv(p[1], k)] += 1
    all_vt = collections.Counter()
    for vt in VT:
        v = dv(vt, k)
        if v is not None: all_vt[v] += 1
    main_all = collections.Counter()
    for vt in MAIN:
        v = dv(vt, k)
        if v is not None: main_all[v] += 1
    q3[k] = dict(match_b_top5=topn(match_b), all_vt_top5=topn(all_vt),
                 main_top5=topn(main_all), main_distinct=len(main_all),
                 all_vt_distinct=len(all_vt), match_b_total=sum(match_b.values()))
    print('  slot %d: match-side vt_b Top5:' % k)
    for a, c in q3[k]['match_b_top5']: print('      %-12s %d' % (a, c))
    print('  slot %d: all %d VT Top5:' % (k, len(VT)))
    for a, c in q3[k]['all_vt_top5']: print('      %-12s %d' % (a, c))
    print('  slot %d: %d MAIN Top5; distinct_impl_on_MAIN=%d; distinct_all_VT=%d'
          % (k, len(MAIN), q3[k]['main_distinct'], q3[k]['all_vt_distinct']))
    for a, c in q3[k]['main_top5']: print('      %-12s %d' % (a, c))
    ck('Q3 slot%d match-side count==Q1 match' % k, q3[k]['match_b_total'] == q1[k]['match'],
       (q3[k]['match_b_total'], q1[k]['match']))
res['Q3'] = {str(k): v for k, v in q3.items()}

print('\n=== Q4 DERIVED-SIDE ADDRESS REUSE ACROSS SLOTS ===')
S = {}
for k in (11, 12, 13):
    S[k] = set(dv(p[0], k) for p in pairs if comparable(p, k) and dv(p[0], k) is not None)
i12 = S[11] & S[12]; i13 = S[11] & S[13]; i23 = S[12] & S[13]
i123 = S[11] & S[12] & S[13]; uni = S[11] | S[12] | S[13]
print('  |S11|=%d |S12|=%d |S13|=%d' % (len(S[11]), len(S[12]), len(S[13])))
print('  |S11&S12|=%d |S11&S13|=%d |S12&S13|=%d |S11&S12&S13|=%d |union|=%d'
      % (len(i12), len(i13), len(i23), len(i123), len(uni)))
trip_list = []
for a in sorted(i123, key=lambda x: -sum(1 for k in (11, 12, 13) if a in S[k]))[:10]:
    per = {str(k): sum(1 for p in pairs if comparable(p, k) and dv(p[0], k) == a) for k in (11, 12, 13)}
    trip_list.append(dict(addr=hx(a), occurrences=sum(per.values()), per_slot=per))
    print('    triple addr %-12s occ=%d per_slot=%s' % (hx(a), trip_list[-1]['occurrences'], per))
ck('Q4 pairwise intersections <= min set sizes',
   len(i12) <= min(len(S[11]), len(S[12])) and len(i13) <= min(len(S[11]), len(S[13]))
   and len(i23) <= min(len(S[12]), len(S[13])), (len(i12), len(i13), len(i23)))
ck('Q4 triple intersection <= every pairwise intersection',
   len(i123) <= min(len(i12), len(i13), len(i23)), len(i123))
ck('Q4 union <= sum of set sizes', len(uni) <= sum(len(s) for s in S.values()), len(uni))
res['Q4'] = dict(sizes={str(k): len(S[k]) for k in S},
                 pair={ '11_12': len(i12), '11_13': len(i13), '12_13': len(i23)},
                 triple=len(i123), union=len(uni), triple_addrs=trip_list)

print('\n=== Q5 BASE-SIDE TRIPLE VALUES ===')
trip = collections.Counter(); eq = 0; targets = collections.Counter()
for p in pairs:
    if not all(comparable(p, k) for k in (11, 12, 13)): continue
    a11, a12, a13 = dv(p[1], 11), dv(p[1], 12), dv(p[1], 13)
    trip[(a11, a12, a13)] += 1
    if a11 == a12 == a13: eq += 1
    for a in (a11, a12, a13):
        if in_text(a): targets[a] += 1
print('  (a11,a12,a13) Top5:')
for (a, b, c), cnt in trip.most_common(5):
    print('      (%s, %s, %s) = %d' % (hx(a), hx(b), hx(c), cnt))
print('  a11==a12==a13 pairs = %d / %d' % (eq, q2['den']))
print('  distinct in-.text target addresses = %d; first 16 bytes (<=5):' % len(targets))
bodies = []
for a, cnt in targets.most_common(5):
    o = P.r2o(a)
    bs = P.RAW[o:o + 16].hex() if o is not None else 'NO_MAP'
    bodies.append(dict(addr=hx(a), occurrences=cnt, bytes16=bs))
    print('      %-12s occ=%-3d bytes16=%s' % (hx(a), cnt, bs))
ck('Q5 tuple counts sum==triple den', sum(trip.values()) == q2['den'], sum(trip.values()))
ck('Q5 equal-triple <= den', eq <= q2['den'], eq)
res['Q5'] = dict(top5=[[hx(a), hx(b), hx(c), cnt] for (a, b, c), cnt in trip.most_common(5)],
                 equal_triples=eq, den=q2['den'], distinct_text_targets=len(targets), bodies=bodies)

print('\n=== Q6 CONTROL GROUPS ===')
GROUPS = [(8, 9, 10), (11, 12, 13), (14, 15, 16)]
grp = {}
for ks in GROUPS:
    ss = [slot_stats(pairs, k) for k in ks]
    ts = triple_states(pairs, ks)
    grp[ks] = dict(slots=ss, den=ts['den'], iso=ts['iso'], ratio=ts['ratio'],
                   states={st: ts['counter'][st] for st in ORDER})
    print('  group %-12s : ' % str(ks)
          + ' | '.join('s%d den=%d M=%d X=%d rate=%.2f%%' % (k, s['den'], s['match'], s['mis'], s['rate'])
                       for k, s in zip(ks, ss)))
    print('       triple_den=%-4d MMM=%-3d XXX=%-3d iso=%-4d iso_ratio=%.2f%%'
          % (ts['den'], ts['counter']['MMM'], ts['counter']['XXX'], ts['iso'], ts['ratio']))
    ck('Q6 group %s state sum==den' % str(ks), sum(ts['counter'].values()) == ts['den'], ts['den'])
r13 = grp[(11, 12, 13)]['ratio']
d8 = abs(r13 - grp[(8, 9, 10)]['ratio']); d14 = abs(r13 - grp[(14, 15, 16)]['ratio'])
def two_prop_z(i1, n1, i2, n2):
    p = (i1 + i2) / float(n1 + n2)
    se = (p * (1 - p) * (1.0 / n1 + 1.0 / n2)) ** 0.5
    return (i1 / n1 - i2 / n2) / se if se else 0.0
z8 = two_prop_z(grp[(11, 12, 13)]['iso'], grp[(11, 12, 13)]['den'],
                grp[(8, 9, 10)]['iso'], grp[(8, 9, 10)]['den'])
z14 = two_prop_z(grp[(11, 12, 13)]['iso'], grp[(11, 12, 13)]['den'],
                 grp[(14, 15, 16)]['iso'], grp[(14, 15, 16)]['den'])
print('  iso_ratio deltas vs (8,9,10)=%.2f pp (z=%.2f), vs (14,15,16)=%.2f pp (z=%.2f)'
      % (d8, z8, d14, z14))
print('  two-sided p: z>1.96 significant at 0.05; |z8|=%.2f |z14|=%.2f' % (abs(z8), abs(z14)))
if abs(z8) >= 1.96 and abs(z14) >= 1.96:
    verdict = '11/12/13 与两组对照在三槽同构比例上均存在显著差异(p<0.05)'
elif abs(z8) < 1.96 and abs(z14) < 1.96:
    verdict = '11/12/13 不特殊，R199 的 37.60% 三连不是结构信号'
else:
    verdict = '11/12/13 仅与部分对照显著不同，证据不足以下定论'
print('  VERDICT: ' + verdict)
res['Q6'] = {str(ks): v for ks, v in grp.items()}
res['Q6']['deltas_pp'] = [round(d8, 2), round(d14, 2)]
res['Q6']['z_vs_8_9_10'] = round(z8, 3)
res['Q6']['z_vs_14_15_16'] = round(z14, 3)
res['Q6']['verdict'] = verdict

print('\n=== R1 ORDER PERMUTATION CONTROLS ===')
r1a = triple_states(pairs, (11, 12, 14))
r1b = triple_states(pairs, (11, 13, 12))
print('  (11,12,14): triple_den=%d iso=%d ratio=%.2f%%' % (r1a['den'], r1a['iso'], r1a['ratio']))
print('  (11,13,12): triple_den=%d iso=%d ratio=%.2f%%' % (r1b['den'], r1b['iso'], r1b['ratio']))
ck('R1 permutation invariance (11,13,12)==(11,12,13)', r1b['iso'] == q2['iso'], (r1b['iso'], q2['iso']))
res['R1'] = dict(g11_12_14=dict(den=r1a['den'], iso=r1a['iso'], ratio=r1a['ratio']),
                 g11_13_12=dict(den=r1b['den'], iso=r1b['iso'], ratio=r1b['ratio']))

print('\n=== R2 SHUFFLED PAIRING CONTROL ===')
shuf = [(p[0], MAIN[(i * 137 + 11) % len(MAIN)]) for i, p in enumerate(pairs)]
r2 = {}
for k in (11, 12, 13):
    s = slot_stats(shuf, k); r2[k] = s
    print('  slot %d shuffled den=%d match=%d rate=%.2f%% | real match=%d rate=%.2f%%'
          % (k, s['den'], s['match'], s['rate'], q1[k]['match'], q1[k]['rate']))
ck('R2 shuffle match < real on all 3 slots', all(r2[k]['match'] < q1[k]['match'] for k in (11, 12, 13)),
   {k: (r2[k]['match'], q1[k]['match']) for k in (11, 12, 13)})
res['R2'] = {str(k): v for k, v in r2.items()}

print('\n=== R3 SHORT-N SLOT HANDLING ===')
short = sum(1 for p in pairs if min(nslot(p[0]), nslot(p[1])) < 14)
print('  pairs with min(n_d,n_b) < 14 = %d' % short)
r3 = {}
for k in (11, 12, 13):
    skip = slot_stats(pairs, k)
    zero_den = len(pairs)
    zero_m = sum(1 for p in pairs if comparable(p, k) and matched(p, k))
    r3[k] = dict(skip_match=skip['match'], skip_den=skip['den'], skip_rate=skip['rate'],
                 zero_match=zero_m, zero_den=zero_den,
                 zero_rate=round(100.0 * zero_m / zero_den, 2))
    print('  slot %d: SKIP match=%d den=%d rate=%.2f%% | ZERO match=%d den=%d rate=%.2f%%'
          % (k, skip['match'], skip['den'], skip['rate'], zero_m, zero_den, r3[k]['zero_rate']))
ck('R3 skip match == zero match (short pairs counted mismatch)',
   all(r3[k]['skip_match'] == r3[k]['zero_match'] for k in (11, 12, 13)),
   {k: (r3[k]['skip_match'], r3[k]['zero_match']) for k in (11, 12, 13)})
ck('R3 skip den == Q1 den', all(r3[k]['skip_den'] == q1[k]['den'] for k in (11, 12, 13)))
res['R3'] = {str(k): v for k, v in r3.items()}

print('\n=== PROCESS HYGIENE ===')
ps = subprocess.run(['ps', '-eo', 'pid,stat,cmd'], capture_output=True, text=True).stdout
# only count *other* slot1113 python processes, not this one's ancestors/current PID
me = os.getpid()
anc = set()
cur = me
while True:
    anc.add(cur)  # start with self; read ppid from /proc/<cur>/stat (comm may contain ')')
    try:
        ppid = int(open('/proc/%d/stat' % cur).read().split(') ', 1)[1].split()[1])
    except Exception:
        break
    if ppid <= 1 or ppid in anc: break
    cur = ppid
orph = []
for l in ps.splitlines():
    parts = l.strip().split(None, 2)
    if len(parts) < 3: continue
    try: pid = int(parts[0])
    except ValueError: continue  # 'PID STAT CMD' header
    if pid == me or pid in anc: continue
    cmd = parts[2]
    # only a genuine python process whose argv actually contains our script as a token
    is_py = False
    try:
        exe = os.path.realpath('/proc/%d/exe' % pid)
        is_py = os.path.basename(exe).startswith('python')
    except Exception:
        pass
    argv = []
    try:
        argv = open('/proc/%d/cmdline' % pid, 'rb').read().split(b'\0')
    except Exception:
        pass
    if is_py and any(os.path.basename(a.decode('latin1')) == 'slot1113.py' for a in argv if a):
        orph.append(l.strip())
print('orphan slot1113 python processes at close: %d %s' % (len(orph), orph))
ck('no orphan slot1113 python processes', len(orph) == 0, len(orph))

print('\n=== FINAL ===')
ck('asserts >= 12', N >= 12, N)
res['asserts'] = N; res['fails'] = fails
res['verdict'] = verdict
res['orphan_processes'] = orph
js = OUT + '/slot1113.json'
tx = OUT + '/slot1113.txt'
json.dump(res, open(js, 'w'), ensure_ascii=False, indent=1)
open(tx, 'w').write(''.join(_buf))
sys.stdout = _orig
print('wrote %s and %s' % (js, tx))
print('SUMMARY asserts=%d fails=%d verdict=%s' % (N, len(fails), verdict))
for p in [js, tx, '/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json',
          '/home/t628/projects/ra2-campaign-forge/_r185/pe185.py']:
    h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    print('sha256 %s %s' % (h, p))
print('lines %s %d' % (tx, len(open(tx, 'rb').read().splitlines())))
print('lines %s %d' % (js, len(open(js, 'rb').read().splitlines())))
