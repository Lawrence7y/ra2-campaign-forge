"""Task 1 step 3: constructor tail (return value), destructor, RTTI scan."""
import sys, os, struct, capstone
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN, md, disasm, fmt

EVID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out = []
def P(s=""): out.append(str(s))

# 1) constructor tail: last ~0x100 bytes before ret 0x667a26, check eax=this
ins = disasm(0x667980, 0xF0)
P("=== tail of ctor 0x665650 (0x667980..0x667a26) ===")
P(fmt(ins))

# 2) destructor/cleanup 0x6BE1C0 - dump around the delete and NULL store
P("\n=== cleanup 0x6BEAA0..0x6BEB20 around NULL store 0x6BEABD ===")
P(fmt(disasm(0x6BEAA0, 0x80)))

# scan cleanup for vftable refs (immediate .rdata values in mov/lea)
m = md()
data = BIN.read(0x6BE1C0, 0x1000)
P("\n=== .rdata immediates in 0x6BE1C0..0x6BE1C0+0x1000 ===")
for insn in m.disasm(data, 0x6BE1C0):
    if insn.id == 0: continue
    for op in insn.operands:
        if op.type == capstone.x86.X86_OP_IMM:
            v = op.imm & 0xFFFFFFFF
            if 0x7E1000 <= v < 0x811000:
                P("  %08X  %s %s  ; imm=%08X" % (insn.address, insn.mnemonic, insn.op_str, v))

# 3) RTTI class-name scan: find ASCII strings matching known RA2 class names, and generic COL? pattern
# RTTI string format in MSVC: '.<classname>@@' e.g. '.?AVRulesClass@@'
def ascii_at(va, maxn=80):
    try:
        b = BIN.read(va, maxn)
    except Exception:
        return None
    s = b.split(b"\x00")[0]
    return s

# scan .rdata for patterns '.?AV' followed by name + '@@'
rdata = BIN.sec(".rdata")
buf = BIN.pe.__data__[rdata["raw"]:rdata["raw"]+rdata["rawsize"]]
import re
pats = [b".?AV", b".?AU"]
found = []
for pat in pats:
    i = 0
    while True:
        j = buf.find(pat, i)
        if j < 0: break
        va = rdata["va"] + j
        s = buf[j:j+120].split(b"\x00")[0]
        found.append((va, s))
        i = j + 1
P("\n=== RTTI name strings containing 'Rules' or 'Rad' or near our vfts ===")
for va, s in found:
    if any(k in s.lower() for k in [b"rules", b"rad", b"game", b"super"]):
        P("  %08X  %r" % (va, s))
P("total RTTI '.?AV/.?AU' strings found: %d" % len(found))

with open(EVID + r"\t1_tail_destructor_rtti.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print("\n".join(out[:60]))
print("... (full in file)")
