import json, os
p=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json'
j=json.load(open(p,encoding='utf-8'))['vtables']
targets=[0x7E18FC,0x7E192C,0x7E9F64,0x7E5EDC,0x7F07A4,0x7E9FA4,0x7E9EE4,0x007E192C,0x007E9F00]
for t in set(targets):
    hits=[v for v in j if v['vt']==t]
    print(f'{t:08X}: {[(v["class"],v["col"],v["col_offset"],v["sig"]) for v in hits]}')
# class names containing Logic, Team etc
for kw in ['Logic','Team','Tag','Factory','DiskLaser','RadSite','House','ObjectClass']:
    hs=[(hex(v['vt']),v['class']) for v in j if kw.lower() in v['class'].lower()]
    print(kw, hs[:20], 'n=',len(hs))
