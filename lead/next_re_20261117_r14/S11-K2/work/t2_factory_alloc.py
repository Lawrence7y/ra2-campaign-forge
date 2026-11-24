"""
S11-K2 T2 PART B: find factory CreateInstance functions and their allocation push.
Route: registration fn 0x6BB9A0 -> call <factory_ctor> (11) -> factory vtable (mov [reg],imm) -> slot3=CreateInstance.
Then disasm CreateInstance for push imm (68 imm32 / 6A imm8) feeding operator new, per §972.
"""
from pehelp import u32, rd, is_code, disasm, fmt, section_of, IMAGE_BASE, MD
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM

OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\t2_factory_alloc.txt'
L=[]
def P(s=''):
    L.append(str(s)); print(s)

# Step 1: registration function range from audit: 0x6BC453..0x6BD6AC, calls to factory ctors in 0x6C0000..0x6D0000
reg_lo, reg_hi = 0x6BC400, 0x6BD700
ctors=set()
for ins in disasm(reg_lo, reg_hi-reg_lo):
    if ins.mnemonic in ('call',):
        for op in ins.operands:
            if op.type==X86_OP_IMM and 0x6C0000 <= op.imm < 0x6D0000:
                ctors.add(op.imm)
P('=== factory ctors found in registration fn: %d ===' % len(ctors))
for c in sorted(ctors): P('  ctor %08X' % c)

# Step 2: for each ctor, find vtable it installs (mov dword ptr [reg], imm where imm in .rdata)
def find_vtable_installed(ctor, nbytes=0x150):
    cand=[]
    for ins in disasm(ctor,nbytes):
        if ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[0].type==X86_OP_MEM and ins.operands[1].type==X86_OP_IMM:
            imm=ins.operands[1].imm & 0xffffffff
            if section_of(imm)=='.rdata':
                cand.append((ins.address,imm,ins.op_str))
    return cand

P('\n=== vtable installed by each factory ctor ===')
factory_ci={}  # ctor -> (vtable, createinstance)
for c in sorted(ctors):
    cand=find_vtable_installed(c)
    P('ctor %08X : %s' % (c, ['%08X@%08X'%(v,a) for a,v,_ in cand]))
    # pick the vtable whose slot3 points to code near this ctor region and slot0-2 are QI/AddRef/Release-like
    for a,vt,_ in cand:
        try: s3=u32(vt+3*4)
        except: continue
        if is_code(s3):
            factory_ci[c]=(vt,s3)
            P('    -> vtable %08X slot3(CreateInstance)=%08X' % (vt,s3))
            break

# Step 3: disasm each CreateInstance, find push imm feeding new
P('\n=== CreateInstance allocation push scan (68 imm32 / 6A imm8 / C7 04 24 imm) ===')
def scan_alloc(ci, nbytes=0x400):
    pushes=[]
    code=rd(ci,nbytes)
    for ins in MD.disasm(code,ci):
        if ins.mnemonic=='push' and ins.operands and ins.operands[0].type==X86_OP_IMM:
            v=ins.operands[0].imm & 0xffffffff
            pushes.append((ins.address,ins.bytes.hex(),v))
        if ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[0].type==X86_OP_MEM and ins.operands[1].type==X86_OP_IMM:
            # C7 04 24 imm  (mov dword ptr [esp],imm)
            opstr=ins.op_str
            if '[esp]' in opstr and 'esp +' not in opstr:
                pushes.append((ins.address,ins.bytes.hex(),ins.operands[1].imm & 0xffffffff))
    return pushes

alloc_by_ci={}
for c,(vt,ci) in sorted(factory_ci.items()):
    pushes=scan_alloc(ci)
    P('CreateInstance %08X (ctor %08X vt %08X):' % (ci,c,vt))
    for a,h,v in pushes:
        P('    push@%08X %-14s imm=%d (0x%X)' % (a,h,v,v))
    alloc_by_ci[ci]=pushes

import json
with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\work\factory_alloc.json','w') as f:
    json.dump({'ctors':sorted(ctors),'factory_ci':{('%08X'%k):[('%08X'%v[0]),('%08X'%v[1])] for k,v in factory_ci.items()},
               'alloc':{('%08X'%k):[[('%08X'%a),h,v] for a,h,v in vv] for k,vv in alloc_by_ci.items()}},f,indent=1)
with open(OUT,'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE',OUT)
