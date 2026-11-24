# -*- coding: utf-8 -*-
"""AUDIT-MARGIN F4 exhaustive: byte features for EVERY [已证] row in S15/S16/S17.

Classification used (recorded, not silently applied):
  own-body ③a  := no jump table AND no backward jump AND <=1 direct call AND <=1 cond branch
                   (i.e. linear / single-call / 清零+置默认值 -- exactly D-42 ③a)
  contract-in-body := jump_table OR (backward jump AND a non-stack write) OR (>=2 mutually
                   exclusive branches leading to calls with different targets)
The script only reports features; whether a row's ③b is satisfied is adjudicated in
FRAGILE_ROWS.tsv / PROGRESS.md.
"""
import sys, os, csv, collections

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import disasm_lib as D
import frag_scan as F
import f4_check as F4

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
WORK = os.path.join(R14, "AUDIT_MARGIN", "work")


def main():
    atlas = F4.load_atlas()
    rows = F.load()
    dom = [r for r in rows if r['subsystem'] in F.TARGETS and r['in_atlas']]
    pe = D.PE()
    out = []
    missing = []
    for r in dom:
        if r['grade'] != F.GRADE_PROVED:
            continue
        size = atlas.get(r['entry'])
        if not size:
            missing.append(r['entry'])
            continue
        ins = D.disasm(pe, int(r['entry'], 16), size)
        f = D.features(ins, int(r['entry'], 16), size)
        own_a = (not f['jump_table']) and len(f['back_jumps']) == 0 and \
                len(f['calls']) <= 1 and f['cond_branches'] <= 1
        loop_io = len(f['back_jumps']) > 0 and len(f['nonspace_writes']) > 0
        contract = f['jump_table'] or loop_io
        out.append(dict(entry=r['entry'], subsystem=r['subsystem'], name=r['name'],
                        size=size, n=f['n'], calls=len(f['calls']), ind=len(f['indirect_calls']),
                        cond=f['cond_branches'], back=len(f['back_jumps']), jt=int(f['jump_table']),
                        memw=len(f['mem_writes']), nonspacew=len(f['nonspace_writes']),
                        own_body_3a=int(own_a), contract_in_body=int(contract),
                        sem=r['sem'][:200]))

    cols = ['entry', 'subsystem', 'name', 'size', 'n', 'calls', 'ind', 'cond', 'back',
            'jt', 'memw', 'nonspacew', 'own_body_3a', 'contract_in_body', 'sem']
    p = os.path.join(WORK, 'f4_all_proved.tsv')
    with open(p, 'w', encoding='utf-8', newline='') as g:
        g.write('\t'.join(cols) + '\n')
        for x in out:
            g.write('\t'.join(str(x[k]).replace('\t', ' ') for k in cols) + '\n')

    print('proved rows measured = %d ; atlas-size missing = %s' % (len(out), missing or 'none'))
    print('\n%-4s %7s %10s %12s %10s' % ('sub', 'proved', 'own_body_3a', 'contract_body', 'jump_table'))
    for s in F.TARGETS:
        sub = [x for x in out if x['subsystem'] == s]
        print('%-4s %7d %10d %12d %10d' % (
            s, len(sub), sum(x['own_body_3a'] for x in sub),
            sum(x['contract_in_body'] for x in sub), sum(x['jt'] for x in sub)))

    print('\n--- rows whose OWN body is ③a (linear/single-call/清零+ret) ---')
    for x in sorted([x for x in out if x['own_body_3a']], key=lambda y: (y['subsystem'], y['entry'])):
        print('  %s %s %-42s n=%-4d calls=%d ind=%d cond=%d back=%d | %s'
              % (x['subsystem'], x['entry'], x['name'][:42], x['n'], x['calls'],
                 x['ind'], x['cond'], x['back'], x['sem'][:70]))

    print('\n--- rows whose own body DOES contain a contract form (jump table or loop+write) ---')
    for x in sorted([x for x in out if x['contract_in_body']], key=lambda y: (y['subsystem'], y['entry'])):
        print('  %s %s %-42s n=%-4d jt=%d back=%d nonspacew=%d'
              % (x['subsystem'], x['entry'], x['name'][:42], x['n'], x['jt'], x['back'], x['nonspacew']))

    # claim vs body cross-check
    import re
    LOOP = re.compile('\u904d\u5386|\u5faa\u73af|\u9010')
    JT = re.compile('\u8df3\u8868|switch')
    print('\n--- claim/body cross-check (semantics claim vs measured body) ---')
    bad_loop = [x for x in out if LOOP.search(x['sem']) and x['back'] == 0]
    bad_jt = [x for x in out if JT.search(x['sem']) and not x['jt'] and x['own_body_3a']]
    for x in bad_loop:
        print('  LOOP-CLAIM-NO-LOOP  %s %s %-38s back=0 | %s' % (x['subsystem'], x['entry'], x['name'][:38], x['sem'][:60]))
    for x in bad_jt:
        print('  JT-CLAIM-NO-JT      %s %s %-38s jt=0 own3a=1 | %s' % (x['subsystem'], x['entry'], x['name'][:38], x['sem'][:60]))
    print('  loop-claim-but-no-loop = %d ; jumptable-claim-but-thin-body = %d' % (len(bad_loop), len(bad_jt)))


if __name__ == '__main__':
    main()
