#!/usr/bin/env python3
"""S15-K4 T0: live recompute of S15 named(S)/proved baseline from disk."""
import csv, math, pathlib, hashlib, re, json
ROOT = pathlib.Path(r'D:\Project\ra2-campaign-forge')
COV = ROOT / 'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATLAS = ROOT / 'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
EXE = ROOT / 'ra2youli/gamemd.exe'
OUT = pathlib.Path(__file__).resolve().parents[1] / 'EVIDENCE'
OUT.mkdir(exist_ok=True)
def rows(p):
    with p.open('r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))
def is_unnamed(name: str) -> bool:
    n = (name or '').strip()
    return (not n) or n.lower().startswith('sub_') or bool(re.search(r'::sub_[0-9a-fA-F]{8}$', n))
def main():
    cov = rows(COV)
    atlas = rows(ATLAS)
    at = {r['entry'].strip().lower() for r in atlas}
    s15 = [r for r in cov if r.get('subsystem','').strip() == 'S15']
    inter = [r for r in s15 if r['entry'].strip().lower() in at]
    outside = [r for r in s15 if r['entry'].strip().lower() not in at]
    named = [r for r in inter if not is_unnamed(r.get('name',''))]
    proved = [r for r in inter if r.get('grade','').strip() == '[已证]']
    unnamed = [r for r in inter if is_unnamed(r.get('name',''))]
    sha = hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
    need = math.ceil(0.9 * len(inter))
    lines = []
    add = lines.append
    add('S15-K4 T0 baseline (live disk recompute; no card claims used)')
    add('gamemd.exe bytes=%d sha256=%s' % (EXE.stat().st_size, sha))
    add('coverage.tsv data rows=%d; function_atlas.tsv data rows=%d' % (len(cov), len(atlas)))
    add('coverage rows subsystem=S15=%d; atlas entries=%d; intersection denominator=%d' % (len(s15), len(at), len(inter)))
    add('named(S) baseline=%d/%d (%.2f%%); DoD 90%% target=%d; shortfall=%d' % (len(named), len(inter), 100*len(named)/len(inter), need, need-len(named)))
    add('proved [已证] baseline=%d/%d (%.2f%%)' % (len(proved), len(inter), 100*len(proved)/len(inter)))
    add('intersection grade counts=' + json.dumps({g:sum(1 for r in inter if r['grade']==g) for g in sorted({r['grade'] for r in inter})}, sort_keys=True))
    add('S15 rows outside atlas (%d):' % len(outside))
    for r in outside: add('\t'.join([r['entry'], r['name'], r['grade']]))
    add('currently unnamed in intersection (%d):' % len(unnamed))
    for r in unnamed: add('\t'.join([r['entry'], r['name'], r['grade'], r['one_line_semantics'], r['evidence_path']]))
    add('all intersection rows (full dump, no truncation):')
    for r in sorted(inter, key=lambda x:x['entry'].lower()): add('\t'.join([r[k] for k in ['entry','name','grade','one_line_semantics','evidence_path']]))
    (OUT/'t0_baseline.txt').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('\n'.join(lines[:11]))
    print('WROTE', OUT/'t0_baseline.txt')
if __name__ == '__main__': main()
