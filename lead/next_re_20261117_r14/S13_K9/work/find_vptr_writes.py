# find vptr write sites: mov dword [global], vt  (C7 05 <addr32> <vt32>)
import sys,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *

VTS=[0x7e17d4,0x7e17dc,0x7e1e8c,0x7e1edc,0x7e1ee4,0x7e4680,0x7e4688,0x7ef82c,0x7ef834,0x7f07ac,0x7f07b4,0x7e515c,0x7e5188,0x7ece94,0x7eceb4,0x7e5148,0x7e5174]
# all possible 8-slot vtables containing each entry; plus all vts with first slot=entry
print('=== search raw bytes: C7 05 <global> <vt> for each vt ===')
for vt in VTS:
    pat=b'\xc7\x05'+struct.pack('<II',0,vt)  # global unknown - can't use exact pattern
    # instead scan for C7 05 anywhere then check imm32 == vt
    hits=[]
    for n,v,vs,pr,rs in SECS:
        if n!='.text': continue
        start=pr; end=pr+min(vs,rs)
        i=DATA.find(b'\xc7\x05',start,end)
        while i!=-1:
            if i+10<=end:
                g,imm=struct.unpack('<II',DATA[i+2:i+10])
                if imm==vt:
                    hits.append((IB+v+(i-pr),hex(g)))
            i=DATA.find(b'\xc7\x05',i+1,end)
    print(hex(vt),'C7 05 writes:',hits[:20], 'count',len(hits))
