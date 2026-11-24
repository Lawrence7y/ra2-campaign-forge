from base import BUF, IB, u32, s32, TEXT, blob
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

print("=== exhaustive reference census for 0x004FC0B0 ===")
T=0x004FC0B0
c1=[(a,mn) for a,(sz,mn,op) in insns.items() if mn in ("call","jmp") and op.startswith("0x") and int(op,16)==T]
print("  class1 direct call/jmp:%d  %s" % (len(c1), [("%s@%08X"%(mn,a)) for a,mn in c1]))
print("  class1 owner funcs: %s" % sorted({"%08X"%owner(a) for a,mn in c1}))
ptrs=[]
for s in __import__("base").SECTIONS:
    for va in range(s["va"],s["va"]+s["rawsize"]-3):
        if u32(va)==T: ptrs.append((s["name"],va))
print("  class3 dword slots: %d  %s" % (len(ptrs), [("%s:%08X"%x) for x in ptrs]))
imm=[a for a,(sz,mn,op) in insns.items() if str(T) in op and mn not in ("call","jmp")]
print("  class2 address-as-immediate in .text: %s" % (["%08X"%a for a in imm] or "none"))

print()
print("=== where does 0x4F8440 get called from? (function-level, whole .text) ===")
F=0x004F8440
callers=[]
for a,(sz,mn,op) in insns.items():
    if mn in ("call","jmp") and op.startswith("0x"):
        if int(op,16)==F: callers.append((a,mn))
print("  direct call/jmp sites: %s" % [("%s@%08X"%(mn,a)) for a,mn in callers])
print("  dword slots holding 0x4F8440:")
for s in __import__("base").SECTIONS:
    for va in range(s["va"],s["va"]+s["rawsize"]-3):
        if u32(va)==F: print("     %s:%08X" % (s["name"],va))
