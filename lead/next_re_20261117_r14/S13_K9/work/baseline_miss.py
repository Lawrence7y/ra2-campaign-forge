# Check the 3 missed entries (slot6/slot1) for exact bindings + baseline test
import sys,struct,json,re,random
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
ENTRIES={0x40b880,0x40b930,0x40f7c0,0x40fd90,0x40fe40,0x46b7e0,0x46b890,0x62b250,0x62b300,0x65c0d0,0x65c180}
MISS={0x48ad60:'slot6',0x54e8e0:'slot6',0x48ad70:'slot1'}
T0,T1=text_range();o=va2off(T0);text=DATA[o:o+(T1-T0)]
def va(p):return T0+p
# collect C7 05 writes
GVT={}
for m in re.finditer(b'\xc7\x05',text):
    p=m.start()
    if p+10>len(text):continue
    g,vt=struct.unpack_from('<II',text,p+2)
    if 0x7e1000<=vt<0x810000:GVT.setdefault(g,set()).add(vt)
# For each target entry, find vtable written to global with entry at some slot, then exact call at that slot
def exact_for(target):
    out=[]
    for G,vts in GVT.items():
        gp=struct.pack('<I',G)
        for vt in vts:
            for slotb in range(0,0x20,4):
                if u32(vt+slotb)!=target:continue
                # find call [reg+disp] where disp==slotb and mov ecx,G within 16 bytes of a mov reg,[G]
                loadseqs=[(b'\x8b\x15'+gp,b'\xff\x52'),(b'\xa1'+gp,b'\xff\x50'),(b'\x8b\x0d'+gp,b'\xff\x51')]
                for ls,cp in loadseqs:
                    for lm in re.finditer(re.escape(ls),text):
                        p=lm.start();chunk=text[p:p+28]
                        for cm in re.finditer(re.escape(cp),chunk):
                            if chunk[cm.start()+2]!=slotb:continue
                            near=text[max(0,p-16):min(len(text),p+28)]
                            if b'\xb9'+gp not in near and b'\x8d\x0d'+gp not in near and b'\xba'+gp not in near:
                                # allow mov edx,G (BA) too
                                continue
                            out.append((hex(va(p+cm.start())),hex(G),hex(vt),slotb//4,ls[:2].hex()))
    return sorted(set(out))
print('=== 3 missed entries exact check ===')
for e,n in MISS.items():
    r=exact_for(e)
    print(hex(e),n,'exact hits',len(r))
    for x in r[:10]:print('  ',x)
# For the 11 entries, per-entry call site count
print('=== 11 entries exact call-site counts ===')
tot=0
for e in sorted(ENTRIES):
    r=exact_for(e);tot+=len(r)
    print(hex(e),len(r))
print('sum call sites (with dedupe by entry+site)',tot)
# baseline: random 11 distinct .text addresses aligned 16 that are NOT in our set / not vtable slot values
# criterion: same exact_for(e) > 0
allvt=set()
for vts in GVT.values():
    for vt in vts:
        for s in range(0,0x20,4):
            v=u32(vt+s)
            if v and T0<=v<T1:allvt.add(v)
random.seed(1337)
cands=[a for a in range(T0+0x100,T1-0x100,16) if a not in ENTRIES and a not in MISS]
base_hits=0;base_detail=[]
for e in random.sample(cands,11):
    r=exact_for(e)
    if r:base_hits+=1;base_detail.append((hex(e),r))
print('BASELINE random 11 entries, false hits',base_hits,'detail',base_detail)
