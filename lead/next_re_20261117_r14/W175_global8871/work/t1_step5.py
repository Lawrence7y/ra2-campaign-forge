"""Task 1 step 5: all writes to [esi+0] in ctor/dtor; search 'Rule' RTTI; find vftables by RTTI locator link."""
import sys, os, struct, capstone, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN, md, disasm, fmt

EVID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out=[]
def P(s=""): out.append(str(s))

m=md()
def writes_to_esi0(start,end):
    data=BIN.read(start,end-start+16)
    res=[]
    for insn in m.disasm(data,start):
        if insn.id==0: continue
        if insn.mnemonic in ("mov","movdword","and","or","add","sub","xor"):
            for op in insn.operands[:1]:
                if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_ESI and op.mem.index==0 and op.mem.disp==0:
                    res.append((insn.address,"%s %s"%(insn.mnemonic,insn.op_str)))
    return res

P("=== all writes to [esi+0] in ctor 0x665650..0x667a26 ===")
for x in writes_to_esi0(0x665650,0x667a26): P("  %08X  %s"%x)
P("=== all writes to [esi+0] in dtor 0x667a30..0x667d00 ===")
for x in writes_to_esi0(0x667a30,0x667d00): P("  %08X  %s"%x)

# search "Rule" anywhere in RTTI file
P("\n=== 'Rule' / 'Session' / 'Scenario' in RTTI strings ===")
txt=open(EVID+r"\t1_rtti_allsecs.txt",encoding="utf-8").read()
for line in txt.splitlines():
    if any(k in line.lower() for k in ["rule", "session", "scenario", "tactical", "countdown"]):
        P("  "+line)

# find RTTI by vftable address: for each vftable value stored to [esi+off] in ctor,
# check the dword BEFORE the vftable (vftable[-1] = COL pointer -> typeinfo) in .rdata.
P("\n=== vftable -> RTTI name for vft values seen in ctor ===")
vft_vals = sorted(set([0x7eb6d4,0x7e4dd8,0x7eabe8,0x7eabc8,0x7eac08,0x7ed90c,0x7f0d3c,0x7f0cfc,0x7e4db8,0x7e4df8]))
for vft in vft_vals:
    try:
        col = BIN.u32(vft-4)  # MSVC: vftable[-4] = COL
        # COL: +0 flags, +4 offset-to-top, +8 cdOffset, +C typeinfo ptr
        ti = BIN.u32(col+0xC)
        nameptr = BIN.u32(ti+8)
        name = BIN.read(nameptr,64).split(b"\x00")[0]
        P("  vft=%08X col=%08X ti=%08X name=%r" % (vft,col,ti,name))
    except Exception as e:
        P("  vft=%08X  ERR %s" % (vft,e))

with open(EVID+r"\t1_esi0_rtti_link.txt","w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print("\n".join(out[:80]))
