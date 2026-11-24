"""Step 3: independent raw-.text call/jmp target sweep (channel B, atlas-free).
Saves compact JSON to work/calls_map.json and a human-readable evidence file.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *

b=Bin()
calls,jmps,stats=scan_calls(b,'.text')
out=[]
out.append("scan stats: "+repr(stats))
out.append(f"distinct call targets: {len(calls)}  total call sites: {sum(map(len,calls.values()))}")
out.append(f"distinct jmp targets: {len(jmps)}  total jmp sites: {sum(map(len,jmps.values()))}")
json.dump({'calls':{hex(k):[hex(x) for x in v] for k,v in calls.items()},
           'jmps':{hex(k):[hex(x) for x in v] for k,v in jmps.items()},
           'stats':stats},
          open(os.path.join(os.path.dirname(__file__),'calls_map.json'),'w'), indent=0)

keys=[0x6CBCA0,0x6CB560,0x6CC390,0x4F8440,0x4F9370,0x6CBEE0,0x6CB820,
      0x6CAF90,0x6CE700,0x6CE5B0,0x6CE210,0x6CE8F0,0x6CE900,0x6CE910,
      0x6CDEF0,0x6CE020,0x55DE81,0x6CB920,0x6CC360,0x6CE2C0]
for k in keys:
    sites=calls.get(k,[])
    out.append(f"\ncallers of {k:08X}: {len(sites)} -> "+" ".join(f"{x:08X}" for x in sites))

text="\n".join(out)
open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E03_callmap.txt'),'w',encoding='utf-8').write(text)
print(text)
