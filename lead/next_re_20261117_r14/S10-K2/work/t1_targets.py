"""
S10-K2 T1: analyze S10 rows in coverage.tsv, count named (L/S) and proved,
build TARGETS.tsv = S10 rows ∩ function_atlas, with per-row 'what is missing' + plan.
Byte-level input files are read-only. Output only into S10-K2/.
"""
import csv, os, re, collections

ROOT = r'D:\Project\ra2-campaign-forge'
COV  = os.path.join(ROOT, r'lead\next_re_20261117_r14\COVERAGE\coverage.tsv')
ATL  = os.path.join(ROOT, r'lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv')
OUTD = os.path.join(ROOT, r'lead\next_re_20261117_r14\S10-K2')
TARGETS = os.path.join(OUTD, 'TARGETS.tsv')
EVID = os.path.join(OUTD, 'EVIDENCE', 't1_targets_report.txt')

def load_tsv(p):
    with open(p, 'r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))

cov = load_tsv(COV)
atl = load_tsv(ATL)
atlas_entries = {r['entry'].upper() for r in atl}

s10 = [r for r in cov if r.get('subsystem') == 'S10']
L = []
def P(s=''):
    L.append(str(s)); print(s)

P('===== T1 S10 inventory =====')
P('coverage total data rows = %d' % len(cov))
P('atlas total data rows   = %d' % len(atl))
P('S10 coverage rows       = %d' % len(s10))
s10_atlas = [r for r in s10 if r['entry'].upper() in atlas_entries]
s10_out   = [r for r in s10 if r['entry'].upper() not in atlas_entries]
P('S10 rows in atlas       = %d' % len(s10_atlas))
P('S10 rows NOT in atlas   = %d : %s' % (len(s10_out), ', '.join(r['entry'] for r in s10_out)))

# grade distribution
gdist = collections.Counter(r['grade'] for r in s10)
P('\nS10 grade distribution (all %d rows):' % len(s10))
for g,n in sorted(gdist.items()): P('  %-14s %d' % (g,n))
gdist_a = collections.Counter(r['grade'] for r in s10_atlas)
P('S10 grade distribution (atlas-only %d rows):' % len(s10_atlas))
for g,n in sorted(gdist_a.items()): P('  %-14s %d' % (g,n))

# named counts: L = name非空且不以sub_开头; S = L 且 非 Class::sub_
def is_named_L(name):
    n = (name or '').strip()
    return bool(n) and not n.startswith('sub_')
def is_class_sub(name):
    n=(name or '').strip()
    return bool(re.match(r'^[A-Za-z_][A-Za-z0-9_]*::sub_[0-9A-Fa-f]{8}$', n)) or '::sub_' in n

named_L = [r for r in s10 if is_named_L(r['name'])]
named_S = [r for r in s10 if is_named_L(r['name']) and not is_class_sub(r['name'])]
class_sub = [r for r in s10 if is_class_sub(r['name'])]
plain_sub = [r for r in s10 if (r['name'] or '').strip().startswith('sub_')]
P('\nS10 named口径 (all %d rows):' % len(s10))
P('  named L (name非空且非sub_)      = %d  (%.2f%%)' % (len(named_L), 100.0*len(named_L)/len(s10)))
P('  Class::sub_ placeholder rows    = %d' % len(class_sub))
P('  named S (L minus Class::sub_)   = %d  (%.2f%%)' % (len(named_S), 100.0*len(named_S)/len(s10)))
P('  plain sub_ rows                 = %d' % len(plain_sub))
# same for atlas denom 513
P('\nS10 named口径 (atlas %d rows):' % len(s10_atlas))
nLa=[r for r in s10_atlas if is_named_L(r['name'])]
nSa=[r for r in s10_atlas if is_named_L(r['name']) and not is_class_sub(r['name'])]
P('  named L = %d (%.2f%%); named S = %d (%.2f%%)' % (len(nLa),100.0*len(nLa)/len(s10_atlas),len(nSa),100.0*len(nSa)/len(s10_atlas)))

# proved counts
prov = [r for r in s10 if r['grade'] == '[已证]']
prov_a = [r for r in s10_atlas if r['grade'] == '[已证]']
P('\nS10 proved ([已证]):')
P('  all rows    : %d / %d = %.2f%%' % (len(prov),len(s10),100.0*len(prov)/len(s10)))
P('  atlas rows  : %d / %d = %.2f%%' % (len(prov_a),len(s10_atlas),100.0*len(prov_a)/len(s10_atlas)))
P('  50%% gate (atlas 513): need %d proved; card-claim 28 gap=%d; disk-atlas %d gap=%d; disk-all %d gap=%d' %
  (257, 257-28, len(prov_a), 257-len(prov_a), len(prov), 258-len(prov)))
P('  Note: card face claims proved=28 (5.46%%); PANEL.md reports 55 (10.72%%); disk self-count above is authoritative.')

P('\nAll NON-named S10 rows (name patterns) in atlas:')
for r in s10_atlas:
    if not is_named_L(r['name']):
        P('  %s  name=%-24s grade=%s' % (r['entry'], r['name'], r['grade']))

P('\nClass::sub_ rows (first 40):')
for r in class_sub[:40]: P('  %s  %s  %s' % (r['entry'], r['name'], r['grade']))
if len(class_sub)>40: P('  ... (%d more)' % (len(class_sub)-40))

# ---- build TARGETS.tsv ----
# For each S10 atlas row, classify what's missing and give a forensic plan.
def what_missing(r):
    grade=r['grade']; name=(r['name'] or '').strip()
    miss=[]
    if grade != '[已证]': miss.append('grade非已证(%s)'%grade)
    if not is_named_L(name): miss.append('name占位(%s)'%name)
    elif is_class_sub(name): miss.append('Class::sub_占位')
    if not miss: miss.append('证据链完整性待核')
    return ';'.join(miss)
def plan(r):
    grade=r['grade']; name=(r['name'] or '').strip()
    if 'Mission' in name or re.match(r'Mission_', name):
        return 'T2虚槽语义: .rdata定界+RTTI对齐父类+调用点上下文'
    if grade=='[已证]':
        return '复核双通道;优先GetSize双点闭合(T3)/字段增量(T4)'
    if is_class_sub(name) or not is_named_L(name):
        return 'RTTI TD定名(COL+0xC→TD+8,fail-closed);再补调用点语义'
    return 'capstone skipdata全.text扫xref;双重支撑升级grade'

rows=[]
for r in s10_atlas:
    rows.append([r['entry'], r['name'], r['grade'], what_missing(r), plan(r)])
# TARGETS.tsv = STRICT intersection (coverage S10 ∩ function_atlas) = 513 rows.
# The 2 non-atlas S10 rows are documented in the report only, not in TARGETS.tsv.
with open(TARGETS,'w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n')
    w.writerow(['entry','name','grade','missing','plan'])
    w.writerows(rows[:len(s10_atlas)])
P('\nTARGETS.tsv written: %d data rows (strict S10∩atlas) -> %s' % (len(s10_atlas), TARGETS))
P('(2 non-atlas S10 rows %s documented above, excluded from TARGETS)' % ', '.join(r['entry'] for r in s10_out))

with open(EVID,'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE', EVID)
