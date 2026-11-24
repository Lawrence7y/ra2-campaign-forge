"""Check which proven addresses are in coverage.tsv and current grade."""
import csv, json
COV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
ATLAS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
cov={}; rows=[]
with open(COV,encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        e=r['entry'].upper().replace('0X','').zfill(8)
        cov[e]=r; rows.append(r)
atlas=set()
with open(ATLAS,encoding='utf-8') as f:
    f.readline()
    for line in f:
        p=line.split('\t')
        if p: atlas.add(p[0].upper().replace('0X','').zfill(8))

gets=[0x4B4CF0,0x4B66E0,0x4D0390,0x5172B0,0x54DF90,0x5B1B40,0x6635B0,0x6A42A0,0x71A120,0x72A200,0x75CBD0]
ctors=[0x4AF540,0x54AC40,0x513C20,0x661EC0,0x728A00,0x75AA90,0x4B5AB0,0x4CC9A0,0x718000,0x5AFEF0,0x69EC50]
cis=[0x6C4010+0x180*k for k in range(11)]  # 0x6C4010..0x6C4F10
base=[0x4C9150,0x55A6C0,0x55ABD0,0x55A8C0]

for label,addrs in [('GetSize',gets),('ctors',ctors),('CreateInstance',cis),('base/stubs',base)]:
    print('\n===',label,'===')
    for a in addrs:
        e='%08X'%a
        ina = e in atlas
        c=cov.get(e)
        print(e,'atlas' if ina else '-----', (c['grade'] if c else 'NOT-IN-COV'), (c['name'] if c else ''))
