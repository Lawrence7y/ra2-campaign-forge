import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R
import audit_lib as A

print("=== string @ 0x817854 ===")
print(repr(R.cstr(0x817854, 80)))

print("\n=== base Load 0x410A60 full (key reads) ===")
R.dump(0x410A60, 0x240)

print("\n=== sweep direct-call callers ===")
calls, jmps, stats = A.sweep_calls(R.BIN)
print("stats:", stats)
# who calls each key function
for tgt, label in [(0x46CE10,"CreateFromINIList"),(0x46CC90,"FindIndex"),
                   (0x46CCD0,"slot25/Load"),(0x52CB90,"BATTLE enum"),
                   (0x46CB60,"noinit_t"),(0x471500,"CampaignScore::slot0"),
                   (0x46FC00,"CampaignScore::slot1")]:
    sites = calls.get(tgt, [])
    print(f"\n{label} {tgt:08X}: {len(sites)} call sites")
    for s in sites:
        print(f"   {s:08X}")
