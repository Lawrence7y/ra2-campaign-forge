import sys,struct
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False; md.skipdata=True
def dis(a,n=20):
    o=P.r2o(a); out=[]
    for i in md.disasm_lite(R[o:o+n*8], a):
        out.append((hex(i[0]),i[2],i[3]))
        if len(out)>=n: break
    return out
print("--- 0x7cdcf0..0x7cde60")
for t in dis(0x7cdcf0,90): print("   ",t)
# 12-byte records from 0x87c480
for k in range(7):
    b=0x87c480+k*12
    print("rec%d base %#x: name=%#x field1=%#x func=%#x  (%s / %s)"%(
      k,b,P.dw(b),P.dw(b+4),P.dw(b+8),P.cstr(P.dw(b),24),P.where(P.dw(b+4))))
print("bound 0x87c4c0 - 0x87c480 =",0x87c4c0-0x87c480,"/12 =",(0x87c4c0-0x87c480)/12)
