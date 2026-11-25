import struct
import pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
RD=S['.rdata']; RD_LO=RD.VirtualAddress+IB; RD_HI=RD_LO+RD.Misc_VirtualSize
DA=S['.data']; DA_LO=DA.VirtualAddress+IB; DA_HI=DA_LO+DA.Misc_VirtualSize
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def i32(va):
    b=rd(va,4); return struct.unpack('<i',b)[0] if len(b)==4 else None
def cstr(va,n=200):
    b=rd(va,n); e=b.find(b'\x00'); return (b[:e] if e>=0 else b).decode('latin1')
TGT=[0x429270,0x429210,0x6cf430,0x7e36c0,0x7e9b20]
for t in TGT:
    hits=[]
    for base,hi,nm in ((RD_LO,RD_HI,'.rdata'),(DA_LO,DA_HI,'.data')):
        for va in range(base,hi-4,4):
            if u32(va)==t: hits.append((nm,va))
    print(hex(t),'x4 hits:',[(n,hex(v)) for n,v in hits][:12], len(hits))
def colname(vt):
    col=u32(vt-4)
    if col is None or not (RD_LO<=col<RD_HI): return None
    chd=u32(col+16)
    if chd is None or not (RD_LO<=chd<RD_HI): return None
    n,arr=u32(chd+8),u32(chd+12)
    out=[]
    for i in range(min(n or 0,64)):
        bcd=u32(arr+4*i)
        td=u32(bcd)
        out.append((cstr(td+8,200), i32(bcd+8), i32(bcd+16), u32(bcd+4)))
    return out
# for each hit that looks like vtable start (next slots are .text ptrs), dump
def dump_vt(vt,n=12):
    vals=[u32(vt+4*i) for i in range(n)]
    print('  vt 0x%x slots=%s'%(vt,' '.join('%x'%v if v else '0' for v in vals)))
    cn=colname(vt)
    print('   rtti:', None if cn is None else [(a,hex(b) if b is not None else b,d,e) for a,b,d,e in cn])
dump_vt(0x7f4108)
