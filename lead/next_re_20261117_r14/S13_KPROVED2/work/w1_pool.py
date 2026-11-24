"""Build S13 candidate pool with exact exclusions, recompute proved counts.
Card S13-KPROVED2.
"""
import json, csv, re, os
from s13lib import u32

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = BASE + r"\COVERAGE\coverage.tsv"
CLS = BASE + r"\SURVEY_RING24\EVIDENCE\classification.tsv"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_KPROVED2"

# --- load coverage ---
rows = {}
with open(COV, encoding='utf-8') as f:
    f.readline()
    for line in f:
        p = line.rstrip('\n').split('\t')
        if len(p) >= 8:
            rows[p[0]] = dict(entry=p[0], subsystem=p[1], name=p[2], semantics=p[3],
                              grade=p[4], evidence=p[5], n_sources=p[6], conflict=p[7])

s13 = [r for r in rows.values() if r['subsystem'] == 'S13']
assert len(s13) == 240, len(s13)

# --- 240 caliber ---
from collections import Counter
g240 = Counter(r['grade'] for r in s13)
proved240 = g240['[已证]']

# --- 148 caliber (exclude 92 container-template rows) ---
def is_container_template(name):
    # D-37: 92 rows are container template instantiations; names carry VectorClass / ?$ prefix / vslot
    return ('VectorClass' in name) or ('?$' in name) or name.startswith('?')

cont = [r for r in s13 if is_container_template(r['name'])]
noncont = [r for r in s13 if not is_container_template(r['name'])]
assert len(cont) == 92, len(cont)
assert len(noncont) == 148, len(noncont)
g148 = Counter(r['grade'] for r in noncont)
proved148 = g148['[已证]']

# --- static-inference pool (126) ---
static = [r for r in s13 if r['grade'] == '[静态推断]']
assert len(static) == 126, len(static)

# --- exclusion sets ---
# 3 M26 whitelist (already 已证, not in static pool) -- verify
m26 = {'0040F870', '0054E890', '0054EA70'}
# S13_K8 18 dtor rows (D-39 pending) -- from S13_K8 delta
k8_18 = {'0040BBC0','0040BC10','0040F8A0','0040F8F0','0040FE70','0040FEC0',
         '0046B8C0','0046B910','0048AFD0','0048B020','0054EB50','0054EBA0',
         '0062B330','0062B380','0065BED0','0065C1B0','0065C200','0075E510'}
# S13_K9 11 rows (already 已证, not in static pool)
k9_11 = {'0040B880','0040B930','0040F7C0','0040FD90','0040FE40',
         '0046B7E0','0046B890','0062B250','0062B300','0065C0D0','0065C180'}

# survey flags
survey = {}
with open(CLS, encoding='utf-8') as f:
    rd = csv.DictReader(f, delimiter='\t')
    for r in rd:
        survey[r['entry']] = r

# container slot1-6 rows: names indicating VectorClass/DynamicVectorClass slots 1..6,
# per §8.4 mapping (slot1=operator==,2=SetCapacity,3=Clear,4=FindItemIndex,5=GetItemIndex,6=GetItem)
# name patterns: vslot1..vslot6, T_VectorClass...::slotN / T_DynamicVectorClass...::slotN,
# and explicit VectorClass<..>::GetItem/operator== etc.
def container_slot16(name):
    # business-class slots (BombClass::slot13 etc.) are NOT container family
    if re.search(r'(VectorClass|DynamicVectorClass)', name, re.I):
        m = re.search(r'(?:v?slot)(\d+)', name)
        if m and 1 <= int(m.group(1)) <= 6:
            return True
        if re.search(r'::(GetItem|GetItemIndex|FindItemIndex|operator==|SetCapacity|Clear)(?:$|[^A-Za-z0-9_])', name):
            return True
    # ?$DynamicVectorClass::...vslotN / ?$VectorClass::...vslotN
    m = re.search(r'^\?\$(Dynamic)?VectorClass.*vslot(\d+)', name)
    if m and 1 <= int(m.group(2)) <= 6:
        return True
    return False

excluded_k8 = static and [r for r in static if r['entry'] in k8_18]
excluded_cont = [r for r in static if container_slot16(r['name']) and r['entry'] not in k8_18]

candidate = [r for r in static
             if r['entry'] not in k8_18
             and not container_slot16(r['name'])]

# attach survey flags
for r in candidate:
    s = survey.get(r['entry'], {})
    r['has2_rtti'] = s.get('has2_rtti', '?')
    r['has2_yrpp'] = s.get('has2_yrpp', '?')
    r['has4_strict'] = s.get('has4_strict', '?')
    r['has4_loose'] = s.get('has4_loose', '?')
    r['n_direct_all'] = s.get('n_direct_all', '?')
    r['n_direct_out'] = s.get('n_direct_out', '?')
    r['rtti_classes'] = s.get('rtti_classes', '')
    r['rtti_vt'] = s.get('rtti_vt', '')
    r['rtti_slot'] = s.get('rtti_slot', '')
    r['ext_lo'] = s.get('ext_lo', '')
    r['ext_hi'] = s.get('ext_hi', '')
    r['atlas_size'] = s.get('atlas_size', '')

print('S13 rows =', len(s13))
print('240 caliber: proved=%d/%d = %.4f%%' % (proved240, 240, 100*proved240/240))
print('container-template rows =', len(cont), ' non-container =', len(noncont))
print('148 caliber: proved=%d/%d = %.4f%%' % (proved148, 148, 100*proved148/148))
print('static pool =', len(static))
print('excluded K8 dtors =', len(excluded_k8))
print('excluded container slot1-6 (non-K8) =', len(excluded_cont))
print('CANDIDATE POOL =', len(candidate))
print('  m26 in static?', [e for e in m26 if e in {r['entry'] for r in static}])
print('  k9 in static?', [e for e in k9_11 if e in {r['entry'] for r in static}])
cc = Counter(r['has4_strict'] for r in candidate)
print('  candidate has4_strict dist:', dict(cc))
print('  candidate has4_loose dist:', dict(Counter(r['has4_loose'] for r in candidate)))
print('  candidate has2_rtti dist:', dict(Counter(r['has2_rtti'] for r in candidate)))
print('  candidate n_direct_all>0:', [r['entry'] for r in candidate if r['n_direct_all'].isdigit() and int(r['n_direct_all'])>0])

os.makedirs(OUT, exist_ok=True)
json.dump({
    's13_n': len(s13),
    'caliber240': dict(proved=proved240, denom=240, pct=100*proved240/240, grades=dict(g240)),
    'container_rows': len(cont), 'noncontainer_rows': len(noncont),
    'caliber148': dict(proved=proved148, denom=148, pct=100*proved148/148, grades=dict(g148)),
    'static_pool': len(static),
    'excluded_k8_dtors': sorted(k8_18),
    'excluded_container_slot16': sorted(r['entry'] for r in excluded_cont),
    'candidate_pool': len(candidate),
    'candidates': candidate,
}, open(OUT + r'\work\pool.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print('wrote work/pool.json')
