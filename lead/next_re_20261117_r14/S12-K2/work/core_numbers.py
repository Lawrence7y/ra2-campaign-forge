"""Core numbers: (1) 0x47C620 gate-reading census, (2) v73 call/jmp split."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import capstone
from re_helper import Bin, md, load_atlas, EVID
b=Bin(); L=[]
m=md(skipdata=True)
start,end=0x47C620,0x47C620+1116
recs=[]
for ins in m.disasm(b.read(start,end-start), start):
    if ins.id==0: continue
    for op in ins.operands:
        if op.type!=capstone.x86.X86_OP_MEM: continue
        if op.access not in (capstone.CS_AC_READ, capstone.CS_AC_READ|capstone.CS_AC_WRITE): continue
        mem=op.mem
        if mem.base in (capstone.x86.X86_REG_ESP, capstone.x86.X86_REG_EBP): continue
        recs.append((ins.address, ins.mnemonic, ins.op_str, mem.base, mem.disp, mem.disp&0xffffffff, op.size))
L.append("0x47C620 non-stack memory READ operands (gate/field reads): count=%d"%len(recs))
for r in recs: L.append("  %08X %-8s %-46s base=%s disp=%s size=%d"%(r[0],r[1],r[2],r[3],hex(r[5]),r[6]))
# unique sites
L.append("unique instruction sites=%d"%len(set(r[0] for r in recs)))
# unique (disp,size) among this/arg/list reads excluding abs globals
L.append("distinct (disp,size) with base!=0 = %d"%len(set((r[4],r[6]) for r in recs if r[3]!=0)))
# v73 split
t=b.sec(".text"); data=b.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
callc=jmpc=0
for ins in m.disasm(data,t["va"]):
    if ins.id==0 or ins.mnemonic not in ("call","jmp"): continue
    if any(op.type==capstone.x86.X86_OP_MEM and op.mem.base!=0 and op.mem.disp==0x124 for op in ins.operands):
        if ins.mnemonic=="call": callc+=1
        else: jmpc+=1
L.append("v73 [reg+0x124] dispatch: call=%d jmp=%d total=%d"%(callc,jmpc,callc+jmpc))
out=os.path.join(EVID,"core_numbers.txt")
with open(out,"w",encoding="utf-8") as f:f.write("\n".join(L)+"\n")
print("wrote",out,"gate_reads",len(recs),"unique_sites",len(set(r[0] for r in recs)),"v73",callc,jmpc)
