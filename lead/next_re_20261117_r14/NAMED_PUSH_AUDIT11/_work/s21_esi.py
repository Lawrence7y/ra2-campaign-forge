import sys, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

print("### every write to esi inside 006BB9A0..006BE1B0 (init fn)")
for i in dis(0x6BB9A0, 0x2810):
    if i.mnemonic == "mov" and i.op_str.startswith("esi,"):
        print(f"   {i.address:08X}  {i.op_str}")
print()
print("### all 'call esi' sites in init fn and the CLSID pushed just before")
cur = 0x6BB9A0
lines = list(dis(0x6BB9A0, 0x2810))
for i in lines:
    if i.mnemonic == "call" and i.op_str == "esi":
        # find preceding push imm in same block
        prev = [j for j in lines if j.address < i.address][-6:]
        cid = None
        for j in prev:
            if j.mnemonic == "push" and j.op_str.startswith("0x7e9"):
                cid = j.op_str
        print(f"   call esi @{i.address:08X} clsid={cid}")
