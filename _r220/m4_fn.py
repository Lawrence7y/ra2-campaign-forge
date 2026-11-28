import sys,struct,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW
seg=P.B['.text']; lo=seg['lo']; rp=seg['rawptr']; rs=seg['rawsize']
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False; md.skipdata=True
def find_start(va):
    o=P.r2o(va)
    # search backwards for >=2 consecutive 0xCC
    i=o-1
    while i>rp:
        if R[i]==0xCC and R[i-1]==0xCC:
            return lo+(i+1)-rp
        i-=1
    return None
def dis_range(start,end,cap=2000):
    o=P.r2o(start); n=end-start
    res=[]
    for ins in md.disasm_lite(R[o:o+n], start):
        res.append((ins[0],ins[2],ins[3]))
        if len(res)>=cap: break
    return res
targets=[0x7c742f,0x7c7432]
out={}
for t in targets:
    s=find_start(t)
    # find end: forward to next >=2 CC after a ret
    o=P.r2o(s); i=o
    end=None
    while i<rp+rs-1:
        if R[i]==0xC3 and R[i+1]==0xCC and R[i+2]==0xCC:
            end=lo+(i+1)-rp; break
        i+=1
    out[hex(t)]={'start':hex(s) if s else None,'end':hex(end) if end else None,
                 'len':(end-s) if end else None}
    if s: out[hex(t)]['ins']=dis_range(s,end)[:60]
json.dump(out,open('_r220/m4.json','w'),indent=1,default=str)
for k,v in out.items():
    print(k, v['start'], v['end'], v['len'])
    for i in v.get('ins',[]): print('   ',hex(i[0]),i[1],i[2])
