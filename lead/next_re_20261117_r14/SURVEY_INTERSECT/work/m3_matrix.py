"""m3: three-ring matrix over the 21 subsystems + caliber reconciliation with the two prior cards.

Ring predicates (all byte-derived, see m2_rings.py):
  has2    = ②RTTI  OR ②YRpp
  has2R   = ②RTTI only            (SURVEY-RING24 主口径)
  has4    = direct(out-of-body) OR livevt(slot unanimous across every vt on that global)
  has4S   = direct(out-of-body) OR livevt(global carries a single vt)   (SURVEY-RING24 严格档)
  has3b   = any of ③b①..③b④
"""
import sys, json, math, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

OUT = Path(__file__).parent.parent
SUBS = ['S%02d' % i for i in range(1, 22)]

rings = json.loads((OUT/'work'/'rings.json').read_text(encoding='utf-8'))
pool = json.loads((OUT/'work'/'pool.json').read_text(encoding='utf-8'))
met  = json.loads((OUT/'work'/'metrics.json').read_text(encoding='utf-8'))['metrics']
U    = json.loads((OUT/'work'/'union.json').read_text(encoding='utf-8'))

R = {r['entry']: r for r in rings if 'err' not in r}
def has2(r):   return r['has2_rtti'] or r['has2_yrpp']
def has4(r):   return r['n_direct_out'] > 0 or r['n_livevt_live'] > 0
def has4S(r):  return r['n_direct_out'] > 0 or r['n_livevt_live'] > 0
def has3b(r):  return bool(r['cats'])

# ---------------- primary matrix: my pool (静态推断 ∩ atlas ∩ S01..S21) ----------------
mat = {}
for s in SUBS:
    rows = [R[p['entry']] for p in pool if p['sub'] == s]
    m = dict(n=len(rows),
             h2=sum(has2(x) for x in rows),
             h4=sum(has4(x) for x in rows),
             h3=sum(has3b(x) for x in rows),
             A=sum(has2(x) and has4(x) for x in rows),
             R3=sum(has2(x) and has4(x) and has3b(x) for x in rows),
             proved=met[s]['proved'], threshold=met[s]['threshold'], total_n=met[s]['n'])
    m['gap_now'] = max(0, m['threshold'] - m['proved'])
    m['proved_up'] = m['proved'] + m['R3']
    m['achieved_now'] = m['proved'] >= m['threshold']
    m['achieved_up'] = m['proved_up'] >= m['threshold']
    m['ok_now'] = m['proved'] >= m['threshold']
    m['ok_up'] = m['proved_up'] >= m['threshold']
    m['gap_up'] = max(0, m['threshold'] - m['proved_up'])
    mat[s] = m

T = {k: sum(mat[s][k] for s in SUBS) for k in
     ('n', 'h2', 'h4', 'h3', 'A', 'R3', 'proved', 'threshold', 'gap_now', 'proved_up', 'gap_up')}
T['achieved_now'] = sum(mat[s]['achieved_now'] for s in SUBS)
T['achieved_up']  = sum(mat[s]['achieved_up'] for s in SUBS)
T['newly'] = [s for s in SUBS if mat[s]['achieved_up'] and not mat[s]['achieved_now']]

print('=== PRIMARY MATRIX (pool = %d) ===' % T['n'])
print('%-5s %5s %5s %5s %5s %5s %5s %6s %6s %6s %6s %6s' % (
    'SUB', 'pool', '②', '④', '③b', '②∧④', '3RING', 'proved', 'thr', 'up', 'gap', 'ach'))
for s in SUBS:
    m = mat[s]
    print('%-5s %5d %5d %5d %5d %5d %5d %6d %6d %6d %6d   %s->%s' % (
        s, m['n'], m['h2'], m['h4'], m['h3'], m['A'], m['R3'],
        m['proved'], m['threshold'], m['proved_up'], m['gap_up'],
        'Y' if m['achieved_now'] else 'n', 'Y' if m['achieved_up'] else 'n'))
print('%-5s %5d %5d %5d %5d %5d %5d %6d %6d %6d %6d   %d->%d' % (
    'TOTAL', T['n'], T['h2'], T['h4'], T['h3'], T['A'], T['R3'],
    T['proved'], T['threshold'], T['proved_up'], T['gap_up'],
    T['achieved_now'], T['achieved_up']))
print('newly_crossing =', T['newly'])
print('3-ring share    = %d/%d = %.2f%%' % (T['R3'], T['n'], 100.0*T['R3']/T['n']))
print('A (②∧④) share   = %d/%d = %.2f%%' % (T['A'], T['n'], 100.0*T['A']/T['n']))
print('P(③b|A)         = %d/%d = %.2f%%' % (T['R3'], T['A'], 100.0*T['R3']/max(1, T['A'])))
print('P(③b)           = %d/%d = %.2f%%' % (T['h3'], T['n'], 100.0*T['h3']/T['n']))
print('P(②)=%.2f%%  P(④)=%.2f%%  indep E[A]=%.1f  obs/exp=%.3f' % (
    100.0*T['h2']/T['n'], 100.0*T['h4']/T['n'],
    T['h2']*T['h4']/T['n'], T['A']/(T['h2']*T['h4']/T['n'])))

