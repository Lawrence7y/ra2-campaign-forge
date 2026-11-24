import json, os
p = r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE\W160_Q1_channelA.json"
r = json.load(open(p, encoding="utf-8"))
print("call sites:", len(r["call_sites"]))
print("forms:", r["call_site_forms"])
print("SIB sites:", [c for c in r["call_sites"] if c["form"]=="SIB"])
cs = r["call_sites"]
print("REG modrm counts:")
from collections import Counter
print(Counter(c["text"].split()[2][:0] or c["text"] for c in cs).most_common(3))
# function membership: nearest atlas entry <= site (for context only)
atlas = []
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv", encoding="utf-8") as f:
    next(f)
    for ln in f:
        p=ln.split()
        if len(p)>=2: atlas.append((int(p[0],16),int(p[1])))
atlas.sort()
import bisect
starts=[a for a,s in atlas]
funcs=Counter()
for c in cs:
    va=int(c["va"],16); i=bisect.bisect_right(starts,va)-1
    funcs[hex(atlas[i][0]) if i>=0 else "NONE"]+=1
print("unique funcs:", len(funcs))
print("top:", funcs.most_common(8))
# all add 0x5c (capstone detail would be better; show raw)
print("add 0x5c count:", len(r["add_0x5c_instrs"]))
for x in r["add_0x5c_instrs"][:30]: print(x)
