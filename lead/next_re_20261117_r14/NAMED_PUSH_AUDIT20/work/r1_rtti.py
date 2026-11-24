import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
E = 0x006DBE00

for vt in (0x007F4348, 0x007F432C, 0x007F4324, 0x007F431C):
    i = b.rtti(vt)
    print(f"--- vt {vt:08X} COL={i['col'] and hex(i['col'])} ofs={i['offset']} pTD={i['pTD'] and hex(i['pTD'])} pCHD={i['pCHD'] and hex(i['pCHD'])} name={i['name']} notes={i['notes']}")
    print("    slots:", [(n, hex(v) if v else v) for n, v in b.vt_dump(vt, 12)])
    print("    entry slot idx:", b.slot_holding(vt, E, 60))
    print("    COL bytes:", b.hexat((i['col'] or 0), 0x14))
    if i['pTD']:
        print("    TD+0..+0x18:", b.hexat(i['pTD'], 0x18))

print("\n=== callee 00410320 ===")
print(show(b.func(0x410320, maxbytes=0x120)))
