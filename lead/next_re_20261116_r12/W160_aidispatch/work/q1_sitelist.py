import json, os, bisect
from collections import Counter
R=r"D:\Project\ra2-campaign-forge"
r=json.load(open(os.path.join(R,"lead","next_re_20261116_r12","W160_aidispatch","EVIDENCE","W160_Q1_channelA.json"),encoding="utf-8"))
atlas=[]
with open(os.path.join(R,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv"),encoding="utf-8") as f:
    next(f)
    for ln in f:
        p=ln.split()
        if len(p)>=2: atlas.append((int(p[0],16),int(p[1])))
atlas.sort(); starts=[a for a,s in atlas]
def fn(va):
    i=bisect.bisect_right(starts,va)-1
    if i<0: return "NONE"
    a,s=atlas[i]
    return f"{a:06X}+{va-a} (size {s})" if va < a+s else f"GAP near {a:06X}+{va-a} (size {s})"
raw={int(h["va"],16):h for h in r["raw_hits"]}
for c in r["call_sites"]:
    va=int(c["va"],16)
    print(f"{c['va']:>10} {raw[va]['bytes'] if va in raw else '????':<16} {c['text']:<40} fn={fn(va)}")
