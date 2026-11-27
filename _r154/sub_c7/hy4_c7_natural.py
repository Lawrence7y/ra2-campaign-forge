# -*- coding: utf-8 -*-
"""R154-C7NAT exec: independent recompute of C7 dead-branch natural rows.
Read-only on all source files. Artifacts only under _r154/sub_c7/hy4_*.
One command, one script, all evidence printed.
"""
import csv, io, os, re, json, hashlib, random

ROOT = os.path.abspath('.')
DR   = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'DISC_RECHECK.tsv')
OUT  = os.path.join(ROOT, '_r154', 'sub_c7')
os.makedirs(OUT, exist_ok=True)

def read(p):
    with io.open(p, encoding='utf-8', newline='') as f:
        return f.read()

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

# ---- load 31 rows ----
with io.open(DR, encoding='utf-8', newline='') as f:
    table = list(csv.reader(f, delimiter='\t'))
header, rows = table[0], table[1:]
assert len(rows) == 31, 'expected 31 rows, got %d' % len(rows)

# ---- full-repo file inventory (exclude .git), streamed, low memory ----
repo_files = []
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d != '.git']
    for fn in fns:
        repo_files.append(os.path.join(dp, fn))

bak_files = [p for p in repo_files if p.endswith('.bak')]
basename_index = {}
for p in repo_files:
    basename_index.setdefault(os.path.basename(p), []).append(p)

# ---- per-row observation logic ----
def observations_of(art_rel):
    """STRICT reading of the card:
       - '同目录下 basename 相同' = the artifact itself in its own directory (no repo-wide same-basename copies,
         which are sibling subagent files, not historical versions of this artifact).
       - <name>.bak / <name>.before_*.bak and any *.bak whose filename contains the basename, repo-wide.
    """
    bn = os.path.basename(art_rel)
    art_abs = os.path.normpath(os.path.join(ROOT, art_rel))
    out = set()
    if os.path.isfile(art_abs):
        out.add(art_abs)
    for p in bak_files:
        if bn in os.path.basename(p):
            out.add(p)
    return sorted(out)

results = []
for r in rows:
    rid = r[0].strip()
    sec = r[1].strip()
    art_rel = r[4].strip().replace('\\', '/')
    art_abs = os.path.normpath(os.path.join(ROOT, art_rel))
    expr = r[5].strip()
    exists = os.path.isfile(art_abs)
    cur_b = os.path.getsize(art_abs) if exists else None
    bn = os.path.basename(art_rel)
    obs = observations_of(art_rel)
    # measure each observation's bytes; dedupe identical file paths
    sizes = []
    obs_detail = []
    for p in obs:
        if os.path.isfile(p):
            sz = os.path.getsize(p)
            sizes.append(sz)
            obs_detail.append({'path': os.path.relpath(p, ROOT), 'bytes': sz, 'sha256': sha256(p)})
    distinct = sorted(set(sizes))
    n = len(sizes)
    # A/B/C grading
    if n >= 2 and len(distinct) == 1:
        tier = 'A'
    elif n == 1:
        tier = 'B'
    elif n >= 2 and len(distinct) >= 2:
        tier = 'C'
    else:
        tier = 'B0'  # 0 observations
    results.append({
        'id': rid, 'section': sec, 'artifact': art_rel, 'artifact_exists': exists,
        'current_bytes': cur_b, 'checkexpr': expr, 'basename': bn,
        'observations': n, 'distinct_bytes': distinct, 'tier': tier,
        'obs_detail': obs_detail,
    })

# ---- C-tier check: run checkexpr on every historical version ----
def eval_expr(expr, text):
    """Mirror check_disc.py C7 semantics: grep=/grepcount=/rows=/bytes=."""
    if expr.startswith('grep='):
        pat = expr[len('grep='):].strip()
        try:
            n = len(re.findall(pat, text, re.M))
        except re.error as e:
            return ('REGEX_ERROR', str(e))
        return {'hits': n, 'pass': n >= 1}
    if expr.startswith('grepcount='):
        rest = expr[len('grepcount='):].strip()
        m = re.fullmatch(r'(.*)=(\d+)$', rest, re.S)
        if not m:
            return ('BAD_EXPR', rest)
        pat, want = m.group(1), int(m.group(2))
        try:
            n = len(re.findall(pat, text, re.M))
        except re.error as e:
            return ('REGEX_ERROR', str(e))
        return {'hits': n, 'want': want, 'pass': n == want}
    if expr.startswith('rows='):
        m = re.match(r'(\d+)', expr[len('rows='):].strip())
        if not m:
            return ('BAD_EXPR', expr)
        want = int(m.group(1))
        n = len([l for l in text.split('\n') if l])
        return {'hits': n, 'want': want, 'pass': n == want}
    if expr.startswith('bytes='):
        m = re.match(r'(\d+)', expr[len('bytes='):].strip())
        if not m:
            return ('BAD_EXPR', expr)
        want = int(m.group(1))
        return ('BYTES_EXPR', want)  # not a content grep; handled separately
    return ('UNKNOWN_EXPR', expr)

