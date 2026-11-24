
import sys, json, re
import pefile
from capstone import *
p = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(p)
image = pe.OPTIONAL_HEADER.ImageBase
raw = open(p,'rb').read()
def off(va): return pe.get_offset_from_rva(va-image)
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = False
def body(va,limit=80):
    r=[]
    for i in md.disasm(raw[off(va):off(va)+600], va):
        r.append((i.address,i.mnemonic,i.op_str,i.bytes))
        if i.mnemonic=='ret' or len(r)>=limit: break
    return r

def classify(va):
    b=body(va)
    if not b: return ('?',0,'')
    ops=[(m,o) for (a,m,o,by) in b]
    txt=' | '.join(f"{m} {o}" for m,o in ops)
    # signature helpers
    if any(m.startswith('ret') for m,o in ops):
        rets=[o for m,o in ops if m.startswith('ret')]
    # GetItem: mov eax,[ecx+4]; mov ecx,[esp+4]; mov eax,[eax+ecx*4]; ret 4
    if len(b)>=4 and 'mov'==b[0][1] and b[0][2]=='eax, dword ptr [ecx + 4]' and b[1][1]=='mov' and b[1][2]=='ecx, dword ptr [esp + 4]' and b[2][1]=='mov' and 'eax + ecx*4' in b[2][2]:
        return ('GetItem',len(b),txt)
    # operator==: compare Count at [reg+8] between this and other, loop cmp [item], return al, ret 4
    if any(o.startswith('al, 1') for m,o in ops) and any('dword ptr [edi + 8]' in o or 'dword ptr [edx + 8]' in o for m,o in ops) and any(m=='cmp' and 'dword ptr [' in o for m,o in ops):
        if any(re.match(r'ret',m) and o=='4' for m,o in ops):
            return ('operator==',len(b),txt)
    # Clear (Vec/DynVec): xor reg,reg; mov eax,[this+4]; [DynVec: mov [this+0x10],0]; cmp [this+0xd]; call 7c8b3d; mov [this+4],0; mov [this+8],0; ret
    if any(m=='call' and '0x7c8b3d' in o for m,o in ops) and any('dword ptr [esi + 4], 0' in o or 'dword ptr [eax + 4], 0' in o or 'dword ptr [edx + 4], 0' in o for m,o in ops):
        if any('[esi + 8], 0' in o or '[eax + 8], 0' in o or '[edx + 8], 0' in o for m,o in ops):
            return ('Clear',len(b),txt)
    # FindItemIndex (Vec): xor eax,eax; loop cmp dword ptr [ecx], esi; inc eax; add ecx,4; cmp eax,edx; or eax,0xffffffff; ret 4
    if any('or eax, 0xffffffff' in o for m,o in ops) and any(m=='ret' and o=='4' for m,o in ops):
        return ('FindItemIndex',len(b),txt)
    # GetItemIndex (n=5): mov al,[ecx+0xc]; test al,al; (jne); ... sub Items -> ret 4
    if len(b)>0 and b[0][1]=='mov' and b[0][2]=='al, byte ptr [ecx + 0xc]' and any(m=='test' and o.startswith('al, al') for m,o in ops):
        return ('GetItemIndex',len(b),txt)
    # SetCapacity: call 7c8e17 (operator new) -- K9 already proved; skip
    return ('other',len(b),txt)

if __name__=='__main__':
    entries=[s.strip() for s in sys.argv[1].split(',') if s.strip()]
    out={}
    for s in entries:
        nm,n,txt=classify(int(s,16))
        out[s]={'class':nm,'n':n,'txt':txt}
    print(json.dumps(out,indent=1))
