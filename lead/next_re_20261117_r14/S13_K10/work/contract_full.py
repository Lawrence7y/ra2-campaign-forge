
import sys, json, re
import pefile
from capstone import *
p=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(p); img=pe.OPTIONAL_HEADER.ImageBase; raw=open(p,'rb').read()
def off(va): return pe.get_offset_from_rva(va-img)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True; md.detail=False
def insns(va, maxb=400):
    r=[]
    for i in md.disasm(raw[off(va):off(va)+maxb],va):
        r.append((i.address,i.mnemonic,i.op_str,i.bytes))
        if len(r)>=200: break
    return r
def contract(va):
    b=insns(va)
    ops=[(m,o) for a,m,o,by in b]
    full=' | '.join(f"{m} {o}" for m,o in ops[:40])
    if len(b)>=4 and b[0][1]=='mov' and b[0][2]=='eax, dword ptr [ecx + 4]' and b[1][2]=='ecx, dword ptr [esp + 4]' and 'eax + ecx*4' in b[2][2]:
        return ('GetItem',full)
    if b[0][1]=='mov' and b[0][2]=='al, byte ptr [ecx + 0xc]' and any(m=='shr' and o=='eax, 2' for m,o in ops[:10]):
        return ('GetItemIndex',full)
    if any(m=='call' and '0x7c8b3d' in o for m,o in ops[:25]) and any(re.search(r'\+ 8\], (0|ebx|edx|eax)',o) for m,o in ops[:25]):
        return ('Clear',full)
    if any(m=='mov' and o=='al, 1' for m,o in ops[:25]) and any(m=='cmp' and re.search(r'ptr \[edi \+ 8\]',o) for m,o in ops[:12]):
        return ('operator==',full)
    if any(m=='or' and '0xffffffff' in o for m,o in ops[:20]) and any(m=='inc' and o=='eax' for m,o in ops[:20]):
        return ('FindItemIndex',full)
    return ('other',full)
if __name__=='__main__':
    entries=[s.strip() for s in sys.argv[1].split(',') if s.strip()]
    out={ea:dict(zip(('cls','txt'),contract(int(ea,16)))) for ea in entries}
    print(json.dumps(out,indent=1))
