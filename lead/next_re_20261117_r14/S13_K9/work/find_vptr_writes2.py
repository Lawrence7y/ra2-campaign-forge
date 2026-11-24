# examine cited evidence and search all C7 05 writes with vt-like imm in .rdata
import sys,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
from capstone import *
print('=== bytes at 0x438560 ===')
b=rd(0x438560,32); print(b.hex() if b else None)
md=Cs(CS_ARCH_X86,CS_MODE_32)
for i in md.disasm(rd(0x438560,48),0x438560):
    print(hex(i.address),i.mnemonic,i.op_str,i.bytes.hex())
print('=== search C7 05 <g> <imm> where imm in .rdata 0x7e1000-0x810000 ===')
cnt=0
hits=[]
for n,v,vs,pr,rs in SECS:
    if n!='.text': continue
    start=pr; end=pr+min(vs,rs)
    i=DATA.find(b'\xc7\x05',start,end)
    while i!=-1 and i+10<=end:
        g,imm=struct.unpack('<II',DATA[i+2:i+10])
        if 0x7e1000<=imm<0x810000:
            hits.append((IB+v+(i-pr),g,imm))
        i=DATA.find(b'\xc7\x05',i+1,end)
print('total C7 05 .rdata-immediate writes',len(hits))
for h in hits[:60]: print(hex(h[0]),'global',hex(h[1]),'vt',hex(h[2]))
