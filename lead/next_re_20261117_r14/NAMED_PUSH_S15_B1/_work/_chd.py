import sys, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S15_B1\_work")
from analyze import rtti_chain
from core2 import u32
for vb in (0x007F443C,0x007F44E0,0x007F45C4,0x007F5578,0x007F5858,0x007F5904):
    ch = rtti_chain(u32(vb-4))
    c = ch["chd"]
    print("%08X %-22s nbase=%s bases=%s" % (vb, ch["td_name"], c["nbase"] if c else None,
          [b["name"] for b in c["bases"]] if c else None))
