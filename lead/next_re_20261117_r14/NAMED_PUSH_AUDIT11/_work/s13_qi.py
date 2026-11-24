import sys, json, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

print("### 00410260 (QI thunk) body")
for i in dis(0x410260, 200):
    print("   " + fmt(i))
    if i.mnemonic.startswith("ret"):
        break
print()

print("### all rets + return constants in 00410260..00410300")
for i in dis(0x410260, 0xA0):
    if i.mnemonic.startswith("ret") or (i.mnemonic == "mov" and i.op_str.startswith("eax, 0x")):
        print("   " + fmt(i))
print()

print("### CoCreateInstance (0x7e15fc) refs")
name, sva, vsz, rawsz, raw = sec_of(0x401000)
blob = DATA[raw:raw + rawsz]
for iat, label in ((0x7E15FC, "CoCreateInstance"), (0x7E15D8, "CoRegisterClassObject")):
    hs = []
    p = blob.find(iat.to_bytes(4, "little"))
    while p >= 0:
        hs.append(sva + p)
        p = blob.find(iat.to_bytes(4, "little"), p + 1)
    print(f"-- {label}: {len(hs)} refs")
    for h in hs:
        print(f"   {h:08X}  bytes={hexs(h-6,12)}")
