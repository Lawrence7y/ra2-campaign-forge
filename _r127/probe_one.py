import sys,os,bisect
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import tracer2 as TR
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
TX=S['.text']; T_LO=TX.VirtualAddress+IB
raw=pe.get_data(TX.VirtualAddress,TX.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
A=[a for a,m,o in ins]
def show(v,n):
    i=bisect.bisect_left(A,v)
    for j in range(i,i+n): print('   %x: %s %s'%ins[j])
print('=== pre-QI 4b62f0..4b6319');show(0x4b62f0,16)
i=[k for k,(a,m,o) in enumerate(ins) if a==0x4b630b]
print('--- trace after call ---')
r=TR.walk(ins, 0x3f42f+1, 120, seed_ppv=TR.qi_ppv_key(ins,0x3f42f))
print('pk=',TR.qi_ppv_key(ins,0x3f42f))
print('iat=',r['iatcalls'])
