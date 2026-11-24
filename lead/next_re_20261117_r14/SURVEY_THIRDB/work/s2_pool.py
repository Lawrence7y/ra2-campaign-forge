"""s2: build the row domain (pool) — coverage grade=[静态推断] ∧ entry∈function_atlas ∧ subsystem≠S22."""
import sys, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core as C

COV = C.ROOT/'lead'/'next_re_20261117_r14'/'COVERAGE'/'coverage.tsv'
ATLAS = C.ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv'

def norm(e): return e.strip().upper().replace('0X', '')

lines = COV.read_text(encoding='utf-8-sig').splitlines()
hdr = lines[0].split(',')          # 表头是逗号分隔、数据行是 Tab 分隔（项目既有约定）
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
    k = norm(r['entry'])
    try: sz = int(r['size'], 0)
    except Exception: sz = -1
    atlas[k] = dict(size=sz, n_instr=r['n_instr'])

SUB_RE = re.compile(r'S(0[1-9]|1[0-9]|2[01])')
pool = []
for r in cov:
    sub = r['subsystem'].strip().upper()
    if not SUB_RE.fullmatch(sub): continue
    if r['grade'].strip() != '[静态推断]': continue
    k = norm(r['entry'])
    if k not in atlas: continue
    pool.append(dict(entry=k, sub=sub, name=r['name'], atlas_size=atlas[k]['size']))

import collections
bysub = collections.Counter(p['sub'] for p in pool)
print('pool N =', len(pool))
print('per subsystem:', dict(sorted(bysub.items())))
print('grade histogram', collections.Counter(r['grade'].strip() for r in cov))
print('coverage rows', len(cov), 'atlas rows', len(atlas))

(C.OUT/'work'/'pool.json').write_text(json.dumps(pool, ensure_ascii=False), encoding='utf-8')
with open(C.OUT/'work'/'pool.tsv', 'w', encoding='utf-8', newline='\n') as f:
    f.write('entry\tsubsystem\tname\tatlas_size\n')
    for p in pool:
        f.write('%s\t%s\t%s\t%d\n' % (p['entry'], p['sub'], p['name'], p['atlas_size']))
print('wrote pool.tsv / pool.json')
