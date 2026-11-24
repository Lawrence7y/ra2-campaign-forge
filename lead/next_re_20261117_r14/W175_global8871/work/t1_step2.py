"""Task 1 step 2: characterize 0x665650 — extent, vftable stores, callers."""
import sys, os, capstone
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN, md, disasm

EVID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out = []
def P(s=""): out.append(str(s))

# --- 1) find extent: linear disasm from 0x665650 up to first `ret` at/after 0x665650
m = md()
data = BIN.read(0x665650, 0x8000)
first_ret = None
n = 0
for insn in m.disasm(data, 0x665650):
    if insn.id == 0:
        continue
    n += 1
    if insn.mnemonic.startswith("ret") and insn.address > 0x665650:
        first_ret = insn.address
        break
P("0x665650 first ret at %s after %d insns" % (hex(first_ret) if first_ret else "NOT FOUND", n))

# --- 2) scan for vftable-like immediate stores to [esi+off] with off < 0x40
vft_stores = []
if first_ret:
    data2 = BIN.read(0x665650, first_ret - 0x665650 + 16)
    for insn in m.disasm(data2, 0x665650):
        if insn.id == 0:
            continue
        ops = insn.operands
        if len(ops) == 2 and insn.mnemonic == "mov":
            dst, src = ops
            if dst.type == capstone.x86.X86_OP_MEM and src.type == capstone.x86.X86_OP_IMM:
                imm = src.imm & 0xFFFFFFFF
                # .rdata is 0x7E1000..0x811000; vftables live there
                if 0x7E1000 <= imm < 0x811000:
                    mem = dst.mem
                    if mem.base == capstone.x86.X86_REG_ESI and mem.index == 0:
                        vft_stores.append((insn.address, mem.disp, hex(imm), insn.op_str))
P("vftable-like stores to [esi+off] in 0x665650..%s:" % (hex(first_ret) if first_ret else "?"))
for x in vft_stores:
    P("  %08X  [esi+%s] = %s   (%s)" % x)

# --- 3) all callers of 0x665650 via audit_lib.sweep_calls (byte channel, skipdata=True)
calls, jmps, stats = A.sweep_calls(BIN)
P("")
P("sweep_calls stats: %s" % stats)
P("callers of 0x665650: %s" % [hex(x) for x in calls.get(0x665650, [])])

# --- 4) also find where [esi] gets vftable anywhere in first 0x200 bytes using raw byte pattern C7 06 <vft>
# mov dword ptr [esi], imm32  == C7 06 xx xx xx xx
raw = BIN.read(0x665650, 0x8000)
i = 0
hits = []
while True:
    j = raw.find(b"\xc7\x06", i)
    if j < 0: break
    imm = int.from_bytes(raw[j+2:j+6], 'little')
    if 0x7E1000 <= imm < 0x811000:
        hits.append((0x665650+j, hex(imm)))
    i = j+1
P("raw C7 06 [esi],imm(vft-range) hits in 0x665650 region: %s" % hits[:20])

with open(EVID + r"\t1_ctor_665650_extent.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
print("\n".join(out))
