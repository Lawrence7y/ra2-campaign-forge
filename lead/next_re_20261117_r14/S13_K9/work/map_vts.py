import sys,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
# Identify vtable boundaries: a vtable block ends where next slot is non-function or 0x00000000 or obvious data (floats)
# Examine region 0x7e17a0-0x7e18a0 slot by slot and mark .text targets
def cls(va):
    s=sec_of(va)
    return s
for base,end in [(0x7e17a0,0x7e18a0),(0x7e1e80,0x7e1f20),(0x7e4660,0x7e46c0)]:
    print('=== region',hex(base),hex(end),'===')
    for a in range(base,end,4):
        v=u32(a)
        tag = 'T' if v and sec_of(v)=='.text' else ('.' if v==0 else 'D')
        print(hex(a),'%08X'%v,tag)
