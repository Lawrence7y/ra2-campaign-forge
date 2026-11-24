"""
S11-K2 T3 fresh: field double-support for DriveLocomotionClass.
Rigorous this-tracking per calling convention:
  off=0 (IPersistStream COM thiscall): ecx=this at entry.
  off=4/24 (ILocomotion/IPiggyback, explicit this on stack): this=[esp+4] (or [esp+8] after prologue).
  ctor: ecx=this.
Exclude virtual dispatch call/jmp [reg+disp] from data-field reads; report excluded count.
Record writer set + reader list per displacement. Emit EVIDENCE/fresh_fields.txt
"""
import json
from pehelp import u32, rd, disasm, fmt, section_of, MD, IMAGE_BASE
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM
from capstone.x86 import (X86_REG_ECX, X86_REG_ESP, X86_REG_EBP)

FC=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\fresh_core.json',encoding='utf-8'))
classes=FC['classes']
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\fresh_fields.txt'
L=[]
def P(s=''):
    L.append(str(s)); print(s)

name='.?AVDriveLocomotionClass@@'
# gather functions with their interface convention
funcs=[]  # (label,addr,conv)
funcs.append(('ctor',0x4AF540,'ecx'))
for s in sorted(classes[name],key=lambda x:x['off']):
    for i in range(s['slots']):
        a=u32(s['vt']+4*i)
        if section_of(a)=='.text':
            conv='ecx' if s['off']==0 else 'stack'
            funcs.append(('off%d_s%d'%(s['off'],i),a,conv))

# dedupe by address (keep first label)
seen={}
for lab,a,conv in funcs:
    if a not in seen: seen[a]=(lab,conv)
funcs=[(lab,a,conv) for a,(lab,conv) in seen.items()]

STORE={'mov','movzx','movsx','add','sub','and','or','xor','inc','dec','shl','shr','adc','sbb','imul'}
def this_regs(fn, conv, n=0x120):
    regs=set()
    if conv=='ecx': regs.add(X86_REG_ECX)
    # seed from stack-passed this: [esp+4] / [ebp+8]
    for ins in disasm(fn,n):
        try:
            ops=ins.operands
        except Exception:
            continue
        if ins.mnemonic=='mov' and len(ops)==2:
            d,s=ops
            if d.type==X86_OP_REG:
                if s.type==X86_OP_MEM and s.mem.base in (X86_REG_ESP,X86_REG_EBP):
                    if (s.mem.base==X86_REG_ESP and s.mem.disp in (4,8,0xc)) or (s.mem.base==X86_REG_EBP and s.mem.disp in (8,0xc)):
                        regs.add(d.reg)
                if s.type==X86_OP_REG and s.reg in regs:
                    regs.add(d.reg)
        if ins.mnemonic=='ret': break
    return regs

field={}   # disp -> {'w':[(lab,addr,kind)],'r':[...]}
virt_excluded=0
for lab,fn,conv in funcs:
    if section_of(fn)!='.text': continue
    tr=this_regs(fn,conv)
    for ins in disasm(fn,0x180):
        try:
            ops=ins.operands
        except Exception:
            continue  # skipdata pseudo-instruction
        if ins.mnemonic=='ret': break
        # virtual dispatch exclusion
        if ins.mnemonic in ('call','jmp') and ops and ops[0].type==X86_OP_MEM:
            virt_excluded+=1; continue
        for oi,op in enumerate(ops):
            if op.type!=X86_OP_MEM: continue
            m=op.mem
            if m.base not in tr or m.index!=0: continue
            if m.disp<=0 or m.disp>0x200: continue
            kind='r'
            if oi==0 and ins.mnemonic in STORE: kind='w'
            field.setdefault(m.disp,{'w':[],'r':[]})[kind].append((lab,'%08X'%ins.address,ins.mnemonic,ins.op_str))

P('DriveLocomotionClass funcs scanned=%d  virtual call/jmp [reg+disp] EXCLUDED=%d'%(len(funcs),virt_excluded))
P('')
P('offset | writers(n) | readers(n) | writer sites | reader sites (first 4)')
for d in sorted(field):
    w=field[d]['w']; r=field[d]['r']
    ws=';'.join('%s:%s'%(x[0],x[1]) for x in w)
    rs=';'.join('%s:%s'%(x[0],x[1]) for x in r[:4])
    P('+0x%-4X w=%-2d r=%-2d %s | W:%s | R:%s'%(d,len(w),len(r),'DOUBLE' if (w and r) else '',ws,rs))

# double-supported fields with reader>=3
P('\n=== DOUBLE-supported, readers>=3 (candidate 双支撑) ===')
for d in sorted(field):
    w=field[d]['w']; r=field[d]['r']
    if w and len(r)>=3:
        P('+0x%-4X writers=%d readers=%d'%(d,len(w),len(r)))
        for x in w: P('    W %s %s %s %s'%x)
        for x in r: P('    R %s %s %s %s'%x)

with open(OUT,'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
json.dump({('0x%X'%d):field[d] for d in field},open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\work\fresh_fields.json','w'),indent=1)
print('\nWROTE',OUT)
