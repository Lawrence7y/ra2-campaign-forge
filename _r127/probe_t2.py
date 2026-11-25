import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import tracer2 as T
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
TX=S['.text']; T_LO=TX.VirtualAddress+IB
raw=pe.get_data(TX.VirtualAddress,TX.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
idx={a:i for i,(a,m,o) in enumerate(ins)}
IAT={0x7e15f4:'OleSaveToStream',0x7e15f8:'OleLoadFromStream'}
G={0x7f7c70:'010C.r',0x818858:'010C.d',0x7f7c80:'0109.r',0x820270:'0109.d'}
for i,(a,m,o) in enumerate(ins):
    if m=='push' and T.num(o) in G and ins[i+1][1]=='push' and ins[i+2][1]=='call':
        ic=i+2
        r=T.walk(ins, ic+1, 120)
        print('%-7s %x slots=%s iat=%s trunc=%s steps=%d states=%d'%(
            G[T.num(o)],a,sorted(hex(x) for x in r['slots']),
            [(hex(x),IAT.get(v,hex(v))) for x,v in r['iatcalls']][:3],
            r['truncated'],r['steps'],r['states']))
