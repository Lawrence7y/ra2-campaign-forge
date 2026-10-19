import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\tools")
from re_gap_spysat_deep import read_bytes, md, base, names, secs, disasm_func

text = next(s for s in secs if s['name'] == '.text')
code = text['raw'][:text['vsize']]
tva = text['va']

targets = {
    0x00843E6C: "SuperGapRadiusInCells",
    0x00843E84: "GapRadiusInCells",
    0x00843E98: "GapGenerator",
    0x0081AE58: "SpySat",
}

pos = 0
import capstone as _cs
found = []
while pos < len(code):
    for insn in md.disasm(code[pos:], tva + pos):
        for op in insn.operands:
            if op.type == _cs.x86.X86_OP_IMM and op.imm in targets:
                found.append((insn.address, insn.mnemonic, insn.op_str, op.imm, targets[op.imm]))
        pos = insn.address - tva + insn.size
    if pos < len(code):
        pos += 1

for a, m, ops, imm, name in found:
    print(f"0x{a:08X}: {m} {ops} -> {name} (0x{imm:08X})")

# Let's disassemble the function around the first occurrence!
if found:
    disasm_func(found[0][0] - 0x20, 60)
