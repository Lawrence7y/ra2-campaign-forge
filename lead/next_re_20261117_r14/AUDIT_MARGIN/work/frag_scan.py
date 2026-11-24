# -*- coding: utf-8 -*-
"""AUDIT-MARGIN: consolidated fragility scan -> FRAGILE_ROWS.tsv + counts.

F1  placeholder name (Xxx::slotN / Xxx::vslotN) counted into named_S
    (reported separately + the "D-38 rules (B)" scenario)
F2  name given but evidence_path carries docs/re | re_atlas | ledger as a channel (§8.5 主条)
F3  grade [已证] but one_line_semantics self-declares unproven
      F3a = literal tag "[未证]" in the semantics cell (semantic is "据名" = name-derived only)
      F3b = other hedge words 未定 / 弱信号 / 线索 / 待证 / 存疑 / 未审计 / 槽语义未证
F5  grade [已证] but evidence_path points at an unaudited card or a card PROGRESS.md
"""
import sys, os, re, json, collections

sys.stdout.reconfigure(encoding='utf-8')

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
OUT = os.path.join(R14, "AUDIT_MARGIN")
TARGETS = ("S15", "S16", "S17")

RE_SLOT = re.compile(r'::(?:vslot|slot)\d+$', re.I)
F3A_TAG = '[\u672a\u8bc1]'                     # [未证]
F3B_WORDS = ['\u5f85\u5b9a', '\u5f31\u4fe1\u53f7', '\u7ebf\u7d22', '\u5f85\u8bc1',
             '\u5b58\u7591', '\u672a\u5ba1\u8ba1', '\u672a\u5ba1',
             '\u69fd\u8bed\u4e49\u672a\u8bc1', '\u5f85\u6392\u67e5', '\u63a8\u6d4b\u4e0d\u8db3']
F2_TOKENS = ['docs/re', 'docs\\re', 're_atlas', 'ledger', '\u53f0\u8d26']
F5_WORDS = ['\u5f85\u5ba1\u8ba1', '\u5f85\u5ba1', '\u672a\u5ba1\u8ba1', '\u672a\u5ba1']
GRADE_PROVED = '[\u5df2\u8bc1]'


def tsv(path):
    with open(path, 'r', encoding='utf-8', newline='') as f:
        lines = f.read().split('\n')
    if lines and lines[-1] == '':
        lines = lines[:-1]
    h0 = lines[0].rstrip('\r')
    hdr = [h.strip() for h in (h0.split(',') if ',' in h0 and '\t' not in h0 else h0.split('\t'))]
    return hdr, [ln.rstrip('\r').split('\t') for ln in lines[1:]]


def load():
    _, arows = tsv(ATLAS)
    atlas = {r[0].strip().upper() for r in arows if r}
    hdr, crows = tsv(COV)
    i = {h: k for k, h in enumerate(hdr)}
    rows = []
    for r in crows:
        if len(r) <= i['conflict']:
            continue
        rows.append(dict(entry=r[i['entry']].strip().upper(), subsystem=r[i['subsystem']].strip(),
                         name=r[i['name']], sem=r[i['one_line_semantics']],
                         grade=r[i['grade']].strip(), ev=r[i['evidence_path']],
                         nsrc=r[i['n_sources']], conflict=r[i['conflict']],
                         in_atlas=r[i['entry']].strip().upper() in atlas))
    return rows


def named_L(n):
    return bool(n) and not n.startswith('sub_')


def named_S(n):
    return named_L(n) and '::sub_' not in n


def flags(r):
    out = []
    if named_S(r['name']) and RE_SLOT.search(r['name']):
        out.append(('F1', 'name=%s is a vtable-slot placeholder but counts into named_S '
                          '(named_S caliber does not exclude slotN; D-38 undecided)' % r['name']))
    if named_L(r['name']):
        hit = [t for t in F2_TOKENS if t.lower() in r['ev'].lower()]
        if hit:
            out.append(('F2', '\u00a78.5 main rule: name=%s backed by same-project self-note channel %s :: %s'
                        % (r['name'], hit, r['ev'])))
    if r['grade'] == GRADE_PROVED:
        if F3A_TAG in r['sem']:
            out.append(('F3a', '[已证] but semantics cell carries the literal [未证] tag '
                               '(semantic is name-derived only): %s' % r['sem'][:150]))
        elif any(w in r['sem'] for w in F3B_WORDS):
            w = [x for x in F3B_WORDS if x in r['sem']]
            out.append(('F3b', '[已证] but semantics self-declares unproven (%s): %s'
                        % ('/'.join(w), r['sem'][:150])))
        elif '\u5f85\u5ba1' in r['ev'] or 'progress.md' in r['ev'].lower():
            out.append(('F5', 'evidence_path is a card-level claim, not byte evidence: %s' % r['ev']))
    return out


