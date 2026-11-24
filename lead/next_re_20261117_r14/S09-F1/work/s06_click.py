"""S09-F1 recon 06: ProcessClickCoords 0x692300 / GetObjectAt 0x6DA380 / cell mapping."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09-F1\work")
from s09lib import *

b = Bin(); atlas = Atlas()
calls, jmps, nins = sweep_calls(b)

print("=== ProcessClickCoords 0x692300 dump (0x260) ===")
print(dump(b, 0x692300, 0x260))
print("\n=== 0x692300 callers ===")
for s in calls.get(0x692300, []):
    i=atlas.contains(s); print("  %08X in %s"%(s,"%08X+%d"%(i[0],i[1]) if i else "HOLE"))
print("\n=== GetObjectAt 0x6DA380 dump (0x180) ===")
print(dump(b, 0x6DA380, 0x180))
print("\n=== 0x6DA380 callers ===")
for s in calls.get(0x6DA380, []):
    i=atlas.contains(s); print("  %08X in %s"%(s,"%08X+%d"%(i[0],i[1]) if i else "HOLE"))
