import struct,collections
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
def num(t):
    t=t.strip()
    if t and t[0] in '0123456789':
        try: return int(t,0)
        except ValueError: pass
    return None
GUID={0x7f7c70:'10C.r',0x818858:'10C.d',0x7f7c80:'109.r',0x820270:'109.d'}
def back(a,limit=40):
    out=[]
    for j in range(len(ins)):
        pass
    return out
byaddr={a:i for i,(a,m,o) in enumerate(ins)}
def prev_guid(calladdr,maxn=60):
    i=byaddr[calladdr]; res=[]
    for j in range(i-1,max(0,i-maxn),-1):
        aj,mj,oj=ins[j]
        n=num(oj.rsplit(', ',1)[-1]) if mj=='push' else None
        if n in GUID: res.append((hex(aj),GUID[n]))
        if mj=='ret': break
    return res
for slot,nm in ((0x7e15f4,'OleSaveToStream'),(0x7e15f8,'OleLoadFromStream')):
    c=collections.Counter(); tot=0; ex=[]
    for a,m,o in ins:
        if m=='call' and o=='dword ptr [0x%x]'%slot:
            tot+=1
            pg=prev_guid(a)
            key=tuple(sorted(set(x[1] for x in pg))) or ('NONE',)
            c[key]+=1
            if nm=='OleLoadFromStream': ex.append((hex(a),pg[:3]))
    print(nm,'calls',tot,dict(c))
    if ex:
        print('  load examples',ex[:8])
# GUID at 0x7e9b10, 0x7e9ac0
def guid_text(b):
    d1,d2,d3=struct.unpack('<IHH',b[:8])
    return '{%08X-%04X-%04X-%s-%s}'%(d1,d2,d3,b[8:10].hex().upper(),b[10:].hex().upper())
for va in (0x7e9ac0,0x7e9b10,0x7e9b00,0x7e9b20):
    print(hex(va),guid_text(pe.get_data(va-IB,16)))
