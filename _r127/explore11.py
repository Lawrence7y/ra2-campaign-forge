import struct,json,collections,bisect,re
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
idx={a:i for i,(a,m,o) in enumerate(ins)}
def num(t):
    t=t.strip()
    if t and t[0] in '0123456789':
        try: return int(t,0)
        except ValueError: pass
    return None
def show(site,span=70):
    i=idx[site]; out=[]
    for j in range(i,min(len(ins),i+span)):
        a,m,o=ins[j]
        if m.startswith('call') or m.startswith('j') or m in ('mov','lea','test','cmp'):
            out.append('%x: %s %s'%(a,m,o))
        if m=='ret': out.append('%x: ret'%a); break
    print('--- site %x'%site)
    for l in out: print('   ',l)
for s in [a for a,m,o in ins if m=='push' and num(o) in (0x818858,0x820270)]:
    show(s)
