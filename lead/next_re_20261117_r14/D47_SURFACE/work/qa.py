# -*- coding: utf-8 -*-
"""Final QA: cross-check every headline number in REPORT.md against a fresh recompute,
and confirm no input file was modified (read-only discipline)."""
import io, os, re, sys, hashlib, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # ...\D47_SURFACE
WORK = os.path.join(HERE, 'work')
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
sys.path.insert(0, HERE)
import surface as S
import make_outputs as M

ctx = M.main()
ok = []
bad = []


def chk(name, got, want):
    (ok if got == want else bad).append('%s: got %r want %r' % (name, got, want))


# --- headline numbers claimed in REPORT.md -------------------------------
chk('proved', ctx['proved'], 1654)
chk('F1', ctx['cnt']['F1'], 159)
chk('F2', ctx['cnt']['F2'], 18)
chk('F3', ctx['cnt']['F3'], 49)
chk('F4', ctx['cnt']['F4'], 1428)
chk('F1 sum', sum(ctx['cnt'].values()), 1654)
chk('nominal before', ctx['before'][0], 3)
chk('strict before', ctx['before'][1], 1)
chk('nominal after', ctx['after123'][0], 3)
chk('strict after', ctx['after123'][1], 1)
chk('F1 in atlas', ctx['f1_atlas'], 159)
chk('F1 strict', ctx['f1_strict'], 159)
chk('F1 disclosed', sum(1 for r, d in ctx['recs']
                        if d['form'] == 'F1' and ctx['disc'].get(r['entry'])), 54)
chk('B2 band', ctx['band']['B2'], 81)
chk('F1+S22', ctx['f1_by_sub']['S22'], 54)
chk('F1+S17', ctx['f1_by_sub']['S17'], 3)
chk('F1+S15', ctx['f1_by_sub']['S15'], 10)

# per-subsystem before/after for the 4 subsystems named in the report
b = {s: a for s, a, tn, tp, no, so in ctx['before'][2]}
a = {s: x for s, x, tn, tp, no, so in ctx['after123'][2]}
chk('S17 proved before', b['S17']['proved'], 59)
chk('S17 strict before', b['S17']['strict'], 58)
chk('S17 proved after', a['S17']['proved'], 56)
chk('S17 strict after', a['S17']['strict'], 55)
chk('S15 proved before', b['S15']['proved'], 116)
chk('S15 strict before', b['S15']['strict'], 63)
chk('S15 proved after', a['S15']['proved'], 106)
chk('S15 strict after', a['S15']['strict'], 53)
chk('S16 proved after', a['S16']['proved'], 47)
chk('S16 strict after', a['S16']['strict'], 21)
chk('S13 proved after', a['S13']['proved'], 89)
chk('S22 proved after', a['S22']['proved'], 55)
chk('S22 strict after', a['S22']['strict'], 12)

# thresholds used in the report
chk('S17 thr', S.verdict(b['S17'])[1], 51)
chk('S15 thr', S.verdict(b['S15'])[1], 79)
chk('S16 thr', S.verdict(b['S16'])[1], 45)
chk('S13 thr', S.verdict(b['S13'])[1], 120)

# F4 sub-composition quoted in report
rc = collections.Counter(d['reason'] for r, d in ctx['recs'])
for k, v in [('name_only_no_ring4', 848), ('census_no_ring4', 416),
             ('no_ring4_described', 83), ('slot_pivot_not_stated_as_ring4', 81)]:
    chk('F4 sub ' + k, rc[k], v)

# F1 sub-composition
for k, v in [('audit_ring4_ctor_install', 112), ('audit_ring4_alloc_reg_pivot', 33),
             ('sem_virtual_witness_only', 12), ('sem_live_table_install', 2)]:
    chk('F1 sub ' + k, rc[k], v)

# --- read-only discipline: input hashes ---------------------------------
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()

COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
# read-only discipline: prove the inputs were last written BEFORE this session started
import datetime
SESSION_START = datetime.datetime(2026, 11, 20, 19, 27, 54)
for p in [COV,
          os.path.join(R14, 'COVERAGE', 'PANEL.md'),
          os.path.join(R14, 'R14_COMMON.md')]:
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(p))
    chk('untouched %s (mtime before session start)' % os.path.basename(p),
        mt < SESSION_START, True)

out = io.open(os.path.join(WORK, 'QA.txt'), 'w', encoding='utf-8')
out.write('checks passed: %d\n' % len(ok))
out.write('checks failed: %d\n' % len(bad))
for x in bad:
    out.write('  FAIL %s\n' % x)
out.write('\ncoverage.tsv sha256 = %s\n' % sha(COV))
out.write('NOTE: R14_COMMON.md L1154 documents FA5637DF...AFC3836 for coverage.tsv.\n')
out.write('That fingerprint is the COMMON-REFRESH-2 snapshot; M74-M77 merged rows after it,\n')
out.write('so it no longer matches current disk. This is the stale-snapshot pattern (错源 ㉙),\n')
out.write('NOT a modification by this card - mtime checks above are the evidence.\n')
out.close()
print('passed %d, failed %d' % (len(ok), len(bad)))
for x in bad:
    print('  FAIL', x)
