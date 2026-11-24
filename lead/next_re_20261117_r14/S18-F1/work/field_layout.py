"""S18-F1: verify NetworkEvent/EventClass field layout from FillEvent writers + executor readers.
Also count Here_I_Am (0x6CF240) registration calls (the '476' claim) and attribute them.
capstone skipdata=True; dual output for cross-check.
"""
import sys, struct, re
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import disasm_insns, read, scan_rel32_calls, sections, u32

FILL = {
    'Place':        (0x4C6AE0, 0x4C6B60),
    'SWPlace_A':    (0x4C6B60, 0x4C6BE0),
    'SWPlace_B':    (0x4C6BE0, 0x4C6C60),
    'Animation':    (0x4C6800, 0x4C6870),
    'Waypoints':    (0x4C6780, 0x4C6800),
    'PlayerBased':  (0x4C6720, 0x4C6780),
    'SellCell':     (0x4C6650, 0x4C66C0),
    'Noopt':        (0x4C66C0, 0x4C6720),
    'Produce1':     (0x4C6970, 0x4C69E0),
    'Produce2':     (0x4C69E0, 0x4C6A60),
    'Produce3':     (0x4C6A60, 0x4C6AE0),
}

def insn_range(start, end):
    out=[]
    for ins in disasm_insns(start, 400):
        if ins.address >= end: break
        out.append(ins)
    return out

print("===== FillEvent writers: writes to [esi+off] (this=NetworkEvent*); mask writes to field base =====")
all_offsets = {}
for name,(s,e) in FILL.items():
    writes=[]
    for ins in insn_range(s,e):
        ops = ins.op_str
        # detect writes `mov ... ptr [esi + 0xNN]` or [esi+reg] patterns
        m = re.search(r'\[esi\s*\+\s*(0x[0-9a-fA-F]+|\d+)\]', ops)
        if ins.mnemonic.startswith('mov') and m:
            off=int(m.group(1),0)
            writes.append((ins.address, off, ins.mnemonic, ops))
        # [edx+4] where edx=esi+off
    print(f"\n-- {name} @0x{s:08X} --")
    for a,off,mn,ops in writes:
        print(f"  {a:08X}: {mn} {ops}   -> [esi+{off:#x}]")
        all_offsets.setdefault(off,[]).append((name,a))

print("\n===== distinct [esi+off] write offsets across all FillEvent_* =====")
for off in sorted(all_offsets):
    sites=all_offsets[off]
    print(f"  +{off:#04x} ({off}): {len(sites)} writes; funcs={sorted(set(x[0] for x in sites))}")

print("\n===== executor 0x4C6CB0 reads [esi+off] in dispatch prologue =====")
for ins in insn_range(0x4C6CB0,0x4C6CD7):
    print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")

# Here_I_Am registration count
print("\n===== Here_I_Am(0x6CF240) call-site count (the '476' claim) =====")
sites = scan_rel32_calls(0x6CF240)
print(f"  total call sites to 0x6CF240 = {len(sites)}")
# also slot6 0x6CF2C0
sites2 = scan_rel32_calls(0x6CF2C0)
print(f"  total call sites to 0x6CF2C0 = {len(sites2)}")
print(f"  union = {len(set(sites)|set(sites2))}")
