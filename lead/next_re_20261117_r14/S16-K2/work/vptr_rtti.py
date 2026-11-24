#!/usr/bin/env python3
"""S16-K2: resolve vptr globals used by unnamed functions to RTTI class names."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16-K2\work")
import re_lib as R
b=R.Bin()

def find_ptr_refs(val):
    out=[]
    for secn in ('.rdata','.data'):
        s=b.sec(secn); buf=b.data[s['raw']:s['raw']+s['rawsize']]
        for i in range(0,len(buf)-3,4):
            if struct.unpack_from('<I',buf,i)[0]==val:
                out.append((s['va']+i,secn))
    return out

def class_from_vtable(vt):
    """vt points to vtable[0] (first virtual fn). VC6: vt-4 = pointer to COL."""
    try: col=b.u32(vt-4)
    except Exception: return None
    if not (0x400000<=col<0xC00000): return None
    # COL: sig,off,cd,pTypeDescriptor(+0xC),pClassDescriptor(+0x10)
    try: sig,off,cd,ptd,pcd=struct.unpack('<IIIII',b.read(col,20))
    except Exception: return None
    if sig!=0 or not (0x400000<=ptd<0xC00000): return None
    try: name=R.cstr(b,ptd+8,128)
    except Exception: return None
    return dict(col=col,off=off,ptd=ptd,name=name,pcd=pcd)

for g in (0x89c430,0x89c434,0x89c438):
    v=b.u32(g)
    print(f"[{g:08X}] = {v:08X}")
    refs=find_ptr_refs(v)
    for loc,secn in refs[:3]:
        print(f"  vptr value referenced at {loc:08X} ({secn}), [loc-4]={b.u32(loc-4):08X}")
    ci=class_from_vtable(v)
    if ci: print(f"  RTTI: COL={ci['col']:08X} off={ci['off']} TD={ci['ptd']:08X} name='{ci['name']}'")
    else: print("  no RTTI via vt-4->COL")
    print("  slots:", " ".join(f"{b.u32(v+4*k):08X}" for k in range(6)))
