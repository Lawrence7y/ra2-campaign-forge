"""
S17-F1: proper function-end boundary (last ret before next entry), IAT resolution,
TEventClass swizzle field registrations, and full E8 call inventory of Save_Core.
"""
import pe_util as P
from capstone import x86_const
import struct

def f(ins):
    return f"0x{ins.address:08X}  {ins.bytes.hex():<20s} {ins.mnemonic:<8s} {ins.op_str}"

# ===== 1. IAT resolution (pefile channel) =====
print("="*100); print("1. IAT slot resolution via pefile (independent channel)"); print("="*100)
for va in [0x7E11C4,0x7E15C8,0x7E15CC,0x7E15E4,0x7E15E8,0x7E15F4,0x7E15F8,0x7E15FC,0x7E1600]:
    print(f"  0x{va:08X} -> {P.iat_name(va)}")

# ===== 2. Function end = LAST ret before next function entry =====
print("\n"+"="*100); print("2. Function end (capstone: last ret in [entry, next_entry)) — atlas-independent size"); print("="*100)
def last_ret(entry, limit):
    insns = P.disasm(entry, limit-entry)
    rets = [i for i in insns if i.mnemonic in ('ret','retf')]
    if not rets: return None
    r = rets[-1]
    return r.address + r.size
# known next entries
for entry, nxt, label in [(0x67D300,0x67E440,'Save_Core'),(0x67CEF0,0x67D300,'outer'),
                          (0x67E440,0x67EB00,'Load_Core'),(0x67FDF0,0x67FE70,'tmpl#1'),
                          (0x6CF240,0x6CF2C0,'HereIAm'),(0x6CF350,0x6CF410,'Reset'),
                          (0x6CF2C0,0x6CF320,'slot6')]:
    r = last_ret(entry, nxt)
    print(f"  {label} 0x{entry:X}: last-ret-end=0x{r:X} size=0x{r-entry:X}={r-entry} (next_entry=0x{nxt:X})")

# ===== 3. TEventClass ctor swizzle field registrations =====
print("\n"+"="*100); print("3. TEventClass ctor 0x71F8C0 — Here_I_Am registrations (+0x28/+0x30/+0x54)"); print("="*100)
for ins in P.disasm(0x71F8C0, 0x71F940-0x71F8C0):
    print("   " + f(ins))

# ===== 4. Save_Core full E8 call inventory with targets =====
print("\n"+"="*100); print("4. Save_Core 52 direct E8 calls (full list, ordered)"); print("="*100)
insns = P.disasm(0x67D300, 0x67E440-0x67D300)
calls = []
for ins in insns:
    if ins.mnemonic=='call' and ins.bytes[0]==0xE8:
        for op in ins.operands:
            if op.type==P.X86_OP_IMM:
                calls.append((ins.address, op.imm)); break
for i,(site,tgt) in enumerate(calls,1):
    print(f"  {i:2d}. 0x{site:08X} -> 0x{tgt:08X}")

# unique targets & counts
from collections import Counter
c = Counter(t for _,t in calls)
print("\n  unique targets (count):")
for t,n in sorted(c.items()):
    print(f"    0x{t:08X} x{n}")
