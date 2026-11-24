# -*- coding: utf-8 -*-
"""Final artifact: full evidence table for C1-C4."""
from base import BUF, IB, TEXT, u32, blob
import json

out = {}
# C1
PAT = bytes.fromhex("8B0D68738800")
TEXTlo, TEXThi = TEXT["va"], TEXT["va"]+TEXT["vsize"]
hits=[va for va in range(TEXTlo,TEXThi-6) if BUF[va-IB:va-IB+6]==PAT]
def s32(va): return int.from_bytes(BUF[va-IB:va-IB+4],"little",signed=True)
qual=[]
for v in hits:
    for k in range(24):
        a=v+6+k
        if BUF[a-IB]==0xE8 and a+5+s32(a+1)==0x00724730:
            qual.append((v,a)); break
out["C1"]={"pattern":"8B0D68738800","total":len(hits),"qualified":len(qual),
           "sites":["%08X"%v for v,_ in qual]}
print(json.dumps(out["C1"],indent=1))
json.dump(out,open("verdict_evidence.json","w"),indent=1)
