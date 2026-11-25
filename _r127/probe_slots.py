import bisect,collections,struct
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
G={0x7f7c70:'109.r',0x818858:'109.d',0x7f7c80:'10C.r',0x820270:'10C.d'}
print('NOTE mapping placeholder: 0x7f7c70=0000010C, 0x7f7c80=00000109')
G={0x7f7c70:'010C.r',0x818858:'010C.d',0x7f7c80:'0109.r',0x820270:'0109.d'}
sites=[]
for i,(a,m,o) in enumerate(ins):
    if m=='push' and num(o) in G:
        sites.append(i)
print('sites',len(sites))
res=[]
for i in sites:
    g=G[num(ins[i][2])]
    # expect: push ppv ; call [reg + 0]
    shape=None; ppv_slot=None
    if i+2<len(ins) and ins[i+1][1]=='push' and ins[i+2][1]=='call':
        shape='push/push/call'
        prev=ins[i-1]
        if prev[1]=='lea' and '[esp + ' in prev[2]:
            ppv_slot=num(prev[2].split('[esp + ')[1].rstrip(']'))
        elif prev[1]=='lea' and prev[2].startswith('edx') is False:
            pass
    res.append((g,hex(ins[i][0]),shape,ppv_slot,ins[i+2][2] if i+2<len(ins) else None))
for r in res[:10]: print(r)
cnt=collections.Counter(r[0] for r in res); print(cnt)
cnt2=collections.Counter((r[0],r[2]) for r in res); print(cnt2)
