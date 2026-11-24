"""Task B: who writes 0x87F778+0x10 Count / +4 Items? Task D: 0x55B8F0 pointers/push."""
import os,re,struct,json
import pefile
R=r"D:\Project\ra2-campaign-forge"
BIN=os.path.join(R,'ra2youli','gamemd.exe')
EV=os.path.join(R,'lead','next_re_20261116_r12','W160_aidispatch','EVIDENCE')
pe=pefile.PE(BIN,fast_load=True)
ts=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text')
base=0x400000+ts.VirtualAddress
data=open(BIN,'rb').read(); blob=data[ts.PointerToRawData:ts.PointerToRawData+ts.SizeOfRawData]
lines=open(os.path.join(EV,'W160_whole_text_disasm.tsv'),encoding='utf-8').read().splitlines()
# all code refs to logic globals with immediate addressing
for target in [0x87F778,0x87F77C,0x87F780,0x87F788,0x87F78C]:
    needle=struct.pack('<I',target)
    raw=[base+i for i in range(len(blob)-4) if blob[i:i+4]==needle]
    print(f'\nVA {target:08X}: {len(raw)} raw imm refs')
    for va in raw[:30]:
        L=[l for l in lines if l.startswith(f'{va:08X}\t')]
        print('  ',L[0] if L else hex(va))
# any literal 0x55B8F0 anywhere in the file (all sections), including unaligned
needle=struct.pack('<I',0x55B8F0)
occ=[i for i in range(len(data)-4) if data[i:i+4]==needle]
print('\n0x55B8F0 dword occurrences in entire file:',[hex(i) for i in occ[:40]],'n=',len(occ))
# push 0x55b8f0 pattern (68 f0 b8 55 00)
pat=b'\x68\xf0\xb8\x55\x00'
print('push 0x55B8F0 occurrences:',[hex(base+i) for i in range(len(blob)) if blob.startswith(pat,i)])
