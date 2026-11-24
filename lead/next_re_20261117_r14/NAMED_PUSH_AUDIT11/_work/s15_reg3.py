import sys, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

rows = json.load(open("verify2.json", encoding="utf-8"))
out = []
for d in rows:
    ct = int(d["factory_ctor_callers"][0], 16)
    print("=" * 100)
    print(f"{d['entry']}  {d['expected_class']}  ctor call@{ct:08X}  factory vt={d['vt']}")
    for i in dis(ct - 0x12, 80):
        print("   " + fmt(i) + ("   <<< ctor call" if i.address == ct else ""))
        if i.address > ct and i.mnemonic == "call":
            break
    print()

print("### 006BB9A0 atexit / caller context")
name, sva, vsz, rawsz, raw = sec_of(0x401000)
blob = DATA[raw:raw + rawsz]
needle = (0x6BB9A0).to_bytes(4, "little")
p = blob.find(needle)
hits = []
while p >= 0:
    hits.append(sva + p)
    p = blob.find(needle, p + 1)
print("imm refs:", [f"{h:08X}" for h in hits])
for h in hits:
    print(f"  {h:08X} ctx={hexs(h - 10, 26)}")
print("direct callers:", [f"{c:08X}" for c in direct_callers(0x6BB9A0)])
