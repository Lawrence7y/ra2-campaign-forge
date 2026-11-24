import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT14\work")
from auditlib import *

def sec(t): print("\n"+"="*72); print(t); print("="*72)

# ---- direct callers ----
sec("Direct call/jmp refs to entries (expect ~0; only vtable dispatch)")
for e in [0x4AF720,0x4B62C0,0x4B6470,0x54DC60]:
    print(f"  {e:08X}: {find_rel_calls(e)}")

# ---- immediate-encoded vtable installs: search for C7 06 <vt> pattern via find_u32_va ----
sec("Where each main-vtable VA is stored as u32 (ctor install / dtor reinstall)")
for vt in [0x7E7F7C,0x7E8344,0x7ECE34]:
    print(f"  refs to {vt:08X}: {[hex(x) for x in find_u32_va(vt)]}")

# ---- constructors ----
sec("CTOR 004AF540 install @004AF5C2 (expect C7 06 7C 7F 7E 00)")
for i in disasm(0x4AF5B8, 0x30): print("   ",fmt_insn(i))
sec("CTOR 004B5AB0 install @004B5ADD (expect C7 06 44 83 7E 00)")
for i in disasm(0x4B5AD3, 0x20): print("   ",fmt_insn(i))
sec("CTOR 0054AC40 install @0054ACC3 (expect C7 06 34 CE 7E 00)")
for i in disasm(0x54ACB9, 0x20): print("   ",fmt_insn(i))

# ---- deletion destructors (dtor reinstall points - should NOT be our 4-anchor) ----
sec("DTOR 004B4D00 @004B4D03 (DriveLocomotion delete dtor reinstall)")
for i in disasm(0x4B4D00, 0x45): print("   ",fmt_insn(i))
sec("DTOR 004B66F0 @004B66F3 (DropPod delete dtor reinstall)")
for i in disasm(0x4B66F0, 0x45): print("   ",fmt_insn(i))
sec("DTOR 0054DFA0 @0054DFA3 (Jumpjet delete dtor reinstall)")
for i in disasm(0x54DFA0, 0x45): print("   ",fmt_insn(i))

# ---- instantiation chains ----
sec("Instantiation DriveLocomotion @006C403C")
for i in disasm(0x6C4034, 0x28): print("   ",fmt_insn(i))
sec("Instantiation DropPod @006C493C")
for i in disasm(0x6C4934, 0x28): print("   ",fmt_insn(i))
sec("Instantiation Jumpjet @006C41BC")
for i in disasm(0x6C41B4, 0x28): print("   ",fmt_insn(i))
