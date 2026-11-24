"""T3b: dump the 54 base+disp writes to +0x13c and find map array allocation/dimension init."""
from pehelp import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, collections
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t3_map_writes.txt"
_l=[]
def p(s=''):
    print(s); _l.append(str(s))
WRITEMN={'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr','imul','neg','not','xchg','fstp','stosd','rep'}
def rname(reg):
    try: return md.reg_name(reg)
    except: return f'r{reg}'
tlo,thi=text_bounds(); data=pe.get_data(SECTIONS[0][2],SECTIONS[0][3])
writes13c=[]
for ins in md.disasm(data,tlo):
    if ins.id==0: continue
    mn=ins.mnemonic; ops=ins.operands
    if mn in ('call','jmp') and ops and ops[0].type==X86_OP_MEM: continue
    for idx,op in enumerate(ops):
        if op.type==X86_OP_MEM and op.mem.disp==0x13c and op.mem.base!=0:
            if idx==0 and mn in WRITEMN:
                writes13c.append((ins.address,mn,f"{ins.mnemonic} {ins.op_str}",rname(op.mem.base)))
p(f"writes to [reg+0x13c] = {len(writes13c)}")
for site,mn,insn,b in writes13c:
    # show 8 insns before with context (look for singleton load / array alloc)
    ctx=list(disasm(max(tlo,site-32),40))
    pre=' | '.join(f"{i.address:#x}:{i.mnemonic} {i.op_str}" for i in ctx if i.id!=0 and i.address<site)
    p(f"  {site:#x} [{b}] {insn}\n      PRE: {pre[-260:]}")

# find likely map init: shl reg,2 + writes to +0x14c/+0x150/+0x154 via any base in a function that also writes +0x13c
p("\n=== candidate map-init functions: functions writing +0x13c and containing +0x14c/+0x150/+0x154 ===")
# cluster write sites by nearby function (approx by scanning back for push ebp/sub esp)
sites=sorted(set(s for s,_,_,_ in writes13c))
for s in sites[:20]:
    win=list(disasm(max(tlo,s-0x100),0x180))
    txt=' '.join(f"{i.mnemonic} {i.op_str}" for i in win if i.id!=0)
    dims=[hex(o) for o in (0x14c,0x150,0x154) if f'0x{o}' in txt or f'+{o}' in txt]
    if dims:
        p(f"  @{s:#x} dims near: {dims}")
with open(OUT,'w') as f: f.write('\n'.join(_l)+'\n')
p(f"\n[saved] {OUT}")
