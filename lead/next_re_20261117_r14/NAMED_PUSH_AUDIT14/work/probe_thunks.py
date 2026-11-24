import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT14\work")
from auditlib import *

def sec(t): print("\n"+"="*72); print(t); print("="*72)

sec("jmp sites that target entries (decode exact VAs)")
for e in [0x4AF720,0x4B6470,0x54DC60]:
    for (addr,mn,by) in find_rel_calls(e):
        print(f"  {e:08X} <- {mn} @0x{addr:08X} bytes={by}")
        for i in disasm(addr-8, 18): print("       ",fmt_insn(i))

sec("SUB-table slot0 bytes (expect this-adjustor thunk)")
subtables = {
 'Drive sub@[this+4] 0x7E7EB0':0x7E7EB0, 'Drive sub@[this+0x18] 0x7E7E8C':0x7E7E8C,
 'Drop sub@[this+4] 0x7E8278':0x7E8278, 'Drop sub@[this+0x18] 0x7E8254':0x7E8254,
 'Jet sub@[this+4] 0x7ECD68':0x7ECD68, 'Jet sub@[this+0x18] 0x7ECD44':0x7ECD44,
}
for name,vt in subtables.items():
    first=u32(vt)
    print(f"  {name}: slot0 VA=0x{first:08X} bytes={hexb(first,10)}")
    for i in disasm(first,10): print("       ",fmt_insn(i))
    cp=u32(vt-4); print(f"      COL ptr=0x{cp:08X}", end=' ')
    if is_va(cp):
        print(f"sig={u32(cp)} offset={u32(cp+4)}")
    else: print()

sec("CTOR starts - verify base ctor call 0x55A6C0")
for ctor in [0x4AF540,0x4B5AB0,0x54AC40]:
    print(f"  --- ctor {ctor:08X} ---")
    for i in disasm(ctor, 0x24): print("       ",fmt_insn(i))
