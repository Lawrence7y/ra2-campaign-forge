# -*- coding: utf-8 -*-
import struct,sys,collections
import pefile
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
PE=pefile.PE(EXE,fast_load=False); IB=PE.OPTIONAL_HEADER.ImageBase; DATA=PE.__data__
SECS=[]
for s in PE.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin1'); SECS.append((nm,s.VirtualAddress,s.Misc_VirtualSize,s.SizeOfRawData,s.PointerToRawData))
def va2off(va):
    r=va-IB
    for nm,va0,vs,rs,rp in SECS:
        if va0<=r<va0+rs: return rp+(r-va0)
def readva(va,n):
    o=va2off(va); return DATA[o:o+n] if o is not None else b''
def u32(va):
    b=readva(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
S01=['00409030','00409100','004091C0','004092F0','00409320','00409360','004093F0','00409880','00409C40','00409D90','00430250','0048C8B0','0048CCC0','004E2450','004E2460','004E24A0','004F1AA0','0052FC20','00554400','0055AF60','0055CFD0','0055D360','0055E420','0055F1E0','005A89D0','005B1D90','005B1E40','005CAF70','005CAFC0','005D2410','005D2530','005D5870','005D5880','005D5890','0063D810','00643E80','00646DF0','00647040','006470F0','006471A0','006521C0','006640E0','00697AD0','0069AE90','0069BAB0','006BB9A0','007240B0','007241A0','00724200','00732CA0','00734120','00734210','007CD80F']
TARGETS={int(x,16) for x in S01}
print('=== JUMP TABLE at 0x69B15C ===')
for i in range(4):
    v=u32(0x69B15C+i*4)
    print(f'  jt[{i}] @ 0x69B15C+{i*4} = {v:08X}' if v is not None else f'  jt[{i}] unreadable')
print('\n=== ECX/byte-match patterns in 0x69AE90 body ===')
body=readva(0x69AE90,713)
for pat,name in [(b'\x38\xb2\xa8\x00','imm 0xA8B238'),(b'\x30\xb2\xa8\x00','imm 0xA8B230')]:
    offs=[i for i in range(len(body)) if body.startswith(pat,i)]
    print(f'  {name}: offsets {[hex(0x69AE90+o) for o in offs]}')
print('\n=== ④ direct E8 calls (linear .text scan) ===')
TEXT_VA=0x401000; TEXT_RAW=[rp for nm,va0,vs,rs,rp in SECS if nm=='.text'][0]; TEXT_RSZ=[rs for nm,va0,vs,rs,rp in SECS if nm=='.text'][0]
tbuf=DATA[TEXT_RAW:TEXT_RAW+TEXT_RSZ]
callhits=collections.defaultdict(list)
for i in range(len(tbuf)-5):
    if tbuf[i]==0xE8:
        rel=struct.unpack('<i',tbuf[i+1:i+5])[0]
        site=TEXT_VA+i; tgt=(site+5+rel)&0xFFFFFFFF
        if tgt in TARGETS: callhits[tgt].append(site)
for x in S01:
    ev=int(x,16)
    if ev in callhits:
        print(f'  {x}: {len(callhits[ev])} raw E8 -> sites {[hex(s) for s in callhits[ev][:30]]}')
print('\n=== broad 4-byte VA occurrence across ALL sections (D-41 style) ===')
occ=collections.defaultdict(list)
for nm,va0,vs,rs,rp in SECS:
    blob=DATA[rp:rp+rs]
    for i in range(len(blob)-3):
        v=struct.unpack('<I',blob[i:i+4])[0]
        if v in TARGETS: occ[v].append(f'{nm}+{i:X}')
for x in S01:
    ev=int(x,16)
    print(f'  {x}: {len(occ[ev])} occurrences {occ[ev][:8]}')
