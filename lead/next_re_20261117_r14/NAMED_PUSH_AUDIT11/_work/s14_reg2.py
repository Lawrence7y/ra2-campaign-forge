import sys, json, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

rows = json.load(open("verify2.json", encoding="utf-8"))

print("### per-row factory ctor call site inside init fn, with CLSID + CoRegisterClassObject")
for d in rows:
    ctorsite = d["factory_ctor_callers"][0]
    va = int(ctorsite, 16)
    print(f"== {d['entry']} factory_ctor={int(d['factory_ctor_site_bytes'][-0:] or 0,16) if False else ''}"
          f" call@{ctorsite}  expected_class={d['expected_class']}")
    # dump from call site backwards 40 bytes / forward 40
    start = va - 32
    for i in dis(start, 96):
        mark = "  <<<" if i.address == va else ""
        print("   " + fmt(i) + mark)
        if i.mnemonic == "call" and i.address > va + 10:
            break
    print()

print("### is 006BB9A0 atexit-registered (push 006BB9A0; call 0x7C978A)?")
name, sva, vsz, rawsz, raw = sec_of(0x401000)
blob = DATA[raw:raw + rawsz]
needle = (0x6BB9A0).to_bytes(4, "little")
p = blob.find(needle)
hits = []
while p >= 0:
    hits.append(sva + p)
    p = blob.find(needle, p + 1)
print("imm refs to 006BB9A0:", [f"{h:08X}" for h in hits])
for h in hits:
    print(f"  ctx {h-8:08X}: {hexs(h-8, 24)}")
print()
print("### who calls 006BB9A0 (direct E8)")
for c in direct_callers(0x6BB9A0):
    print(f"  {c:08X}  ctx={hexs(c-16,24)}")
print()
print("### 007CD8EA context (caller of init)")
for i in dis(0x7CD880, 160):
    print("   " + fmt(i))
