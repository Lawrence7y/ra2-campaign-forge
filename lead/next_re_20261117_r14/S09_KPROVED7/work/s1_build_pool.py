"""S09-KPROVED7 step 1: build candidate pool from S09 A set minus exclusions,
then full-RTTI-table enumeration + CFG extent + direct/livevt sites for each.
Self-implemented via s09lib (no atlas entry+size dependency for extent)."""
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED7\work')
import s09lib as L

BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT = BASE + r'\S09_KPROVED7\work'

# --- A set (S09, has2_rtti & has4_strict) ---
rows = list(csv.DictReader(open(BASE + r'\SURVEY_RING24\EVIDENCE\classification.tsv', encoding='utf-8'), delimiter='\t'))
A = [r for r in rows if r['subsystem'] == 'S09' and r['has2_rtti'] == '1' and r['has4_strict'] == '1']
assert len(A) == 103, len(A)

# --- exclusion set ---
excl = set()
for d in ['S09_KPROVED','S09_KPROVED2','S09_KPROVED3','S09_KPROVED4','S09_KPROVED5','S09_KPROVED6']:
    for line in open(BASE + '\\' + d + r'\coverage_delta.tsv', encoding='utf-8'):
        e = line.split('\t')[0].strip()
        if e and e != 'entry': excl.add(e)
for d in ['SEMFIX_SLOTS2','SEMFIX_SLOTS3']:
    for line in open(BASE + '\\' + d + r'\coverage_delta.tsv', encoding='utf-8'):
        p = line.split('\t')
        if len(p) >= 2 and p[1].strip() == 'S09': excl.add(p[0].strip())
excl |= {'00654320','0069DEB0'}

remain = [r for r in A if r['entry'] not in excl]
print('A=', len(A), 'excl=', len(excl), 'remain=', len(remain))

# --- full RTTI enumeration ---
tables = L.rtti_tables(max_slots=1024)
print('RTTI valid tables:', len(tables), 'total slots:', sum(len(t['slots']) for t in tables))

# --- full E8 sweep (once) ---
insns, calls = L.full_e8_sweep()
print('E8 sweep insns:', len(insns), 'E8@boundary calls:', len(calls))

# --- per candidate ---
out = []
for r in remain:
    e = int(r['entry'], 16)
    holds = L.tables_holding(tables, e)  # list of (table, slot_index)
    holds_info = sorted([(hex(t['vt']), i, t['name'], hex(t['col']), hex(t['td'])) for t, i in holds],
                        key=lambda x: (x[0], x[1]))
    lo, hi, ordered, byaddr = L.cfg_extent(e, cap=8000)
    lo2, hi2, sites = L.direct_sites_for(e, calls)
    good_sites = [s for s in sites if s['ok']]
    rec = dict(entry=r['entry'], name=r['name'],
               rtti_classes_survey=r['rtti_classes'], survey_vt=r['rtti_vt'], survey_slot=r['rtti_slot'],
               n_direct_out_survey=r['n_direct_out'], livevt_survey=r['livevt_valid'],
               holds=holds_info, n_holds=len(holds_info),
               extent=[hex(lo), hex(hi)], nins=len(ordered),
               direct_sites=[hex(s['site']) for s in good_sites], n_direct=len(good_sites),
               dir_rel=[(hex(s['site']), s['rel']) for s in good_sites][:20])
    out.append(rec)

json.dump(out, open(OUT + r'\pool.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote pool.json:', len(out), 'rows')
# distribution of n_holds
from collections import Counter
print('n_holds dist:', dict(Counter(rec['n_holds'] for rec in out)))
print('n_direct=0:', sum(1 for rec in out if rec['n_direct'] == 0))
