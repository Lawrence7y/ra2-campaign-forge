import json, sys
p=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json'
d=json.load(open(p,encoding='utf-8'))
print("stats:", json.dumps(d['stats'])[:600])
v=d['vtables']
print("type of vtables:", type(v), len(v))
if isinstance(v,list):
    print(json.dumps(v[0])[:800])
