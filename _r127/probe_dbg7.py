import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec=importlib.util.spec_from_file_location('m','_r127/r127b_qi_owners.py')
# can't import (it runs). Instead re-derive minimal.
import struct,bisect
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
RD=S['.rdata']; TX=S['.text']
RD_LO=RD.VirtualAddress+IB; RD_HI=RD_LO+RD.Misc_VirtualSize
T_LO=TX.VirtualAddress+IB; T_HI=T_LO+TX.Misc_VirtualSize
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    try: b=rd(va,4)
    except Exception: return None
    return struct.unpack('<I',b)[0] if len(b)==4 else None
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
VT={}
for p in range(RD_LO,RD_HI-4,4):
    r=rtti(p)
    if not r: continue
    if not (r['class'].startswith('.?AV') or r['class'].startswith('.?AU')): continue
    f=u32(p)
    if f is None or not (T_LO<=f<T_HI): continue
    VT[p]=r
FN=sorted({v for p,r in VT.items() for k in range(len(r['bases'])+26) for v in [u32(p+4*k)] if v and T_LO<=v<T_HI})
print('FN count',len(FN))
i=bisect.bisect_right(FN,0x429270)-1
print('fn_end(0x429270)=',hex(FN[i+1]) if i+1<len(FN) else 'T_HI')
e=FN[i+1]
print('is 0x4292ab < end?', 0x4292ab < e)
# does vt 0x7ea564 slot 3 exist in loop
vt=0x7ea564; r=VT[vt]
for k in range(0,8):
    v=u32(vt+4*k)
    print(' k=%d v=%s text=%s'%(k,hex(v) if v else None, (v is not None and T_LO<=v<T_HI)))
