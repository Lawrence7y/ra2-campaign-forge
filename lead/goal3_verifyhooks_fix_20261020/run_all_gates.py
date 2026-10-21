"""三档门禁实跑：调用 v2 的 main()，用 v2 ini 对 P1+SBH 档。"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead"
FIX = LEAD / "goal3_verifyhooks_fix_20261020"
WORK = LEAD / "goal3_p1sbh_merge_20261020/_work"

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("vh2", FIX / "verify_hooks.v2.py")
vh2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh2)

ini_mother = ROOT / "ra2render/ra2render.ini"
ini_v2 = FIX / "ra2render.ini.v2"

cases = [
    ("MOTHER (mother ini)", ROOT / "ra2render/blitter_hooks.cpp", ini_mother),
    ("P1 (mother ini)", WORK / "p1base.cpp", ini_mother),
    ("P1+SBH (mother ini)", WORK / "out_fuzz0.cpp", ini_mother),
    ("P1+SBH (v2 ini)", WORK / "out_fuzz0.cpp", ini_v2),
]

results = []
for label, cpp, ini in cases:
    print("=" * 70)
    print("CASE:", label)
    print("=" * 70)
    vh2.CPP = cpp
    vh2.INI = ini
    vh2.INI_COPY = ini  # 避免 ra2youli 副本干扰
    rc = vh2.main()
    results.append((label, rc))
    print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
for label, rc in results:
    print(f"  {label:24} RC={rc}  {'PASS' if rc == 0 else 'FAIL'}")
