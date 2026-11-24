from base import BUF, IB, u32, s32, TEXT, SECTIONS, blob
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata=True
tlo,thi=TEXT["va"],TEXT["va"]+TEXT["vsize"]
insns={i.address:(i.size,i.mnemonic,i.op_str) for i in md.disasm(bytes(BUF[tlo-IB:thi-IB]),tlo)}

T=0x004FC0B0
print("=== every dword == 0x4FC0B0 in file bytes, with context ===")
for s in SECTIONS:
    for va in range(s["va"], s["va"]+s["rawsize"]-3):
        if u32(va)==T:
            print("  %-8s %08X   prev=%08X next=%08X" % (s["name"],va,u32(va-4),u32(va+4)))

print()
print("=== is .text:0051BF7B inside an instruction (i.e. an immediate, not a pointer)? ===")
a=0x0051BF7B
# find the instruction containing a
best=None
for addr in range(a-15,a+1):
    if addr in insns:
        sz,mn,op=insns[addr]
        if addr<=a<addr+sz:
            best=(addr,sz,mn,op); break
print("  containing insn:", best)
if best:
    addr,sz,mn,op=best
    print("  bytes: %s" % blob(addr,sz).hex())
    print("  -> it is an IMMEDIATE operand of `%s %s`, not a data pointer" % (mn,op))

print()
print("=== disasm around 0x51BF7B ===")
st=0x0051BF50
for ins in md.disasm(bytes(BUF[st-IB:0x0051BFA0-IB]),st):
    m="   <<< dword 0x4FC0B0 here" if ins.address<=0x0051BF7B<ins.address+ins.size else ""
    print("  %08X %-16s %-9s %s%s" % (ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,m))

print()
print("=== .data 0x86F958 / 0x86F95C context ===")
for a in (0x0086F950,0x0086F954,0x0086F958,0x0086F95C,0x0086F960):
    print("  %08X  %08X" % (a,u32(a)))
print("  raw-backed? ", 0x0086F958 < 0x00812000+0x6C000)

print()
print("=== the jmp at 0x4FC6A0: real call or tail-call out of 0x4FC0B0? ===")
for ins in md.disasm(bytes(BUF[0x004FC690-IB:0x004FC6C0-IB]),0x004FC690):
    m="  <<<" if ins.address in (0x004FC6A0,) else ""
    print("  %08X %-14s %-8s %s%s" % (ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,m))
