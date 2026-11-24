from base import BUF, IB, u32, s32, TEXT, blob
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata=True
tlo,thi=TEXT["va"],TEXT["va"]+TEXT["vsize"]
insns={i.address:(i.size,i.mnemonic,i.op_str) for i in md.disasm(bytes(BUF[tlo-IB:thi-IB]),tlo)}
print("=== all direct call/jmp to 0x4FC6B0 (the jmp-target) ===")
t=0x004FC6B0
print("  ", [("%s@%08X"%(mn,a)) for a,(sz,mn,op) in insns.items() if mn in("call","jmp") and op.startswith("0x") and int(op,16)==t])
print()
print("=== who references 0x4F8440 besides the vtable? (exhaustive) ===")
F=0x004F8440
for a,(sz,mn,op) in insns.items():
    if mn in("call","jmp") and op.startswith("0x") and int(op,16)==F:
        print("  direct: %s@%08X" % (mn,a))
from base import SECTIONS
for s in SECTIONS:
    for va in range(s["va"],s["va"]+s["rawsize"]-3):
        if u32(va)==F: print("  dword slot: %s:%08X" % (s["name"],va))
print()
print("=== so: does any code read the HouseClass vtable slot 23? No static ref. ===")
print("=== check the PE: any absolute reference to the vtable start 0x7EA8A0? ===")
V=0x007EA8A0
for s in SECTIONS:
    for va in range(s["va"],s["va"]+s["rawsize"]-3):
        if u32(va)==V: print("  %s:%08X" % (s["name"],va))
