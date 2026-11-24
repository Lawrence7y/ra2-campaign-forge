# -*- coding: utf-8 -*-
"""D47-SURFACE step 0: reproduce PANEL baseline (panel columns) from disk."""
import io, re, collections, math

R = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
COV = R + r'\COVERAGE\coverage.tsv'
ATLAS = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'


def load_coverage():
    lines = open(COV, encoding='utf-8-sig').read().splitlines()
    hdr = lines[0].split('\t')
    assert hdr[0] == 'entry,subsystem,name,one_line_semantics,grade,evidence_path,n_sources,conflict'
    rows = []
    for ln in lines[1:]:
        c = ln.split('\t')
        if len(c) != 8:
            continue
        rows.append(dict(entry=c[0].upper(), subsystem=c[1], name=c[2], sem=c[3],
                         grade=c[4], ev=c[5], n_sources=c[6], conflict=c[7]))
    return rows


def load_atlas():
    out = set()
    for i, ln in enumerate(open(ATLAS, encoding='utf-8-sig')):
        if i == 0:
            continue
        out.add(ln.split('\t')[0].strip().upper())
    return out


SUB_RE = re.compile(r'::sub_[0-9A-Fa-f]+$')
BARE_SUB = re.compile(r'^sub_[0-9A-Fa-f]+$')


def is_named(name):
    n = name.strip()
    if not n:
        return False
    if SUB_RE.search(n) or BARE_SUB.match(n):
        return False
    return True


def panel(rows, atlas):
    agg = collections.defaultdict(lambda: dict(n=0, named=0, proved=0, strict=0))
    for r in rows:
        if r['entry'] not in atlas:
            continue
        k = r['subsystem']
        a = agg[k]
        a['n'] += 1
        if r['grade'] == '[已证]':
            a['proved'] += 1
            if is_named(r['name']):
                a['named'] += 1
            if '[未证]' not in r['sem']:
                a['strict'] += 1
        elif is_named(r['name']):
            # named column counts named rows regardless of grade
            pass
    # named counts all named rows (any grade) in atlas
    agg2 = collections.defaultdict(lambda: dict(n=0, named=0, proved=0, strict=0))
    for r in rows:
        if r['entry'] not in atlas:
            continue
        k = r['subsystem']
        a = agg2[k]
        a['n'] += 1
        if is_named(r['name']):
            a['named'] += 1
        if r['grade'] == '[已证]':
            a['proved'] += 1
            if '[未证]' not in r['sem']:
                a['strict'] += 1
    return agg2


def verdict(a):
    n = a['n']
    thr_named = math.ceil(0.9 * n)
    thr_p = math.ceil(0.5 * n)
    nominal = a['named'] >= thr_named and a['proved'] >= thr_p
    strict = a['named'] >= thr_named and a['strict'] >= thr_p
    return thr_named, thr_p, nominal, strict


if __name__ == '__main__':
    rows = load_coverage()
    atlas = load_atlas()
    agg = panel(rows, atlas)
    out = io.open(R + r'\D47_SURFACE\work\panel_recompute.txt', 'w', encoding='utf-8')
    tot = dict(n=0, named=0, proved=0, strict=0)
    nm = 0
    st = 0
    out.write('S\tn\tnamed\tproved\tstrict\tthr_named\tthr_p\tnominal\tstrict_ok\n')
    for k in sorted(agg):
        a = agg[k]
        tn, tp, no, so = verdict(a)
        nm += no
        st += so
        for f in tot:
            tot[f] += a[f]
        out.write('%s\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%s\n' % (
            k, a['n'], a['named'], a['proved'], a['strict'], tn, tp, no, so))
    out.write('TOTAL\t%d\t%d\t%d\t%d\t-\t-\t%d/22\t%d/22\n' % (
        tot['n'], tot['named'], tot['proved'], tot['strict'], nm, st))
    out.write('\nproved all (no atlas filter) = %d\n' % sum(1 for r in rows if r['grade'] == '[已证]'))
    out.write('proved in atlas = %d\n' % tot['proved'])
    out.write('coverage rows = %d, atlas entries = %d\n' % (len(rows), len(atlas)))
    out.close()
    print('written')
