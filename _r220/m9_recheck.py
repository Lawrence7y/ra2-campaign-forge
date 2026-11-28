import sys,json,struct
from collections import Counter,defaultdict
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW; seg=P.B['.text']; lo=seg['lo']; rp=seg['rawptr']; rs=seg['rawsize']
mdl=Cs(CS_ARCH_X86,CS_MODE_32); mdl.detail=False; mdl.skipdata=True
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
OFFS=[0x77c,0x780,0x784,0x788,0x7a4,0x778,0x78c]
# ---- pass 1: resync sweep, collect candidate sites by raw disp check (fast) then detail decode
hits=defaultdict(list)
pos=rp; n=0
while pos<rp+rs:
    got=False
    for ins in mdl.disasm_lite(R[pos:pos+16], lo+(pos-rp)):
        got=True; n+=1; a=ins[0]
        if ins[2] in ('mov','call','jmp','cmp','fmul','fstp','lea','add','or','test','and'):
            hits[a]=ins
        break
    pos += ins[1] if got else 1
print("sweep instrs",n)
# detail decode the collected instruction bytes
cnt=defaultdict(lambda: defaultdict(int)); sites=defaultdict(lambda: defaultdict(list))
for a in hits:
    o=P.r2o(a)
    for i in md.disasm(R[o:o+16], a):
        mn=i.mnemonic; ops=i.operands
        for op in ops:
            if op.type==3 and op.mem.disp in OFFS and op.mem.base not in (0,) and op.mem.index==0:
                off=op.mem.disp
                kind='?'
                if mn=='mov' and len(ops)==2:
                    if ops[0].type==3 and ops[1].type in (1,2): kind='write_imm' if ops[1].type==2 else 'write_reg'
                    elif ops[0].type==2: kind='read_reg'
                    else: kind='read'
                elif mn in ('call','jmp'): kind='indirect_'+mn
                elif mn=='mov' and len(ops)==2 and ops[0].type==3 and ops[1].type==3: kind='write_mem'
                else: kind='other_'+mn
                cnt[off][kind]+=1; sites[off][kind].append((a,mn,i.op_str))
        break
for off in OFFS:
    c=cnt.get(off,{})
    print("off %#x: "%off, dict(c))
    # imm32 .text writes
    imm=[s for s in sites.get(off,{}).get('write_imm',[]) if s[2].split(', ')[-1].startswith('0x') and 0x401000<=int(s[2].split(', ')[-1],16)<0x801000]
    print("   imm32->.text writes:",len(imm),[hex(x[0]) for x in imm])
json.dump({hex(k):{kk:vv for kk,vv in v.items()} for k,v in cnt.items()},open('_r220/m9_counts.json','w'),indent=1)
json.dump({hex(k):{kk:[hex(x[0])+':'+x[2] for x in vv] for kk,vv in v.items()} for k,v in sites.items()},open('_r220/m9_sites.json','w'),indent=1)
