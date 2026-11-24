#!/usr/bin/env python3
"""S17-K2: compact summary of each unnamed target: first instructions, caller count, vtable, strings."""
import sys, struct, os, re, io, csv
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K2\EVIDENCE"
TARGETS = [
  0x004068E0,0x0040E340,0x0041D6E0,0x00427940,0x0042E410,0x00431B80,0x00433CF0,0x004355B0,0x0043A5D0,0x0043AE50,
  0x0049F740,0x0049F8B0,0x004B6BB0,0x00539AE0,0x0055AAC0,0x0067C690,0x00773450,
]
out=io.StringIO()
def p(*a): print(*a,file=out)

# load atlas sizes for reference
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
asize={}
with open(ATLAS,encoding="utf-8",errors="replace") as f:
    for row in csv.DictReader(f,delimiter="\t"):
        asize[int(row["entry"],16)]=(int(row["size"]),int(row["n_instr"]),int(row["n_callers"]))

for t in TARGETS:
    p(f"\n### 0x{t:08X}  atlas(size,instr,callers)={asize.get(t)}")
    callers=P.scan_rel32_calls(t)
    p(f"  direct E8/E9 callers = {len(callers)}")
    insns=P.disasm(t, 96)
    for ins in insns[:20]:
        extra=""
        if ins.mnemonic in ('call','jmp'):
            for op in ins.operands:
                if op.type==X86_OP_IMM: extra=f" -> 0x{op.imm:08X}"
        p(f"    {ins.address:08X} {ins.bytes.hex():<16s} {ins.mnemonic:<6s} {ins.op_str}{extra}")

with open(os.path.join(OUT,"target_compact.txt"),"w",encoding="utf-8") as f: f.write(out.getvalue())
print("wrote target_compact.txt")
