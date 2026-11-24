"""S18-F1: trace enqueue path - references to QueuedEvents/Queue globals, callers of FillEvent_*.
Uses scan_imm32_refs (independent of atlas) + capstone skipdata.
"""
import sys, struct, re
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import scan_imm32_refs, scan_rel32_calls, disasm_insns, read, u32, sections

def find_code_refs(va, label):
    # absolute dword refs in code (mov reg,[imm32] etc)
    refs = scan_imm32_refs(va)
    code_secs = [(x[1], x[1]+x[4]) for x in sections() if x[4]>0 and (x[5]&0x20000000)]
    cr=[(a,s) for a,s in refs if any(lo<=a<hi for lo,hi in code_secs)]
    print(f"\n===== absolute refs to {label} 0x{va:08X}: total={len(refs)}, in-code={len(cr)} =====")
    for a,s in cr[:60]:
        # disassemble a few insns before to show context
        st=max(0xa40000,a-24)
        ctx=disasm_insns(st, 40)
        line=' | '.join(f'{i.address:X}:{i.mnemonic} {i.op_str}' for i in ctx if i.address<=a+4 and i.address>=a-24)
        print(f"  code@0x{a:08X} [{s}]")
    if len(cr)>60: print(f"  ... +{len(cr)-60} more")

for va,label in [(0xA802C8,'LastEventIndex'),(0xA802D0,'NextPacketIndex'),
                 (0xA802D4,'QueuedEvents_base'),(0x8B41F8,'Queue_count'),
                 (0x8B41FC,'Queue_readcursor'),(0x8B4204,'Queue_ring')]:
    find_code_refs(va,label)

print("\n===== callers of FillEvent_* (rel32 call scan) =====")
FILL = {'Produce':0x4C6970,'SellCell':0x4C6650,'Noopt':0x4C66C0,'PlayerBased':0x4C6720,
        'Waypoints':0x4C6780,'Animation':0x4C6800,'Place':0x4C6AE0,'SWPlace':0x4C6B60}
for nm,t in FILL.items():
    sites=scan_rel32_calls(t)
    ss=[a for a,_ in sites]
    print(f"  {nm:12s} 0x{t:08X}: {len(sites)} callers -> {[hex(a) for a in ss[:20]]}")

print("\n===== callers of key sync functions =====")
for nm,t in [('NetFrameSync',0x647260),('Queue_ValidateExec',0x64C380),
             ('Build_SendPacket',0x64BDD0),('Receive_Packet',0x64A0C0),
             ('Build_FrameInfo',0x649CA0),('Compute_Frame_CRC',0x64DAB0),
             ('Exec_dispatch',0x4C6CB0),('MainLogicFrame',0x55D360)]:
    sites=scan_rel32_calls(t); ss=[a for a,_ in sites]
    print(f"  {nm:20s} 0x{t:08X}: {len(sites)} callers -> {[hex(a) for a in ss[:20]]}")
