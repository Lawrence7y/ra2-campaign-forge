import struct,collections
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
MARK=[0x7e36c0,0x7e9b20,0x7e9b40,0x414290,0x410260,0x4d0510]
for t in MARK:
    refs=collections.defaultdict(list)
    for a,m,o in ins:
        if m in ('call','jmp') and num(o)==t: refs[m].append(a)
        elif m=='push' and num(o)==t: refs['push'].append(a)
        elif '0x%x'%t in o and m not in ('call','jmp','push'): refs['other:'+m].append(a)
    print('==',hex(t), {k:(len(v),[hex(x) for x in v[:8]]) for k,v in refs.items()})
def dump(start,n=45):
    i=idx.get(start)
    if i is None:
        print('   not aligned'); return
    for j in range(i,min(len(ins),i+n)):
        print('   %x: %s %s'%ins[j])
print('=== 0x7e36c0'); dump(0x7e36c0)
print('=== 0x7e9b20'); dump(0x7e9b20)
