"""
S11-K2 T3: field layout double-support for Locomotion classes (incremental).
Focus on DriveLocomotionClass: its ctor sets this=esi; vtable functions provide reads.
Explicitly EXCLUDE virtual calls (call [reg+disp]) from data-field read points (§969/§972).
We record: disp -> list of (func, addr, kind, mnemonic) where kind in {write,data_read,virtcall_excluded}.
"""
import json
from pehelp import u32, disasm, section_of, MD
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM
from capstone.x86 import X86_REG_ECX, X86_REG_ESI, X86_REG_EAX, X86_REG_EDX, X86_REG_EBX, X86_REG_EDI, X86_REG_ESP

J=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\t1_rtti_enum.json'
obj=json.load(open(J,encoding='utf-8'))
classes=obj['classes']

def slots_of(name, off):
    for s in classes[name]:
        if s['off']==off: return s
    return None

# Drive functions: ctor + all unique slot funcs from all 3 interfaces
name='.?AVDriveLocomotionClass@@'
funcs={'ctor_0x4AF540':0x4AF540}
for off in (0,4,24):
    s=slots_of(name,off)
    if not s: continue
    for i in range(s['slots']):
        a=u32(s['vt']+4*i)
        if section_of(a)=='.text': funcs['off%d_slot%d'%(off,i)]=a

# this-register heuristic: in off=0 methods this=ecx at entry; in off=4 methods this=[esp+4/8] (stack-passed);
# in ctor this=ecx. We will accept any base reg whose value came from ecx or from [esp+4/8] early in the fn.
def find_this_regs(fn_start, n=0x200):
    thisregs={X86_REG_ECX}
    # track simple mov reg,ecx and mov reg,[esp+4/8]
    for ins in disasm(fn_start,n):
        try:
            _ops = ins.operands
        except Exception:
            continue
        if ins.mnemonic=='mov' and len(ins.operands)==2:
            dst,src=ins.operands
            if dst.type==X86_OP_REG:
                if src.type==X86_OP_REG and src.reg==X86_REG_ECX: thisregs.add(dst.reg)
                if src.type==X86_OP_MEM and src.mem.base==X86_REG_ESP and src.mem.disp in (4,8,0xc):
                    thisregs.add(dst.reg)
        if ins.mnemonic=='ret': break
    return thisregs

field={}  # disp -> list of records
virt_excluded=0
for fname,fa in funcs.items():
    if section_of(fa)!='.text': continue
    tr=find_this_regs(fa)
    for ins in disasm(fa,0x300):
        try:
            _test = ins.operands
        except Exception:
            continue  # skipdata pseudo-instruction, no operands
        if ins.mnemonic=='ret': break
        # virtual call: call [reg+disp] -> exclude
        if ins.mnemonic=='call' and ins.operands and ins.operands[0].type==X86_OP_MEM:
            virt_excluded+=1
            continue
        # jmp [reg+disp] also virtual tailcall -> exclude
        if ins.mnemonic=='jmp' and ins.operands and ins.operands[0].type==X86_OP_MEM:
            virt_excluded+=1
            continue
        for op in ins.operands:
            if op.type!=X86_OP_MEM: continue
            m=op.mem
            if m.base not in tr and m.index==0: continue
            if m.disp<=0 or m.disp>0x200: continue
            # determine kind by operand position: op is dst for mov->write
            kind='?'
            if ins.mnemonic in ('mov','movzx','movsx','add','sub','and','or','inc','dec','cmp','test'):
                # if this op is the FIRST operand and ins is a store form (mov [mem],reg/imm) -> write
                if op is ins.operands[0] and ins.mnemonic in ('mov','add','sub','and','or','inc','dec'):
                    kind='write'
                else:
                    kind='read'
            field.setdefault(m.disp,[]).append((fname,'%08X'%ins.address,ins.mnemonic,kind,ins.op_str))

print('funcs scanned =',len(funcs),' virtual calls EXCLUDED =',virt_excluded)
print('\ndisp | writes | reads | sample')
for disp in sorted(field):
    recs=field[disp]
    w=[r for r in recs if r[3]=='write']; rd=[r for r in recs if r[3]=='read']
    both='YES' if (w and rd) else ''
    print('+0x%-3X w=%-2d r=%-2d %s | w:%s | r:%s' % (disp,len(w),len(rd),both,
          (w[0][0]+':'+w[0][1]) if w else '-', (rd[0][0]+':'+rd[0][1]) if rd else '-'))

json.dump({('0x%X'%d):field[d] for d in field},open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\work\fields_drive.json','w'),indent=1)
