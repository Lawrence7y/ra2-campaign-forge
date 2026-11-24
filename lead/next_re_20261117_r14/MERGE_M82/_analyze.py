# -*- coding: utf-8 -*-
"""M82 phase 1 (READ ONLY): reproduce EVID_RESOLVE suffix-unique matching.

Goal: from resolve.tsv R_MISSING rows, reproduce REPORT.md's claim:
  92 distinct relative paths; 87 suffix-unique / 5 ambiguous / 0 lost  (path level)
  361 unique / 13 ambiguous / 0 lost  (row level)
Also: enumerate actual candidate files, and propose the new full relative path
for each unique row.

Writes analysis artifacts only inside MERGE_M82 (never to EVID_RESOLVE or card dirs).
"""
import os, re, collections, json

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
RESOLVE = os.path.join(R14, 'EVID_RESOLVE', 'resolve.tsv')
OUTDIR = os.path.join(R14, 'MERGE_M82')

SPLIT_RE = re.compile(r'[;,|]')
ABS_RE = re.compile(r'^(?:[A-Za-z]:[\\/]|\\\\|/)')
LINESPEC_RE = re.compile(r':(?:\d+[0-9A-Za-z\-]*|0x[0-9A-Fa-f\-]+)$')


def strip_anchor(part):
    p = part.split('#', 1)[0].strip()
    if not ABS_RE.match(p):
        p = LINESPEC_RE.sub('', p).strip()
    return p


def load_resolve(path):
    rows = []
    with open(path, 'r', encoding='utf-8', newline='') as fh:
        lines = fh.read().split('\n')
    header = lines[0].rstrip('\r').split('\t')
    for raw in lines[1:]:
        raw = raw.rstrip('\r')
        if not raw.strip():
            continue
        f = raw.split('\t')
        assert len(f) == len(header), (len(f), raw[:120])
        rows.append(dict(zip(header, f)))
    return header, rows


def main():
    header, rows = load_resolve(RESOLVE)
    missing = [r for r in rows if r['class'] == 'R_MISSING']
    print('resolve.tsv total data rows:', len(rows))
    print('R_MISSING row count:', len(missing))
    assert len(missing) == 374, len(missing)

    # index every file under r14 by its posix-style relative path
    file_relpaths = []
    for root, dirs, files in os.walk(R14):
        for fn in files:
            ap = os.path.join(root, fn)
            rel = os.path.relpath(ap, R14).replace('\\', '/')
            file_relpaths.append(rel)
    print('files under r14:', len(file_relpaths))

    def suffix_candidates(relpath):
        """files whose r14-relative path ends with relpath on a component boundary.

        Case-insensitive: EVID_RESOLVE matched EVIDENCE/four_rings.md to
        S13_K12/EVIDENCE/four_rings.md AND S16_PADD/EVIDENCE/FOUR_RINGS.md AND
        S17_PADD/EVIDENCE/FOUR_RINGS.md (report cites this as 3-place ambiguous).
        """
        relpath = relpath.replace('\\', '/').strip('/').lower()
        suffix = '/' + relpath
        hits = [p for p in file_relpaths
                if p.lower() == relpath or p.lower().endswith(suffix)]
        return sorted(hits)

    # distinct recorded relative paths among R_MISSING (after strip anchor, split parts)
    path_to_rows = collections.defaultdict(list)
    row_paths = {}
    for r in missing:
        parts = [p.strip() for p in SPLIT_RE.split(r['evidence_path'].strip()) if p.strip()]
        rels = []
        for p in parts:
            rp = strip_anchor(p)
            if rp:
                rels.append(rp)
        row_paths[r['entry']] = rels
        for rp in rels:
            path_to_rows[rp].append(r['entry'])

    print('distinct recorded relative paths (non-trace):', len(path_to_rows))
    # classify distinct paths
    path_class = {}
    path_hits = {}
    for rp, entries in path_to_rows.items():
        hits = suffix_candidates(rp)
        path_hits[rp] = hits
        if len(hits) == 1:
            path_class[rp] = 'unique'
        elif len(hits) > 1:
            path_class[rp] = 'ambiguous'
        else:
            path_class[rp] = 'lost'
    cnt = collections.Counter(path_class.values())
    print('path-level classes:', dict(cnt))

    # row-level classification: a row is unique if exactly one distinct rel path and it is unique;
    # if any of its rel paths ambiguous -> ambiguous; if any lost -> lost (report says 0 lost)
    row_class = {}
    for r in missing:
        e = r['entry']
        rels = row_paths[e]
        classes = [path_class[rp] for rp in rels] if rels else ['lost']
        if 'lost' in classes:
            row_class[e] = 'lost'
        elif 'ambiguous' in classes:
            row_class[e] = 'ambiguous'
        elif 'unique' in classes:
            row_class[e] = 'unique'
        else:
            row_class[e] = 'lost'
    rcnt = collections.Counter(row_class.values())
    print('row-level classes:', dict(rcnt))

    # dump full detail for review
    detail = []
    for r in missing:
        e = r['entry']
        detail.append({
            'entry': e,
            'subsystem': r['subsystem'],
            'name': r['name'],
            'evidence_path': r['evidence_path'],
            'rel_paths': row_paths[e],
            'row_class': row_class[e],
            'candidates': {rp: path_hits[rp] for rp in row_paths[e]},
        })
    with open(os.path.join(OUTDIR, '_analysis_detail.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'path_class': path_class, 'path_hits': path_hits, 'detail': detail},
                  f, ensure_ascii=False, indent=2)
        f.write('\n')

    # print the 5 ambiguous distinct paths and their hit counts
    print('\n--- AMBIGUOUS distinct paths ---')
    for rp in sorted(rp for rp in path_class if path_class[rp] == 'ambiguous'):
        entries = path_to_rows[rp]
        print('%s : %d hits, %d rows' % (rp, len(path_hits[rp]), len(entries)))
        for h in path_hits[rp]:
            print('    ', h)
    print('\n--- LOST distinct paths ---')
    lost = [rp for rp in path_class if path_class[rp] == 'lost']
    print(lost)
    print('\n--- rows per path count histogram ---')
    print(collections.Counter(len(v) for v in path_to_rows.values()))


if __name__ == '__main__':
    main()
