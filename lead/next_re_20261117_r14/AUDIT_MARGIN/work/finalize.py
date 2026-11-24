# -*- coding: utf-8 -*-
"""AUDIT-MARGIN final consolidation -> FRAGILE_ROWS.tsv + printed summary.

Severity model (deliberately two-tier, so the Lead can re-weight without re-running):
  HARD      = the row contradicts an ALREADY-STANDING written rule
              F2  -> COMMON §8.5 main rule (docs/re, re_atlas, ledger may not be a name channel)
              F3a -> COMMON §8.7 判据 8 / §8.6 条 1 ([已证] may not coexist with a semantics
                     cell that self-declares 未证)
              F3b -> same rule, the 10-row S22 hedge wording (canonical instance)
              F5  -> evidence_path carries a card-level claim instead of byte evidence
  BORROWED  = ③b is not in the row's own body; it lives in the dispatcher / callee,
              so the row stands or falls on a D-42 ruling (NOTHING is downgraded here)
              F4a -> "<Name>: TActionClass::Execute 动作ID N … 实现体; 跳表薄壳唯一call直指"
              F4b -> claims 遍历/完整循环 but the loop has no in-body non-stack write
  SEPARATE  = F1, the D-38 scenario only (Xxx::slotN counted into named_S). Reported
              beside the others, never added into the fragile totals.
"""
import sys, os, re, json, collections, math

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import frag_scan as F

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT = os.path.join(R14, "AUDIT_MARGIN")
WORK = os.path.join(OUT, 'work')

SHELL = re.compile('\u5b9e\u73b0\u4f53; ?\u8df3\u8868\u8584\u58f3\u552f\u4e00call\u76f4\u6307')
LOOP_CLAIM = re.compile('\u904d\u5386|\u5faa\u73af')


