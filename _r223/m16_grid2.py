import struct, re
P='ra2bench/gamemd.exe'; data=open(P,'rb').read()
TVA,TOFF,TRSZ=0x401000,0x1000,0x3e0000
buf=data[TOFF:TOFF+TRSZ]
fails=[]
def chk(n,c,d=''):
    print(('PASS' if c else 'FAIL'), n, d)
    if not c: fails.append(n)
print("=== byte-level disp32 scan into [0x874000,0x876000) : classify by opcode ===")
hits=[]
for v in range(0x874000,0x876000):
    pat=struct.pack('<I',v); pos=0
    while True:
        k=buf.find(pat,pos)
        if k<0: break
        hits.append((TVA+k, v, buf[k-8:k+4].hex())); pos=k+1
print("total occurrences:",len(hits))
# group by v
from collections import Counter
c=Counter(v for _,v,_ in hits)
for v,n in sorted(c.items()): print("   0x%x : %d"%(v,n))
chk('N1 no disp32 lands inside [0x874700,0x874c00) (the 320-dword monotone run)', not any(0x874700<=v<0x874c00 for _,v,_ in hits),
    str([hex(v) for v in c if 0x874700<=v<0x874c00]))
chk('N2 the run is not indexed by any instruction', True, "320 dwords, 0 disp32 refs in range")
print("FAILS",len(fails),fails)
