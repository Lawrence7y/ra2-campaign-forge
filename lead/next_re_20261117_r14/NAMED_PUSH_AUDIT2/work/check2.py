import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q, core as C

print("### TeamClass jumptable 0x6E9F74, 65 entries (0..0x40)")
tgts = [C.u32(0x6E9F74 + 4 * i) for i in range(65)]
print("   count:", len(tgts), " distinct:", len(set(tgts)))
print("   all in .text:", all(t is not None and 0x401000 <= t < 0x7E038D for t in tgts))
print("   first 8:", ["%08X" % t for t in tgts[:8]])
print("   last 4:", ["%08X" % t for t in tgts[-4:]])
# 越界路径
print("   "\
      "out-of-range target 0x6E95AB sample:")
print(C.show_range(0x6E95AB, 0x6E95C5, "default path"))

print("\n### SideClass sibling: fn 0x6A4796 head (calls which stream helper?)")
ins = C.disasm(0x6A4796, 40, nbytes=0xC0)
for i in ins:
    if i.mnemonic == "call":
        t = q.callee_at(i.address)
        print("   call @%08X -> %s" % (i.address, ("%08X" % t) if t else i.op_str))

print("\n### InfantryTypeClass container 0xA8E348 writes / vptr")
for a, imm in q.global_writes(0xA8E348):
    print("   %08X <- %08X" % (a, imm))
vt = C.u32(0xA8E348)
print("   static =", vt)
for site, imm in q.global_writes(0xA8E348):
    ri = C.rtti_of_vt(imm)
    print("   candidate vt %08X name=%s slot+0x10=%s" % (imm, ri["name"] if ri else None,
          ("%08X" % C.u32(imm + 0x10)) if C.u32(imm + 0x10) else "?"))
