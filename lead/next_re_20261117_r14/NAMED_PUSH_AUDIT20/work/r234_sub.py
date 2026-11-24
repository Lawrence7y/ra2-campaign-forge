import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
pairs = [(0x007F2E58, 0x007F2D8C, 0x007F2D68, 0x0069EE30),
         (0x007F50CC, 0x007F5000, 0x007F4FDC, 0x00719E30),
         (0x007F6AC4, 0x007F69F8, 0x007F69D4, 0x0075C7F0)]
for main, sec4, sec18, E in pairs:
    print(f"### main {main:08X}")
    for t in (sec4, sec18):
        i = b.rtti(t)
        print(f"   sub {t:08X}: COL={i['col'] and hex(i['col'])} offset={i['offset']} name={i['name']} slot0={b.u32(t) and hex(b.u32(t))} slot1={b.u32(t+4) and hex(b.u32(t+4))}")
        s0 = b.u32(t)
        if s0 and 0x401000 <= s0 < 0x7E038D:
            print(show(b.dis(s0, 5), "      "))
    print(f"   main slot0 bytes: {b.hexat(main, 4)} = {b.u32(main):08X} (expect {E:08X})")
    # does main table also contain the entry elsewhere?
    print(f"   other slots == entry: {b.slot_holding(main, E, 30)}")
