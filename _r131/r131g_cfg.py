#!/usr/bin/env python3
# R131 r131g: CFG-aware esp model of wrapper 0x6bedb0 (thiscall: this in ecx, args on stack,
# ret 0xc). Resolve every [esp+N] memory operand to a named slot, path-sensitively.
import json, collections
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131g_cfg.json'
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
secs={}
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm]=(base+s.VirtualAddress, base+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData), s)
tlo,thi,ts=secs['.text']; data=ts.get_data()
md=Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True
FN=0x6bedb0; WIN=0xc0
ins={}
for i in md.disasm(data[FN-tlo:FN-tlo+WIN], FN):
    ins[i.address]=i
addrs=sorted(ins)
def nexta(a):
    k=addrs.index(a); return addrs[k+1] if k+1<len(addrs) else None
succ={}
for a in addrs:
    i=ins[a]; mn=i.mnemonic; s=[]
    if mn.startswith('j'):
        tgt=None
        for o in i.operands:
            if o.type==2: tgt=o.imm
        if mn=='jmp': s=[tgt] if tgt else []
        else: s=[tgt, nexta(a)]
    elif mn=='ret': s=[]
    else: s=[nexta(a)]
    succ[a]=[x for x in s if x in ins]
def delta(i):
    mn=i.mnemonic
    if mn=='push': return 4
    if mn=='pop': return -4
    if mn=='ret':
        if not i.op_str: return 4
        return 4+(int(i.op_str,16) if i.op_str.startswith('0x') else int(i.op_str))
    if mn=='call': return 0
    if mn=='sub' and i.op_str.startswith('esp,'): return -int(i.op_str.split(',')[1].strip(),0)
    if mn=='add' and i.op_str.startswith('esp,'): return int(i.op_str.split(',')[1].strip(),0)
    return 0
esp={FN:0}; work=collections.deque([FN]); conflict=[]
while work:
    a=work.popleft(); out=esp[a]+delta(ins[a])
    for s_ in succ[a]:
        if s_ in esp:
            if esp[s_]!=out: conflict.append({'from':hex(a),'to':hex(s_),'have':esp[s_],'new':out})
        else: esp[s_]=out; work.append(s_)
def slot(n):
    if n==0: return 'retaddr(E0)'
    if (n-4)%4==0 and n>=4: return 'arg%d'%((n-4)//4+1)
    return 'local@%d'%n
rows=[]
for a in addrs:
    i=ins[a]
    for o in i.operands:
        if o.type==3 and i.reg_name(o.mem.base)=='esp':
            if a not in esp: continue
            n=o.mem.disp; rel=esp[a]+n
            rows.append({'va':'%08x'%a,'bytes':i.bytes.hex(),'op':i.mnemonic+' '+i.op_str,
                         'esp_at':esp[a],'disp':n,'E0':rel,'slot':slot(rel)})
R={'unreachable':[hex(a) for a in addrs if a not in esp],'conflicts':conflict,'rows':rows,'esp_map':{'%08x'%a:esp.get(a) for a in addrs}}
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1)
print('esp conflicts:',conflict)
print('%-10s %-24s %-32s %-5s %-6s %s'%('va','bytes','op','esp','E0+','slot'))
for r in rows:
    print('%-10s %-24s %-32s %-5d %-6d %s'%(r['va'],r['bytes'],r['op'],r['esp_at'],r['E0'],r['slot']))
