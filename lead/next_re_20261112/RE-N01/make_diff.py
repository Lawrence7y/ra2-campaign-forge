# -*- coding: utf-8 -*-
"""RE-N01 / make_diff.py —— 生成 candidate.diff（原文 vs 候选的统一 diff）。

只读原件目录，输出写在本轮写域内。不做任何 git 操作。
"""
from __future__ import annotations

import difflib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = Path(r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112")
OUT = ROOT / "candidate.diff"

PAIRS = [
    ("_run_hl_match.py",
     BASE / "_run_hl_match.py",
     ROOT / "candidate" / "_run_hl_match_candidate.py"),
    ("e3_stack_sampler_candidate.py",
     BASE / "e3_stack_sampler_candidate.py",
     ROOT / "candidate" / "e3_stack_sampler_candidate_r2.py"),
]


def main():
    chunks = []
    for label, a, b in PAIRS:
        la = a.read_text(encoding="utf-8").splitlines()
        lb = b.read_text(encoding="utf-8").splitlines()
        chunks.append("### %s  →  candidate/%s" % (label, b.name))
        chunks.append("### 原件 SHA-256 与体积见 FACT_CHECK.md（实算比对，零字节改动）")
        chunks.extend(difflib.unified_diff(
            la, lb,
            fromfile="a/lead/re_d13_ruling_20261112/" + a.name,
            tofile="b/lead/next_re_20261112/RE-N01/candidate/" + b.name,
            lineterm="", n=3))
        chunks.append("")
    OUT.write_text("\n".join(chunks) + "\n", encoding="utf-8")
    print("wrote %s (%d lines, %d bytes)" %
          (OUT, len("\n".join(chunks).splitlines()),
           OUT.stat().st_size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
