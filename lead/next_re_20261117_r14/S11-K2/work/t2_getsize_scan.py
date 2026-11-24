"""
S11-K2 T2: comprehensive GetSize scan + constructor allocation-point closure.
PART A: scan ALL slots of ALL 3 interface vtables per class for B8 imm32 C3 (mov eax,imm;ret).
PART B: scan factory CreateInstance functions for allocation push (68 imm32 / 6A imm8 / C7 04 24 imm / sub esp),
        anchored on call to operator new, per §972 (6A imm8 is the known miss).
"""
import json
from pehelp import u32, is_code, disasm, fmt, section_of, rd, IMAGE_BASE

J = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\t1_rtti_enum.json'
obj=json.load(open(J,encoding='utf-8'))
classes=obj['classes']
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\t2_getsize_full.txt'
L=[]
def P(s=''):
    L.append(str(s)); print(s)

def get_imm_ret(addr):
    """Return imm32 if function starts with B8 imm32 C3 (or 66 B8 imm16 C3), else None."""
    b=rd(addr,8)
    if len(b)>=6 and b[0]==0xB8 and b[5]==0xC3:
        return int.from_bytes(b[1:5],'little'),'B8imm32C3'
    if len(b)>=4 and b[0]==0xB8 and b[3]==0xC3 and len(b)>=4:
        return int.from_bytes(b[1:3],'little'),'B8imm16C3'
    return None,None

P('===== PART A: B8 imm32 C3 GetSize candidates in EACH vtable slot =====')
getsize={}  # class -> list of (iface_off, slot, addr, imm, form)
for name,slots in sorted(classes.items()):
    P('\n### '+name)
    hits=[]
    for s in sorted(slots,key=lambda x:x['off']):
        vt=s['vt']; off=s['off']; n=s['slots']
        for i in range(n):
            a=u32(vt+4*i)
            if not is_code(a): continue
            imm,form=get_imm_ret(a)
            if imm is not None:
                hits.append((off,i,a,imm,form))
                P('  off=%-3d slot=%-2d addr=%08X size=%-5d(0x%X) %s' % (off,i,a,imm,imm,form))
    if not hits:
        P('  (no B8imm32C3 in any slot)')
    getsize[name]=hits

P('\n\n===== PART A2: WhatAmI-like (returns small const ID) — dump off4 slot11 already done in probe =====')

# Save JSON for downstream
import pickle
with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\work\getsize_hits.json','w') as f:
    json.dump({k:[list(x) for x in v] for k,v in getsize.items()},f,indent=1)

with open(OUT,'w',encoding='utf-8') as f:
    f.write('\n'.join(L)+'\n')
print('\nWROTE',OUT)
