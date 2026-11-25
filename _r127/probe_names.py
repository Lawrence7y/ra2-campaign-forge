import struct,json,collections
import pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
RD=S['.rdata']; RD_LO=RD.VirtualAddress+IB; RD_HI=RD_LO+RD.Misc_VirtualSize
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def i32(va):
    b=rd(va,4); return struct.unpack('<i',b)[0] if len(b)==4 else None
def cstr(va,n=200):
    b=rd(va,n); e=b.find(b'\x00'); return (b[:e] if e>=0 else b).decode('latin1')
def rtti(vt):
    col=u32(vt-4)
    if not col or not (RD_LO<=col<RD_HI): return None
    ptd=u32(col+12); pchd=u32(col+16)
    if not ptd or not (RD_LO<=ptd<RD_HI): return None
    n,arr=u32(pchd+8),u32(pchd+12)
    out=[]
    for i in range(min(n or 0,64)):
        bcd=u32(arr+4*i); td=u32(bcd)
        out.append((cstr(td+8,200), i32(bcd+8)))
    return out
sym=json.load(open('out/reverse/symbols.json',encoding='utf-8'))['classes']
def _va(x): return None if x is None else (x if isinstance(x,int) else int(str(x).strip(),16))
for target in ('AITriggerTypeClass','HouseClass','HouseTypeClass'):
    for k,v in sym.items():
        if k!=target: continue
        vt=_va(v['vtable_va'])
        print(target,'vt=0x%x'%vt)
        for nm,md in rtti(vt): print('   ',nm,hex(md))
# which classes have 0x7e9ae0 as their QI-accepted riid? find all QI bodies referencing it
import capstone
TX=S['.text']; T_LO=TX.VirtualAddress+IB
raw=pe.get_data(TX.VirtualAddress,TX.Misc_VirtualSize)
md_=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md_.skipdata=True
ins=[(a,m,o) for a,s,m,o in md_.disasm_lite(raw,T_LO)]
refs=[(a,m,o) for a,m,o in ins if '0x7e9ae0' in o]
print('refs to 0x7e9ae0:',len(refs),[hex(a) for a,m,o in refs][:12])
