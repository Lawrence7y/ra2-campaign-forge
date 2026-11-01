#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""`_audit_threshold_support.py` 的负控：证明它的判据**能红**。

★ 这份审计的性质是「如实汇报 + 少数硬断言」。硬断言很容易写成恒真，
  所以每个变异都直接改**被审对象**（判档器的阈值）或**被测数据源**，
  看审计是否随之变红。

  M1 `polls_max` 5 → -1（比实测 min 0 还小）⇒「未误伤」必须红
  M2 `frame_s_max` 2.0 → 0.05（低于实测 max 0.219）⇒「余量充足」必须红
  M3 `polls_min` 200 → 999 ⇒「覆盖 8/9」的数字必须变（但那是打印项，不红）
     ⇒ 本件不拿它当断言，改由 M2 那条带阈值的硬判据承担。跳过。
  M4 把「窗口样木 n>0」的判据反转成 n==0 ⇒ 必红

跑法：python lead/qc161_u0400_trip/_verify_threshold_audit.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "lead" / "qc161_u0400_trip" / "_audit_threshold_support.py"
JUDGE = ROOT / "lead" / "qc161_u0400_trip" / "_judge_l1_20261023.py"

RESULTS = []


def rec(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print("  %s %s%s" % ("✓" if ok else "✗", name,
                         ("  | " + detail) if detail else ""))


def run(audit_text, judge_text):
    """把审计 + 判档器一起复制到临时目录（审计会 import 判档器）。"""
    tmp = Path(tempfile.mkdtemp(prefix="ta_"))
    try:
        pinned = audit_text.replace(
            "ROOT = Path(__file__).resolve().parents[2]",
            "ROOT = Path(r'%s')  # 负控注入" % ROOT, 1)
        assert "负控注入" in pinned, "ROOT 锚点未替换"
        (tmp / "_judge_l1_20261023.py").write_text(judge_text, encoding="utf-8")
        f = tmp / "_audit_threshold_support.py"
        f.write_text(pinned, encoding="utf-8")
        p = subprocess.run([sys.executable, str(f)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    audit_src = AUDIT.read_text(encoding="utf-8")
    judge_src = JUDGE.read_text(encoding="utf-8")

    print("=" * 78)
    print("[基线] 未变异")
    rc, out = run(audit_src, judge_src)
    rec("基线 rc == 0", rc == 0, "rc=%d" % rc)
    m = re.search(r"checks passed: (\d+)/(\d+)", out)
    rec("基线 全绿 n/n", bool(m) and m.group(1) == m.group(2),
        m.group(0) if m else "未找到")

    def bad(text):
        return [l.strip() for l in text.splitlines() if l.strip().startswith("✗")]

    rec("基线无 ✗ 行", not bad(out), str(bad(out)[:2]))

    def mutate(tag, old, new, expect, target="judge"):
        src = judge_src if target == "judge" else audit_src
        assert old in src, "变异锚点未找到：%s" % tag
        newj = src.replace(old, new, 1) if target == "judge" else judge_src
        newa = src.replace(old, new, 1) if target == "audit" else audit_src
        rc2, out2 = run(newa, newj)
        got = bad(out2)
        hit = any(expect in g for g in got) or (rc2 != 0 and not got)
        rec("%s %s" % (tag, expect), hit, "rc=%d 红项=%s" % (rc2, got[:2]))

    print("\n[变异：改被判档器的阈值]")
    # M1 polls_max 5 → -1（实测 min=0，必然被误伤）
    mutate("M1", '"polls_max": 5', '"polls_max": -1', "阈值 -1 未误伤")

    # M2 frame_s_max 2.0 → 0.05（实测采帧开销最大 0.219，余量必不足）
    mutate("M2", '"frame_s_max": 2.0', '"frame_s_max": 0.05', "余量")

    print("\n[变异：改审计自己的判据]")
    # M4 窗口样木判据反转（n>0 改成 n==0）
    mutate("M4", 'rec("窗口样木（fs 缺席 + polls 在场）n=%d" % len(win), len(win) > 0)',
           'rec("窗口样木（fs 缺席 + polls 在场）n=%d" % len(win), len(win) == 0)',
           "窗口样木", target="audit")

    print("\n" + "=" * 78)
    npass = sum(1 for _n, ok, _d in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    for n, ok, d in RESULTS:
        if not ok:
            print("  FAILED: %s | %s" % (n, d))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
