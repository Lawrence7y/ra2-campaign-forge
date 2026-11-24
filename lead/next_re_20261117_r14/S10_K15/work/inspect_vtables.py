import json,os
p=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_v2.json"
with open(p,'r',encoding='utf-8') as f: j=json.load(f)
print(type(j).__name__)
if isinstance(j,dict):
 print('keys',list(j.keys())[:20])
 for k in list(j.keys())[:3]:
  v=j[k]; print('\nKEY',k,'TYPE',type(v).__name__); print(str(v)[:2000])
else:
 print('len',len(j)); print(str(j[:3])[:3000])
