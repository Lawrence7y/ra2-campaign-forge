"""ECV control G: 纯产物件——只有 write_text，零 print 零出口。
预期：ARTIFACT。合成件，绝不执行。"""
from pathlib import Path

Path("_ecv_ctl_g_out.txt").write_text("rows: 3\nstatus: observed\n", encoding="utf-8")
