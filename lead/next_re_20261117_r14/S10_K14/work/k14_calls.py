from collections import Counter
from k14_image import Image, COV
import capstone.x86
img = Image()
START = 0x004D85D0
SIZE = 0x961
code = img.read(START, SIZE)
insns = list(img.md.disasm(code, START))

def coverage_rows():
    rows = {}
    with open(COV, "r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            c = ln.rstrip("\r\n").split("\t")
            if len(c) >= 8 and c[0]:
                rows[c[0].upper()] = c
    return rows
rows = coverage_rows()
direct = []
indirect = []
for i in insns:
    if i.mnemonic == "call":
        ops = i.operands
        if ops and ops[0].type == capstone.x86.X86_OP_IMM:
            direct.append((i.address, ops[0].imm))
        else:
            indirect.append((i.address, i.op_str))
cnt = Counter(t for _, t in direct)
out = ["S10_K14 DIRECT CALLS OF 004D85D0 (independent disassembly)",
       "FUNCTION_RANGE=004D85D0..004D8F30 (atlas size 0x961)",
       "DIRECT_CALL_COUNT=" + str(len(direct)),
       "addr        target      count  coverage_grade  coverage_name"]
for addr, target in sorted(direct, key=lambda x: x[0]):
    r = rows.get(f"{target:08X}")
    out.append(f"{addr:08X}  {target:08X}  {cnt[target]:<5}  {(r[4] if r else 'NOT_IN_COV'):<14}  {(r[2] if r else '')}")
out.append("")
out.append("INDIRECT_CALL_COUNT=" + str(len(indirect)))
for addr, text in indirect:
    out.append(f"{addr:08X}  call {text}")
def exact_hits(needle):
    return [hex(i.address) for i in insns if needle in [o.imm for o in i.operands if o.type == capstone.x86.X86_OP_IMM]]

def raw_hits(needle_le):
    return [hex(START + off) for off in range(len(code)-len(needle_le)+1) if code[off:off+len(needle_le)] == needle_le]

checks = {"0x816CAC": (0x816CAC, bytes.fromhex("ac6c8100")),
          "0x65C7E0": (0x65C7E0, bytes.fromhex("e0c76500")),
          "0x5657A0": (0x5657A0, bytes.fromhex("a0575600")),
          "0x6F5090": (0x6F5090, bytes.fromhex("90506f00"))}
out.append("")
out.append("OPERAND/RAW CHECKS (function body only)")
for label, (imm, raw) in checks.items():
    out.append(f"{label} operand_imm_hits={exact_hits(imm)} raw_byte_hits={raw_hits(raw)}")

probe = ["005B3040","005B3740","005657A0","0065C7E0","006F5090","004D85D0","00519630","00739EC0"]
out.append("")
out.append("PROBE COVERAGE ROWS (grade is field index 4 only)")
for a in probe:
    r = rows.get(a)
    out.append(a + "  " + ("NOT_IN_COV" if not r else "\t".join(r)))
text = "\n".join(out)
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K14\EVIDENCE\CALLEE_STATUS.txt","w",encoding="utf-8").write(text+"\n")
print(text)
