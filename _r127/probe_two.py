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
for addr in (0x4b6319,0x5046a4):
    ic=idx[addr]
    pk=TR.qi_ppv_key(ins,ic)
    r=TR.walk(ins,ic+1,120,seed_ppv=pk)
    print(hex(addr),'pk=',pk,'iat=',[(hex(a),hex(v),q) for a,v,q in r['iatcalls']][:5])
