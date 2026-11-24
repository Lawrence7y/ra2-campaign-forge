# -*- coding: utf-8 -*-
"""Copy Q1's probe into reviews/ with only its OUT path redirected, so rerunning
does not modify any pre-existing file (铁律: 不改既有文件)."""
from pathlib import Path

W = Path(r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F")
src = (W / "_w9_q1.py").read_text(encoding="utf-8")
lines = src.splitlines(keepends=True)
hits = 0
out = []
for ln in lines:
    if ln.startswith("OUT = "):
        ln = ('OUT = ROOT + r"\\lead\\re_line_20261105\\W9_SINGLESTEP_7CFC9F'
              '\\reviews\\_Q1_exact_rerun_out.txt"\n')
        hits += 1
    out.append(ln)
assert hits == 1, "expected exactly one OUT assignment, got %d" % hits
(W / "reviews" / "_Q1_exact_rerun.py").write_text("".join(out), encoding="utf-8")
print("copied; OUT line redirected; hits =", hits)
