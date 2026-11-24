import csv, os, io
base = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S08_KPROVED3'
# 1 delta rows
with io.open(os.path.join(base,'coverage_delta.tsv'),encoding='utf-8') as f:
    rows = list(csv.reader(f, delimiter='\t'))
print('delta header cols =', len(rows[0]), 'data rows =', len(rows)-1)
r = rows[1]
print('entry=%s subsystem=%s name=%s grade=%s' % (r[0],r[1],r[2],r[4]))
sem = r[3]
forbidden = ['未证','未定','弱信号','线索']
print('forbidden words in semantics:', [w for w in forbidden if w in sem])
print('sem has ③b:', '③b' in sem, '| has +0x anchors:', '+0x0A' in sem and '+0x30' in sem and '+0x38' in sem)
print('name class == ② class:', 'VectorClass<FoggedObjectClass*>' in r[2] and 'VectorClass<FoggedObjectClass*>' in sem)
# 2 PROGRESS line count
with io.open(os.path.join(base,'PROGRESS.md'),encoding='utf-8') as f:
    print('PROGRESS lines =', len(f.readlines()))
# 3 required files
for fn in ['PROGRESS.md','UNKNOWNS.md','DISAGREE.md','coverage_delta.tsv','EVIDENCE/PROOFS.md','EVIDENCE/RING_TABLE.tsv','work/v1_disasm_rtti.py','work/v2_sites_baserate.py']:
    print('exists %-32s %s' % (fn, os.path.exists(os.path.join(base,fn))))
# 4 verify delta entry grade transition consistent with disk
cov = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
with io.open(cov,encoding='utf-8') as f:
    for line in f:
        c=line.rstrip('\n').split('\t')
        if c and c[0]=='0045A640':
            print('disk row: grade=%s old_name=%s oldgrade->%s' % (c[4], c[2], r[7]))
            break
