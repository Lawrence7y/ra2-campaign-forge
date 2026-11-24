#!/usr/bin/env python3
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16-K3\work")
import k3_lib as K
b=K.Bin()
for g in (0x89c430,0x89c434,0x89c438,0x89c42c,0x89c43c):
    try: v=b.u32(g)
    except Exception: continue
    print(f"[{g:08X}] = {v:08X}", end=" ")
    try: col=b.u32(v-4)
    except Exception: col=None
    if col:
        r=K.rtti_from_col(b,col)
        if r:
            print(f"COL={col:08X} TD={r['ptd']:08X} name={r['name']} off={r['off']}")
        else:
            print(f"COL={col:08X} no RTTI")
    else:
        print("no col")
