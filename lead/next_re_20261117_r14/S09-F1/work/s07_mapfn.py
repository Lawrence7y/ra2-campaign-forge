"""S09-F1 recon 07: pixel->cell mapping functions 0x6D6590 / 0x6D2280."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09-F1\work")
from s09lib import *

b = Bin(); atlas = Atlas()
calls, jmps, nins = sweep_calls(b)

for addr,label,n in [(0x6D6590,"PixelCoordToCell?",0x200),(0x6D2280,"PixelCoordToCoord?",0x180)]:
    info=atlas.contains(addr)
    print("\n=== %s 0x%08X atlas=%s callers=%d ===" % (label, addr, str(info[:2]) if info else None, len(calls.get(addr,[]))))
    for s in calls.get(addr,[])[:20]:
        i=atlas.contains(s); print("   site %08X in %s"%(s,"%08X+%d"%(i[0],i[1]) if i else "HOLE"))
    print(dump(b, addr, n))
