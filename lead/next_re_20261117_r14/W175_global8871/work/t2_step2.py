"""Task 2 step 2: disassemble INI readers that write +0x1808 / +0x172C and extract string args."""
import sys, os, re, capstone
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN, md, disasm, fmt

EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out=[]
def P(s=""): out.append(str(s))

def readable(va,maxn=100):
    try:
        b=BIN.read(va,maxn)
    except Exception:
        return None
    s=b.split(b"\x00")[0]
    if len(s)==0 or len(s)>maxn: return None
    # printable ascii
    if all(32<=c<127 for c in s): return s
    return None

def str_args(start,end):
    m=md(); d=BIN.read(start,end-start+16)
    res=[]
    for insn in m.disasm(d,start):
        if insn.id==0: continue
        for op in insn.operands:
            if op.type==capstone.x86.X86_OP_IMM:
                v=op.imm & 0xFFFFFFFF
                s=readable(v)
                if s and len(s)>=2:
                    res.append((insn.address,insn.mnemonic,insn.op_str,v,s))
    return res

# 1) verify raw bytes at 0x6677B3 vs ledger 0x6667B3
P("=== verify +0x1808 write site ===")
for va in [0x6677B3,0x6667B3]:
    P("  raw@%08X: %s"%(va," ".join("%02X"%b for b in BIN.read(va,10))))

# 2) function 0x66CF70 (contains +0x1808 write 0x66CFDC)
P("\n=== disasm 0x66CF70..0x66CF70+0x200 ===")
P(fmt(disasm(0x66CF70,0x200)))
P("\n=== string args in 0x66CF70..0x66D150 ===")
for x in str_args(0x66CF70,0x66D150): P("  %08X %-5s %-40s -> %08X %r"%x)

# 3) find function entry containing 0x66BAA3: scan call targets near 0x66B9xx
calls,jmps,stats=A.sweep_calls(BIN)
entries=sorted([t for t in calls if 0x66B700<=t<=0x66BB00])
P("\n=== call targets in 0x66B700..0x66BB00: %s ==="%[hex(x) for x in entries])

# 4) disassemble around 0x66BAA3 and find string args
P("\n=== disasm 0x66B9C0..0x66BAE0 (around +0x172C write 0x66BAA3) ===")
P(fmt(disasm(0x66B9C0,0x140)))
P("\n=== string args in 0x66B8F0..0x66BBB0 ===")
for x in str_args(0x66B8F0,0x66BBB0): P("  %08X %-5s %-40s -> %08X %r"%x)

with open(EVID+r"\t2_ini_readers.txt","w",encoding="utf-8") as f: f.write("\n".join(out)+"\n")
print("file written; lines=%d"%len(out))
