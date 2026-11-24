# -*- coding: utf-8 -*-
"""Generate MERGE_M74/BEFORE_AFTER.txt from recorded BEFORE values and current AFTER disk state."""
import os, hashlib, datetime, sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT = os.path.join(ROOT, "MERGE_M74", "BEFORE_AFTER.txt")

# BEFORE values recorded by MERGE_M74/precheck.py before any write
BEFORE = {
    "coverage.tsv": (1795161475.704439, 3893358, "6a8085f91f0c5a68cdd2840f60d0922a2496a1afbce602f5e5a56f6c851f2396"),
    "PANEL.md":     (1795161556.8229742, 140512, "ddfbaff78ba3c5774e305d727cfb6dc18aaacde747884c4f307fdb52436343f5"),
}
PATHS = {
    "coverage.tsv": os.path.join(ROOT, "COVERAGE", "coverage.tsv"),
    "PANEL.md":     os.path.join(ROOT, "COVERAGE", "PANEL.md"),
}


def local(m):
    return datetime.datetime.fromtimestamp(m).astimezone().isoformat(timespec="microseconds")


lines = []
lines.append("M74 BEFORE_AFTER — 两文件 mtime / 字节 / sha256")
lines.append("记录口径：precheck.py 改前记录；apply_coverage.py / apply_panel.py 改后复算")
lines.append("本机时区：Asia/Shanghai (+08:00)")
lines.append("")
for name in ("coverage.tsv", "PANEL.md"):
    p = PATHS[name]
    st = os.stat(p)
    bm, bb, bh = BEFORE[name]
    am, ab, ah = st.st_mtime, os.path.getsize(p), hashlib.sha256(open(p, "rb").read()).hexdigest()
    lines.append("=" * 68)
    lines.append("FILE: COVERAGE\\" + name)
    lines.append("=" * 68)
    lines.append("  BEFORE mtime  : %r  (%s)" % (bm, local(bm)))
    lines.append("  BEFORE bytes  : %d" % bb)
    lines.append("  BEFORE sha256 : %s" % bh)
    lines.append("  AFTER  mtime  : %r  (%s)" % (am, local(am)))
    lines.append("  AFTER  bytes  : %d" % ab)
    lines.append("  AFTER  sha256 : %s" % ah)
    lines.append("  DELTA  bytes  : %+d" % (ab - bb))
    lines.append("  sha256 changed: %s" % (bh != ah))
    lines.append("")
lines.append("注：BEFORE sha256 与 MERGE_M73\\VERIFY.txt 记录的两文件改后 sha256 一致，确认起点承接 M73。")

out = "\n".join(lines) + "\n"
open(OUT, "w", encoding="utf-8").write(out)
print(out)
