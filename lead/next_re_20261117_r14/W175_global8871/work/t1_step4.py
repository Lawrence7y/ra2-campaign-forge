"""Task 1 step 4: search RTTI across ALL sections; hexdump ctor head; dump destructor 0x667a30 fully."""
import sys, os, capstone
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN, md, disasm, fmt

EVID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out=[]
def P(s=""): out.append(str(s))

# 1) hexdump first 0x40 bytes of ctor to verify 'mov [esi],0xf' is real
raw = BIN.read(0x665650, 0x40)
P("=== raw bytes @0x665650 ===")
P(" ".join("%02X" % b for b in raw))

# 2) RTTI scan across ALL sections for '.?AV' '.?AU' and class-name substrings
P("\n=== RTTI-like strings across all sections ===")
rtti_hits = []
for s in BIN.sections:
    buf = BIN.pe.__data__[s["raw"]:s["raw"]+s["rawsize"]]
    for pat in [b".?AV", b".?AU", b".?AW", b".?AX"]:
        i=0
        while True:
            j=buf.find(pat,i)
            if j<0: break
            va=s["va"]+j
            st=buf[j:j+160].split(b"\x00")[0]
            rtti_hits.append((s["name"],va,st))
            i=j+1
for sec,va,st in rtti_hits:
    P("  [%s] %08X  %r" % (sec,va,st[:80]))
P("total: %d" % len(rtti_hits))

# 3) plain-text class name search
P("\n=== plain strings 'Class' across all sections (sample) ===")
cnt=0
for s in BIN.sections:
    buf = BIN.pe.__data__[s["raw"]:s["raw"]+s["rawsize"]]
    # find printable ascii runs
    import re
    for mt in re.finditer(rb"[ -~]{5,}", buf):
        st=mt.group()
        if b"RulesClass" in st or b"RadSiteClass" in st or b"GameClass" in st:
            P("  [%s] %08X  %r" % (s["name"], s["va"]+mt.start(), st[:100]))
            cnt+=1
P("matches: %d" % cnt)

# 4) destructor 0x667a30: look for [esi+0] vftable store and full extent
P("\n=== destructor 0x667a30 head 0x120 bytes ===")
P(fmt(disasm(0x667a30, 0x120)))
m=md()
data=BIN.read(0x667a30,0x800)
P("\n=== writes to [esi+0] in 0x667a30 (first 0x800) ===")
for insn in m.disasm(data,0x667a30):
    if insn.id==0: continue
    if insn.mnemonic=="mov" and len(insn.operands)==2:
        d=insn.operands[0]
        if d.type==capstone.x86.X86_OP_MEM and d.mem.base==capstone.x86.X86_REG_ESI and d.mem.index==0 and d.mem.disp==0:
            P("  %08X  %s %s" % (insn.address,insn.mnemonic,insn.op_str))

with open(EVID+r"\t1_rtti_allsecs.txt","w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print("\n".join(out[:50]))
print("...(full in file)")
