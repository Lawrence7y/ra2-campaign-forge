import json, os
p=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json'
j=json.load(open(p,encoding='utf-8'))
v=j['vtables']
print('n=',len(v))
if isinstance(v,dict):
    k=list(v)[0]; print('first key',k,'val',json.dumps(v[k])[:600])
else:
    print(json.dumps(v[0])[:600])
print('stats',j.get('stats'))
