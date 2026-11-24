"""m1: row domain (pool) + per-subsystem metrics recomputed from disk.

Pool = coverage.tsv grade == [静态推断] AND entry in function_atlas.tsv AND subsystem in S01..S21.
Also builds the UNION entry list needed for caliber reconciliation with SURVEY-RING24 (4,444)
and SURVEY-THIRDB (4,350): those two lists are read-only inputs used ONLY for comparison,
never for the primary numbers.
"""
import sys, re, json, math, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core2 as C

COV   = C.ROOT/'lead'/'next_re_20261117_r14'/'COVERAGE'/'coverage.tsv'
ATLAS = C.ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv'
R24   = C.ROOT/'lead'/'next_re_20261117_r14'/'SURVEY_RING24'/'EVIDENCE'/'classification.tsv'
TB    = C.ROOT/'lead'/'next_re_20261117_r14'/'SURVEY_THIRDB'/'EVIDENCE'/'classification_all.tsv'

def norm(e): return e.strip().upper().replace('0X', '')

lines = COV.read_text(encoding='utf-8-sig').splitlines()
hdr = lines[0].split(',')              # header comma-separated, data tab-separated
cov = []
for l in lines[1:]:
    if not l.strip(): continue
    q = l.split('\t'); q += ['']*(len(hdr)-len(q))
    cov.append(dict(zip(hdr, q)))

al = ATLAS.read_text(encoding='utf-8-sig').splitlines()
ah = al[0].split('\t')
atlas = {}
for l in al[1:]:
    if not l.strip(): continue
    q = l.split('\t'); q += ['']*(len(ah)-len(q))
    r = dict(zip(ah, q[:len(ah)]))
    try: sz = int(r['size'], 0)
    except Exception: sz = -1
    atlas[norm(r['entry'])] = dict(size=sz, n_instr=r['n_instr'])

SUB_RE = re.compile(r'S(0[1-9]|1[0-9]|2[01])')
SUBS = ['S%02d' % i for i in range(1, 22)]

pool = []
for r in cov:
    sub = r['subsystem'].strip().upper()
    if not SUB_RE.fullmatch(sub): continue
    if r['grade'].strip() != '[静态推断]': continue
    k = norm(r['entry'])
    if k not in atlas: continue
    pool.append(dict(entry=k, sub=sub, name=r['name'],
                     semantics=r['one_line_semantics'], atlas_size=atlas[k]['size']))

metrics = {}
for s in SUBS:
    rs = [r for r in cov if r['subsystem'].strip().upper() == s and norm(r['entry']) in atlas]
    n = len(rs)
    proved = sum(r['grade'].strip() == '[已证]' for r in rs)
    metrics[s] = dict(n=n, proved=proved,
                      static=sum(r['grade'].strip() == '[静态推断]' for r in rs),
                      unproved=sum(r['grade'].strip() == '[未证]' for r in rs),
                      threshold=math.ceil(n/2))

# --- reconciliation lists (read-only; comparison only)
def load_entry_set(p, col):
    out = set()
    ls = p.read_text(encoding='utf-8-sig').splitlines()
    h = ls[0].split('\t'); ci = h.index(col)
    for l in ls[1:]:
        if not l.strip(): continue
        q = l.split('\t')
        out.add(norm(q[ci]))
    return out

r24_list = load_entry_set(R24, 'entry')
tb_list  = load_entry_set(TB, 'entry')

union = sorted({p['entry'] for p in pool} | r24_list | tb_list)

print('coverage rows      =', len(cov))
print('grade histogram    =', dict(collections.Counter(r['grade'].strip() for r in cov)))
print('atlas rows         =', len(atlas))
print('POOL (mine)        =', len(pool))
print('per subsystem      =', dict(sorted(collections.Counter(p['sub'] for p in pool).items())))
print('sanity S22 static  =', sum(1 for r in cov if r['subsystem'].strip().upper() == 'S22'
                                 and r['grade'].strip() == '[静态推断]'))
print('RING24 list        =', len(r24_list), ' THIRDB list =', len(tb_list))
print('UNION entries      =', len(union))
print('sum proved S01-21  =', sum(v['proved'] for v in metrics.values()))
print('sum static S01-21  =', sum(v['static'] for v in metrics.values()))

(C.OUT/'work'/'pool.json').write_text(json.dumps(pool, ensure_ascii=False), encoding='utf-8')
(C.OUT/'work'/'metrics.json').write_text(json.dumps(
    dict(metrics=metrics, cov_rows=len(cov), atlas_rows=len(atlas),
         pool_n=len(pool), sha=C.SHA,
         grade_hist=dict(collections.Counter(r['grade'].strip() for r in cov))),
    ensure_ascii=False, indent=1), encoding='utf-8')
(C.OUT/'work'/'union.json').write_text(json.dumps(
    dict(union=union, r24=sorted(r24_list), tb=sorted(tb_list)), ensure_ascii=False), encoding='utf-8')
print('wrote pool.json / metrics.json / union.json')
