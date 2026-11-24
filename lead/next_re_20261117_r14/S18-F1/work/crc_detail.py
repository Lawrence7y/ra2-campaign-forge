"""S18-F1: detailed frame CRC loop structure + checksummer cluster + accumulation."""
import sys, re
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import disasm_insns, u32

def dump_range(label, s, e):
    print(f"\n===== {label} [0x{s:X},0x{e:X}) =====")
    for ins in disasm_insns(s, 900):
        if ins.address>=e: break
        print(f"  {ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}")

# full CRC body through the RNG tail
dump_range("Frame CRC loop-detail region", 0x64DCB3, 0x64DE60)

# Accumulation mix: 0x64DB33..0x64DB4A
dump_range("Frame CRC mix formula", 0x64DB2C, 0x64DB55)

# CalculateChecksum v[13] addresses from clue - verify Checksummer calls
for va, nm in [(0x410410,'AbstractClass::CalculateChecksum v13'),
               (0x5F6250,'ObjectClass::CalculateChecksum v13'),
               (0x70C270,'TechnoClass::CalculateChecksum v13')]:
    dump_range(nm, va, va+0x50)

# Checksummer cluster
for va, nm in [(0x4A1C10,'Checksummer bulk Add'),(0x4A1DE0,'Checksummer Process loop'),
               (0x4A1FB0,'Checksummer GetValue/Commit')]:
    dump_range(nm, va, va+0x40)
