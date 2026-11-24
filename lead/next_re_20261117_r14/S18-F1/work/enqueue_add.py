"""S18-F1: enqueue Add operation + delay/rollback + dual-check frame sync."""
import sys, re
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import disasm_insns, disasm, u32, scan_rel32_calls, scan_imm32_refs

def dump(label, s, n):
    print(f"\n===== {label} @0x{s:08X} =====")
    for ins in disasm_insns(s, n):
        print(f"  {ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}")

# After FillEvent_Noopt call at 0x48CA43 - what's the enqueue operation?
dump("UI pump after FillEvent_Noopt (0x48CA43)", 0x48CA30, 60)
# Produce caller
dump("Produce caller 0x6AA7E7 (event add)", 0x6AA7D0, 55)
# Find function that copies event to QueuedEvents: look at WriteEvent helper candidates
# 0x4C7D5C/0x4C7DA9 region referenced LastEventIndex - dump
dump("Event add helper 0x4C7D40", 0x4C7D40, 70)
# 0x646EF0 region (CreateClickedMission caller adds event?)
dump("0x646EF0", 0x646EF0, 40)

# Delay: Build_FrameInfo delay computation - find ecx source
dump("Build_FrameInfo 0x649CA0 (full head)", 0x649CA0, 80)
# execute-time delay check in 0x64C380 around 0x64C6E2 (desync compare)
dump("Desync compare 0x64C6D0", 0x64C6D0, 40)
# 0x64C6EL region delay
dump("Timestamp rewrite 0x64C3A3 already seen; exit handling 0x64C7B6", 0x64C7B0, 30)

# Who sets executed bit [event+1]&1?
print("\n===== writes to byte [reg+1] near event loop (scan for 'or byte ptr ...,1') =====")
for ins in disasm_insns(0x64C380, 700):
    if 'byte ptr' in ins.op_str and '0x1' in ins.op_str and ins.mnemonic in ('or','mov','and'):
        # print if near queue ring addressing
        if '8b420' in ins.op_str or 'esi' in ins.op_str or 'eax' in ins.op_str:
            print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")