def main():
    rows = load()
    dom = [r for r in rows if r['subsystem'] in TARGETS and r['in_atlas']]
    print('domain rows = %d (S15 %d / S16 %d / S17 %d)' % (
        len(dom), *[sum(1 for r in dom if r['subsystem'] == s) for s in TARGETS]))

    # ---------- per-row flags ----------
    recs = []
    for r in dom:
        for code, why in flags(r):
            recs.append((r, code, why))

    # ---------- per subsystem summary ----------
    print('\n%-4s %5s %8s %7s | %4s %4s %4s %4s %4s | %s' % (
        'sub', 'n', 'named_S', 'proved', 'F1', 'F2', 'F3a', 'F3b', 'F5', 'fragile_rows(distinct)'))
    summ = {}
    for s in TARGETS:
        sub = [r for r in dom if r['subsystem'] == s]
        n = len(sub)
        ns = sum(1 for r in sub if named_S(r['name']))
        pv = sum(1 for r in sub if r['grade'] == GRADE_PROVED)
        c = collections.Counter(code for (r, code, _) in recs if r['subsystem'] == s)
        distinct = len({r['entry'] for (r, code, _) in recs if r['subsystem'] == s})
        summ[s] = dict(n=n, named_S=ns, proved=pv, f1=c['F1'], f2=c['F2'],
                       f3a=c['F3a'], f3b=c['F3b'], f5=c['F5'], fragile_distinct=distinct)
        print('%-4s %5d %8d %7d | %4d %4d %4d %4d %4d | %d' % (
            s, n, ns, pv, c['F1'], c['F2'], c['F3a'], c['F3b'], c['F5'], distinct))

    with open(os.path.join(OUT, 'FRAGILE_ROWS.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('entry\tsubsystem\tflags\tbasis\tname\tgrade\tevidence_path\n')
        for r, code, why in sorted(recs, key=lambda x: (x[0]['subsystem'], x[0]['entry'], x[1])):
            f.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                r['entry'], r['subsystem'], code, why.replace('\t', ' '),
                r['name'], r['grade'], r['ev'].replace('\t', ' ')))
    print('\nFRAGILE_ROWS.tsv rows = %d (row-level flags; multi-flag rows repeat)' % len(recs))

    # ---------- F3 global validation (control) ----------
    allf3a = [r for r in rows if r['grade'] == GRADE_PROVED and F3A_TAG in r['sem']]
    allf3b = [r for r in rows if r['grade'] == GRADE_PROVED and F3A_TAG not in r['sem']
              and any(w in r['sem'] for w in F3B_WORDS)]
    print('\n--- F3 over WHOLE coverage.tsv ---')
    print('F3a (literal [未证] tag) total=%d  by sub=%s' % (
        len(allf3a), dict(collections.Counter(r['subsystem'] for r in allf3a).most_common())))
    print('F3b (other hedge words)  total=%d  by sub=%s' % (
        len(allf3b), dict(collections.Counter(r['subsystem'] for r in allf3b).most_common())))
    # COMMON-R12 §8.7 判据8 claims: exactly 10 rows, all S22
    s22 = sorted(r['entry'] for r in allf3a + allf3b if r['subsystem'] == 'S22')
    print('§8.7 判据8 check: S22 hedge rows=%d ; non-S22 hedge rows=%d' % (
        len(s22), len(allf3a) + len(allf3b) - len(s22)))
    print('COMMON-R12 literal-10 list = %s' % s22)

    # ---------- F1 global ----------
    f1all = [r for r in rows if named_S(r['name']) and RE_SLOT.search(r['name'])]
    print('\nF1 over WHOLE coverage.tsv: total=%d  (top: %s)' % (
        len(f1all), dict(collections.Counter(r['subsystem'] for r in f1all).most_common(6))))

    # ---------- positive controls ----------
    print('\n--- NAMED CONTROLS ---')
    for e in ('004E2690', '0045A640'):
        r = next((x for x in rows if x['entry'] == e), None)
        if not r:
            print('%s NOT FOUND' % e)
            continue
        got = flags(r)
        print('%s sub=%s grade=%s name=%s' % (e, r['subsystem'], r['grade'], r['name']))
        print('   flags: %s' % ([c for c, _ in got] or 'NONE'))
        for c, w in got:
            print('     %s %s' % (c, w[:130]))
        print('   sem: %s' % r['sem'][:160])

    with open(os.path.join(OUT, 'work', 'frag_stats.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(domain=summ, f3a_total=len(allf3a), f3b_total=len(allf3b),
                       s22_hedge=s22), f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
