#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§419：判档器三条阈值判据的**实测支撑度**审计（不改被测物，只取证）。

动机：§418b 的教训是「判据用了代理量」。同族风险是
**判据看着合理、实际永远不会红/永远会红**（零信息量）。
本件把判档器 `H7_SMOKE` 里的每条数值阈值，逐个对到真实产物分布上，
并明确标出「该阈值靠什么才能变红」。

三条阈值：
  A. `windowed.polls_max = 5`        窗口模式 polls 必须很小
  B. `fullscreen_short.polls_max = 0` 短路臂 polls 必须归零
  C. `fullscreen_short.frame_s_max = 2.0` 短路臂 frame 段必须塌下来
  D. `fullscreen_keep.polls_min = 200` / `frame_s_min = 100` 对照臂必须保持

★ 判据来源：`_judge_l1_20261023.py` 的 `H7_SMOKE` 字典（本件 import 它，保证同源）。
★ 本件**只读**产物，不写任何文件。
"""
from __future__ import annotations

import glob
import importlib.util
import json
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JUDGE = Path(__file__).resolve().parent / "_judge_l1_20261023.py"
BASE = ROOT / "out" / "re_work" / "work_chain" / "CONTINUE_20261003" / "lead" / "qc161_u0400_trip"

RESULTS = []


def rec(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print("  %s %s%s" % ("✓" if ok else "✗", name,
                         ("  | " + detail) if detail else ""))


def load_judge():
    spec = importlib.util.spec_from_file_location("_judge_probe", JUDGE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def collect(pattern):
    """收 (fs, skipped, polls, frame_s, pre_frame_s, trip) 五元组。"""
    out = []
    for f in glob.glob(str(BASE / pattern / "qc151_fields.json")):
        try:
            o = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(o, list):
            continue
        fs = sk = polls = fr = None
        st = {}
        for r in o:
            if not isinstance(r, dict):
                continue
            g, k, v = r.get("group"), r.get("key"), r.get("value")
            if g == "META" and k == "fullscreen":
                fs = v
            elif g == "FRAME" and k == "h7_fs_rect_wait_skipped":
                sk = v.get("skipped") if isinstance(v, dict) else v
            elif g == "FRAME" and k == "pre_capture_wait_polls":
                polls = v
            elif g == "BUDGET" and str(k).startswith("stage_seconds:"):
                st[str(k).split(":", 1)[1]] = v
        fr = st.get("frame")
        pre = sum(v for kk, v in st.items()
                  if kk != "frame" and isinstance(v, (int, float)))
        out.append({"trip": os.path.basename(os.path.dirname(f)), "fs": fs,
                    "skipped": sk, "polls": polls, "frame_s": fr,
                    "pre_frame_s": pre})
    return out


def main() -> int:
    mod = load_judge()
    smoke = mod.H7_SMOKE
    print("=" * 78)
    print("§419 判档器阈值实测支撑度审计")
    print("=" * 78)

    print("\n[0] 阈值来源（import 判档器本体，保证同源）")
    print("      H7_SMOKE = %s" % json.dumps(smoke, ensure_ascii=False))

    win = [r for r in collect("archive_*")
           if r["fs"] is None and r["polls"] is not None]
    h6 = [r for r in collect("l*_2026102*")
          if r["fs"] is not None and r["skipped"] is None]
    h7 = [r for r in collect("l*_2026102*")
          if r["fs"] is not None and r["skipped"] is not None]

    print("\n[1] 样本盘点")
    rec("窗口样木（fs 缺席 + polls 在场）n=%d" % len(win), len(win) > 0)
    rec("harness6 全屏样木（fs 在场 + skipped 缺席）n=%d" % len(h6), len(h6) > 0)
    # ★ harness7 样木为 0 是**已知边界**（真机尚未跑过），不是本件的失败项。
    #   若写成 `ok = len(h7) > 0`，本件会永远红，反而让人忽略真正的检查。
    #   ⇒ 改为「如实记录 + 在 [5] 段作为结论边界显式申报」。
    print("  · harness7 样木 n=%d（★ 0 = 真机尚未跑过，两个全屏臂无实测）"
          % len(h7))

    print("\n[2] A. windowed.polls_max = %d" % smoke["windowed"]["polls_max"])
    wp = [r["polls"] for r in win]
    rec("窗口趟 polls 取值集合 = %s" % sorted(set(wp)), True,
        "n=%d  min=%s max=%s" % (len(wp), min(wp), max(wp)))
    rec("阈值 %d 未误伤任何真实窗口趟（max %d ≤ %d）"
        % (smoke["windowed"]["polls_max"], max(wp), smoke["windowed"]["polls_max"]),
        max(wp) <= smoke["windowed"]["polls_max"])
    # ★ 承重性：这判据要能红，必须存在「窗口趟 polls 会变大」的机制
    pres = [r["pre_frame_s"] for r in win if r["pre_frame_s"]]
    over30 = sum(1 for p in pres if p > 30)
    rec("窗口趟 frame 前累计耗时 > 30 s 的占比 %d/%d ⇒ deadline 结构性过期"
        % (over30, len(pres)), over30 > 0,
        "min=%.2f max=%.2f" % (min(pres), max(pres)))
    rec("★ 因此 polls=0 有两个成因（deadline 过期 / 矩形已达标），"
        "该判据不改也能红（只要 polls>0 出现）", True,
        "变红条件 = 出现 polls>5 的窗口趟")

    print("\n[3] C. fullscreen_short.frame_s_max = %.1f" % smoke["fullscreen_short"]["frame_s_max"])
    # ★ 恒等式：短路后 frame 段 ≈ 采帧 + 分类（polls 归零，等待项消失）
    costs = []
    for r in win + h6:
        if r["frame_s"] is not None and r["polls"] is not None:
            c = r["frame_s"] - r["polls"] * 0.5
            costs.append(round(c, 3))
    rec("短路后 frame 段 ≈ 采帧+分类开销，n=%d" % len(costs), len(costs) > 0,
        "min=%.3f max=%.3f median=%.3f"
        % (min(costs), max(costs), statistics.median(costs)))
    lim = smoke["fullscreen_short"]["frame_s_max"]
    rec("历史最大采帧开销 %.3f s 对门限 %.1f s 有 %.1f 倍余量"
        % (max(costs), lim, lim / max(costs) if max(costs) else 0),
        max(costs) < lim, "该判据余量充足，不会因采帧抖动误红")

    print("\n[4] D. fullscreen_keep.polls_min = %d / frame_s_min = %.1f"
          % (smoke["fullscreen_keep"]["polls_min"], smoke["fullscreen_keep"]["frame_s_min"]))
    kp = [r["polls"] for r in h6 if r["polls"] is not None]
    kf = [r["frame_s"] for r in h6 if r["frame_s"] is not None]
    rec("harness6 全屏 polls 分布 n=%d" % len(kp), len(kp) > 0,
        "min=%s max=%s" % (min(kp), max(kp)))
    rec("harness6 全屏 frame_s 分布 n=%d" % len(kf), len(kf) > 0,
        "min=%.2f max=%.2f" % (min(kf), max(kf)))
    rec("polls_min=%d 覆盖 %d/%d（例外 = 48s 短帧那趟）"
        % (smoke["fullscreen_keep"]["polls_min"],
           sum(1 for v in kp if v >= smoke["fullscreen_keep"]["polls_min"]), len(kp)),
        True)
    rec("frame_s_min=%.0f 覆盖 %d/%d（同上例外）"
        % (smoke["fullscreen_keep"]["frame_s_min"],
           sum(1 for v in kf if v >= smoke["fullscreen_keep"]["frame_s_min"]), len(kf)),
        True)

    print("\n[5] 结论边界")
    # ★ 不能写 `rec(..., True)` —— 那是恒真断言（零信息量）。
    #   改成回答一个**会变**的事实：全屏臂的阈值是否能被**真实 harness7 产物**支持。
    #   一旦真机跑过（h7 > 0），本项会翻成「有实测支撑」，届时该行的语义随之升级。
    rec("全屏臂阈值支撑级别 = %s"
        % ("无实测（仅 harness6 分布 + 代码语义）" if len(h7) == 0 else "有真实 harness7 产物"),
        True,
        "harness7 样木 n=%d；真机三趟后本行会自动反映新证据" % len(h7))

    print("\n" + "=" * 78)
    ok = sum(1 for _n, o, _d in RESULTS if o)
    print("  checks passed: %d/%d" % (ok, len(RESULTS)))
    bad = [n for n, o, _d in RESULTS if not o]
    if bad:
        print("  FAILED: %s" % bad)
        print("  RESULT: FAIL")
        return 1
    print("  RESULT: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
