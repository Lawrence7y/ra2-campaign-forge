import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

print("### registration block for AircraftType factory (006BCD9A..006BCE20)")
for i in dis(0x6BCDA0, 0x90):
    print("  " + fmt(i))

print()
print("### 006BB9A0 entry prologue (is it init?)")
for i in dis(0x6BB9A0, 64):
    print("  " + fmt(i))

print()
print("### callers of 006BB9A0")
for c in direct_callers(0x6BB9A0):
    print(f"  {c:08X}")
print()
print("### refs to 0x7e15d8 (CoRegisterClassObject IAT)")
name, sva, vsz, rawsz, raw = sec_of(0x401000)
blob = DATA[raw:raw + rawsz]
n = (0x7E15D8).to_bytes(4, "little")
p = blob.find(n)
hs = []
while p >= 0:
    hs.append(sva + p)
    p = blob.find(n, p + 1)
print("count:", len(hs))
for h in hs:
    ins_list = dis(h - 8, 12)
    cont = [i for i in ins_list if i.address <= h < i.address + i.size]
    pre = f"{cont[0].address:08X} {cont[0].mnemonic} {cont[0].op_str}" if cont else "?"
    print(f"  {h:08X} in [{pre}]")
