"""S18-F1: caller scan only (FillEvent_* + key sync fns). Independent of atlas."""
import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import scan_rel32_calls

print("===== callers of FillEvent_* =====")
FILL = {'Produce':0x4C6970,'SellCell':0x4C6650,'Noopt':0x4C66C0,'PlayerBased':0x4C6720,
        'Waypoints':0x4C6780,'Animation':0x4C6800,'Place':0x4C6AE0,'SWPlace':0x4C6B60,
        'SWPlace2':0x4C6BE0}
for nm,t in FILL.items():
    ss=[a for a,_ in scan_rel32_calls(t)]
    print(f"  {nm:12s} 0x{t:08X}: {len(ss)} -> {[hex(a) for a in ss]}")

print("\n===== callers of key sync/exec functions =====")
for nm,t in [('NetFrameSync',0x647260),('Queue_ValidateExec',0x64C380),
             ('Build_SendPacket',0x64BDD0),('Receive_Packet',0x64A0C0),
             ('Build_FrameInfo',0x649CA0),('Compute_Frame_CRC',0x64DAB0),
             ('Exec_dispatch',0x4C6CB0),('MainLogicFrame',0x55D360),
             ('HereIAm_s4',0x6CF240),('CreateClickedMission',0x646E90)]:
    ss=[a for a,_ in scan_rel32_calls(t)]
    print(f"  {nm:22s} 0x{t:08X}: {len(ss)} -> {[hex(a) for a in ss[:30]]}")

print("\n===== calls MADE by UI pump 0x48C8B0 (first 0x300 bytes) =====")
from pe_util import disasm_insns
for ins in disasm_insns(0x48C8B0, 200):
    if ins.mnemonic in ('call','jmp') and ins.op_str.startswith('0x'):
        try:
            tgt=int(ins.op_str,16)
        except: tgt=0
        print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")
