"""Precision verification: (1) armor->Verses dataflow with full caller context;
(2) health<=0 death branch + DamageState jump table; (3) Destroy 0x708080; (4) GetFireError slot.
"""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\work")
import re_lib as R
import capstone

EV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\EVIDENCE"
out=[]
def p(s=""): out.append(str(s))

p("=== 1. ReceiveDamage -> GetTotalDamage caller FULL context (armor source) ===")
p(R.dump_insns(R.disasm(0x701D00, 0x70)))

p("\n=== 2. GetTotalDamage armor index writes (trace edx all writes 0x489180..0x48926A) ===")
g=R.disasm(0x489180,0xEC)
for insn in g:
    if insn.mnemonic in ("mov","xor") and insn.operands:
        d=insn.operands[0]
        if d.type==capstone.x86.X86_OP_REG and insn.reg_name(d.reg) in ("edx","edi","esi"):
            p("   "+R.fmt_insn(insn))

p("\n=== 3. DamageState jump table @0x702D24 (6 entries) ===")
p("   raw: "+R.read(0x702D24,24).hex(" "))
for i in range(6):
    p(f"   [{i}] = 0x{R.u32(0x702D24+4*i):08X}")

p("\n=== 4. Health<=0 branch: context around 0x70202E (health load) ===")
p(R.dump_insns(R.disasm(0x702020, 0x40)))

p("\n=== 5. Is 0x708080 Destroy? first 60 bytes + its callees ===")
p(R.dump_insns(R.disasm(0x708080, 0x60)))

p("\n=== 6. GetFireError: probe slot 240 fn 0x6FC0B0 ===")
p(R.dump_insns(R.disasm(0x6FC0B0, 0x50)))

p("\n=== 7. Fire ret convention (last insns) & [ebp] stack args ===")
fire=R.disasm_fn(0x6FDD50)
p("   last 6: "+" | ".join(R.fmt_insn(x) for x in fire[-6:]))
p("   [ebp+8]/[ebp+0xC] uses:")
for insn in fire:
    for op in insn.operands:
        if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_EBP and op.mem.disp in (8,0xC):
            p("      "+R.fmt_insn(insn))

txt="\n".join(out)
open(EV+r"\trace_precision.txt","w",encoding="utf-8").write(txt)
print(txt)
