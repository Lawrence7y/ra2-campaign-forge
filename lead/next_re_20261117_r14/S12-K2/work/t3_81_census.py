"""T3: full-image census of [reg+0x81] byte accesses and [reg+0x80] dword accesses
(which cover byte 0x81). Checks ALL operands (not just op0) per discipline E.
Also dump 0x5F4D30 full and contexts of 0x81 accesses in 0x43F180 / 0x7014A0 / 0x5F4D30.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import capstone
from re_helper import Bin, disasm_range, fmt_insn, md, load_atlas, EVID
from collections import Counter

b = Bin(); L=[]
m = md(skipdata=True)
t = b.sec(".text")
data = b.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
rows,_ = load_atlas()
def fnof(va):
    for r in rows:
        if r["_va"]<=va<r["_va"]+r["_size"]: return r["_va"]
    return None

reads81=[]; writes81=[]; rw81=[]; dword80=[]
for ins in m.disasm(data, t["va"]):
    if ins.id==0: continue
    for op in ins.operands:
        if op.type!=capstone.x86.X86_OP_MEM: continue
        mem=op.mem
        if mem.base==0: continue
        # exact byte at +0x81
        if mem.disp==0x81 and op.size==1:
            rec=(ins.address,ins.mnemonic,ins.op_str,op.access,fnof(ins.address))
            if op.access==capstone.CS_AC_READ: reads81.append(rec)
            elif op.access==capstone.CS_AC_WRITE: writes81.append(rec)
            else: rw81.append(rec)
        # dword access at +0x80 covers byte 0x81
        if mem.disp==0x80 and op.size==4:
            dword80.append((ins.address,ins.mnemonic,ins.op_str,op.access,fnof(ins.address)))

L.append("T3 [reg+0x81] BYTE census (byte-width operands only)")
L.append("reads  = %d"%len(reads81))
L.append("writes = %d"%len(writes81))
L.append("read+write(RMW) = %d"%len(rw81))
L.append("dword [reg+0x80] accesses covering byte 0x81 = %d"%len(dword80))
L.append("")
L.append("--- all byte [reg+0x81] WRITES (site mnemonic opstr fn) ---")
for r in writes81: L.append("  %08X %-8s %-46s fn=%s"%(r[0],r[1],r[2],("%08X"%r[4]) if r[4] else "?"))
L.append("--- all byte [reg+0x81] READS ---")
for r in reads81: L.append("  %08X %-8s %-46s fn=%s"%(r[0],r[1],r[2],("%08X"%r[4]) if r[4] else "?"))
L.append("--- RMW ---")
for r in rw81: L.append("  %08X %-8s %-46s fn=%s"%(r[0],r[1],r[2],("%08X"%r[4]) if r[4] else "?"))
L.append("--- dword [reg+0x80] (covers 0x81) ---")
for r in dword80: L.append("  %08X %-8s %-46s access=%d fn=%s"%(r[0],r[1],r[2],r[3],("%08X"%r[4]) if r[4] else "?"))

# distribution by write value (immediate source) — inspect writes
L.append(""); L.append("write-value distribution (immediate byte written):")
wc=Counter()
for r in writes81:
    # parse last token after comma
    last=r[2].split(",")[-1].strip()
    wc[last]+=1
for k,v in wc.most_common(): L.append("  %-20s %d"%(k,v))

# full 0x5F4D30 (Limbo)
L.append(""); L.append("="*88); L.append("0x5F4D30 full (Limbo, atlas size 398)"); L.append("="*88)
for ins in disasm_range(b,0x5F4D30,0x5F4D30+398,skipdata=True): L.append(fmt_insn(ins))

# 0x81 access contexts in key functions
for fa,fs,name in [(0x43F180,2443,"0x43F180"),(0x7014A0,1014,"0x7014A0"),(0x5F4D30,398,"0x5F4D30")]:
    L.append(""); L.append("="*88); L.append("byte[+0x81] sites inside %s"%name); L.append("="*88)
    insns=disasm_range(b,fa,fa+fs,skipdata=True)
    for idx,ins in enumerate(insns):
        hit=False
        if ins.id:
            for op in ins.operands:
                if op.type==capstone.x86.X86_OP_MEM and op.mem.base!=0:
                    if op.mem.disp==0x81 and op.size==1: hit=True
                    if op.mem.disp==0x80 and op.size==4: hit=True
        if hit:
            for x in insns[max(0,idx-3):min(len(insns),idx+4)]: L.append(fmt_insn(x))
            L.append("---")

out=os.path.join(EVID,"t3_81_census.txt")
with open(out,"w",encoding="utf-8") as f: f.write("\n".join(L)+"\n")
print("wrote",out,"lines",len(L),"reads",len(reads81),"writes",len(writes81),"rw",len(rw81),"dword80",len(dword80))
