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
A=[a for a,m,o in ins]; idx={a:i for i,(a,m,o) in enumerate(ins)}
def show(v,n):
    i=bisect.bisect_left(A,v)
    for j in range(i,i+n): print('   %x: %s %s'%ins[j])
# 0x6cf478 accepts IID 0x7e9b20 (ISwizzle) and 0x7f7c90 (IUnknown) -> but 0x7e9b20 not IID of ISwizzle?
# Check: which IIDs does the QI body at 0x6cf430 compare? and 0x429270/0x429360?
print('=== 0x429270 body (TiberianSunClassFactory +0xc)');show(0x429270,54)
