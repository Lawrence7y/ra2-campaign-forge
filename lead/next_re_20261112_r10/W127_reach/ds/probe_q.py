from base import BUF, IB, u32, s32, TEXT, blob
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata=True
tlo,thi=TEXT["va"],TEXT["va"]+TEXT["vsize"]
insns={i.address:(i.size,i.mnemonic,i.op_str) for i in md.disasm(bytes(BUF[tlo-IB:thi-IB]),tlo)}

T=0x004FC0B0
print("=== find all 'ff a0 <disp32>'  (jmp dword ptr [eax+disp32]) whose disp == 0x4FC0B0 - something ===")
# A forwarder in a subclass vtable is: jmp dword ptr [eax+off]  where off points
# at the base subobject's slot in the base vtable. The disp is the BYTE offset
# into the base vtable, NOT an absolute address, so it cannot equal 0x4FC0B0.
# Instead: find vtable slots that hold tiny forwarder functions.
print()
print("=== tiny functions in .text that are just jmp [eax+disp] ===")
cnt=0
for a in sorted(starts) if False else []:
    pass
small=[]
for a,(sz,mn,op) in insns.items():
    raw=blob(a,6)
    if mn=="jmp" and raw[:2]==b"\xff\xa0":
        small.append((a,u32(a+2)))
print("  count of 'jmp dword ptr [eax+disp32]' trampolines: %d" % len(small))
for a,d in small[:20]:
    print("    %08X  jmp [eax+0x%X]" % (a,d))
