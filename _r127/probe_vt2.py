import struct,bisect
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def i32(va):
    b=rd(va,4); return struct.unpack('<i',b)[0] if len(b)==4 else None
def cstr(va,n=200):
    b=rd(va,n); e=b.find(b'\x00'); return (b[:e] if e>=0 else b).decode('latin1')
def in_img(v): return v is not None and 0x400000<=v<0xB80000
def rtti(vt):
    col=u32(vt-4)
    if not in_img(col): return None
    ptd=u32(col+12); chd=u32(col+16)
    if not in_img(ptd) or not in_img(chd): return None
    n,arr=u32(chd+8),u32(chd+12)
    if n is None or n>64 or not in_img(arr): return None
    bases=[]
    for i in range(n):
        bcd=u32(arr+4*i)
        if not in_img(bcd): return None
        td=u32(bcd)
        if not in_img(td): return None
        bases.append({'name':cstr(td+8,200),'mdisp':i32(bcd+8)})
    return {'class':cstr(ptd+8,200),'bases':bases}
for a in (0x429360,0x429270,0x6cf430,0x4292ab,0x42937f,0x6cf44e):
    print(hex(a), end=' -> ')
    found=False
    for k in range(0,200):
        p=a-4*k
        r=rtti(p)
        if r and (r['class'].startswith('.?AV') or r['class'].startswith('.?AU')):
            print('vt=0x%x k=%d class=%s'%(p,k,r['class'])); found=True; break
    if not found: print('NOT FOUND')
