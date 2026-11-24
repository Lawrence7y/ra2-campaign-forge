from base import BUF, IB, u32, s32, TEXT
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True
tlo, thi = TEXT["va"], TEXT["va"]+TEXT["vsize"]
insns = {i.address:(i.size,i.mnemonic,i.op_str) for i in md.disasm(bytes(BUF[tlo-IB:thi-IB]), tlo)}

# A jump target is INTERNAL if it is inside [F, F+size) of a known function.
# Proper approach: compute function extents by walking from starts until ret.
starts = set()
for a,(sz,mn,op) in insns.items():
    if mn.startswith("ret"):
        n=a+sz
        while n in insns and insns[n][1]=="nop": n+=insns[n][0]
        if n in insns: starts.add(n)
for a,(sz,mn,op) in insns.items():
    if mn in ("call","jmp") and op.startswith("0x"):
        t=int(op,16)
        if tlo<=t<thi: starts.add(t)
starts.discard(tlo)
print("raw start candidates:", len(starts))

# Keep only starts that are instruction boundaries (they are by construction),
# then filter out targets that fall INSIDE another start's body: iteratively
# drop starts that are reachable only as an internal branch from an earlier start
# Simpler: for call/jmp targets, drop those that a conditional branch targets
# and that are not preceded by nop padding / ret / another function end.
import bisect
sl=sorted(starts)
def prev_boundary(a):
    return sl[bisect.bisect_left(sl,a)-1] if bisect.bisect_left(sl,a)>0 else None
# Determine which starts are preceded by a 'gap' = nop padding or ret end
good=set()
for a in sl:
    p=prev_boundary(a)
    if p is None: good.add(a); continue
    # scan forward from p: does it hit a ret then nops then a?
    ok=False
    addr=p
    steps=0
    while addr in insns and addr < a and steps < 4000:
        sz,mn,op=insns[addr]
        if mn.startswith("ret"):
            n=addr+sz
            while n in insns and insns[n][1]=="nop": n+=insns[n][0]
            if n==a: ok=True
            break
        addr+=sz; steps+=1
    if ok: good.add(a)
print("starts that follow a ret(+padding):", len(good))

# 0x4F8440 must be in good
print("0x4F8440 in good?", 0x004F8440 in good)
print("0x4F8F79 in good?", 0x004F8F79 in good)
print("0x4FC0B0 in good?", 0x004FC0B0 in good)
print("0x4F8F87 in good?", 0x004F8F87 in good)

# what does 0x4F8F79 come from? check if a conditional branch targets it
for a,(sz,mn,op) in insns.items():
    if mn.startswith("j") and op=="0x4f8f79":
        print("  branch to 0x4F8F79 from %08X %s %s" % (a,mn,op))
