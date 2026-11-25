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
GUID={0x7f7c70:'10C.r',0x818858:'10C.d',0x7f7c80:'109.r',0x820270:'109.d',
      0x7f7c90:'000.r',0x7f7ca0:'001.r'}
for name,slot in (('OleSaveToStream',0x7e15f4),('OleLoadFromStream',0x7e15f8),('CoCreateInstance',0x7e15fc)):
    print('===',name)
    for i,(a,m,o) in enumerate(ins):
        if m=='call' and o=='dword ptr [0x%x]'%slot:
            back=[]
            for j in range(i-1,max(0,i-30),-1):
                aj,mj,oj=ins[j]
                n=num(oj.rsplit(', ',1)[-1]) if mj in ('push','mov','lea') else None
                if mj=='push' and n in GUID: back.append((hex(aj),GUID[n]))
            print('  call@%x prev-GUID-pushes %s'%(a,back[:3]))
