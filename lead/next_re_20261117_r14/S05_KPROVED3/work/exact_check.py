import sys,json,struct
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work")
from pe_helpers import *
from capstone import *
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True
# exact disasm of 0070BF50 around 0x70c240..0x70c250 and entry
lo=0x70BF50
for (a,n) in [(0x70c240,0x20),(0x70BF50,0x30)]:
    print(f"--- disasm {a:08X} +{n} ---")
    for i in MD.disasm(bytes_at(a,n),a):
        print(f"  {i.address:08X} +0x{i.address-lo:03X}  {i.bytes.hex():<16} {i.mnemonic:<8} {i.op_str}")
# 005F9720 loop region 0x5F98E0..0x5F9900
print("--- 005F9720 loop region ---")
lo2=0x5F9720
for i in MD.disasm(bytes_at(0x5F98D0,0x50),0x5F98D0):
    print(f"  {i.address:08X} +0x{i.address-lo2:03X}  {i.mnemonic:<8} {i.op_str}")