for res in results:
    if res['tier'] != 'C':
        continue
    runs = []
    for od in res['obs_detail']:
        p = os.path.join(ROOT, od['path'])
        try:
            txt = read(p)
        except Exception as e:
            runs.append({'path': od['path'], 'error': str(e)})
            continue
        ev = eval_expr(res['checkexpr'], txt)
        runs.append(dict({'path': od['path'], 'bytes': od['bytes']}, **ev))
    res['c_grep_runs'] = runs
    hits = sum(1 for x in runs if isinstance(x, dict) and x.get('pass') is True)
    res['c_grep_hit_ratio'] = '%d/%d' % (hits, len(runs))

# ---- controls ----
# control 1: fabricated artifact name -> 0 hits
rng = random.Random(154)
fake = 'R154_FABRICATED_NEVER_EXISTS_%04d.md' % rng.randint(1000, 9999)
fake_hits = []
for p in repo_files:
    if fake in os.path.basename(p) or fake == os.path.basename(p):
        fake_hits.append(os.path.relpath(p, ROOT))
# control 2: stub set non-empty (all checkexprs parse to something other than UNKNOWN_EXPR)
unknown_exprs = [x['id'] for x in results if eval_expr(x['checkexpr'], '') == ('UNKNOWN_EXPR', x['checkexpr'])]
stub_set = [x['id'] for x in results if x['id'] not in unknown_exprs]
# control 3: not all rows same tier
tiers_all = [x['tier'] for x in results]
controls = {
    'fabricated_name': fake,
    'fabricated_hits': fake_hits,
    'fabricated_is_zero': len(fake_hits) == 0,
    'stub_set_nonempty': len(stub_set) > 0,
    'stub_set_size': len(stub_set),
    'unknown_expr_ids': unknown_exprs,
    'tiers_present': sorted(set(tiers_all)),
    'not_all_same_tier': len(set(tiers_all)) > 1,
}

# ---- write artifacts ----
json_path = os.path.join(OUT, 'hy4_c7_natural.json')
with io.open(json_path, 'w', encoding='utf-8') as f:
    json.dump({'controls': controls, 'rows': results}, f, ensure_ascii=False, indent=2)

md_path = os.path.join(OUT, 'hy4_c7_natural.md')
with io.open(md_path, 'w', encoding='utf-8') as f:
    f.write('# R154-C7NAT hy4 independent recompute\n\n')
    f.write('Observation semantics (strict): current artifact + repo-wide *.bak whose filename contains its basename; repo-wide same-basename copies excluded (sibling-run duplicates, not historical versions).\n\n')
    f.write('| id | section | tier | observations | distinct_bytes | current_bytes | artifact |\n')
    f.write('|---|---|---|---|---|---|---|\n')
    for x in results:
        cb = str(x['current_bytes']) if x['current_bytes'] is not None else 'none'
        db = ','.join(str(z) for z in x['distinct_bytes']) or 'none'
        f.write('| %s | %s | %s | %d | %s | %s | %s |\n' %
                (x['id'], x['section'], x['tier'], x['observations'], db, cb, x['artifact']))
    f.write('\n## C tier grep on historical versions\n\n')
    crows = [x for x in results if x['tier'] == 'C']
    if not crows:
        f.write('(no C-tier rows)\n')
    for x in crows:
        f.write('- id %s: %s (%s), ratio %s\n' %
                (x['id'], x['checkexpr'], x.get('c_grep_hit_ratio', '?'), 
                 ', '.join('%s:%s' % (os.path.basename(y['path']), y.get('hits', y.get('error','?'))) for y in x.get('c_grep_runs', []))))
    f.write('\n## Controls\n\n')
    f.write(json.dumps(controls, ensure_ascii=False, indent=2))
    f.write('\n')

# ---- print full evidence summary ----
print('=== CONTROLS ===')
print(json.dumps(controls, ensure_ascii=False))
print('=== TIER COUNTS ===')
from collections import Counter
print(json.dumps(dict(Counter(tiers_all)), ensure_ascii=False))
print('=== 31 ROWS ===')
print('| id | tier | obs | distinct | current | artifact |')
for x in results:
    print('| %s | %s | %d | %s | %s | %s |' %
          (x['id'], x['tier'], x['observations'],
           ','.join(map(str, x['distinct_bytes'])) or '-',
           x['current_bytes'] if x['current_bytes'] is not None else 'none',
           x['artifact']))
print('=== C-TIER GREP RUNS ===')
for x in results:
    if x['tier'] == 'C':
        print(json.dumps({'id': x['id'], 'expr': x['checkexpr'], 'ratio': x.get('c_grep_hit_ratio'),
                          'runs': x.get('c_grep_runs')}, ensure_ascii=False))
print('=== ARTIFACTS ===')
for p in (json_path, md_path):
    print(os.path.relpath(p, ROOT), os.path.getsize(p), 'bytes', sha256(p))
