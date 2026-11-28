import sys,json,struct
from collections import Counter,defaultdict
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW; seg=P.B['.text']; lo=seg['lo']; rp=seg['rawptr']; rs=seg['rawsize']
mdl=Cs(CS_ARCH_X86,CS_MODE_32); mdl.detail=False; mdl.skipdata=True
TARGETS={0x8758e4:'IMA_STEP',0x87b170:'TAB162',0x879b30:'DELTA',0x87bd90:'DITHER',0x876ff4:'TAB162_DUP',0x87c484:'DISPATCH'}
hits=defaultdict(list)
pos=rp
while pos<rp+rs:
    got=False
    for ins in mdl.disasm_lite(R[pos:pos+16], lo+(pos-rp)):
        got=True
        for t in TARGETS:
            if ('%x'%t) in ins[3]: hits[t].append((ins[0],ins[2],ins[3]))
        break
    pos += ins[1] if got else 1
for t,name in TARGETS.items():
    print(name,hex(t),"refs",len(hits[t]), [hex(a) for a,_,_ in hits[t][:6]])
# who references IMA step table => is the cluster audio?
# also test: does 0x879b30 equal a 16-point/8-point DCT kernel? compare to int(cos*scale)
import math
vals=struct.unpack_from('<16i',R,P.r2o(0x879b30))
print("first16:",vals)
for scale in (16,32,64,128,256):
    for k in range(1,9):
        model=[round(scale*math.cos(math.pi*(2*i+1)*k/16)) for i in range(8)]
        if model[:8]==list(vals[:8]): print("DCT match scale",scale,"k",k)
print("vals[0:8] as ratio of 1,3,5,7 ->",[v for v in vals[:8]])
# check IMA usage neighbors: function starts near 0x7c8110 and what 0x7c8d20 is (527 callers)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False; md.skipdata=True
def dis(start,n=30):
    o=P.r2o(start); out=[]
    for i in md.disasm_lite(R[o:o+n*8], start):
        out.append((hex(i[0]),i[2],i[3]))
        if len(out)>=n: break
    return out
for f in (0x7c8110,0x7c8d20):
    print("--- fn",hex(f))
    for t in dis(f,18): print("   ",t)
