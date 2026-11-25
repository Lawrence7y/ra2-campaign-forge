import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import tracer, collections
import pefile, capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
idx={a:i for i,(a,m,o) in enumerate(ins)}
def num(t): return tracer.num(t)
G={0x7f7c70:'010C.r',0x818858:'010C.d',0x7f7c80:'0109.r',0x820270:'0109.d'}
IAT={}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in e.imports:
        IAT[imp.address]=imp.name.decode() if imp.name else '?'
for i,(a,m,o) in enumerate(ins):
    if m=='push' and num(o) in G:
        if not (ins[i+1][1]=='push' and ins[i+2][1]=='call'): continue
        icall=i+2
        ppv=tracer.find_ppv_slot(ins,icall)
        s=tracer.Sim(ins,icall+1,limit=90).run('QI')
        vc=[e for e in s.events if e[1]=='vcall']
        iat=[(hex(e[0]),IAT.get(e[2],hex(e[2]))) for e in s.events if e[1]=='iatcall']
        st=[(hex(e[0]),e[2]) for e in s.events if e[1]=='stkslot' and e[2]==ppv]
        print('%-7s %x ppv=%s vcall=%s iat=%s ppvwrite=%s'%(G[num(o)],a,ppv,
              [(hex(e[0]),hex(e[2]),e[3]) for e in vc][:5], iat[:3], st[:2]))
