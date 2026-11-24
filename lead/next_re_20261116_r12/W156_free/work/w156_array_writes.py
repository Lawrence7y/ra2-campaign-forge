"""Byte scan: writes to building array Count/Items and AbstractClass array Count/Items,
plus any dec/sub of a DynamicVectorClass Count accessed via absolute address.
Also list callers of CRT free 0x7C93E8 / 0x7C8B3D that are in engine code (<0x7C0000)."""
import w156_core as C
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

# target absolute globals: Count/Items of BuildingClass::Array and AbstractClass::Array
targets = {
    0xA8EB50: 'Bld.Count', 0xA8EB44: 'Bld.Items', 0xA8EB48: 'Bld.Cap', 0xA8EB40: 'Bld.vptr',
    0xB0F650: 'Abs.Count', 0xB0F644: 'Abs.Items', 0xB0F648: 'Abs.Cap', 0xB0F640: 'Abs.vptr',
}
WRITE_MN = {'mov','inc','dec','add','sub','and','or','xor','adc','sbb','neg','not','xchg'}
found = {k: [] for k in targets}
for e in sorted(C.FUNC.keys()):
    for ins in C.disas_fn(e, cap=8000):
        for i,op in enumerate(ins.operands):
            if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp in targets:
                if i==0 and ins.mnemonic in WRITE_MN:
                    found[op.mem.disp].append((ins.address, e, C.fmt(ins)))
for va,label in targets.items():
    print("=== writes to [%08X] %s : %d ===" % (va,label,len(found[va])))
    for site,fn,txt in sorted(found[va]):
        print("  site=%08X fn=%s  %s" % (site, C.fn_label(fn), txt))
