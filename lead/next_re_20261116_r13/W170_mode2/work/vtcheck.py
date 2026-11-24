import json
p=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json"
d=json.load(open(p,encoding="utf-8"))
print("type",type(d),"len",len(d))
if isinstance(d,list):
    print("first",json.dumps(d[0],indent=1)[:900])
    # print one with .?AVBuildingClass
    for r in d:
        s=json.dumps(r)
        if "BuildingClass" in s or "BulletClass" in s:
            print("MATCH",json.dumps(r,indent=1)[:900]); break
else:
    k=list(d.keys())[:3]; print("keys",k)
    for kk in k:
        print("sample",kk,json.dumps(d[kk],indent=1)[:900]); break
