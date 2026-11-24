"""Focused: Array remove, bullet factory/allocator, Fire prologue, GetWeapon/GetFireError."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\work")
import re_lib as R
import capstone

EV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\EVIDENCE"
out=[]
def p(s=""): out.append(str(s))

p("=== 1. Array REMOVE point in BulletAI Update @0x466610..0x466660 ===")
p(R.dump_insns(R.disasm(0x4665F0, 0x80)))

p("\n=== 2. Other writer 0x4E6891 ===")
p(R.dump_insns(R.disasm(0x4E6860, 0x60)))

p("\n=== 3. BulletClass ctor caller @0x6C50CF (class factory?) ===")
p(R.dump_insns(R.disasm(0x6C5090, 0x90)))

p("\n=== 4. Fire prologue 0x6FDD50..0x6FDE20 (guards + GetWeapon/GetFireError) ===")
p(R.dump_insns(R.disasm(0x6FDD50, 0xD0)))

p("\n=== 5. Where does [esp+0x4C] come from before Construct? scan writes in Fire ===")
fire=R.disasm_fn(0x6FDD50)
for i,insn in enumerate(fire):
    if insn.mnemonic=="mov" and insn.operands and insn.operands[0].type==capstone.x86.X86_OP_MEM:
        m=insn.operands[0].mem
        if m.base==capstone.x86.X86_REG_ESP and m.disp==0x4c:
            p(f"   {R.fmt_insn(insn)}")

p("\n=== 6. Backtrace esi/edi at Construct: look at 0x6FF749..0x6FF859 already shown; find call before that sets edi ===")
# search backwards in Fire for 'mov edi,' assignments
for i,insn in enumerate(fire):
    if 0x6FF000 <= insn.address <= 0x6FF859 and insn.mnemonic=="mov" and insn.operands:
        d=insn.operands[0]
        if d.type==capstone.x86.X86_OP_REG and insn.reg_name(d.reg)=="edi":
            p(f"   {R.fmt_insn(insn)}")

txt="\n".join(out)
open(EV+r"\trace_array_factory.txt","w",encoding="utf-8").write(txt)
print(txt)
