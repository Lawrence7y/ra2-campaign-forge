"""
S11-K2 T4 fresh: vtable slot semantics. For every slot of the base+Drive off=4 tables,
record target addr, first instructions, ret form; scan for constant-returning funcs
(WhatAmI candidates) across ALL slots of all 12 classes. Verify K1 anchors' call sites.
Emit EVIDENCE/fresh_slots.txt
"""
import json, struct
from pehelp import u32, rd, disasm, fmt, section_of, is_code
from capstone.x86 import X86_OP_IMM

FC=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\fresh_core.json',encoding='utf-8'))
classes=FC['classes']
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\fresh_slots.txt'
L=[]
def P(s=''):
    L.append(str(s)); print(s)

def sig(a,n=0x50):
    ins=list(disasm(a,n))
    out=[]
    for x in ins[:5]:
        out.append(x.mnemonic+' '+x.op_str)
        if x.mnemonic.startswith('ret'): break
    return ' | '.join(out)

# 1) base LocomotionClass off=4 50-slot dump
P('===== LocomotionClass (base) off=4 main vtable, 50 slots =====')
base=[s for s in classes['.?AVLocomotionClass@@'] if s['off']==4][0]
for i in range(base['slots']):
    a=u32(base['vt']+4*i)
    if not is_code(a): P('  slot%-2d %08X noncode'%(i,a)); continue
    P('  slot%-2d %08X %s'%(i,a,sig(a)))

# 2) Drive off=4 dump (derived overrides)
P('\n===== DriveLocomotionClass off=4 main vtable (50 slots) =====')
drv=[s for s in classes['.?AVDriveLocomotionClass@@'] if s['off']==4][0]
drv_slots=[]
for i in range(drv['slots']):
    a=u32(drv['vt']+4*i); drv_slots.append(a)
    if not is_code(a): P('  slot%-2d %08X noncode'%(i,a)); continue
    P('  slot%-2d %08X %s'%(i,a,sig(a)))

# 3) scan ALL slots of ALL classes for constant-return (mov eax,imm; ret / xor eax,eax;ret / mov al,imm;ret)
P('\n===== constant-returning slot funcs across ALL 12 classes (WhatAmI/GetSize candidates) =====')
seen={}
for name in sorted(classes):
    for s in sorted(classes[name],key=lambda x:x['off']):
        for i in range(s['slots']):
            a=u32(s['vt']+4*i)
            if not is_code(a) or a in seen: continue
            b=rd(a,8)
            # mov eax,imm32;ret  OR xor eax,eax;ret  OR mov al,imm8;ret
            kind=None; val=None
            if b[0]==0xB8 and b[5]==0xC3: kind='B8imm32C3'; val=struct.unpack('<I',b[1:5])[0]
            elif b[0:3]==b'\x33\xc0\xc3': kind='xor-eax-ret'; val=0
            elif b[0]==0xB0 and b[2]==0xC3: kind='mov-al-imm8-ret'; val=b[1]
            if kind:
                seen[a]=(kind,val,name,s['off'],i)
                P('  %-44s off=%-3d slot=%-2d %08X %-14s val=%s'%(name,s['off'],i,a,kind,val))

# 4) verify K1 slot anchors call sites: ecx=vtable, disp->slot
P('\n===== K1 anchor call-site verification (per K1 PROGRESS/VERDICT, re-disasm) =====')
for site,expect_disp,expect_slot in [(0x4D9C4B,0x1C,7),(0x4DA877,0x40,16),(0x4D562C,0x44,17),(0x4D55E0,0x48,18)]:
    P('  site %08X (expect [ecx+0x%X] -> slot %d):'%(site,expect_disp,expect_slot))
    for ins in list(disasm(site-0x14,0x30)):
        P('     '+fmt(ins))
        if ins.address>=site+6: break

with open(OUT,'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE',OUT)
