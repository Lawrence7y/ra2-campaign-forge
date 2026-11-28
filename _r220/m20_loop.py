import sys,struct
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False; md.skipdata=True
def dis(a,n=40):
    o=P.r2o(a); out=[]
    for i in md.disasm_lite(R[o:o+n*8], a):
        out.append((hex(i[0]),i[2],i[3]))
        if len(out)>=n: break
    return out
print("--- 0x7cdca0..0x7cdd10 (loop head)")
for t in dis(0x7cdca0,40): print("   ",t)
print("--- 0x7cdda6..0x7cde50")
for t in dis(0x7cdda6,60): print("   ",t)
