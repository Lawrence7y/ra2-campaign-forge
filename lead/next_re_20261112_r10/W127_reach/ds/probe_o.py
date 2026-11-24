from base import BUF, IB, u32, s32, cstr, in_raw, blob, TEXT, SECTIONS
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata=True
tlo,thi=TEXT["va"],TEXT["va"]+TEXT["vsize"]
insns={i.address:(i.size,i.mnemonic,i.op_str) for i in md.disasm(bytes(BUF[tlo-IB:thi-IB]),tlo)}
starts=set()
for a,(sz,mn,op) in insns.items():
    if mn.startswith("ret"):
        n=a+sz
        while n in insns and insns[n][1]=="nop": n+=insns[n][0]
        if n in insns: starts.add(n)
starts.add(tlo); starts=sorted(starts)
import bisect
def owner(a):
    i=bisect.bisect_right(starts,a)-1
    return starts[i] if i>=0 else None

print("=== PE entry point + process-level handlers ===")
from base import pe
print("  AddressOfEntryPoint = 0x%08X (VA %08X)" % (pe.OPTIONAL_HEADER.AddressOfEntryPoint,
      0x400000+pe.OPTIONAL_HEADER.AddressOfEntryPoint))
for d in pe.DIRECTORY_ENTRY_IMPORT or []:
    print("  imported DLL %s" % d.dll.decode())

print()
print("=== which functions are registered as window procs? (RegisterClass/WndProc slots) ===")
# WinMain / WndProc are usually taken by address: `push imm32` or `mov [x], imm32`
# Find push imm32 whose imm is a code address, and collect targets
from collections import Counter
pushimm=Counter()
for a,(sz,mn,op) in insns.items():
    if mn=="push" and op.startswith("0x"):
        v=int(op,16)
        if tlo<=v<thi: pushimm[v]+=1
print("  distinct code addresses pushed as immediates: %d" % len(pushimm))
print("  most frequent:", [("%08X"%k,v) for k,v in pushimm.most_common(8)])

print()
print("=== BFS upward from 0x4F8440 via BOTH call edges and vtable-slot hosting ===")
# call edge map
callers=dict()
for a,(sz,mn,op) in insns.items():
    if mn in ("call","jmp") and op.startswith("0x"):
        t=int(op,16)
        if tlo<=t<thi:
            cf,tf=owner(a),owner(t)
            if cf and tf and cf!=tf:
                callers.setdefault(tf,set()).add(cf)
print("  owner(0x4F8440)=%08X" % owner(0x004F8440))
print("  call-level callers of 0x4F8440: %s" % ["%08X"%c for c in callers.get(0x004F8440,())])
