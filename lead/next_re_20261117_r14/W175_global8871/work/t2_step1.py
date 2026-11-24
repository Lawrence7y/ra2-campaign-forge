"""Task 2 step 1: scan all .text for [reg+0x1808] and [reg+0x172C] operands (skipdata=True)."""
import sys, os, capstone
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN, md

EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out=[]
def P(s=""): out.append(str(s))

m=md()
t=BIN.text
data=BIN.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
TARGETS={0x1808,0x172c}
hits={k:[] for k in TARGETS}
nins=0
for insn in m.disasm(data,t["va"]):
    if insn.id==0: continue
    nins+=1
    for opi,op in enumerate(insn.operands):
        if op.type==capstone.x86.X86_OP_MEM:
            mem=op.mem
            disp=mem.disp & 0xFFFFFFFF
            for tgt in TARGETS:
                if disp==tgt or (disp & 0xFFFFFFFF)==tgt:
                    hits[tgt].append((insn.address, insn.mnemonic, insn.op_str, opi))
                    break
P("scanned %d instructions (skipdata=True)"%nins)
for tgt in sorted(TARGETS):
    P("\n=== [reg+0x%X] refs (%d) ==="%(tgt,len(hits[tgt])))
    for va,mn,ops,opi in hits[tgt]:
        P("  %08X  %-6s %s   (operand #%d)"%(va,mn,ops,opi))

with open(EVID+r"\t2_disp_1808_172c.txt","w",encoding="utf-8") as f: f.write("\n".join(out)+"\n")
print("\n".join(out))
