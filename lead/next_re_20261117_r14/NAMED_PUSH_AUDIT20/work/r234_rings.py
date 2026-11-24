import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
rows = [
    (0x0069EE30, 0x007F2E58, 0x0069EC50, 0x0069ECD2, 0x70),
    (0x00719E30, 0x007F50CC, 0x00718000, 0x0071805E, 0x4C),
    (0x0075C7F0, 0x007F6AC4, 0x0075AA90, 0x0075AADF, 0x3C),
]
for E, VT, CTOR, INST, SZ in rows:
    print("#" * 70)
    print(f"### entry {E:08X} vt {VT:08X} ctor {CTOR:08X} install@{INST:08X} size {SZ:#x}")
    i = b.rtti(VT)
    print(f"  COL={i['col'] and hex(i['col'])} offset={i['offset']} pTD={i['pTD'] and hex(i['pTD'])} pCHD={i['pCHD'] and hex(i['pCHD'])} name={i['name']}")
    print(f"  COL bytes: {b.hexat(i['col'], 0x14)}")
    print(f"  TD bytes:  {b.hexat(i['pTD'], 0x20)}" if i['pTD'] else "  TD none")
    print(f"  vt slots 0..9: {[(n, hex(v) if v else v) for n, v in b.vt_dump(VT, 10)]}")
    print(f"  slot holding entry: {b.slot_holding(VT, E, 40)}  bytes at vt+0: {b.hexat(VT, 8)}")
    print(f"  writers of {VT:08X}:")
    for w in b.writers_of_imm(VT):
        print(f"    imm@{w['imm_at']:08X} ins@{w['ins_va']:08X} {w['text']} bytes={w['bytes']}")
    print(f"  ctor prologue:")
    print(show(b.dis(CTOR, 10), "    "))
    print(f"  install site:")
    print(show(b.dis(INST - 0x10, 10), "    "))
    print(f"  callers of ctor: {[hex(x) for x in b.callers_of(CTOR)]}")
    print(f"  push-imm sites of ctor (atexit?): {[hex(x) for x in b.push_sites(CTOR)]}")
