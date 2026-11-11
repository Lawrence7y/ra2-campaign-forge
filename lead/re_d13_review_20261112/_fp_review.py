# -*- coding: utf-8 -*-
"""独立评审方指纹实算件（写域内自建；只读仓库其他文件）。

实算 sha256：
  1) 冻结母本两件（对照任务书给定值）
  2) 被评审候选件本身（留档用）
  3) 对方自跑的 _selftest_stdout.txt
"""
import hashlib
import os
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
targets = [
    ("mother_probe_v2", REPO / "lead" / "qc161_u0400_trip" / "_drive_c2_x_probe_v2.py"),
    ("mother_earlyclose", REPO / "lead" / "qc161_u0400_trip" / "_drive_c2_x_earlyclose.py"),
    ("candidate", REPO / "lead" / "re_d13_ruling_20261112" / "e3_stack_sampler_candidate.py"),
    ("their_selftest_stdout", REPO / "lead" / "re_d13_ruling_20261112" / "_selftest_stdout.txt"),
    ("ruling_receipt_611", REPO / "lead" / "re_d13_ruling_20261112" / "RULING_RECEIPT_611.md"),
]

EXPECT = {
    "mother_probe_v2": "6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9",
    "mother_earlyclose": "2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1",
}

print("python -I -X utf8 独立指纹实算（hashlib.sha256 直算）")
for name, p in targets:
    if not p.exists():
        print("%-24s MISSING %s" % (name, str(p)))
        continue
    data = p.read_bytes()
    h = hashlib.sha256(data).hexdigest()
    nline_lf = data.count(b"\n")
    nline_crlf = data.count(b"\r\n")
    n_cr_only = data.count(b"\r") - nline_crlf
    mark = ""
    if name in EXPECT:
        mark = "EXPECT-MATCH" if h == EXPECT[name] else "EXPECT-MISMATCH!!"
    print("%-24s %s %8d B  lines(lf=%d crlf=%d cr_only=%d) %s %s"
          % (name, h, len(data), nline_lf, nline_crlf, n_cr_only, mark, p.name))
