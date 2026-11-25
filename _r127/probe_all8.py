import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import tracer2 as TR
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
TX=S['.text']; T_LO=TX.VirtualAddress+IB
raw=pe.get_data(TX.VirtualAddress,TX.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
idx={a:i for i,(a,m,o) in enumerate(ins)}
GSET={0x7f7c70:'010C.r',0x818858:'010C.d',0x7f7c80:'0109.r',0x820270:'0109.d'}
for i,(a,m,o) in enumerate(ins):
    if m!='push': continue
    t=TR.num(o)
    if t not in GSET or GSET[t]!='0109.d': continue
    ic=None
    for d in (2,3):
        if i+d<len(ins) and ins[i+d][1]=='call' and ins[i+d][2].startswith('dword ptr [e'):
            ic=i+d; break
    pk=TR.qi_ppv_key(ins,ic)
    r=TR.walk(ins,ic+1,120,seed_ppv=pk)
    hits=[(hex(a2),hex(v),q) for a2,v,q in r['iatcalls'] if v==0x7e15f4]
    print('%x ic=%x pk=%s trunc=%s hits=%s'%(a,ins[ic][0],pk,r['truncated'],hits))
