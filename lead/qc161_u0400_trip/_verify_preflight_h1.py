#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""`_preflight_h1.py` 的负控：证明 16 条飞行前检查**能红**。

为什么必须有：这些全是「小于阈值」「不存在」类断言，
若判据写错（比如比较方向反了、字段取空），会全绿而毫无信息量。

做法：把 preflight 复制到临时目录，注入变异（改阈值 / 改路径 / 塞目录），
重跑，只判输出文本与退出码是否随之变化。**不 import 其内部判据**，避免两边同绿。

  M1 把载体目录长度阈值从 127 降到 50  ⇒ 必须红（改的是判据方向）
  M2 把 MAX_PATH 阈值从 260 降到 100   ⇒ 必须红
  M3 预先创建 h7a 的 out-dir          ⇒ 「尚不存在」必须红
  M4 把窗口预算余量门限从 20 s 抬到 999 ⇒ 必须红（证明余量判据承重）

跑法：python lead/qc161_u0400_trip/_verify_preflight_h1.py
退出码：0 = 全部变异被捕获；1 = 有变异存活。
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRE = ROOT / "lead" / "qc161_u0400_trip" / "_preflight_h1.py"
OUT_ROOTS = ROOT / "out" / "re_work" / "work_chain" / "CONTINUE_20261003" / "lead" / "qc161_u0400_trip"

RESULTS = []


def rec(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print("  %s %s%s" % ("✓" if ok else "✗", name,
                         ("  | " + detail) if detail else ""))


def run(script_text):
    """把变异后的脚本写到临时目录，用绝对 ROOT 注入后执行。"""
    tmp = Path(tempfile.mkdtemp(prefix="pf_"))
    try:
        # ★ 钉死 ROOT：临时目录的 parents[2] 不是项目根，必须注入
        pinned = script_text.replace(
            "ROOT = Path(__file__).resolve().parents[2]",
            "ROOT = Path(r'%s')  # 负控注入" % ROOT, 1)
        assert pinned != script_text or "负控注入" in pinned, "ROOT 锚点未替换"
        f = tmp / "_preflight_mut.py"
        f.write_text(pinned, encoding="utf-8")
        p = subprocess.run([sys.executable, str(f)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def fails(text):
    return [l.strip() for l in text.splitlines() if l.strip().startswith("✗")]


def main() -> int:
    base_text = PRE.read_text(encoding="utf-8")

    print("=" * 78)
    print("[基线] 未变异")
    rc, out = run(base_text)
    rec("基线 rc == 0", rc == 0, "rc=%d" % rc)
    m = re.search(r"checks passed: (\d+)/(\d+)", out)
    rec("基线 全绿 n/n", bool(m) and m.group(1) == m.group(2),
        m.group(0) if m else "未找到")
    rec("基线无 ✗ 行", not fails(out), str(fails(out)[:2]))

    def mutate(tag, old, new, expect):
        assert old in base_text, "变异锚点未找到：%s" % tag
        rc2, out2 = run(base_text.replace(old, new, 1))
        got = fails(out2)
        hit = any(expect in g for g in got)
        rec("%s %s" % (tag, expect), hit, "rc=%d 红项=%s" % (rc2, got[:2]))

    print("\n[变异]")
    # M1 ★§422b 口径修正后锚点随之迁移：旧判据 `len(ct) < 127`（量 out_dir\ct=110）
    #   已被发射器占位符口径 `gate_len <= 130`（真值 130）取代。
    #   变异把阈值降到 50 ⇒ 130>50 必红（证明新判据真的在比 gate_len）。
    mutate("M1", "gate_len <= 130", "gate_len <= 50", "载体目录")

    # M2 MAX_PATH 260 → 100（实际 134 ⇒ 必红）
    mutate("M2", "len(full) < 260", "len(full) < 100", "最长载体全路径")

    # M3 ★§423：out-dir 判据已升级为 trip-id 感知（三趟跑完后目录存在是常态，
    #   旧「尚不存在」锚点失效——变异打不中判据本体导致 M3 假红，同 §420 坑②）。
    #   新变异把 rec 条件里的相等比较**取反**：在场的目录明明 trip_id 相符，
    #   取反后必须报「混叠」变红 ⇒ 证明判据真的在读盘上的 trip_id（消费方），
    #   不是装饰性文案。
    mutate("M3", "exist_tid == this_tid,", "exist_tid != this_tid,",
           "无混叠证据")

    # M4 窗口预算余量门限 15 → 999（实际余量 18.3 ⇒ 必红）
    mutate("M4", "slack > 15", "slack > 999", "窗口模式预算")

    # M5 ★§418b：把标定 delta 强制改为 0（即退回「sum 当总时长」的旧错法）
    #   ⇒ 余量会虚高到 36.06 s，但门限 15 仍会过 ⇒ **不能靠门限抓**。
    #   必须改用「报告里 delta 数值」这条断言来判：delta=0 时行内出现 "+ delta上界=0.00"。
    #   ★ 这正是本轮要防的：**判据本身用错了量**，改门限抓不到。
    mutate("M5", "hist_max + cal_max", "hist_max + 0.0",
           "校准已进入余量计算")

    print("\n" + "=" * 78)
    npass = sum(1 for _n, ok, _d in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    for n, ok, d in RESULTS:
        if not ok:
            print("  FAILED: %s | %s" % (n, d))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
