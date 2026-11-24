"""Final self-check: delta integrity, M2/M5/M6/M8, ring evidence, write-domain.
Card S05-KPROVED3."""
import sys, os, json, csv, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work")
BASE=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
DELTA=BASE+r"\S05_KPROVED3\coverage_delta.tsv"
EVID=BASE+r"\S05_KPROVED3\EVIDENCE"
CLS=BASE+r"\SURVEY_RING24\EVIDENCE\classification.tsv"
MERGED={'00413F80','006F4AB0','006F6AC0','0070C270','007077C0','00716DC0','007162F0','00700600'}
BAD=['未证','未定','弱信号','线索']

rows=list(csv.DictReader(open(DELTA,encoding='utf-8'),delimiter='\t'))
print("delta rows:",len(rows)); assert len(rows)==8
# A set + exclusion check
cls={r['entry']:r for r in csv.DictReader(open(CLS,encoding='utf-8'),delimiter='\t')}
for r in rows:
    e=r['entry']
    assert e in cls and cls[e]['subsystem']=='S05' and cls[e]['has2_rtti']=='1' and cls[e]['has4_strict']=='1', f"not in A set {e}"
    assert e not in MERGED, f"already merged {e}"
print("all 8 rows in A set (41) and not in merged-8: OK")

for r in rows:
    e=r['entry']; sem=r['one_line_semantics']
    # M8 no self-undeclared words in semantics
    for b in BAD: assert b not in sem, f"badword {b} in {e}"
    # M2 class name in name appears in TD+8 string
    clsname=r['name'].split('::')[0]
    assert '.?AV'+clsname+'@@' in sem, f"class {clsname} not in ② field {e}"
    # grade
    assert r['grade']=='[已证]'
    # M5 offset consistency: every +0xNNNN in delta appears in EVIDENCE ROW file
    ev=open(os.path.join(EVID,f"ROW_{e}.txt"),encoding='utf-8').read()
    offs=set(re.findall(r'\+0x[0-9A-Fa-f]{4}',sem))
    miss=[o for o in offs if o not in ev]
    assert not miss, f"offset mismatch {e}: {miss}"
    # evidence file exists per evidence_path
    for ep in r['evidence_path'].split(';'):
        assert os.path.exists(os.path.join(BASE,r"S05_KPROVED3",ep)), f"missing {ep}"
print("M2/M5/M6/M8 + evidence paths: OK")

# ROW_SUMMARY consistency
RS=json.load(open(os.path.join(EVID,'ROW_SUMMARY.json'),encoding='utf-8'))
assert len(RS)==8
for r in rows:
    s=next(z for z in RS if z['entry']==r['entry'])
    assert s['n_dir_valid']>=1, f"no valid site {r['entry']}"
    assert s['n_holders']>=1
print("ROW_SUMMARY: 8 rows, all have >=1 valid site and >=1 holder: OK")

# baselines present
b=json.load(open(os.path.join(EVID,'baselines.json'),encoding='utf-8'))
assert 'strict' in b and 'loose' in b and b['strict']['N']==387
print("baselines strict/loose present, N=387: OK")

# write-domain: ensure no forbidden files changed (just list what we created)
print("\nDeliverables in S05_KPROVED3:")
for f in sorted(os.listdir(BASE+r"\S05_KPROVED3")):
    print("  ",f)
print("_ghidra/S05_KPROVED3 exists:",os.path.isdir(BASE+r"\_ghidra\S05_KPROVED3"))
print("\nALL SELF-CHECKS PASSED")