def main():
    rows = F.load()
    dom = [r for r in rows if r['subsystem'] in F.TARGETS and r['in_atlas']]

    # ③b-in-body facts, when available
    body = {}
    p = os.path.join(WORK, 'f4_all_proved.tsv')
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            hdr = f.readline().rstrip('\n').split('\t')
            for ln in f:
                v = ln.rstrip('\n').split('\t')
                if len(v) == len(hdr):
                    body[v[0]] = dict(zip(hdr, v))

    recs = []
    for r in dom:
        e = r['entry']
        # --- HARD
        if F.named_L(r['name']):
            hit = [t for t in F.F2_TOKENS if t.lower() in r['ev'].lower()]
            if hit:
                recs.append((r, 'F2', 'HARD',
                             'name=%s; evidence_path uses the forbidden same-project channel %s '
                             '(§8.5 main rule); first channel is an inference from the forward target, '
                             'not a YRpp CALL(0x..) line :: %s' % (r['name'], hit, r['ev'])))
        if r['grade'] == F.GRADE_PROVED:
            if F.F3A_TAG in r['sem']:
                recs.append((r, 'F3a', 'HARD',
                             'grade=[已证] but the semantics cell ends in the literal [未证] tag '
                             '(name proven, semantics name-derived) :: %s' % r['sem'][:120]))
            elif any(w in r['sem'] for w in F.F3B_WORDS):
                w = [x for x in F.F3B_WORDS if x in r['sem']]
                recs.append((r, 'F3b', 'HARD',
                             'grade=[已证] but semantics self-declares unproven (%s) :: %s'
                             % ('/'.join(w), r['sem'][:120])))
            if ('\u5f85\u5ba1' in r['ev']) or ('progress.md' in r['ev'].lower()):
                recs.append((r, 'F5', 'HARD', 'evidence_path is a card-level claim: %s' % r['ev']))
        # --- BORROWED (③b outside own body)
        if r['grade'] == F.GRADE_PROVED and SHELL.search(r['sem']):
            b = body.get(e, {})
            own = ('own body has NO contract form (instr=%s calls=%s cond=%s back=%s jt=%s)'
                   % (b.get('n', '?'), b.get('calls', '?'), b.get('cond', '?'),
                      b.get('back', '?'), b.get('jt', '?')))
            if b.get('contract_in_body') == '1':
                own = ('own body DOES carry a contract form (back=%s nonspacew=%s) - weakest hit'
                       % (b.get('back'), b.get('nonspacew')))
            recs.append((r, 'F4a', 'BORROWED',
                         '③b is borrowed from TActionClass::Execute 145-way jump table, not in own body; '
                         + own + ' :: ' + r['sem'][:110]))
        elif r['grade'] == F.GRADE_PROVED and LOOP_CLAIM.search(r['sem']):
            b = body.get(e, {})
            if b.get('nonspacew') == '0':
                recs.append((r, 'F4b', 'BORROWED',
                             'claims 遍历/完整循环 but loop advances a register only and has no in-body '
                             'non-stack write (write delegated to the callee); same shape as the card '
                             'control 0045A640 :: ' + r['sem'][:110]))
        # --- SEPARATE: F1
        if F.named_S(r['name']) and F.RE_SLOT.search(r['name']):
            recs.append((r, 'F1', 'SEPARATE',
                         'name=%s is a vtable-slot placeholder counted into named_S; only bites if '
                         'D-38 rules (B) :: %s' % (r['name'], r['sem'][:80])))

    with open(os.path.join(OUT, 'FRAGILE_ROWS.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('entry\tsubsystem\tflag\tseverity\tbasis\tname\tgrade\tevidence_path\n')
        for r, flag, sev, why in sorted(recs, key=lambda x: (x[0]['subsystem'], x[0]['entry'], x[1])):
            f.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                r['entry'], r['subsystem'], flag, sev, why.replace('\t', ' '),
                r['name'], r['grade'], r['ev'].replace('\t', ' ')))

    # ---------- summary ----------
    print('FRAGILE_ROWS.tsv: %d flag rows' % len(recs))
    print('\n%-4s %5s %7s %7s %7s %7s %7s | %7s %7s %9s %9s' % (
        'sub', 'n', 'named', 'proved', 'thr_n', 'thr_p', 'F1', 'HARD', 'HARD+F4', 'can_absorb_n', 'can_absorb_p'))
    summ = {}
    for s in F.TARGETS:
        sub = [r for r in dom if r['subsystem'] == s]
        n = len(sub)
        ns = sum(1 for r in sub if F.named_S(r['name']))
        pv = sum(1 for r in sub if r['grade'] == F.GRADE_PROVED)
        tn, tp = math.ceil(0.9 * n - 1e-9), math.ceil(0.5 * n - 1e-9)
        by = collections.defaultdict(set)
        for r, flag, sev, _ in recs:
            if r['subsystem'] == s:
                by[flag].add(r['entry'])
                by[sev].add(r['entry'])
        hard = len(by['HARD'])
        hard_f4 = len(by['HARD'] | by['BORROWED'])
        summ[s] = dict(n=n, named_S=ns, proved=pv, thr_named=tn, thr_proved=tp,
                       margin_named=ns - tn, margin_proved=pv - tp,
                       F1=len(by['F1']), F2=len(by['F2']), F3a=len(by['F3a']), F3b=len(by['F3b']),
                       F4a=len(by['F4a']), F4b=len(by['F4b']), F5=len(by['F5']),
                       HARD=hard, HARD_plus_BORROWED=hard_f4)
        print('%-4s %5d %7d %7d %7d %7d %7d | %7d %7d %9d %9d' % (
            s, n, ns, pv, tn, tp, len(by['F1']), hard, hard_f4, ns - tn, pv - tp))

    tot_hard = sum(v['HARD'] for v in summ.values())
    print('\ntotal rows in domain = %d ; HARD fragile = %d ; HARD+BORROWED = %d ; F1 (separate) = %d'
          % (len(dom), tot_hard, sum(v['HARD_plus_BORROWED'] for v in summ.values()),
             sum(v['F1'] for v in summ.values())))

    # scenario table
    print('\n--- margin scenarios ---')
    for s in F.TARGETS:
        d = summ[s]
        print('%s: named now %d(%+d)' % (s, d['named_S'], d['margin_named']))
        print('    after F2 (standing)      %d  %s' % (d['named_S'] - d['F2'],
              'PASS' if d['named_S'] - d['F2'] >= d['thr_named'] else 'FAIL (needs %d)' % d['thr_named']))
        print('    after F1+F2 (D-38 (B))   %d  %s' % (d['named_S'] - d['F2'] - d['F1'],
              'PASS' if d['named_S'] - d['F2'] - d['F1'] >= d['thr_named'] else 'FAIL (needs %d)' % d['thr_named']))
        print('    proved now %d(%+d)' % (d['proved'], d['margin_proved']))
        print('    after F3 (standing)      %d  %s' % (d['proved'] - d['F3a'] - d['F3b'],
              'PASS' if d['proved'] - d['F3a'] - d['F3b'] >= d['thr_proved'] else 'FAIL (needs %d)' % d['thr_proved']))
        print('    after F3+F4 (D-42)       %d  %s' % (
              d['proved'] - d['F3a'] - d['F3b'] - d['F4a'] - d['F4b'],
              'PASS' if d['proved'] - d['F3a'] - d['F3b'] - d['F4a'] - d['F4b'] >= d['thr_proved']
              else 'FAIL (needs %d)' % d['thr_proved']))

    with open(os.path.join(WORK, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summ, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
