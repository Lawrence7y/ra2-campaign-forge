import json
j=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json',encoding='utf-8'))['vtables']
for t in [0x7E9F24,0x7E9F44,0x7E192C,0x7E18FC,0x7E9FA4,0x7E9FC4,0x7E4F64]:
    print(f'{t:08X}:',[(v['class'],v['col'],v['col_offset']) for v in j if v['vt']==t])
