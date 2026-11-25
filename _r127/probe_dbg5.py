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
ic=idx[0x4af6ab]
print('ic=',ic,'ins=',ins[ic])
# replicate walk with tracing
i0=ic+1
lo,hi=i0,min(len(ins),i0+150)
work=[(i0,0,{'eax':('Q',)},{12:('Q',)},0)]
seen=set()
for step in range(400):
    if not work: print('work empty'); break
    pc,dsp,reg,stk,nargs=work.pop()
    a,m,o=ins[pc]
    # manual single step print
    print('%x %s %s | dsp=%d nargs=%d regs=%s'%(a,m,o,dsp,nargs,{k:v for k,v in reg.items() if v in (('Q',),('VT',))}))
    r=T.walk  # unused
    break
