import sys,struct,json
from collections import Counter
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW; seg=P.B['.text']; lo=seg['lo']; rp=seg['rawptr']; rs=seg['rawsize']
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False; md.skipdata=True
# full-text resync sweep, collect E8 rel32 targets
e8=Counter(); sites={}
pos=rp; end=rp+rs; n=0
while pos<end:
    got=False
    for ins in md.disasm_lite(R[pos:pos+16], lo+(pos-rp)):
        got=True; n+=1
        a,mn,op=ins[0],ins[2],ins[3]
        if mn=='call' and op and not op.startswith(('dword','word','qword','byte')):
            try: t=int(op,16)
            except: t=None
            if t is not None:
                e8[t]+=1; sites.setdefault(t,[]).append(a)
        break
    pos += ins[1] if got else 1
print("instrs",n,"distinct E8 targets",len(e8))
# candidates near 0x7c7350..0x7c7400
cand=sorted([(t,c) for t,c in e8.items() if 0x7c7300<=t<0x7c7450])
print("E8 targets in 0x7c7300..0x7c7450:",[(hex(t),c) for t,c in cand])
# candidates for the table-reading function region
cand2=sorted([(t,c) for t,c in e8.items() if 0x7c8c00<=t<0x7c8e00])
print("E8 targets 0x7c8c00..0x7c8e00:",[(hex(t),c) for t,c in cand2])
# 0x4a1ca0 callers
print("E8 to 0x4a1ca0:",e8.get(0x4a1ca0),"first10",[hex(x) for x in sites.get(0x4a1ca0,[])[:10]])
json.dump({'n':n,'e8_7c73':[[hex(t),c] for t,c in cand],'e8_7c8c':[[hex(t),c] for t,c in cand2],
 'crc_sites':[hex(x) for x in sites.get(0x4a1ca0,[])],'crc_n':e8.get(0x4a1ca0,0)},
 open('_r220/m5.json','w'),indent=1)
