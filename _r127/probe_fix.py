import sys,os,struct,bisect,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import tracer2 as TR
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
TX=S['.text']; T_LO=TX.VirtualAddress+IB
raw=pe.get_data(TX.VirtualAddress,TX.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
A=[a for a,m,o in ins]; idx={a:i for i,(a,m,o) in enumerate(ins)}
def show(v,n):
    i=bisect.bisect_left(A,v)
    for j in range(i,i+n): print('   %x: %s %s'%ins[j])
print('--- 0x69ed90 area ---'); show(0x69ed90,30)
GSET={0x7f7c70:'010C.r',0x818858:'010C.d',0x7f7c80:'0109.r',0x820270:'0109.d'}
c=collections.Counter(); shapes=collections.Counter()
for i,(a,m,o) in enumerate(ins):
    if m=='push' and TR.num(o) in GSET:
        c[GSET[TR.num(o)]]+=1
        for d in range(2,6):
            if i+d<len(ins) and ins[i+d][1]=='call':
                shapes[(GSET[TR.num(o)],d)]+=1; break
        else: shapes[(GSET[TR.num(o)],'none')]+=1
print('push counts',dict(c))
print('shapes',dict(shapes))
