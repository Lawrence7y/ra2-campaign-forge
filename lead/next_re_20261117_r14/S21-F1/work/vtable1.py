import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R

VT = 0x7E4A28
print("=== CampaignClass vtable @ 0x7E4A28 (COL @ -4 = 0x7FC920) ===")
for i in range(0, 40):
    va = VT + i*4
    try:
        v = R.u32(va)
    except Exception:
        break
    marker = " <== slot25" if i == 25 else (" <== slot12/GetSize" if i == 12 else "")
    print(f"  slot{i:<2} @{va:08X} = {v:08X}{marker}")

print("\n=== slot12 (0x46D070) GetSize check ===")
R.dump(0x46D070, 0x30)

print("\n=== slot25 (vtable[0x64]) ===")
s25 = R.u32(VT+0x64)
print(f"slot25 = {s25:08X}")
R.dump(s25, 0x300)

print("\n=== 0x46CC90 FindIndex ===")
R.dump(0x46CC90, 0x60)
print("\n=== 0x46CB60 noinit_t ===")
R.dump(0x46CB60, 0x80)
