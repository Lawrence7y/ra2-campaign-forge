import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16_PADD\work")
import re_lib as R
from capstone.x86 import X86_OP_REG, X86_OP_MEM, X86_OP_IMM

# Find "call [reg+disp]" sites where disp matches a target slot offset.
# Then within prior ~60 bytes look for a vptr load "mov reg2,[reg1+0]" pattern,
# indicating the call base is a vptr. Report candidate dispatch sites with slot offsets.
data = R.all_bytes()
# candidate slot offsets: 0xC (slot3), 0x14 (slot5)
TARGET_DISP = {0xC: "slot3", 0x14: "slot5"}

# Build set of function entries from atlas for extent checks
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
entries=[]
with open(ATLAS, encoding="utf-8") as f:
    f.readline()
    for line in f:
        p=line.rstrip("\n").split("\t")
        if len(p)>=2:
            entries.append((int(p[0],16), int(p[1])))
entries.sort()
import bisect
starts=[e[0] for e in entries]
def containing_fn(va):
    i=bisect.bisect_right(starts,va)-1
    if i>=0 and va < entries[i][0]+entries[i][1]:
        return entries[i]
    return None

# Scan .text linearly with capstone from each atlas entry (so we get instruction boundaries)
results=[]
for va,size in entries:
    insns=R.disasm(va,size)
    for idx,ins in enumerate(insns):
        if ins.mnemonic != "call" or not ins.operands:
            continue
        op=ins.operands[0]
        if op.type != X86_OP_MEM:
            continue
        disp=op.mem.disp
        if disp not in TARGET_DISP:
            continue
        base=ins.reg_name(op.mem.base) if op.mem.base is not None else None
        idx_reg=ins.reg_name(op.mem.index) if op.mem.index is not None else None
        if idx_reg is not None:
            continue
        # look back up to 12 instructions for "mov <base or its source>, [reg+0]" (vptr load)
        vptr_load=False
        ctx=[]
        for j in range(max(0,idx-14),idx):
            pi=insns[j]
            ctx.append("%08X %s %s"%(pi.address,pi.mnemonic,pi.op_str))
            if pi.mnemonic=="mov" and len(pi.operands)==2 and pi.operands[1].type==X86_OP_MEM:
                m=pi.operands[1].mem
                if m.disp==0 and ins.reg_name(pi.operands[0].type and pi.operands[0].reg or 0) == base:
                    vptr_load=True
        results.append((ins.address, hex(disp), TARGET_DISP[disp], base, vptr_load, containing_fn(ins.address)))

print("Total call [reg+disp] with disp in {0xC,0x14}:", len(results))
for va,d,slot,base,vl,fn in results[:120]:
    print("%08X slot=%s(%s) base=%s vptr_load=%s fn=%s"%(va,d,slot,base,vl,("%08X+%X"%(fn[0],fn[1])) if fn else "NONE"))
