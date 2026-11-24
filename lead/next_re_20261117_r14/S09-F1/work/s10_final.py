"""S09-F1 recon 10: tab base +0x1544, box-select 0x6DA5C0, FillEvent bridge."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09-F1\work")
from s09lib import *

b = Bin(); atlas = Atlas()
calls, jmps, nins = sweep_calls(b)

print("=== search disp 0x1544 (tab base) refs ===")
found = sweep_disps(b, 0x1544)
print(" count=%d"%len(found))
for f in found[:20]: print("  %08X %s"%(f["va"],f["insn"]))

print("\n=== box-select 0x6DA5C0 dump (first 0x180) ===")
print(dump(b, 0x6DA5C0, 0x180))

print("\n=== 0x6D9FF0 wrapper dump ===")
print(dump(b, 0x6D9FF0, 0x80))

print("\n=== FillEvent 0x4C65E0 callers ===")
for s in calls.get(0x4C65E0,[])[:20]:
    i=atlas.contains(s); print("  %08X in %s"%(s,"%08X+%d"%(i[0],i[1]) if i else "HOLE"))
print("\n=== house filter 0x50B6F0 callers count ===", len(calls.get(0x50B6F0,[])))
for s in calls.get(0x50B6F0,[])[:20]:
    i=atlas.contains(s); print("  %08X in %s"%(s,"%08X+%d"%(i[0],i[1]) if i else "HOLE"))
