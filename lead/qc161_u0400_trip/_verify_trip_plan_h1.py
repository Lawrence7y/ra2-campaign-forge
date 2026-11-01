#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""`_trip_plan_h1.py` 的负控：证明这 17 条自检**能红**。

为什么必须有：编排器的自检几乎全是「应当不出现」「应当出现一次」
这类断言。若判据本身失效，它们会全绿而毫无信息量。
故本件把编排器当**黑盒**（不 import 其内部判据，避免两边同绿），
改 TRIPS 定义后重跑，只判输出文本与退出码是否随之变化。

每个变异都对应一个真实会犯的错：
  M1 三趟 suffix 撞车        ⇒ out-dir/trip-id 覆盖前一趟证据
  M2 第 1 趟忘关全屏        ⇒ 发成第 2 趟，窗口模式证据永远缺失
  M3 第 2 趟误加 keep 开关   ⇒ 短路臂变成对照臂，核心收益测不到
  M4 第 3 趟漏掉 keep 开关   ⇒ 对照臂变成短路臂，A/B 对照消失
  M5 第 2 趟用 harness6      ⇒ 用缺补丁的件跑「补丁验证」

跑法：python lead/qc161_u0400_trip/_verify_trip_plan_h1.py
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
PLAN = ROOT / "lead" / "qc161_u0400_trip" / "_trip_plan_h1.py"

RESULTS: list[tuple[str, bool, str]] = []


def rec(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print("  %s %s%s" % ("✓" if ok else "✗", name,
                         ("  | %s" % detail) if detail else ""))


def run(text: str) -> tuple[int, str]:
    """把改写后的编排器放到临时目录跑。

    ★★ 关键：编排器用 `Path(__file__).parents[2]` 推仓库根。
      若原样搬进 `<tmp>/lead/qc161_u0400_trip/`，推出来的是 **Temp 目录**，
      发射器根本导入不到 ⇒ 所有变异都因「发射器缺失」而失败、
      ✗ 行里什么细节都没有（本轮实测踩到：8 条全红且红项为空）。
      ⇒ 注入一行把 ROOT 钉回真仓库根，其余保持不变。
    """
    td = Path(tempfile.mkdtemp(prefix="plan_"))
    try:
        d = td / "lead" / "qc161_u0400_trip"
        d.mkdir(parents=True)
        f = d / "_trip_plan_h1.py"

        anchor = "ROOT = Path(__file__).resolve().parents[2]"
        assert anchor in text, "未找到 ROOT 推导锚点"
        pinned = text.replace(
            anchor,
            "ROOT = Path(r'%s')  # 负控注入" % ROOT, 1)
        f.write_text(pinned, encoding="utf-8")

        p = subprocess.run([sys.executable, str(f)], capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=180, cwd=str(ROOT))
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    finally:
        shutil.rmtree(td, ignore_errors=True)


def fails(out: str) -> list[str]:
    return re.findall(r"✗ ([^\n|]+)", out)


def main() -> int:
    base_text = PLAN.read_text(encoding="utf-8")
    print("=" * 84)
    print("[基线] 未变异")
    rc, out = run(base_text)
    rec("基线 rc == 0", rc == 0, "rc=%d" % rc)
    # ★ 不写死「17/17」：判据条数会随自检增长而变（本轮 17→19），
    #   写死数字会让负控因「条数变了」而假红，掩盖真正的判据失效。
    #   改判「TOTAL n/n」的 n 前后相等且无 ✗ 行。
    m = re.search(r"TOTAL (\d+)/(\d+) PASS", out)
    rec("基线 TOTAL n/n（全绿）",
        bool(m) and m.group(1) == m.group(2), m.group(0) if m else "未找到")
    base_fails = fails(out)
    rec("基线无 ✗ 行", not base_fails, str(base_fails))

    def mutate(tag: str, old: str, new: str, expect: str) -> None:
        assert old in base_text, "变异锚点未找到：%s" % tag
        t = base_text.replace(old, new, 1)
        rc2, out2 = run(t)
        got = fails(out2)
        hit = any(expect in g for g in got)
        rec("%s %s" % (tag, expect), hit,
            "rc=%d 红项=%s" % (rc2, got[:3]))

    print("\n[变异]")
    # M1 suffix 撞车（第 3 趟改成与第 1 趟相同）
    #   ★§423：suffix 已迁 ha/hb/hc（h7 后缀被发射器 130 门禁 BLOCK，见预检件），
    #     锚点随之迁移——**被测件动了，负控锚点必须跟着动**（§421 教训第三次应验）。
    mutate("M1", '"suffix": "hc"', '"suffix": "ha"', "C1")

    # M2 第 1 趟忘关全屏
    mutate("M2", '"no_fullscreen": True', '"no_fullscreen": False', "C3a")

    # M3 第 2 趟误加 keep 开关
    mutate("M3",
           '"suffix": "hb",\n        "harness": H7,\n        "no_fullscreen": False,\n        "extra_argv": ""',
           '"suffix": "hb",\n        "harness": H7,\n        "no_fullscreen": False,\n        "extra_argv": "--h7-keep-rect-wait"',
           "C4b")

    # M4 第 3 趟漏掉 keep 开关
    mutate("M4", '"extra_argv": "--h7-keep-rect-wait"', '"extra_argv": ""',
           "C4a")

    # M5 第 2 趟用 harness6
    mutate("M5",
           '"suffix": "hb",\n        "harness": H7',
           '"suffix": "hb",\n        "harness": H6',
           "C5")

    # M6 ★ §417：把 quote() 退回旧实现（只在含空白时加引号）
    #   ⇒ 打印命令里的 Windows 反斜杠路径裸奔 ⇒ C11 必须变红。
    #   ★ 这是 C11 的负控：没有它，C11 可能只是「恰好都对」而不是「抓得住」。
    mutate("M6",
           "return '\"%s\"' % a.replace('\"', '\\\\\"')",
           "return '\"%s\"' % a if (\" \" in a or \"\\t\" in a) else a",
           "C11")

    print("\n" + "=" * 84)
    npass = sum(1 for _n, ok, _d in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    for n, ok, d in RESULTS:
        if not ok:
            print("  FAILED: %s | %s" % (n, d))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
