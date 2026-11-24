import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT14\work")
from auditlib import *

def sec(t): print("\n" + "="*72); print(t); print("="*72)

# ============ ENTRY 004AF720 : DriveLocomotionClass ============
sec("004AF720 RTTI: vt 0x7E7F7C slot0, COL, TD name")
print("vt[0] (0x7E7F7C) =", hex(u32(0x7E7F7C)))  # expect 0x4AF720
print_col(0x7E7F7C)
print("first slot bytes @0x7E7F7C:", hexb(0x7E7F7C, 8))
print("first slot target disasm (should be real fn 0x4AF720):")
for i in disasm(u32(0x7E7F7C), 12): print("   ", fmt_insn(i))

# ============ ENTRY 004B6470 & 004B62C0 : DropPodLocomotionClass ============
sec("004B6470/004B62C0 RTTI: main vt 0x7E8344 slot0=0x4B6470 slot6=0x4B62C0")
print("main vt[0] 0x7E8344 =", hex(u32(0x7E8344)))     # 0x4B6470
print("main vt[6] 0x7E835C =", hex(u32(0x7E835C)))     # 0x4B62C0
print_col(0x7E8344)
print("main first slot bytes @0x7E8344:", hexb(0x7E8344, 8))
for i in disasm(u32(0x7E8344), 12): print("   ", fmt_insn(i))

# ============ ENTRY 0054DC60 : JumpjetLocomotionClass ============
sec("0054DC60 RTTI: vt 0x7ECE34 slot0, COL, TD name")
print("vt[0] (0x7ECE34) =", hex(u32(0x7ECE34)))  # 0x54DC60
print_col(0x7ECE34)
print("first slot bytes @0x7ECE34:", hexb(0x7ECE34, 8))
for i in disasm(u32(0x7ECE34), 12): print("   ", fmt_insn(i))

# ============ direct callers of each entry (should be 0) ============
sec("Direct call/jmp references to each entry (expect 0 - only vtable dispatch)")
for e in [0x4AF720, 0x4B62C0, 0x4B6470, 0x54DC60]:
    hits = find_rel_calls(e)
    print(f"  {e:08X}: {len(hits)} hits {hits[:5]}")

# ============ vtable slot as stored VA references (who points to these vtables) ============
sec("Where is each vtable address stored as u32 (ctor installs + dtor reinstalls)")
for vt in [0x7E7F7C, 0x7E8344, 0x7ECE34]:
    print(f"  references to vt {vt:08X}: ", [hex(x) for x in find_u32_va(vt)])
