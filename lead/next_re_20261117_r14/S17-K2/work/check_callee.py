import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P
for a,b in [(0x4A1D50,0x4A1D90),(0x65CA00,0x65CA40)]:
    print(f"=== 0x{a:X} ===")
    for i in P.disasm(a,b-a):
        if i.mnemonic.startswith('.'):
            print(f"  {i.address:08X} {i.bytes.hex():<18s} {i.mnemonic}"); continue
        print(f"  {i.address:08X} {i.bytes.hex():<18s} {i.mnemonic:<7s} {i.op_str}")
