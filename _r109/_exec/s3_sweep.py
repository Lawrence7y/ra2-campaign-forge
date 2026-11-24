import sys,struct,json,collections,time
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
import array

TL,TH=0x401000,0x7e1000
md=Cs(CS_ARCH_X86,CS_MODE_32)
CHUNK=0x10000
insn_addr=array.array('I'); insn_size=array.array('B')
rel_targets=set()      # E8/E9 rel32 targets
addr_list=[]           # instruction starts (python list, for bisect)
t0=time.time()
va=TL
while va<TH:
    end=min(va+CHUNK,TH)
    blob=rd(va,end-va)
    pos=0; n=len(blob)
    while pos<n:
        got=None
        for ins in md.disasm_lite(blob[pos:pos+16],va+pos):
            got=ins; break
        if got is None:
            pos+=1; continue
        a,sz,mn,op=got
        if sz==0: pos+=1; continue
        insn_addr.append(a); insn_size.append(sz); addr_list.append(a)
        if mn in ('call','jmp') and op and op[0] in '0123456789abcdef' and not op.startswith('0x'):
            pass
        pos+=sz
    va=end
print('insns',len(insn_addr),'time %.1fs'%(time.time()-t0))
# rel32 targets from raw bytes at instruction starts (E8/E9)
for idx,a in enumerate(insn_addr):
    o=foff(a)
    if o is None: continue
    b=_img[o]
    if b in (0xE8,0xE9) and insn_size[idx]==5:
        tgt=(a+5+struct.unpack('<i',_img[o+1:o+5])[0])&0xffffffff
        if TL<=tgt<TH: rel_targets.add(tgt)
    elif b==0x0f and insn_size[idx]==6:
        b2=_img[o+1]
        if 0x80<=b2<=0x8f:
            tgt=(a+6+struct.unpack('<i',_img[o+2:o+6])[0])&0xffffffff
            if TL<=tgt<TH: rel_targets.add(tgt)
print('rel targets',len(rel_targets))
json.dump(dict(n_insn=len(insn_addr)),open('_r109/_exec/_sweepstat.json','w'))
arr=array.array('I'); arr.fromlist(addr_list)
with open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_insn.bin','wb') as f:
    f.write(arr.tobytes()); f.write(insn_size.tobytes())
with open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_reltgt.bin','wb') as f:
    f.write(array.array('I',sorted(rel_targets)).tobytes())
print('written')
