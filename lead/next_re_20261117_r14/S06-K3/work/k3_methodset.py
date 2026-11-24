"""S06-K3: build strict CellClass method set + independently recount virtual [mem] calls.
Verifies audit-confirmed caliber: method set = 42 funcs (32 vtable slots + 10 nonvirtual),
whole-.text call/jmp [reg+disp] = 18946.
Outputs EVIDENCE/k3_methodset.txt
"""
from lib import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, collections

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K3\EVIDENCE\k3_methodset.txt"
_l = []
def p(s=''):
    print(s); _l.append(str(s))

# CellClass vtables from S06-K2 foundation (4 tables). COL boundary in .rdata.
CELL_VTS = [0x7E4EC0, 0x7E4EC8, 0x7E4ED0, 0x7E4EEC]

p("=" * 70)
p("S06-K3 method-set + virtual-call recount")
p("=" * 70)

# Dump each vtable's first 40 dwords, determine natural end (first non-.text value).
vt_funcs = []
for vt in CELL_VTS:
    slots = []
    for i in range(48):
        f = u32(vt + i * 4)
        if f is None or not in_text(f):
            break
        slots.append(f)
    p(f"vtable {vt:#x}: {len(slots)} .text slots; end marker @ {vt+len(slots)*4:#x} = {u32(vt+len(slots)*4)!r}")
    for i, f in enumerate(slots):
        p(f"   [{i:2d}] {f:#010x}  size={atlas.get(f,'?')}")
    vt_funcs += slots

uniq_vt = sorted(set(vt_funcs))
p(f"\nunique vtable slots across 4 tables = {len(uniq_vt)}")

NONVIRT = {
    0x47BBF0: 'ctor(main, GetSize push pair)',
    0x47BB60: 'dtor',
    0x483A00: 'ctor2',
    0x485020: 'ore-value (this=CellClass*)',
    0x47FF80: 'getcenter',
    0x5683C0: 'attach wrapper',
    0x5687F0: 'detach wrapper',
    0x47E8A0: 'link-add',
    0x47EA90: 'link-del',
    0x5657A0: 'GetCellAt (ret4 thiscall, returns cell*)',
}
all_methods = set(uniq_vt) | set(NONVIRT)
p(f"unique vtable({len(uniq_vt)}) + nonvirtual({len(NONVIRT)}) = {len(all_methods)} total methods")

# Virtual [mem] calls inside the method set, using atlas bounds.
vcalls_method = []
for e in sorted(all_methods):
    end = fn_end(e)
    for ins in disasm(e, end - e):
        if ins.id == 0:
            continue
        if ins.mnemonic in ('call', 'jmp') and ins.operands:
            op = ins.operands[0]
            if op.type == X86_OP_MEM:
                vcalls_method.append((e, ins.address, ins.mnemonic, ins.op_str))
p(f"\ncall/jmp [mem] inside method set = {len(vcalls_method)}  (audit value 43)")

# Whole .text recount of call/jmp with a memory operand whose base is a register ([reg+disp]).
tlo, thi = text_bounds()
code = read(tlo, thi - tlo)
vc_total = 0
vc_base_reg = 0
for ins in md.disasm(code, tlo):
    if ins.id == 0:
        continue
    if ins.mnemonic in ('call', 'jmp') and ins.operands:
        op = ins.operands[0]
        if op.type == X86_OP_MEM:
            vc_total += 1
            if op.mem.base != X86_REG_INVALID:
                vc_base_reg += 1
p(f"whole .text call/jmp [mem] (any) = {vc_total}")
p(f"whole .text call/jmp [reg+disp]  = {vc_base_reg}  (audit value 18946)")

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(_l) + '\n')
print(f"[saved] {OUT}")
