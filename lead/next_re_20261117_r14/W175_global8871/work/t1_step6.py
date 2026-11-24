"""Task 1 step 6: compare constructor 0x6832c0 (object at 0xa8b230); check esi usage around 0x6667B3; check any indirect call via [esi] vptr."""
import sys, os, capstone
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN, md, disasm, fmt

EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out=[]
def P(s=""): out.append(str(s))

# compare: constructor 0x6832c0 for object at 0xa8b230 - does it set vptr at [ecx]?
P("=== 0x6832c0 head (constructor for 0xa8b230) ===")
P(fmt(disasm(0x6832c0,0x60)))

# context around 0x6667B3 within 0x665650
P("\n=== 0x665650 around 0x6667B3 (+/- 0x40) ===")
P(fmt(disasm(0x666770,0xC0,stop_at=0x666830)))

# reassignments of esi inside 0x665650
m=md()
data=BIN.read(0x665650,0x667a26-0x665650+16)
P("\n=== writes to esi in 0x665650 (excluding push) ===")
for insn in m.disasm(data,0x665650):
    if insn.id==0: continue
    if insn.mnemonic in ("mov","lea","pop","xchg","add","sub"):
        for op in insn.operands[:1]:
            if op.type==capstone.x86.X86_OP_REG and op.reg==capstone.x86.X86_REG_ESI:
                P("  %08X  %s %s"%(insn.address,insn.mnemonic,insn.op_str))

# any indirect call/jmp through [esi] (i.e., call dword ptr [esi+off]) in ctor/dtor
P("\n=== indirect calls via [esi+off] in ctor/dtor ===")
for start,end in [(0x665650,0x667a26),(0x667a30,0x667d00)]:
    d=BIN.read(start,end-start+16)
    for insn in m.disasm(d,start):
        if insn.id==0: continue
        if insn.mnemonic in ("call","jmp") and insn.operands and insn.operands[0].type==capstone.x86.X86_OP_MEM:
            mm=insn.operands[0].mem
            if mm.base==capstone.x86.X86_REG_ESI:
                P("  %08X  %s %s"%(insn.address,insn.mnemonic,insn.op_str))

with open(EVID+r"\t1_compare_ctor.txt","w",encoding="utf-8") as f: f.write("\n".join(out)+"\n")
print("\n".join(out[:80]))
