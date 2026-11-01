#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""`_preview_h7_fullpath.py` 的负控：证明 9 条判据**能红**。

本件的判据分两类，都需要单独打：
  - 「判型正确」类：改形态构造方式（把 skipped 写错）⇒ 判型错 ⇒ 必红
  - 「冒烟段被执行到」类：把 harness_sha16 撤掉 ⇒ 提早 return ⇒ 必红
  - 「两段互不干扰」类：让三窗缺文件 ⇒ 三窗段红，验证它**不是**恒绿

  M1 short 形态把 skipped 写成 False ⇒ 判型变 keep（不是 short）⇒「判型」必红
  M2 撤掉 harness_sha16 且去掉 h7_* 记录 ⇒ 冒烟段 return ⇒「走到[4b]」必红
  M3 删掉 measure_w2.json ⇒ 三窗段红 ⇒ 用来验证 C 那条「三窗段仍绿」不是恒真

跑法：python lead/qc161_u0400_trip/_verify_h7_fullpath.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREV = ROOT / "lead" / "qc161_u0400_trip" / "_preview_h7_fullpath.py"
JUDGE = ROOT / "lead" / "qc161_u0400_trip" / "_judge_l1_20261023.py"

RESULTS = []


def rec(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print("  %s %s%s" % ("✓" if ok else "✗", name,
                         ("  | " + detail) if detail else ""))


def run(text):
    tmp = Path(tempfile.mkdtemp(prefix="hf_"))
    try:
        pinned = text.replace(
            "ROOT = Path(__file__).resolve().parents[2]",
            "ROOT = Path(r'%s')  # 负控注入" % ROOT, 1)
        assert "负控注入" in pinned, "ROOT 锚点未替换"
        # ★★ 必须**同时**钉住 JUDGE：它写成 `Path(__file__).resolve().parent`，
        #   在临时副本里会指向临时目录 ⇒ 判档器不存在 ⇒ 每个子进程 rc=2、
        #   无 stderr、9 条全红且红项一模一样。
        #   首跑就是这样：**全红且红项相同 = 装置没跑起来**，不是被测物坏。
        pinned = pinned.replace(
            "JUDGE = Path(__file__).resolve().parent / \"_judge_l1_20261023.py\"",
            "JUDGE = Path(r'%s')  # 负控注入" % JUDGE, 1)
        assert "负控注入" in pinned.split("JUDGE")[1], "JUDGE 锚点未替换"
        f = tmp / "_preview_mut.py"
        f.write_text(pinned, encoding="utf-8")
        p = subprocess.run([sys.executable, str(f)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=400)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    src = PREV.read_text(encoding="utf-8")

    print("=" * 78)
    print("[基线] 未变异")
    rc, out = run(src)
    rec("基线 rc == 0", rc == 0, "rc=%d" % rc)
    m = re.search(r"checks passed: (\d+)/(\d+)", out)
    rec("基线 全绿 n/n", bool(m) and m.group(1) == m.group(2),
        m.group(0) if m else "未找到")
    reds = [l.strip() for l in out.splitlines() if l.strip().startswith("✗")]
    rec("基线无 ✗ 行", not reds, str(reds[:2]))

    def mutate(tag, old, new):
        assert old in src, "变异锚点未找到：%s" % tag
        rc2, out2 = run(src.replace(old, new, 1))
        reds2 = [l.strip() for l in out2.splitlines() if l.strip().startswith("✗")]
        rec("%s 必须变红" % tag, rc2 != 0 and bool(reds2),
            "rc=%d 红项=%s" % (rc2, reds2[:2]))
        return out2

    print("\n[变异]")
    # M1 short 臂的 **META** 值写错成 False ⇒ 判型应翻 keep（§422 后判型只读 META，
    #   FRAME dict 不再参与判型 ⇒ 首版打 FRAME 侧的变异**存活**，改打 META 侧）
    old = 'add(recs, "META", "h7_fs_rect_wait_skipped", True)'
    new = 'add(recs, "META", "h7_fs_rect_wait_skipped", False)'
    assert old in src, "变异锚点未找到：M1"
    rc2, out2 = run(src.replace(old, new, 1))
    reds2 = [l.strip() for l in out2.splitlines() if l.strip().startswith("✗")]
    rec("M1 short 臂 META 值写错 ⇒ 判型翻 keep",
        rc2 != 0 and any("判型" in r for r in reds2),
        "rc=%d 红项=%s" % (rc2, reds2[:2]))

    # M2 撤掉 harness7 标记。
    #   ★ 首版只改 `lr["harness_sha16"]` ⇒ **变异存活**（rc=0）。
    #     原因：判档器 `is_h7_run = (sha==H7) or (sk is not None) or (n2m is not None)`
    #     有**三条**退路，改一条不影响结论。这是判据本身的性质（不是缺陷）：
    #     任何一条在场就认定 harness7。
    #   ⇒ 要真正模拟「非 harness7 趟」，必须**三条全撤**：sha 换掉 + 不写
    #     h7_fs_rect_wait_skipped + 不写 h7_nav_to_measure。
    assert 'add(recs, "MEASURE", "h7_nav_to_measure"' in src
    mutate2 = src.replace('lr["harness_sha16"] = H7_SHA16',
                          'lr["harness_sha16"] = "0000000000000000"', 1)
    mutate2 = mutate2.replace('    add(recs, "MEASURE", "h7_nav_to_measure",\n'
                              '        {"nav_to_measure_s": 12.5, "limit_s": 90.0,\n'
                              '         "late_start": False, "fs_rect_wait_skipped": True})\n',
                              '    pass  # 负控：不写 h7_nav_to_measure\n', 1)
    mutate2 = mutate2.replace('        add(recs, "FRAME", "h7_fs_rect_wait_skipped",\n',
                              '        _dummy = (recs, "FRAME", "h7_fs_rect_wait_skipped")\n'
                              '        _ = (\n', 1)
    rc2, out2 = run(mutate2)
    reds2 = [l.strip() for l in out2.splitlines() if l.strip().startswith("✗")]
    rec("M2 三路标记全撤 ⇒ 必须变红", rc2 != 0 and bool(reds2),
        "rc=%d 红项=%s" % (rc2, reds2[:2]))

    # M3 少拷 measure_w2 ⇒ 三窗段应红（验证 C 那条不是恒绿）
    mutate("M3 缺 measure_w2",
           '"measure_w0.json", "measure_w1.json", "measure_w2.json"',
           '"measure_w0.json", "measure_w1.json"')

    print("\n" + "=" * 78)
    npass = sum(1 for _n, ok, _d in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    for n, ok, d in RESULTS:
        if not ok:
            print("  FAILED: %s | %s" % (n, d))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
