# -*- coding: utf-8 -*-
"""Direct scan: all aligned/unaligned dword occurrences of 0x7E89F4 and 0x8006A8; dump context."""
import pefile,struct
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data=open(EXE,'rb').read();pe=pefile.PE(EXE,fast_load=True);BASE=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b"\x00").decode('latin1');secs.append((nm,BASE+s.VirtualAddress,s.PointerToRawData,s.SizeOfRawData,s.Misc_VirtualSize))
def va_of_fo(fo):
    for nm,v,r,rs,vs in secs:
        if r<=fo<r+rs: return v+(fo-r),nm
    return None,None
def rd(va,n):
    for nm,v,r,rs,vs in secs:
        if v<=va<v+max(vs,rs):return data[r+(va-v):r+(va-v)+n]
    return b''
def u32(va):
    b=rd(va,4);return struct.unpack('<I',b)[0] if len(b)==4 else None
def cstr(va):
    b=rd(va,100);z=b.find(b'\x00');return b[:z].decode('latin1') if z!=-1 else ''
for target in [0x7E89F4,0x8006A8]:
    print("\n=== dword %08X occurrences ==="%target)
    needle=struct.pack('<I',target)
    start=0
    cnt=0
    while cnt<20:
        i=data.find(needle,start)
        if i<0: break
        va,nm=va_of_fo(i)
        if va is not None:
            # context: check if this is COL: sig at va-0x10
            sig=u32(va-0x10) if va>=0x400000 else None
            td=u32(va-4) if va>=0x400000 else None
            nm2=cstr(td+8) if td and td>0x400000 else ''
            print("  file=%08X va=%08X (%s) [va-0x10]=%s [va-4]=%s name=%r"%(i,va,nm,hex(sig or 0),hex(td or 0),nm2))
        start=i+1;cnt+=1
print("\n=== dump 0x8006A0..0x8006C0 ===")
for va in range(0x8006A0,0x8006C0,4):
    print("  %08X: %08X"%(va,u32(va) or 0))
