#!/usr/bin/env python3
"""S16-K2: independent RTTI verification for SuperClass / SuperWeaponTypeClass vtables."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16-K2\work")
import re_lib as R
b=R.Bin()
for col in (0x80B610, 0x80B6C8):
    sig,off,cd,ptd,pcd = struct.unpack('<IIIII', b.read(col,20))
    name=R.cstr(b,ptd+8,128)
    print(f"COL {col:08X}: sig={sig} off={off} cd={cd} TD={ptd:08X} CD={pcd:08X} name='{name}'")
    # find vftable that references COL
    for secn in ('.rdata','.data'):
        s=b.sec(secn); buf=b.data[s['raw']:s['raw']+s['rawsize']]
        for i in range(0,len(buf)-3,4):
            if struct.unpack_from('<I',buf,i)[0]==col:
                vt=s['va']+i+4
                print(f"  COL ref @ {s['va']+i:08X} => vftable {vt:08X}")
                print(f"  v[6]={b.u32(vt+24):08X}  v[8]={b.u32(vt+32):08X}  v[12]={b.u32(vt+48):08X}")
                break
