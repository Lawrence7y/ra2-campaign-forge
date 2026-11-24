import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R
import audit_lib as A

for va in [0x81784C, 0x817830, 0x817854, 0x817828]:
    print(f"string @{va:08X} = {R.cstr(va, 100)!r}")

calls, jmps, stats = A.sweep_calls(R.BIN)

def show_callers(tgt):
    sites = calls.get(tgt, [])
    print(f"\ncallers of {tgt:08X}: {len(sites)}")
    for s in sites:
        print(f"   {s:08X}")
    return sites

print("\n=== BATTLE enum 0x52CB90 ===")
R.dump(0x52CB90, 0x200)

print("\n=== FindIndex caller 0x52F260 ===")
R.dump(0x52F260, 0x200)
show_callers(0x52F260)

print("\n=== caller of BATTLEenum @0x685609 context (0x685DC0/0x685609) ===")
# 0x685609 is within some function; find its entry via scan
R.dump(0x6855C0, 0x100)

print("\n=== 0x52C605 / 0x52DF25 / 0x52E0C4 callers ===")
for t in [0x52C605,0x52DF25,0x52E0C4]:
    show_callers(t)
