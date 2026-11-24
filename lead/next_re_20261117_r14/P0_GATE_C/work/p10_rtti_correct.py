# -*- coding: utf-8 -*-
"""Correct RTTI: scan ALL COLs (sig=0, TD=valid name) and match COL+0x10 vptr to target vtables."""
import pefile,struct
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data=open(EXE,'rb').read();pe=pefile.PE(EXE,fast_load=True);BASE=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b"\x00").decode('latin1');secs.append((nm,BASE+s.VirtualAddress,s.PointerToRawData,s.SizeOfRawData,s.Misc_VirtualSize))
def rd(va,n):
    for nm,v,r,rs,vs in secs:
        if v<=va<v+max(vs,rs):return data[r+(va-v):r+(va-v)+n]
    return b''
def u32(va):
    b=rd(va,4);return struct.unpack('<I',b)[0] if len(b)==4 else None
def cstr(va):
    b=rd(va,100);z=b.find(b'\x00');return b[:z].decode('latin1') if z!=-1 else ''
TARGETS={0x7E89F4:'vtable containing 4CCA20',0x7EE0F4:'5C0247 obj vtable',0x7F7958:'7B23B0 slot',0x7F79C8:'7B23B0 slot2'}
results={k:[] for k in TARGETS}
# scan all sections aligned dwords as potential COL
for nm,v,r,rs,vs in secs:
    if nm=='.text': continue
    for off in range(0,rs-0x14,4):
        colva=v+off
        if u32(colva)!=0: continue
        td=u32(colva+0xC); vp=u32(colva+0x10)
        if not td or not vp: continue
        nm2=cstr(td+8)
        if not nm2.startswith('.?AV'): continue
        for t in TARGETS:
            if vp==t or (t<=vp<t+0x100):
                results[t].append((hex(colva),hex(vp),hex(td),nm2))
for t,label in TARGETS.items():
    print("%08X (%s):"%(t,label))
    for r in results[t][:10]: print("   ",r)
    if not results[t]: print("    NONE (fail-closed)")
