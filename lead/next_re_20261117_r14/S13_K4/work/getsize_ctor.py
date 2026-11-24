#!/usr/bin/env python3
"""Confirm GetSize factory ctor writes the class vtable (vptr init) for Bomb/Parasite/RadSite.
For each candidate factory (push imm -> new 0x7C8E17 -> call ctor), disasm the ctor
and check it writes the class main vtable into [this]. Emits EVIDENCE/getsize_ctor.txt"""
import struct, pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K4\EVIDENCE\getsize_ctor.txt"
pe=pefile.PE(EXE); IB=pe.OPTIONAL_HEADER.ImageBase; DATA=open(EXE,'rb').read()
SECS=[]
for s in pe.sections:
    nm=s.Name.decode('ascii','replace').rstrip('\x00'); lo=IB+s.VirtualAddress
    hi=lo+max(s.Misc_VirtualSize,s.SizeOfRawData); rl=s.PointerToRawData; rh=rl+s.SizeOfRawData
    SECS.append((nm,lo,hi,rl,rh))
def off_of(va):
    for n,lo,hi,rl,rh in SECS:
        if lo<=va<hi:
            o=rl+(va-lo)
            if o<rh: return o
    return None
def disasm(va,n):
    md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
    o=off_of(va)
    if o is None: return ''
    return '\n'.join(f'{i.address:08X}: {i.mnemonic} {i.op_str}' for i in md.disasm(DATA[o:o+n],va))
L=[]
def p(x=''): L.append(str(x))
# vtables: Bomb 0x7e3d10, Parasite 0x7ef890, RadSite 0x7f0810
CTORS={
 'BombClass': {'vt':0x7e3d10,'factory':0x438EAD,'ctor':0x410170,'imm':0x5c},
 'ParasiteClass': {'vt':0x7ef890,'factory':0x6C103C,'ctor':0x629210,'imm':0x58},
 'RadSiteClass': {'vt':0x7f0810,'factory':0x4691B3,'ctor':0x65B1E0,'imm':0x74},
}
for cls,d in CTORS.items():
    p(f'========== {cls} ==========')
    p(f'factory {hex(d["factory"])} imm={hex(d["imm"])} ctor {hex(d["ctor"])} expected_vt={hex(d["vt"])}')
    p(f'--- factory window ---')
    p(disasm(d['factory'],40))
    p(f'--- ctor window (first 96 bytes) ---')
    p(disasm(d['ctor'],96))
    p()
open(OUT,'w',encoding='utf-8').write('\n'.join(L))
print('wrote',OUT,len(L),'lines')
