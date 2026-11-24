"""
S06-K2 T3: MapClass deepening (single-pass .text sweep).
Outputs EVIDENCE/t3_map.txt
"""
from pehelp import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, collections

OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t3_map.txt"
_l=[]
def p(s=''):
    print(s); _l.append(str(s))

MAP_VT=0x7ed404
MAP_SINGLE=0x87f7e8
FIELD_ADDR=0x87f924
DIM_ADDRS={MAP_SINGLE+0x14c:'width=512',MAP_SINGLE+0x150:'height=512',MAP_SINGLE+0x154:'count=0x40000'}
TARGET_ABS={FIELD_ADDR:'cell_array_ptr(+0x13c)'}
TARGET_ABS.update(DIM_ADDRS)
WRITEMN={'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr','sar','imul','neg','not','xchg','fstp','stosd','rep'}

def rname(reg):
    try: return md.reg_name(reg)
    except: return f'r{reg}'

p("="*72); p("S06-K2 T3 MapClass deepening"); p("="*72)
p("\n[1] MapClass vtable 0x7ed404 slot table (30 slots, terminator @0x7ed47c=0x8055e0)")
for i in range(30):
    f=u32(MAP_VT+i*4); sec=section_of(f)
    ins=list(disasm(f,1)); first=f"{ins[0].mnemonic} {ins[0].op_str}" if ins and ins[0].id!=0 else '?'
    tag='SHARED-STUB' if f==0x4c9150 else ''
    p(f"  [{i:2d}] {f:#x} {sec[4] if sec else '---':6} {first:38} {tag}")
stub=[i for i in range(30) if u32(MAP_VT+i*4)==0x4c9150]
p(f"  slots pointing to 0x4c9150 shared stub: {stub}")
p(f"  slot12=0x{u32(MAP_VT+12*4):x} (thunk, NOT B8/C3 GetSize); slot11=0x{u32(MAP_VT+11*4):x}")

# single-pass sweep
tlo,thi=text_bounds()
data=pe.get_data(SECTIONS[0][2],SECTIONS[0][3])
abs_acc=collections.defaultdict(list)
base13c=[]
for ins in md.disasm(data,tlo):
    if ins.id==0: continue
    mn=ins.mnemonic; ops=ins.operands
    if mn in ('call','jmp') and ops and ops[0].type==X86_OP_MEM: continue
    for idx,op in enumerate(ops):
        if op.type!=X86_OP_MEM: continue
        mem=op.mem
        kind='W' if (idx==0 and mn in WRITEMN) else 'R'
        if mem.base==0 and mem.index==0:
            d=mem.disp&0xffffffff
            if d in TARGET_ABS:
                abs_acc[d].append((ins.address,kind,mn,f"{ins.mnemonic} {ins.op_str}"))
        if mem.disp==0x13c and mem.base!=0:
            base13c.append((ins.address,kind,mn,f"{ins.mnemonic} {ins.op_str}",rname(mem.base)))

p(f"\n[2] +0x13C cell-array pointer field (0x87f924)")
aa=abs_acc[FIELD_ADDR]
p(f"  Form A absolute [0x87f924]: {len(aa)} (W={sum(1 for x in aa if x[1]=='W')} R={sum(1 for x in aa if x[1]=='R')})")
for a in aa[:10]: p(f"    {a[0]:#x} {a[1]} {a[3]}")
p(f"  Form B [reg+0x13c]: {len(base13c)} (W={sum(1 for x in base13c if x[1]=='W')} R={sum(1 for x in base13c if x[1]=='R')})")
# verify base reg = singleton by looking back for mov reg,0x87f7e8 within same basic region
sing=[]
for site,kind,mn,insn,breg in base13c:
    back=list(disasm(max(tlo,site-48),48))
    if any(i.id!=0 and i.mnemonic=='mov' and i.op_str.lower().replace(' ','')==f'{breg},0x87f7e8' for i in back):
        sing.append((site,kind,mn,insn,breg))
p(f"  Form B verified base=0x87f7e8 (MapClass singleton): {len(sing)} W={sum(1 for x in sing if x[1]=='W')} R={sum(1 for x in sing if x[1]=='R')}")
for a in sing[:15]: p(f"    {a[0]:#x} {a[1]} {a[3]}")

p(f"\n[3] dimension fields (absolute refs via singleton)")
for addr,desc in sorted(DIM_ADDRS.items()):
    refs=abs_acc[addr]
    p(f"  {addr:#x} (+{addr-MAP_SINGLE:#x}) {desc}: {len(refs)} abs refs W={sum(1 for x in refs if x[1]=='W')} R={sum(1 for x in refs if x[1]=='R')}")
    for a in refs[:5]: p(f"    {a[0]:#x} {a[1]} {a[3]}")

p(f"\n[4] GetCellAt stride evidence (already dumped in map_getcellat.txt)")
p("  0x5657BB mov ecx,[ecx+0x13c]; 0x5657C1 mov eax,[ecx+eax*4] => stride=4; idx=(Y<<9)+X in [0,0x40000)")
p("\n[5] viewport origin 0x886fa0/0x886fa4: §4.4 already proven (each 2 writes), reference only.")

with open(OUT,'w') as f: f.write('\n'.join(_l)+'\n')
p(f"\n[saved] {OUT}")
