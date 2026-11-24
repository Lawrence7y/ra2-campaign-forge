"""
S11-K2 T2 PART B2: map each Locomotion factory CreateInstance -> Locomotion class via
the class ctor it calls (ctor installs one of the 12 canonical off=0 vtables).
Then close GetSize (off0 slot9 B8 imm32 C3) == factory allocation push (6A/68).
"""
import json
from pehelp import u32, rd, is_code, disasm, fmt, section_of, MD
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM

J=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\t1_rtti_enum.json'
obj=json.load(open(J,encoding='utf-8')); classes=obj['classes']
off0_vt={}
for name,slots in classes.items():
    for s in slots:
        if s['off']==0:
            off0_vt[s['vt']]=name.split('AV')[1].split('@@')[0]
gs=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\work\getsize_hits.json'))
getsize={k:v[0][3] for k,v in gs.items() if v}

OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\t2_getsize_closure.txt'
L=[]
def P(s=''):
    L.append(str(s)); print(s)

CI=[0x6C3F40+0x180*k+0xD0 for k in range(11)]

def find_alloc_push(ci, nbytes=0xD0):
    for ins in disasm(ci,nbytes):
        if ins.mnemonic=='push' and ins.operands and ins.operands[0].type==X86_OP_IMM:
            v=ins.operands[0].imm & 0xffffffff
            if 0x20<=v<=0x1000:
                return ins.address, v, ins.bytes.hex()
    return None,None,None

def find_ctor_call(ci, nbytes=0xD0):
    calls=[]
    for ins in disasm(ci,nbytes):
        if ins.mnemonic=='call' and ins.operands and ins.operands[0].type==X86_OP_IMM:
            calls.append((ins.address, ins.operands[0].imm & 0xffffffff))
    return calls

def class_of_ctor(ctor, nbytes=0x40):
    for ins in disasm(ctor,nbytes):
        if ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[0].type==X86_OP_MEM and ins.operands[1].type==X86_OP_IMM:
            v=ins.operands[1].imm & 0xffffffff
            if v in off0_vt:
                return off0_vt[v], v, ins.address
    return None,None,None

P('=== Per-factory GetSize closure (B8 imm32 C3 @ off0 slot9  vs  allocation push in CreateInstance) ===')
P('ci        alloc_push imm   class_via_ctor       off0_vt     GetSize  CLOSED?')
closed=0
mapping=[]
for ci in CI:
    aa,av,ah=find_alloc_push(ci)
    calls=find_ctor_call(ci)
    cls=None; ovt=None; csite=None
    for ca,ct in calls:
        c,ov,cs=class_of_ctor(ct)
        if c: cls=c; ovt=ov; csite=cs; break
    gsiz=getsize.get(cls) if cls else None
    ok=(av==gsiz) if (av is not None and gsiz is not None) else False
    if ok: closed+=1
    P('%08X  %08X(%s) %-5s %-22s %08X %-6s %s' % (ci, aa or 0, ah or '-', av, cls or '?', ovt or 0, gsiz, 'YES' if ok else 'no'))
    mapping.append(dict(ci=ci,alloc=av,cls=cls,getsize=gsiz,closed=ok))

P('')
P('closure count = %d / %d' % (closed,len(CI)))
P('')
P('=== §972 encoding check: allocation push encoding forms ===')
for m in mapping:
    aa,av,ah=find_alloc_push(m['ci'])
    form='6A imm8' if ah.startswith('6a') else ('68 imm32' if ah.startswith('68') else '?')
    P('  %-24s imm=%-5s enc=%s' % (m['cls'] or '?', av, form))
n_6a=sum(1 for m in mapping if find_alloc_push(m['ci'])[2].startswith('6a'))
n_68=sum(1 for m in mapping if find_alloc_push(m['ci'])[2].startswith('68'))
P('6A imm8=%d , 68 imm32=%d  (imm32-only scan would MISS %d/%d)' % (n_6a,n_68,n_6a,len(CI)))

with open(OUT,'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
json.dump(mapping,open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\work\getsize_closure.json','w'),indent=1)
print('\nWROTE',OUT)
