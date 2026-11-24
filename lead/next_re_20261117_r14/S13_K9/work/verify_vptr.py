# For each exact call site on family globals, determine the vptr value at the vptr_load
# by tracing C7 05 writes to that global and nearest preceding write (static dataflow within same function).
import sys,struct,json
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
from capstone import *
from capstone.x86 import *
# list ALL C7 05 writes to the 8 family globals with their vtable, and full slot2/slot4 values
FAMG={'0x87f5d8':('F1a',0x7e17cc), '0x89c668':('F1b',0x7e17cc), '0x8874c0':('F2',0x7e1e84), '0x887568':('F3',0x7e1ed4), '0x89de18':('F4a',0x7e4678), '0xa8ed40':('F4b',0x7e4678), '0xac4910':('F5',0x7ef824), '0xb04bd0':('F6',0x7f07a4)}
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
print('=== all C7 05 [family global], vt writes (both D1 and D2 variants) ===')
for ghex,(fam,basevt) in FAMG.items():
    g=int(ghex,16)
    print(fam,'global',ghex,'D1 vt',hex(basevt),'D1 slot2',hex(u32(basevt+8)),'D1 slot4',hex(u32(basevt+0x10)),
          'D2 vt',hex(basevt+0x20),'D2 slot4',hex(u32(basevt+0x20+0x10)))
    # scan raw for writes to g
    pat=b'\xc7\x05'+struct.pack('<I',g)
    for n,v,vs,pr,rs in SECS:
        if n!='.text':continue
        end=pr+min(vs,rs);i=DATA.find(pat,pr,end)
        while i!=-1 and i+10<=end:
            imm=struct.unpack('<I',DATA[i+6:i+10])[0]
            slot2=u32(imm+8) if imm else None; slot4=u32(imm+0x10) if imm else None
            print('   write@',hex(IB+v+(i-pr)),'vt',hex(imm),'slot2',hex(slot2) if slot2 else None,'slot4',hex(slot4) if slot4 else None)
            i=DATA.find(pat,i+1,end)
