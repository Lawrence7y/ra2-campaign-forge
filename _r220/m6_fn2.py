import sys,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False; md.skipdata=True
def dis(start,end,cap=4000):
    o=P.r2o(start); res=[]
    for ins in md.disasm_lite(R[o:o+(end-start)], start):
        res.append((ins[0],ins[2],ins[3]))
        if len(res)>=cap: break
    return res
# function 0x7c7371 .. next >=2CC
start=0x7c7371
o=P.r2o(start); i=o
while True:
    if R[i]==0xC3 and R[i+1]==0xCC and R[i+2]==0xCC: end=(i+1); break
    i+=1
end=P.B['.text']['lo']+(end-P.B['.text']['rawptr'])
ins=dis(start,end)
print("fn 0x7c7371 end",hex(end),"ins",len(ins))
# find the table usage block
for k,(a,m,op) in enumerate(ins):
    if '0x879b30' in op or '0x87b170' in op or '0x7c7778' in op:
        print("HIT",hex(a),m,op)
# print region 0x7c7417..0x7c7470
for a,m,op in ins:
    if 0x7c7415<=a<=0x7c7470: print(hex(a),m,op)
json.dump({'start':hex(start),'end':hex(end),'n':len(ins)},open('_r220/m6.json','w'))
