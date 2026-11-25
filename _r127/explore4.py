import struct,collections
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=S['.text']; T_LO=T.VirtualAddress+IB; T_HI=T_LO+T.Misc_VirtualSize
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
print('ins',len(ins))
def num(t):
    t=t.strip()
    if t and t[0] in '0123456789':
        try: return int(t,0)
        except ValueError: pass
    return None
TARGETS={0x7f7c70:'10C.rdata',0x818858:'10C.data',0x7f7c80:'109.rdata',0x820270:'109.data',
         0x7f7c90:'000.rdata',0x7f7ca0:'001.rdata'}
sites=collections.defaultdict(list)
for a,m,o in ins:
    for t in TARGETS:
        if ('0x%x'%t) in o.split(',')[-1] or o.endswith('0x%x'%t):
            sites[t].append((a,m,o))
for t,lab in TARGETS.items():
    print('==',hex(t),lab,len(sites[t]))
    for a,m,o in sites[t][:20]:
        print('   %x: %s %s'%(a,m,o))
