#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""`_adjudicate_h5_v12.py` 的负控自检：每条承重判据都要「改坏被测物必红」。

协议：子进程跑基线（期望全绿 rc=0）+ 逐条变异跑，断言
  ① 该变异使目标判据变红；
  ② 变异之间互不传染（非目标判据仍绿）——防「全红=装置没跑起来」。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ADJ = HERE / "_adjudicate_h5_v12.py"

# 变异名 → (目标判据 id, 目标判据必须变红)
MUTANTS = {
    "rc_flip": "X1",          # wait_returncode 期望 0→1 ⇒ X1 红
    "maxf_flip": "X4b",       # 峰值帧 1260→10000 ⇒ X4b 红
    "zero_widen": "X4c",      # 强加一条恒假区间断言 ⇒ X4c 红（演示装置活）
    "pngsize_flip": "X9",     # 画面尺寸期望 41583→1 ⇒ X9 红
    "docneedle_flip": "X10",  # S397 期望文案换成 A 趟才可能有的 ⇒ X10 红
}

RESULTS = []


def run(args):
    p = subprocess.run([sys.executable, str(ADJ)] + args,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300)
    lines = {}
    for ln in p.stdout.splitlines():
        m = re.match(r"\s*\[(PASS|FAIL)\]\s+(\S+)(.*)$", ln)
        if m:
            lines[m.group(2)] = m.group(1)
    return p.returncode, lines, p.stdout


def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    print("  [%s] %-56s %s" % ("PASS" if ok else "FAIL", name, detail))


def main() -> int:
    print("=" * 78)
    print("H-5 v12 裁决件负控自检")
    print("=" * 78)

    rc, base, _ = run([])
    npass = sum(1 for v in base.values() if v == "PASS")
    check("V0 基线全绿且 rc=0", rc == 0 and len(base) >= 12 and npass == len(base),
          "checks=%d rc=%d" % (len(base), rc))

    for mut, target in MUTANTS.items():
        rc2, got, _ = run(["--mutate-" + mut])
        red_target = got.get(target) == "FAIL"
        others_green = all(v == "PASS" for k, v in got.items() if k != target)
        check("V1[%s] 目标判据 %s 变红" % (mut, target), red_target,
              "rc=%d target=%s" % (rc2, got.get(target)))
        check("V2[%s] 非目标判据互不传染" % mut, others_green,
              "非目标全绿" if others_green else "有串红")

    print("\n" + "=" * 78)
    npass = sum(1 for _n, ok in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
