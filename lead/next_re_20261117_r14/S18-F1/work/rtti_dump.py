import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import read, u32

def show(va, n=40):
    b = read(va, n)
    if b is None:
        print(f"0x{va:08X}: <unreadable>")
        return
    hx = ' '.join(f'{x:02X}' for x in b)
    asc = ''.join(chr(x) if 32 <= x < 127 else '.' for x in b)
    print(f"0x{va:08X}: {hx}  |{asc}|")

for va in [0x8446F0, 0x8446F8, 0x844700, 0x8446C0, 0x8446C8,
           0x80C548, 0x80C560, 0x80C578, 0x80C5E0, 0x80C500]:
    show(va)

print("\n--- decode_vt corrected: TD name ptr ---")
def decode(vt):
    col = u32(vt-4)
    td = u32(col+0xC) if col else None
    nameptr = u32(td+8) if td else None
    nm = None
    if nameptr and 0x400000 < nameptr < 0xC00000:
        nb = read(nameptr, 160)
        if nb:
            nm = nb.split(b'\x00')[0].decode('latin1')
    return col, td, nameptr, nm

for vt in [0x7F550C, 0x7F554C, 0x7F5554, 0x7F555C, 0x7F5578]:
    print(f"  vt 0x{vt:08X}: COL/TD/nameptr/name = {decode(vt)}")
