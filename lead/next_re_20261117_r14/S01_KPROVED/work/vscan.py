# -*- coding: utf-8 -*-
"""Scan .rdata for vtables referencing S01 entries; verify RTTI chain COL->TD->name."""
import sys,struct,json
import pefile
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
PE=pefile.PE(EXE,fast_load=False); IB=PE.OPTIONAL_HEADER.ImageBase
DATA=PE.__data__
SECS=[]
for s in PE.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin1')
    SECS.append((nm,s.VirtualAddress,s.Misc_VirtualSize,s.SizeOfRawData,s.PointerToRawData))
def rva2off(rva):
    for nm,va0,vs,rs,rp in SECS:
        if va0<=rva<va0+rs: return rp+(rva-va0)
def va2off(va): return rva2off(va-IB)
def readva(va,n):
    o=va2off(va); return DATA[o:o+n] if o is not None else b''
def u32(va):
    b=readva(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
TEXT_VA=0x401000; TEXT_END=0x401000+0x3DF38D
RDATA_VA=0x7E1000; RDATA_END=RDATA_VA+0x30074
RDATA_RAWPTR=[rp for nm,va0,vs,rs,rp in SECS if nm=='.rdata'][0]
RDATA_FOFF=RDATA_RAWPTR; RDATA_FEND=RDATA_RAWPTR+0x31000
S01=['00409030','00409100','004091C0','004092F0','00409320','00409360','004093F0','00409880','00409C40','00409D90','00430250','0048C8B0','0048CCC0','004E2450','004E2460','004E24A0','004F1AA0','0052FC20','00554400','0055AF60','0055CFD0','0055D360','0055E420','0055F1E0','005A89D0','005B1D90','005B1E40','005CAF70','005CAFC0','005D2410','005D2530','005D5870','005D5880','005D5890','0063D810','00643E80','00646DF0','00647040','006470F0','006471A0','006521C0','006640E0','00697AD0','0069AE90','0069BAB0','006BB9A0','007240B0','007241A0','00724200','00732CA0','00734120','00734210','007CD80F']
S01VA={int(x,16) for x in S01}
# scan .rdata dword-aligned for the S01 VAs
hits=[]
for off in range(RDATA_FOFF,RDATA_FEND-4,4):
    val=struct.unpack('<I',DATA[off:off+4])[0]
    if val in S01VA:
        va=IB+(off-RDATA_FOFF+ (RDATA_VA-IB)) # = off - RDATA_FOFF + RDATA_VA
        hits.append((va,val))
print('raw dword hits in .rdata referencing S01 entries:',len(hits))
from collections import defaultdict
byent=defaultdict(list)
for va,val in hits: byent[val].append(va)
for ent in S01:
    eva=int(ent,16)
    if eva in byent:
        print(f'\n{ent}: {len(byent[eva])} vt-slot-like refs: '+', '.join(hex(x) for x in byent[eva][:20]))
        # for each, try to find vtable start by scanning backward for COL at [-4]
        for ref in byent[eva][:5]:
            col=u32(ref-4)
            if col and 0x7E1000<=col<=0x7E4100:
                td=u32(col+0xC)
                if td:
                    nameb=readva(td+8,80)
                    # strip at null/nonprintable
                    nm=''
                    for b in nameb:
                        if b==0: break
                        if 32<=b<127: nm+=chr(b)
                        else: break
                    print(f'    ref@{ref:08X} COL={col:08X} TD={td:08X} name={nm!r}')
            else:
                print(f'    ref@{ref:08X} prev dword={col!r} (no COL)')
