import sys,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
def dump(va,n=80):
    b=rd(va,n)
    for i in range(0,len(b),16):
        c=b[i:i+16]
        vals=[struct.unpack('<I',c[j:j+4])[0] for j in range(0,len(c)-3,4)]
        print(hex(va+i),' '.join('%08X'%v for v in vals))
for a in [0x7e17cc,0x7e17ac,0x7e17ec,0x7e1ea4,0x7e1ed4,0x7e1ef4,0x7fc6c8]:
    print('===',hex(a),'===');dump(a,48)
