"""用 verify_hooks 的原始 main() 逻辑，对「P1+SBH 合并件」重跑 ③ 门（只读）。

用法：python run_gate_on_merged.py
原理：import tools/verify_hooks.py 后把模块级输入路径改指合并件，再调 main()。
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead"
MERGED = LEAD / "goal3_p1sbh_merge_20261020/_work/out_fuzz0.cpp"

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("vh", ROOT / "tools" / "verify_hooks.py")
vh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh)

print("=== baseline (mother) ===")
rc_mother = vh.main()

print()
print("=== merged (P1+SBH) ===")
vh.CPP = MERGED
rc_merged = vh.main()

print()
print("RC_MOTHER=%d  RC_MERGED=%d" % (rc_mother, rc_merged))
sys.exit(0)
