import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R

for va in [0x81B2EC,0x81B304,0x81B2D0,0x81B490]:
    try: print(f"str@{va:08X} = {R.cstr(va,80)!r}")
    except Exception as e: print(va,e)

print("\n=== 0x46D2xx (before 0x46D360, references CampaignScoreClass vtable) ===")
R.dump(0x46D300, 0x70)
print("\n=== 0x471500 (CampaignScoreClass::slot0) ===")
R.dump(0x471500, 0x90)
print("\n=== 0x471520 (CampaignEndScoreClass::slot0) ===")
R.dump(0x471520, 0x90)
