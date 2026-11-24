"""
Map class ctor -> class by scanning ctor body for any of the 24 canonical vtable immediates
(off=0 and off=4 for each of 12 classes), encoded as mov [reg],imm (C7 0x/8x .. imm32).
"""
import json, struct
from pehelp import u32, rd, disasm, section_of, MD
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

J=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\t1_rtti_enum.json'
obj=json.load(open(J,encoding='utf-8')); classes=obj['classes']
vt2class={}
for name,slots in classes.items():
    short=name.split('AV')[1].split('@@')[0]
    for s in slots:
        if s['off'] in (0,4):
            vt2class[s['vt']]=short

gs=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\work\getsize_hits.json'))
getsize={}
for k,v in gs.items():
    if v: getsize[k.split('AV')[1].split('@@')[0]]=v[0][3]

CI=[0x6C3F40+0x180*k+0xD0 for k in range(11)]

def ctor_from_ci(ci):
    for ins in disasm(ci,0xD0):
        if ins.mnemonic=='call' and ins.operands and ins.operands[0].type==X86_OP_IMM:
            t=ins.operands[0].imm & 0xffffffff
            if t==0x7C8E17: continue  # operator new
            if is_code(t): return t, ins.address
    return None,None

def is_code(va): return section_of(va)=='.text'

def class_from_ctor(ctor, n=0x500):
    # find any mov [reg/mem],imm where imm matches canonical vtable
    hits=[]
    for ins in disasm(ctor,n):
        if ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[0].type==X86_OP_MEM and ins.operands[1].type==X86_OP_IMM:
            v=ins.operands[1].imm & 0xffffffff
            if v in vt2class:
                hits.append((ins.address,v,vt2class[v]))
    return hits

print('ci        ctor      vtable-hits (addr imm class)')
mapping=[]
for ci in CI:
    ctor,csite=ctor_from_ci(ci)
    hits=class_from_ctor(ctor) if ctor else []
    cls=hits[0][2] if hits else None
    print('%08X  %08X  %s' % (ci, ctor or 0, [(('%08X'%a),('%08X'%v),c) for a,v,c in hits[:6]]))
    mapping.append((ci,ctor,cls,hits))

print('\n=== closure ===')
closed=0
for ci,ctor,cls,hits in mapping:
    aa=None;av=None;ah=None
    for ins in disasm(ci,0xD0):
        if ins.mnemonic=='push' and ins.operands and ins.operands[0].type==X86_OP_IMM:
            v=ins.operands[0].imm&0xffffffff
            if 0x20<=v<=0x1000:
                aa,av,ah=ins.address,v,ins.bytes.hex();break
    g=getsize.get(cls)
    ok=(av==g)
    if ok: closed+=1
    print('%-24s alloc=%-5s(%s) getsz=%-5s %s' % (cls or '?',av,ah,g,'CLOSED' if ok else 'NO'))
print('closure %d/11'%closed)
