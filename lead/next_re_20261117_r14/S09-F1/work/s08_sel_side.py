"""S09-F1 recon 08: selection container, sidebar cameo table, command dispatch."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09-F1\work")
from s09lib import *

b = Bin(); atlas = Atlas()
calls, jmps, nins = sweep_calls(b)

print("### SELECTION funcs ###")
for addr,label in [(0x732D00,"IsSelected?"),(0x7327D0,"RemoveFromSelection?"),(0x732600,"AddToSelection?"),(0x70D150,"ClearSelection?")]:
    info=atlas.contains(addr)
    print("\n--- %s 0x%08X atlas=%s callers=%d ---"%(label,addr,str(info[:2]) if info else None,len(calls.get(addr,[]))))
    print(dump(b, addr, 0x90))

print("\n### SIDEBAR: 0x6AAD00 (Cameo click produce) ###")
print(dump(b, 0x6AAD00, 0x160))
print("\n--- callers of 0x6AAD00 ---")
for s in calls.get(0x6AAD00,[]): print("  %08X"%s)

print("\n### 0x4C6970 FillEvent_Produce callers ###")
print(" count=%d"%len(calls.get(0x4C6970,[])))
for s in calls.get(0x4C6970,[]):
    i=atlas.contains(s); print("  %08X in %s"%(s,"%08X+%d"%(i[0],i[1]) if i else "HOLE"))
