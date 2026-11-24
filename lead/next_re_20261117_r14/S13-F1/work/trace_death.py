"""Death branch in ReceiveDamage + function containment for factory/array-remove + GetFireError slot."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\work")
import re_lib as R
import capstone

EV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\EVIDENCE"
out=[]
def p(s=""): out.append(str(s))

p("=== Function containment ===")
for va in (0x6C50BC, 0x466616, 0x466630, 0x4E6891, 0x489180, 0x489AB6, 0x70D4A0):
    fa=R.fn_at(va)
    p(f"   0x{va:08X} -> fn 0x{fa:08X}" if fa else f"   0x{va:08X} -> None")

p("\n=== ReceiveDamage death branch 0x702580..0x702720 ===")
p(R.dump_insns(R.disasm(0x702580, 0x1A0)))

p("\n=== Health +0x6C writes/reads in ReceiveDamage death context (scan function) ===")
rd=R.disasm_fn(0x701900)
for i,insn in enumerate(rd):
    for op in insn.operands:
        if op.type==capstone.x86.X86_OP_MEM and op.mem.disp==0x6C:
            p(f"   {R.fmt_insn(insn)}")

p("\n=== Death-state writes: cmp eax,4 / cmp ...,5 in ReceiveDamage ===")
for i,insn in enumerate(rd):
    if insn.mnemonic=="cmp" and len(insn.operands)==2:
        a,b=insn.operands
        if b.type==capstone.x86.X86_OP_IMM and b.imm in (4,5):
            p(f"   {R.fmt_insn(insn)}")
            for x in rd[max(0,i-3):i+5]:
                p("      "+R.fmt_insn(x))

p("\n=== TechnoClass vtable slot 240 (0x3C0) fn called in Unit wrapper ===")
for slot in (240, 254, 256, 258, 91, 92, 65):
    v=R.u32(0x7F4960+4*slot)
    p(f"   slot {slot} (+0x{4*slot:X}) -> 0x{v:08X}")

txt="\n".join(out)
open(EV+r"\trace_death.txt","w",encoding="utf-8").write(txt)
print(txt)
