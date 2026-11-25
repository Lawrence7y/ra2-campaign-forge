import struct,bisect
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
RD=S['.rdata']; RD_LO=RD.VirtualAddress+IB; RD_HI=RD_LO+RD.Misc_VirtualSize
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def i32(va):
    b=rd(va,4); return struct.unpack('<i',b)[0] if len(b)==4 else None
def cstr(va,n=200):
    b=rd(va,n); e=b.find(b'\x00'); return (b[:e] if e>=0 else b).decode('latin1')
def rtti(vt):
    col=u32(vt-4)
    if not col: return None
    ptd=u32(col+12); pchd=u32(col+16)
    if not ptd or not pchd: return None
    n,arr=u32(pchd+8),u32(pchd+12)
    out={'class':cstr(ptd+8,200),'bases':[]}
    for i in range(min(n or 0,64)):
        bcd=u32(arr+4*i); td=u32(bcd)
        out['bases'].append({'name':cstr(td+8,200),'mdisp':i32(bcd+8)})
    return out
for vt,lab in ((0x7e36d4,'ApplicationClass mdisp0'),(0x7f4108,'SwizzleManager mdisp0'),(0x7ea570,'Sub2')):
    r=rtti(vt)
    print('===',lab,'vt=0x%x'%vt)
    print('   class=',r['class'])
    for b in r['bases']: print('     ',b['name'],b['mdisp'])
