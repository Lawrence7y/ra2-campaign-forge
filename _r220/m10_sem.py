import sys,json,struct
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False; md.skipdata=True
def dis(start,n=40):
    o=P.r2o(start); out=[]
    for i in md.disasm_lite(R[o:o+n*8], start):
        out.append((hex(i[0]),i[2],i[3]))
        if len(out)>=n: break
    return out
# 1. IMA table VA
fo=0x4758e4
for s in P.SECS:
    if s['rawptr']<=fo<s['rawptr']+s['rawsize']:
        print("IMA table at file 0x%x -> section %s VA %#x"%(fo,s['name'],s['lo']+(fo-s['rawptr'])))
# 2. callers of 0x7c7371
for c in (0x7c24a2,0x7c2557):
    print("--- caller ctx",hex(c))
    for t in dis(c-24,22): print("   ",t)
# 3. callers of 0x7c7350
print("--- caller of 0x7c7350 @0x7c2a74")
for t in dis(0x7c2a50,14): print("   ",t)
# 4. what strings/data near 0x87bd90 region end + what's at 0x87bd90+0x100
o=P.r2o(0x87bd90)
print("87bd90..+0x120 every16:",[R[o+i] for i in range(0,0x120,0x10)])
print("after:",R[o+0x120:o+0x160].hex())
# 5. twin table extent confirm: 0x879b30 size until next thing (find 0x879b30+? where bytes stop)
o2=P.r2o(0x879b30)
print("0x879b30 prev 16:",R[o2-16:o2].hex())
print("0x879b30 +4828:",R[o2+4828:o2+4828+48].hex())
print("what is 0x879b30+0x1300 (4864):",R[o2+0x1300:o2+0x1340].hex())
# 6. section of 0x87b170 and 0x879b30 and 0x87bd90
for va in (0x876ff4,0x879b30,0x87b170,0x87bd90,0x87c484):
    print(hex(va),P.where(va))
