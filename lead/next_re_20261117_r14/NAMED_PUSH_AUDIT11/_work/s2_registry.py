import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

print("### ctor 006C2A40.. via 006BCDF0 caller")
for va in (0x6BCDF0,):
    print(f"-- callers-of-ctor site @{va:08X}")
    ins = dis(va, 120)
    for i in ins:
        print("   " + fmt(i))

print()
print("### scan whole .text for 'call dword ptr [reg + 0xc]' (slot3 dispatch candidates)")
name, sva, vsz, rawsz, raw = sec_of(0x401000)
blob = DATA[raw:raw + rawsz]
cands = []
for i in range(len(blob) - 3):
    # ff /2 with modrm mod!=3 and rm != 4/5 odd forms: shapes ff 50 0c, ff 51 0c, ff 52 0c, ff 53 0c,
    # ff 55 0c, ff 56 0c, ff 57 0c
    if blob[i] == 0xFF and blob[i + 1] in (0x50, 0x51, 0x52, 0x53, 0x55, 0x56, 0x57) and blob[i + 2] == 0x0C:
        cands.append(sva + i)
print("count =", len(cands))
for c in cands:
    print(f"   {c:08X}")
