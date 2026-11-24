"""S09-F1 recon 12: selection container 0xA8EC78 vftable/type confirmation."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09-F1\work")
from s09lib import *

b = Bin(); atlas = Atlas()
print("=== imm32 refs to container base 0xA8EC78 / members ===")
for v in (0xA8EC78, 0xA8EC7C, 0xA8EC88, 0xA8ECB8):
    hits = sweep_imm(b, v)
    print("  imm %08X: %d" % (v, len(hits)))
    for h in hits[:10]: print("     %08X %s" % (h["va"], h["insn"]))
print("\n=== disps to container base 0xA8EC78 (writes of vftable?) ===")
found = sweep_disps(b, 0xA8EC78)
print(" count=%d"%len(found))
for f in found[:20]:
    i=atlas.contains(f["va"])
    print("  %08X %-46s %s"%(f["va"],f["insn"],"%08X+%d"%(i[0],i[1]) if i else "HOLE"))
