"""Resolve the Verses application function entry + callers, the ReceiveDamage virtual
call inside DamageArea, the BulletClass allocation (push 0x160), and weapon-selection
calls inside Fire. All byte-level, skipdata=True.
"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\work")
import re_lib as R
import capstone

EV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\EVIDENCE"
out = []
def p(s=""): out.append(str(s))

p("=== 1. What contains 0x4891C6? prologue before it ===")
_fa = R.fn_at(0x4891C6)
p("   fn_at(0x4891C6) = " + (f"0x{_fa:08X}" if _fa else "None"))
p(R.dump_insns(R.disasm(0x489150, 0x90)))

p("\n=== 2. Who references 0x489180 / 0x4891C6? full .text call/jmp/jcc target sweep ===")
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); MD.detail=True; MD.skipdata=True
targets = {0x489180, 0x4891C6}
found=[]
for insn in MD.disasm(R.read(R.TEXT[1], R.TEXT[2]-R.TEXT[1]), R.TEXT[1]):
    if insn.mnemonic in ("call","jmp") or insn.mnemonic.startswith("j"):
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) in targets:
                found.append((insn.address, insn.mnemonic, op.imm & 0xFFFFFFFF, R.fmt_insn(insn)))
for f in found:
    p(f"   {f[3]}")
p(f"   total refs = {len(found)}")

p("\n=== 3. Direct call to 0x489180 from ReceiveDamage @0x701D64 window ===")
p(R.dump_insns(R.disasm(0x701D40, 0x50)))

p("\n=== 4. Virtual ReceiveDamage call in DamageArea: scan call [reg+0x16C] ===")
da = R.disasm_fn(0x489280)
for insn in da:
    if insn.mnemonic == "call" and insn.operands and insn.operands[0].type == capstone.x86.X86_OP_MEM:
        m = insn.operands[0].mem
        if m.disp in (0x16C, 0x16c):
            p(f"   {R.fmt_insn(insn)}   [slot 91 = ReceiveDamage]  context:")
            # show 6 insns before
            idx = da.index(insn)
            for x in da[max(0,idx-6):idx+2]:
                p("      "+R.fmt_insn(x))

p("\n=== 5. BulletClass allocation push 0x160 in Fire 0x6FDD50 ===")
fire = R.disasm_fn(0x6FDD50)
for i, insn in enumerate(fire):
    if insn.mnemonic == "push" and insn.operands and insn.operands[0].type == capstone.x86.X86_OP_IMM and (insn.operands[0].imm & 0xFFFFFFFF) == 0x160:
        p(f"   {R.fmt_insn(insn)}  context:")
        for x in fire[max(0,i-3):i+4]:
            p("      "+R.fmt_insn(x))
# also any push imm followed by call 0x7C8E17 (new)
p("   -- all operator new (0x7C8E17) call sites in Fire with preceding push --")
for i, insn in enumerate(fire):
    t = R.call_target(insn)
    if t == 0x7C8E17:
        p(f"   new@0x{insn.address:08X}:")
        for x in fire[max(0,i-4):i+2]:
            p("      "+R.fmt_insn(x))

p("\n=== 6. GetWeapon / GetFireError / SelectWeapon vtable indirect calls in Fire ===")
# vtable slots: GetWeapon=+0x2D8? check from YRpp: virtuals; find call [reg+disp] and map disp/4 = slot
slot_names = {0x2D8:"GetWeapon?", 0x288:"GetFireError?", 0x284:"GetFireErrorWithoutRange?", 0x290:"SelectWeapon?", 0x3CC:"Fire"}
for insn in fire:
    if insn.mnemonic == "call" and insn.operands and insn.operands[0].type == capstone.x86.X86_OP_MEM:
        m = insn.operands[0].mem
        if m.disp in slot_names:
            p(f"   {R.fmt_insn(insn)}   slot~{m.disp//4} {slot_names[m.disp]}")

txt="\n".join(out)
open(EV+r"\resolve_chain_gaps.txt","w",encoding="utf-8").write(txt)
print(txt)
