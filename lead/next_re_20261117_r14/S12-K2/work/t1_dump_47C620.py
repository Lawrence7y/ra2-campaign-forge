"""T1: full disassembly of 0x47C620 to its atlas end (size 1116) plus trailing bytes.
Emits full listing to EVIDENCE/t1_47C620_full.txt and a stack-operand census.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import capstone
from re_helper import Bin, disasm_range, fmt_insn, load_atlas, EVID

b = Bin()
rows, hdr = load_atlas()
r = next(x for x in rows if x["_va"] == 0x47C620)
start = 0x47C620
end = start + r["_size"]           # 0x47CAA4
extra_end = end + 32

insns = disasm_range(b, start, extra_end, skipdata=True)

lines = []
lines.append("T1 full linear disassembly of 0x47C620 (skipdata=True)")
lines.append("atlas: entry=%08X size=%d n_instr=%d n_callers=%s n_callees=%s" %
             (start, r["_size"], int(r["n_instr"]), r["n_callers"], r["n_callees"]))
lines.append("declared function range: [%08X, %08X); dumping through %08X" % (start, end, extra_end))
lines.append("=" * 90)
for ins in insns:
    tag = ""
    if ins.address >= end:
        tag = "  ; [OUTSIDE atlas size]"
    lines.append(fmt_insn(ins) + tag)

lines.append("")
lines.append("=" * 90)
lines.append("STACK OPERAND CENSUS within [%08X,%08X)" % (start, end))
esp_vals = set(); ebp_vals = set()
esp_ops = []; ebp_ops = []
X86_OP_MEM = capstone.x86.X86_OP_MEM
for ins in insns:
    if not (start <= ins.address < end) or ins.id == 0: continue
    for op in ins.operands:
        if op.type == X86_OP_MEM:
            m = op.mem
            if m.base == capstone.x86.X86_REG_ESP and m.index == 0:
                esp_vals.add(m.disp)
                esp_ops.append((ins.address, ins.mnemonic, ins.op_str, m.disp))
            if m.base == capstone.x86.X86_REG_EBP and m.index == 0:
                ebp_vals.add(m.disp)
                ebp_ops.append((ins.address, ins.mnemonic, ins.op_str, m.disp))
lines.append("[esp+d] value set: %s  max=%s" % (sorted(esp_vals), max(esp_vals) if esp_vals else None))
lines.append("[ebp+d] value set: %s  max=%s" % (sorted(ebp_vals), max(ebp_vals) if ebp_vals else None))
lines.append("--- all [esp+d] operands ---")
for a,m,o,d in esp_ops:
    lines.append("  %08X %-7s %-46s [esp%+d]" % (a,m,o,d))
lines.append("--- all [ebp+d] operands ---")
for a,m,o,d in ebp_ops:
    lines.append("  %08X %-7s %-46s [ebp%+d]" % (a,m,o,d))

out = os.path.join(EVID, "t1_47C620_full.txt")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("wrote", out, "lines", len(lines))
