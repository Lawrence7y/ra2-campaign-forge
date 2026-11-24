"""S18-F1 initial exploration: verify key addresses/clues from binary.
capstone skipdata=True. No atlas dependency.
"""
import sys, struct
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import disasm, disasm_insns, u32, read, sections, va2off

def dump(label, va, nins):
    print(f"\n===== {label} @ 0x{va:08X} ({nins} insns) =====")
    for ins in disasm_insns(va, nins):
        print(f"  {ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}")

# 1. TEventClass ctor (from S17-F1 clue): +0x28/+0x30/+0x54 swizzle fields
dump("TEventClass ctor (alleged) 0x71F8C0", 0x71F8C0, 60)

# 2. network event executor 0x4C6CB0 (head)
dump("NetworkEvent::Execute 0x4C6CB0 head", 0x4C6CB0, 60)

# 3. jump table at 0x4C8114: 0x2D (45) dwords
print("\n===== jump table @ 0x4C8114 (48 dwords) =====")
for i in range(48):
    v = u32(0x4C8114 + 4*i)
    print(f"  [{i:#04x}] +{4*i:#05x} @0x{0x4C8114+4*i:08X} = {v:#010x}")

# 4. validate/execute 0x64C380 head + around call 0x4C6CB0
dump("Queue_ValidateExecute 0x64C380 head", 0x64C380, 50)

# 5. frame CRC 0x64DAB0 head
dump("Compute_Frame_CRC 0x64DAB0 head", 0x64DAB0, 40)

# 6. key globals raw dwords
print("\n===== key globals =====")
for name, va in [("CurrentFrame",0xA8ED84),("CurrentFrameCRC",0xAC51FC),
                 ("QueuedEvents_base",0xA802D4),("LastEventIndex",0xA802C8),
                 ("NextPacketIndex",0xA802D0),("Queue_ring_base",0x8B4204),
                 ("Queue_count",0x8B41F8),("Queue_readcursor",0x8B41FC),
                 ("LatestFramesCRC",0xB04474),("ExtraSyncInfo",0xB04880),
                 ("TEventClass_vftable_guess",0x7F550C)]:
    print(f"  {name:26s} @0x{va:08X} = {u32(va)!s}")
