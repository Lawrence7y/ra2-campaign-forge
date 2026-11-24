# For each of the 8 container vtable families, enumerate ALL C7 05 writes of ANY of its 3 variants
# Variants differ by +0x20 (D0/D1/D2) typically; find globals, then exact call sites on those globals.
import sys,struct,json
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
# base vtables (constructor-written variants) containing our entries
# 0x40B880/930 family: 0x7E17CC (slot2/4), 0x7E17EC (slot2=0x40B740) ... need all 3
FAMILIES={
 'F1_40B':[0x7e17ac,0x7e17cc,0x7e17ec,0x7e180c],
 'F2_40F7':[0x7e1e84,0x7e1ea4],
 'F3_40FD':[0x7e1ed4,0x7e1ef4],
 'F4_46B7':[0x7e4678,0x7e4698],
 'F5_62B2':[0x7ef824,0x7ef844],
 'F6_65C0':[0x7f07a4,0x7f07c4],
}
ENTRIES={0x40b880:'slot2@F1',0x40b930:'slot4@F1',0x40f7c0:'slot2@F2',0x40fd90:'slot2@F3',0x40fe40:'slot4@F3',0x46b7e0:'slot2@F4',0x46b890:'slot4@F4',0x62b250:'slot2@F5',0x62b300:'slot4@F5',0x65c0d0:'slot2@F6',0x65c180:'slot4@F6'}
# find all C7 05 writes of these vtable addresses
VT2G={}
for fam,vts in FAMILIES.items():
    for vt in vts:
        for n,v,vs,pr,rs in SECS:
            if n!='.text':continue
            end=pr+min(vs,rs);i=DATA.find(b'\xc7\x05',pr,end)
            while i!=-1 and i+10<=end:
                g,imm=struct.unpack('<II',DATA[i+2:i+10])
                if imm==vt:
                    VT2G.setdefault(vt,[]).append((hex(IB+v+(i-pr)),hex(g)))
                i=DATA.find(b'\xc7\x05',i+1,end)
for fam,vts in FAMILIES.items():
    print('===',fam,'===')
    for vt in vts:
        print(' vt',hex(vt),'slots2/4',hex(u32(vt+8)),hex(u32(vt+0x10)),'writes',VT2G.get(vt,[]))
