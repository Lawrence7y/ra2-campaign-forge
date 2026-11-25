# -*- coding: utf-8 -*-
import re,struct,pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.decode().strip('\x00'),IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),
       s.PointerToRawData,s.Misc_VirtualSize,s.SizeOfRawData) for s in pe.sections]
def rd(va,n):
    for nm,lo,hi,ptr,vs,rs in SECS:
        if lo<=va<hi:
            o=va-lo
            if o>=rs: return b''
            return pe.__data__[ptr+o:ptr+o+min(n,rs-o)]
    return None
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if b and len(b)==4 else None
def cstr(va,n=200):
    b=rd(va,n)
    if not b: return None
    z=b.find(b'\x00'); return b[:z if z>=0 else len(b)].decode('latin-1')
print('## A')
print(' 0x87f7e8 in section:',[nm for nm,lo,hi,ptr,vs,rs in SECS if lo<=0x87f7e8<hi])
print(' rd(0x87f7e8,4)=',repr(rd(0x87f7e8,4)))
print(' .data raw span VA %s..%s'%(hex(0x812000),hex(0x812000+0x6c000)))
vt=0x7e1964; col=u32(vt-4)
print(' vt=%s  [vt-4]=%s'%(hex(vt),hex(col)))
print(' COL raw:',rd(col,20).hex(' '),'sig=%s'%u32(col))
ptd=u32(col+12); pchd=u32(col+16)
print(' pTD=%s pCHD=%s'%(hex(ptd),hex(pchd)))
print(' TD raw:',rd(ptd,16).hex(' '),'name=%r'%cstr(ptd+8))
print(' TD vftable=%s spare=%s'%(hex(u32(ptd)),hex(u32(ptd+4))))
print(' CHD raw:',rd(pchd,16).hex(' '),'attr=%s numBase=%s pBCA=%s'%(hex(u32(pchd+4)),u32(pchd+8),hex(u32(pchd+12))))
n=u32(pchd+8); bca=u32(pchd+12)
for i in range(n):
    bcd=u32(bca+4*i)
    t,ncb,md_,pd,vd,at=struct.unpack('<Iiiiii',rd(bcd,24))
    print('  [%2d] BCD=%s name=%-22r ncb=%2d mdisp=%5d pdisp=%3d vdisp=%d attr=%s'%(i,hex(bcd),cstr(t+8),ncb,md_,pd,vd,hex(at)))
print(' slot0=%s'%hex(u32(vt)))
print()
print('## B')
def g(b):
    d1,d2,d3=struct.unpack('<IHH',b[:8]); r=b[8:16]
    return '{%08X-%04X-%04X-%02X%02X-%s}'%(d1,d2,d3,r[0],r[1],''.join('%02X'%x for x in r[2:]))
for va in (0x7ea6e8,0x7e36c0,0x7f7c90):
    b=rd(va,16); print(' %s %s -> %s'%(hex(va),b.hex(' '),g(b)))
