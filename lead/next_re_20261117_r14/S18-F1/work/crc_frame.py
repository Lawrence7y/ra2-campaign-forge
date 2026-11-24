"""S18-F1: frame CRC traversal + execute timing + frame sync ordering.
capstone skipdata=True. Independent PE parsing (no atlas).
"""
import sys, re
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import disasm_insns, disasm, u32, read

def dump(label, va, nins):
    print(f"\n===== {label} @0x{va:08X} =====")
    for ins in disasm_insns(va, nins):
        print(f"  {ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}")

# Frame CRC full function - find loop structure, arrays, RNG call
print("===== Frame CRC 0x64DAB0 full (skipdata; look for loops/arrays) =====")
insns = disasm_insns(0x64DAB0, 500)
# print all but compress: show calls, [glob] loads, loop cmp/jg
for ins in insns:
    o=ins.op_str
    interesting = (ins.mnemonic in ('call','jmp') or
                   re.search(r'\[0x[0-9a-fA-F]+\]',o) or
                   ins.mnemonic.startswith('j'))
    if interesting:
        print(f"  {ins.address:08X}: {ins.mnemonic:8s} {o}")

# Count loops: look for 'inc reg' + 'cmp reg, [glob]' + backward jg/jl pattern
print("\n===== Frame CRC: array/Count globals referenced =====")
gset={}
for ins in insns:
    for m in re.finditer(r'\[(0x[0-9a-fA-F]+)\]', ins.op_str):
        va=int(m.group(1),16)
        if va>=0xA00000: gset.setdefault(va,[]).append(ins.address)
for va in sorted(gset):
    print(f"  0x{va:08X}: {len(gset[va])} refs @ {[hex(x) for x in gset[va][:8]]}")

# Execute timing in 0x64C380: find Timestamp==CurrentFrame check
dump("Queue_ValidateExec 0x64C380 2nd half", 0x64C434, 130)

# Frame sync: MainLogicFrame tail
dump("MainLogicFrame tail 0x55DE00-0x55DE90", 0x55DE00, 45)

# GameRunner ordering 0x48CE70+
dump("GameRunner 0x48CE70", 0x48CE70, 30)

# Build_FrameInfo 0x649CA0 - timestamp/delay computation
dump("Build_FrameInfo 0x649CA0 head", 0x649CA0, 60)

# LatencyFudge handler 0x4C7F35
dump("LatencyFudge handler 0x4C7F35", 0x4C7F35, 40)

# MegaMission secondary buffer references 0xA83EDC
print("\n===== refs to MegaMission buffer 0xA83EDC / 0xA83ED0 =====")
for g in (0xA83EDC,0xA83ED0,0xA8B554,0xA8B1F8,0xA8B1DC):
    from pe_util import scan_imm32_refs
    refs=scan_imm32_refs(g)
    refs=[a for a,s in refs if 0x400000<=a<0x900000]
    print(f"  0x{g:08X}: {len(refs)} code refs -> {[hex(a) for a in refs[:12]]}")
