import bisect,collections
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
A=[a for a,m,o in ins]; idx={a:i for i,(a,m,o) in enumerate(ins)}
def num(t):
    t=t.strip()
    if t and t[0] in '0123456789':
        try: return int(t,0)
        except ValueError: pass
    return None
IAT={}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in e.imports:
        IAT[imp.address]=(e.dll.decode(), imp.name.decode() if imp.name else 'ord%d'%imp.ordinal)
G={0x7f7c70:'10C.r',0x818858:'10C.d',0x7f7c80:'109.r',0x820270:'109.d'}
sites=[(i,a,m,o) for i,(a,m,o) in enumerate(ins) if m=='push' and num(o) in G]
print('push sites:',len(sites))
def window(i,n=46):
    return [(j,)+ins[j] for j in range(i,min(len(ins),i+n))]
for i,a,m,o in sites[:3]:
    print('=== site %x %s'%(a,G[num(o)]))
    for j,aj,mj,oj in window(i,14):
        print('   %x: %s %s'%(aj,mj,oj))
