# -*- coding: utf-8 -*-
"""r134ds_t2t5.py -- HOLE A candidate-set scan + T5 vacuity, faithful copy of C7 run_expr."""
import io, os, re, sys, json

ROOT = '/home/t628/projects/ra2-campaign-forge'
DR = os.path.join(ROOT, 'lead/next_re_20261117_r14/DISC_RECHECK.tsv')

def read(p): return io.open(p, encoding='utf-8', newline='').read()

rows = []
for ln in read(DR).split('\n'):
    if not ln: continue
    r = ln.split('\t')
    rows.append(r)
hdr, body = rows[0], rows[1:]
body = [r for r in body if len(r) == 7]
sys.stderr.write('rows=%d\n' % len(body))

CANDS = sorted(set(r[4].strip() for r in body))
sys.stderr.write('distinct col5 = %d\n' % len(CANDS))

# ---- faithful copy of gate run_expr (check_disc.py:150-204) ----
def run_expr(path, expr):
    ap = os.path.join(ROOT, path.replace('\\', '/'))
    if not os.path.isfile(ap): return False, 'FILE_MISSING'
    head = expr.split(' ')[0]
    txt_cache = None
    def get_txt():
        nonlocal txt_cache
        if txt_cache is None:
            txt_cache = io.open(ap, encoding='utf-8', errors='replace').read()
        return txt_cache
    if head.startswith('grep='):
        pat = expr[len('grep='):].strip()
        try:
            n = len(re.findall(pat, get_txt(), re.M))
        except re.error as e:
            return False, 'BAD_REGEX:%s' % e
        return (n >= 1), 'grep hits=%d' % n
    if head.startswith('grepcount='):
        rest = expr[len('grepcount='):].strip()
        m0 = re.match(r'^(.*)=(\d+)$', rest, re.S)
        if not m0: return False, 'BAD_GREPCOUNT'
        pat, want = m0.group(1), int(m0.group(2))
        try:
            n = len(re.findall(pat, get_txt(), re.M))
        except re.error as e:
            return False, 'BAD_REGEX:%s' % e
        return (n == want), 'grepcount %d vs %d' % (n, want)
    m = re.search(r'[\(（](\d+)\s*B[\)）]', expr)
    if head == 'exists':
        if m:
            want = int(m.group(1)); got = os.path.getsize(ap)
            return (got == want), 'bytes %d vs %d' % (got, want)
        return False, 'exists-without-size-annotation'
    m2 = re.fullmatch(r'bytes=(\d+)', head)
    if m2:
        return (os.path.getsize(ap) == int(m2.group(1))), 'bytes=%d' % os.path.getsize(ap)
    m3 = re.fullmatch(r'rows=(\d+)', head)
    if m3:
        n = 0; hdr_seen = 0
        with io.open(ap, encoding='utf-8', errors='replace') as f:
            for l2 in f:
                s = l2.strip()
                if s.startswith('DISC_RECHECK '): continue
                if hdr_seen == 0:
                    hdr_seen = 1; continue
                n += 1
        return (n == int(m3.group(1))), 'rows=%d' % n
    if head == 'none': return None, 'none'
    return False, 'BAD_EXPR:' + head

out = []
for r in body:
    rid, path, expr = r[0], r[4].strip(), r[5].strip()
    ok0, det0 = run_expr(path, expr)
    hits = []
    for c in CANDS:
        ok, det = run_expr(c, expr)
        if ok: hits.append(c)
    # T5: nullability under re.M for regex shapes
    head = expr.split(' ')[0]
    nullable = None
    if head.startswith('grep=') or head.startswith('grepcount='):
        if head.startswith('grep='):
            pat = expr[len('grep='):].strip()
        else:
            rest = expr[len('grepcount='):].strip()
            pat = re.match(r'^(.*)=(\d+)$', rest, re.S).group(1)
        try:
            nullable = re.search(pat, '', re.M) is not None
        except re.error as e:
            nullable = 'BAD:%s' % e
    out.append({'id': rid, 'path': path, 'expr': expr, 'head': head,
                'own_true': ok0, 'own_detail': det0,
                'set_size': len(hits), 'set': hits, 'nullable': nullable})

json.dump({'cands': CANDS, 'rows': out}, open(os.path.join(ROOT, '_r134/sub_deepseek/r134ds_t2t5.json'), 'w'), ensure_ascii=False, indent=1)

print('=== T2: rows whose TRUE-set has size >= 2 ===')
for o in out:
    if o['set_size'] >= 2:
        print('id %-3s size=%d head=%s' % (o['id'], o['set_size'], o['head']))
        for c in o['set']:
            mark = ' <== own' if c == o['path'] else ''
            print('      %s%s' % (c, mark))
print()
print('=== T2 summary ===')
print('rows total=%d ; size>=2=%d ; size==1=%d ; size==0=%d'
      % (len(out), sum(1 for o in out if o['set_size'] >= 2),
         sum(1 for o in out if o['set_size'] == 1),
         sum(1 for o in out if o['set_size'] == 0)))
print('own_true all? %s' % all(o['own_true'] for o in out))
print()
print('=== T5: nullability (regex rows) + hit count over 23 candidates ===')
print('nullable count = %d' % sum(1 for o in out if o['nullable'] is True))
for o in out:
    print('id %-3s %-12s own=%s nullable=%s set=%d' % (o['id'], o['head'], o['own_true'], o['nullable'], o['set_size']))
