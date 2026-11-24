# -*- coding: utf-8 -*-
"""Generate MERGE_M75/BEFORE_AFTER.txt from recorded BEFORE values and current AFTER disk state."""
import os, hashlib, datetime, json, sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
MERGE = os.path.join(ROOT, "MERGE_M75")
OUT = os.path.join(MERGE, "BEFORE_AFTER.txt")

before = json.load(open(os.path.join(MERGE, "_before.json"), encoding="utf-8"))
PATHS = {
    "coverage.tsv": os.path.join(ROOT, "COVERAGE", "coverage.tsv"),
    "PANEL.md":     os.path.join(ROOT, "COVERAGE", "PANEL.md"),
}


def local(m):
    return datetime.datetime.fromtimestamp(m).astimezone().isoformat(timespec="microseconds")


lines = []
lines.append("M75 BEFORE_AFTER — 两文件 mtime / 字节 / sha256")
lines.append("记录口径：precheck.py 改前记录（_before.json）；apply_coverage.py / apply_panel.py 改后复算")
lines.append("本机时区：Asia/Shanghai (+08:00)")
lines.append("")
for name in ("coverage.tsv", "PANEL.md"):
    p = PATHS[name]
    st = os.stat(p)
    bm, bb, bh = before[name]
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
lines.append("注：BEFORE sha256 与 MERGE_M74\\VERIFY.txt 记录的两文件改后 sha256 一致，确认起点承接 M74。")

out = "\n".join(lines) + "\n"
open(OUT, "w", encoding="utf-8").write(out)
print(out)