# ---------------- reconciliation A: SURVEY-RING24 (4,444 row list, A=338) ----------------
print()
print('=== RECONCILIATION vs SURVEY-RING24 (their 4,444-entry list) ===')
r24 = [R[e] for e in U['r24'] if e in R]
A_rtti_S = [r for r in r24 if r['has2_rtti'] and has4S(r)]
A_rtti_L = [r for r in r24 if r['has2_rtti'] and has4(r)]
A_any    = [r for r in r24 if has2(r) and has4(r)]
print('my A  ②RTTI ∧ ④(㉓-filtered) = %d   (theirs 338)' % len(A_rtti_S))
print('my A  ②RTTI ∧ ④literal-unanimous = %d' % len(A_rtti_L))
print('my A  ②RTTI ∧ ④without ㉓ filter  = %d' % len(
    [r for r in r24 if r['has2_rtti'] and (r['n_direct_out'] > 0 or r['n_livevt_unanimous'] > 0)]))
print('my A  ②(RTTI∨YRpp) ∧ ④(㉓)      = %d   (theirs 341 = 338+3)' % len(A_any))
print('②RTTI only = %d  (theirs P(②)=91.90%% => 4084)' % sum(r['has2_rtti'] for r in r24))
print('④ direct-out = %d  livevt-single = %d  livevt-㉓-live = %d' % (
    sum(r['n_direct_out'] > 0 for r in r24), sum(r['n_livevt_single'] > 0 for r in r24),
    sum(r['n_livevt_live'] > 0 for r in r24)))
# row-level diff against their EVIDENCE
theirs = {}
p = OUT.parent/'SURVEY_RING24'/'EVIDENCE'/'classification.tsv'
ls = p.read_text(encoding='utf-8-sig').splitlines(); h = ls[0].split('\t')
for l in ls[1:]:
    if not l.strip(): continue
    q = l.split('\t'); theirs[q[0]] = dict(zip(h, q))
d2 = []; d4 = []; dA = []; dA_dir = []
for r in r24:
    th = theirs.get(r['entry'])
    if not th: continue
    t2 = th['has2_rtti'] == '1'
    t4 = th['has4_strict'] == '1'
    if t2 != r['has2_rtti']: d2.append((r['entry'], t2, r['has2_rtti']))
    if t4 != has4S(r): d4.append((r['entry'], t4, has4S(r)))
    tdir = th['n_direct_out']
    if tdir.isdigit() and int(tdir) != r['n_direct_out']:
        dA_dir.append((r['entry'], tdir, r['n_direct_out']))
    if (t2 and t4) != (r['has2_rtti'] and has4S(r)):
        dA.append((r['entry'], t2 and t4, r['has2_rtti'] and has4S(r)))
print('row-level ② disagreements = %d %s' % (len(d2), d2[:5]))
print('row-level ④strict disagreements = %d %s' % (len(d4), d4[:5]))
print('row-level n_direct_out disagreements = %d %s' % (len(dA_dir), dA_dir[:5]))
print('row-level A disagreements = %d %s' % (len(dA), dA[:5]))

# ---------------- reconciliation B: SURVEY-THIRDB (4,350 row list, ③b=472) ----------------
print()
print('=== RECONCILIATION vs SURVEY-THIRDB (their 4,350-entry list) ===')
tb = [R[e] for e in U['tb'] if e in R]
print('my ③b on their list = %d   (theirs 472)' % sum(has3b(r) for r in tb))
th3 = {}
p2 = OUT.parent/'SURVEY_THIRDB'/'EVIDENCE'/'classification_all.tsv'
ls2 = p2.read_text(encoding='utf-8-sig').splitlines(); h2 = ls2[0].split('\t')
for l in ls2[1:]:
    if not l.strip(): continue
    q = l.split('\t'); th3[q[0]] = dict(zip(h2, q))
d3 = []
for r in tb:
    th = th3.get(r['entry'])
    if not th: continue
    t = th['verdict'] == '③b'
    if t != has3b(r): d3.append((r['entry'], t, has3b(r), r['cats'], th['channels']))
print('row-level ③b disagreements = %d' % len(d3))
for x in d3[:12]: print('   ', x)
print('their ③b total in file =', sum(1 for v in th3.values() if v['verdict'] == '③b'))

json.dump(dict(mat=mat, T=T, A_rtti_S=sorted(r['entry'] for r in A_rtti_S),
               A_any=sorted(r['entry'] for r in A_any),
               diff2=d2, diff4=d4, diffA=dA, diff3=d3,
               n3b_tb=sum(has3b(r) for r in tb), n3b_pool=T['h3']),
          open(OUT/'work'/'matrix.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nwrote matrix.json')
