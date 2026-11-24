"""
S10-K2 T3: GetSize double/triple-point closure for MissionClass + derived classes.
Per S11-K2 ruling: DO NOT assume slot 12. Delimit vtables from .rdata, then read v[11](WhatAmI)
and v[12](size candidate) byte shapes. Triple corroboration: value semantics + allocation
point (6A imm8 / 68 imm32 / C7 04 24 imm / sub esp,imm) + ctor write upper bound.
Base stub 0x4C9150 (33 C0 C3) is NOT a real GetSize.
capstone skipdata=True; no atlas for discovery.
"""
import os, json
from pehelp import (IMAGE_BASE, rd, u32, sections, section_of, is_code, disasm, fmt)
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM

OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2'
EVID=os.path.join(OUT,'EVIDENCE')
L=[]
def P(s=''):
    s=str(s); L.append(s)
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode('ascii'))

md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True

with open(os.path.join(EVID,'t2_rtti_vtables.json')) as f: rj=json.load(f)
cls_vt={}
for x in rj['kvts']:
    if x['off']==0 and x['name'] not in cls_vt:
        cls_vt[x['name']]=int(x['vt'],16)

# 1) v[11] / v[12] shape for each class
P('===== T3 v[11]/v[12] BYTE SHAPES (slot from .rdata, not assumed) =====')
vt11={}
for name,vt in sorted(cls_vt.items()):
    a11=u32(vt+11*4); a12=u32(vt+12*4)
    def shape(a):
        b=rd(a,8)
        if b[0]==0xB8 and b[5]==0xC3:
            imm=int.from_bytes(b[1:5],'little'); return 'B8 imm32 C3',imm
        if b[:3]==b'\x33\xC0\xC3': return '33 C0 C3 (xor eax,eax;ret stub)',0
        try:
            ins=list(md.disasm(b,a,2)); d=' / '.join('%s %s'%(i.mnemonic,i.op_str) for i in ins)
        except: d='?'
        return d,None
    s11,i11=shape(a11); s12,i12=shape(a12)
    P('  %-40s VT=%08X | v[11]=%08X %-34s | v[12]=%08X %-34s' %
      (name,vt,a11,s11+((' imm=0x%X'%i11) if i11 is not None else ''),
       a12,s12+((' imm=0x%X'%i12) if i12 is not None else '')))
    vt11[name]=(vt,a11,s11,i11,a12,s12,i12)

# 2) Find constructors that install each vtable (mov dword ptr [reg], imm_VT)
P('\n===== T3 VTABLE INSTALL SITES (ctor upper-bound evidence) =====')
text_sec=[s for s in sections() if s[0]=='.text'][0]
nm,vaoff,vsize,rsize,praw=text_sec
tlo=IMAGE_BASE+vaoff; thi=IMAGE_BASE+vaoff+min(vsize,rsize)
blob=rd(tlo,thi-tlo)
install={}
for name,vt in cls_vt.items():
    needle=vt.to_bytes(4,'little')
    sites=[]; st=0
    while True:
        k=blob.find(needle,st)
        if k<0: break
        a=tlo+k; st=k+1
        pre=rd(a-2,2)
        if len(pre)==2 and pre[0]==0xC7:
            sites.append(a-2)
    install[name]=sites
    P('  %-40s VT=%08X install-sites(C7)=%s' % (name,vt,','.join('%08X'%a for a in sites[:12])))

# 3) Allocation push scan near install sites
P('\n===== T3 ALLOCATION PUSH SCAN near vtable-install sites =====')
def alloc_pushes(va, before=0x80, after=0x180):
    lo=max(tlo,va-before); hi=min(thi,va+after)
    out=[]
    for ins in md.disasm(rd(lo,hi-lo),lo):
        if ins.mnemonic=='push' and ins.operands and ins.operands[0].type==X86_OP_IMM:
            v=ins.operands[0].imm & 0xffffffff
            out.append((ins.address,ins.bytes.hex(),'push',v))
        if ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[0].type==X86_OP_MEM and ins.operands[1].type==X86_OP_IMM:
            if '[esp]' in ins.op_str and 'esp +' not in ins.op_str:
                out.append((ins.address,ins.bytes.hex(),'mov[esp]',ins.operands[1].imm & 0xffffffff))
        if ins.mnemonic=='sub' and len(ins.operands)==2 and ins.operands[0].type==X86_OP_REG and ins.operands[0].reg==4 and ins.operands[1].type==X86_OP_IMM:
            out.append((ins.address,ins.bytes.hex(),'sub esp',ins.operands[1].imm & 0xffffffff))
    return out
alloc={}
for name,sites in install.items():
    allp=[]
    for s in sites[:6]: allp+=alloc_pushes(s)
    alloc[name]=allp
    P('  %-40s pushes near installs: %s' % (name, ', '.join('%s@%08X=%d(0x%X)'%(k,a,v,v) for a,h,k,v in allp[:16])))

with open(os.path.join(EVID,'t3_getsize_raw.json'),'w') as f:
    json.dump({'install':{k:['%08X'%a for a in v] for k,v in install.items()},
               'alloc':{k:[[('%08X'%a),h,t,v] for a,h,t,v in vv] for k,vv in alloc.items()}}, f, indent=2, default=str)
with open(os.path.join(EVID,'t3_getsize_raw.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE t3_getsize_raw.txt/.json')
