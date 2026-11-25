#!/usr/bin/env python3
# R131 r131p: WHY is C17 checked=0? Hypothesis: vacuous BY CONSTRUCTION.
# C17 scans only products of rows whose col7 starts with 有 (claims recheck).
# C12 requires every frozen-registry row to be claims-有, and frozen rows are by
# definition rows whose products cannot carry a passing self-description line.
# If claims-有 == C11_FROZEN exactly, C17's input set is exactly the set that by
# definition has no such lines => checked=0 always.
import io, os, re, json
R14 = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
ROOT = '/home/t628/projects/ra2-campaign-forge'
OUT = '/home/t628/projects/ra2-campaign-forge/_r131/r131p_c17vac.json'

rows = [l.split('\t') for l in io.open(os.path.join(R14, 'DISC_RECHECK.tsv'),
        encoding='utf-8', errors='replace').read().split('\n')[1:] if l.strip()]
rows = [r for r in rows if len(r) == 7]
claim_you = [int(r[0]) for r in rows if r[6].strip().startswith('有')]
claim_wu = [int(r[0]) for r in rows if not r[6].strip().startswith('有')]
fz = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
frozen = [int(x.split('\t')[0]) for x in io.open(fz, encoding='utf-8').read().split('\n')[1:]
          if x.strip() and x.split('\t')[0].strip().isdigit()]
R = {'rows': len(rows), 'claim_you': claim_you, 'claim_wu_count': len(claim_wu),
     'frozen': frozen,
     'claim_you_equals_frozen': sorted(claim_you) == sorted(frozen),
     'frozen_minus_claimyou': sorted(set(frozen) - set(claim_you)),
     'claimyou_minus_frozen': sorted(set(claim_you) - set(frozen))}
print('rows', len(rows))
print('claims-有 ids:', claim_you)
print('frozen  ids:', frozen)
print('claims-有 == frozen ?', R['claim_you_equals_frozen'])
print('frozen not claims-有:', R['frozen_minus_claimyou'], ' claims-有 not frozen:', R['claimyou_minus_frozen'])

PATHR = re.compile(r'(?:^|[/\\])R(?:17_)?R?(\d+)_')
LINERE = re.compile(r'^DISC_RECHECK discipline=(\d+) round=(R\d+) at=(\S+) '
                    r'anchors=(sha256:[0-9a-f]{64}) conclusion=(\S+?)\r?$')


def scan(idset, tag):
    checked = 0
    imposs = []
    per = []
    for r in rows:
        if int(r[0]) not in idset:
            continue
        p = r[4].strip().replace('\\', '/')
        ap = os.path.join(ROOT, p)
        if not os.path.isfile(ap):
            per.append({'id': int(r[0]), 'exists': False})
            continue
        txt = io.open(ap, encoding='utf-8', errors='replace').read()
        prs = sorted(set(int(m.group(1)) for m in PATHR.finditer(p)))
        n = 0
        for l in txt.splitlines():
            m = LINERE.match(l)
            if not m or int(m.group(1)) != int(r[0]):
                continue
            n += 1
            checked += 1
            rn = int(m.group(2)[1:])
            at = m.group(3)
            if prs and rn < min(prs):
                imposs.append((int(r[0]), rn, at))
        per.append({'id': int(r[0]), 'exists': True, 'lines': n, 'path_rounds': prs})
    return {'tag': tag, 'checked': checked, 'impossible': imposs, 'per_row': per}


R['claims_you_scan'] = scan(set(claim_you), 'claims-有 (what C17 does today)')
R['table_wide_scan'] = scan(set(int(r[0]) for r in rows), 'ALL rows (proposed widening)')
print('--- C17 today (claims-有 only): checked=%d impossible=%d'
      % (R['claims_you_scan']['checked'], len(R['claims_you_scan']['impossible'])))
print('--- table-wide: checked=%d impossible=%d'
      % (R['table_wide_scan']['checked'], len(R['table_wide_scan']['impossible'])))
print('table-wide impossible rows:', R['table_wide_scan']['impossible'])

# controls
R['P1_widening_sees_lines'] = R['table_wide_scan']['checked'] > 0
tmp = '/home/t628/projects/ra2-campaign-forge/_r131/_probe_c17.txt'
h = open(tmp, 'w')
h.write('DISC_RECHECK discipline=99 round=R1 at=2020-01-01T00:00:00+08:00 '
        'anchors=sha256:' + '0' * 64 + ' conclusion=PASS\n')
h.close()
m = LINERE.match(io.open(tmp).read().splitlines()[0])
R['P2_synthetic_line_parsed'] = bool(m) and m.group(1) == '99'
os.remove(tmp)
R['P2_negctl_mismatched_discipline_not_matched'] = not (
    LINERE.match('DISC_RECHECK discipline=99 round=R1 at=x anchors=sha256:' + '0' * 64
                 + ' conclusion=PASS').group(1) == '98')
R['P3_missing_products'] = [x for x in R['table_wide_scan']['per_row'] if not x.get('exists')]
print('P1', R['P1_widening_sees_lines'], 'P2', R['P2_synthetic_line_parsed'],
      'P2neg', R['P2_negctl_mismatched_discipline_not_matched'],
      'P3 missing', len(R['P3_missing_products']))
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
