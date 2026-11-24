"""S09-F1 recon 05: coordinate mapping function 0x63AAC0 + scroll origins."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09-F1\work")
from s09lib import *

b = Bin(); atlas = Atlas()
calls, jmps, nins = sweep_calls(b)

info = atlas.contains(0x63AAC0)
print("0x63AAC0 atlas=%s" % (str(info[:2]) if info else None))
print("=== 0x63AAC0 direct callers (%d) ===" % len(calls.get(0x63AAC0, [])))
for s in calls.get(0x63AAC0, []):
    i = atlas.contains(s)
    print("  %08X in %s" % (s, "%08X+%d"%(i[0],i[1]) if i else "HOLE"))
print("\n=== 0x63AAC0 dump (0x180 bytes) ===")
print(dump(b, 0x63AAC0, 0x180))
print("\n=== scroll-origin ref sites ===")
for g in (0x886FA0, 0x886FA4, 0x886FA8, 0x886FAC):
    found = sweep_disps(b, g)
    print("\n  global %08X: %d refs" % (g, len(found)))
    for f in found[:25]:
        i = atlas.contains(f["va"])
        print("    %08X %-44s %s" % (f["va"], f["insn"], "%08X+%d"%(i[0],i[1]) if i else "HOLE"))
