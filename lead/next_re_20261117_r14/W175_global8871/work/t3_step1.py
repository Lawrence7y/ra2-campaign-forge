"""Task 2 verify + Task 3: proper-boundary disasm of 0x66B900; sweep writes to the two globals."""
import sys, os, capstone
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN, md, disasm, fmt

EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out=[]
def P(s=""): out.append(str(s))

# === Task 2: proper disasm from call-target entry 0x66B900 ===
P("=== 0x66B900 (call target) .. 0x66BAB0, proper boundary ===")
P(fmt(disasm(0x66B900,0x1C0)))

# === Task 3: full-text sweep of writes to absolute 0xA8ED6B and 0xB73550 ===
m=md()
t=BIN.text
data=BIN.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
GLOBALS={0xa8ed6b:'A8ED6B',0xb73550:'B73550'}
abs_refs={k:[] for k in GLOBALS}
all_refs={k:[] for k in GLOBALS}  # any operand referencing, write or read
n=0
for insn in m.disasm(data,t["va"]):
    if insn.id==0: continue
    n+=1
    for opi,op in enumerate(insn.operands):
        if op.type==capstone.x86.X86_OP_MEM:
            mem=op.mem
            va_disp=mem.disp & 0xFFFFFFFF
            if mem.base==0 and mem.index==0 and va_disp in GLOBALS:
                all_refs[va_disp].append((insn.address, insn.mnemonic, insn.op_str, opi))
P("\nscanned %d insns"%n)
for g,name in GLOBALS.items():
    P("\n=== all absolute-address refs to 0x%X [%s] ==="%(g,name))
    for x in all_refs[g]:
        P("  %08X  %-6s %-40s (op#%d)"%x)

# === Task 3b: [reg+off] form where reg loaded with base immediately before ===
# Pattern: mov reg,0xA8ED6B/0xB73550  (B8+r imm32) then [reg] access.
P("\n=== immediates equal to the two globals loaded into regs (base+[reg+off]) ===")
for insn in m.disasm(data,t["va"]):
    if insn.id==0: continue
    for op in insn.operands:
        if op.type==capstone.x86.X86_OP_IMM:
            v=op.imm & 0xFFFFFFFF
            if v in GLOBALS:
                P("  %08X  %s %s"%(insn.address,insn.mnemonic,insn.op_str))

with open(EVID+r"\t3_global_writes.txt","w",encoding="utf-8") as f: f.write("\n".join(out)+"\n")
print("written; lines=%d"%len(out))
