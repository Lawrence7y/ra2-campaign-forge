# dump rdata around vtable for entry 0x40B880 (vt=0x7e17d4)
import sys,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
def dump(va,n=160):
    b=rd(va,n)
    for i in range(0,len(b),16):
        chunk=b[i:i+16]
        vals=[struct.unpack('<I',chunk[j:j+4])[0] for j in range(0,len(chunk)-3,4)]
        print(hex(va+i),' '.join('%08X'%v for v in vals), repr(chunk))
print('=== around 0x7e17d4 ===')
dump(0x7e17d4-64,224)
print('=== around 0x7e4680 ===')
dump(0x7e4680-64,224)
print('=== find COL pattern: dword at vt-4 should point into .rdata (0x7e1000-0x810000) ===')
for vt in [0x7e17d4,0x7e17dc,0x7e1e8c,0x7e4680,0x7e515c,0x7e5148]:
    print(hex(vt),'vt[-4]=',hex(u32(vt-4)),'vt[-8]=',hex(u32(vt-8)),'vt[-0xC]=',hex(u32(vt-0xc)))
