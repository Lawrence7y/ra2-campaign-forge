#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W4 离线重渲染：只从 out/*.json 重新生成 4 份 MD，不启动游戏、不抓栈、不改原始 JSON。

用途：分析/文档口径修订后，无需再发射真机即可刷新 VERDICT/SAFETY/RUNLOG/UNCOVERED。
原始 out/*.json 逐字节不动；CONFIG_RESTORE.md 是运行时实算产物，本脚本不改写。

用法：
  python -X utf8 reanalyze.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

W4 = Path(__file__).resolve().parent
OUT = W4 / "out"
PROBE_PATH = W4 / "exit_dialog_probe.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def jread(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main():
    probe = load(PROBE_PATH, "w4_reanalyze_probe")
    # render_verdict 内部用 w3.norm_frame；离线路径也需要把只读资产模块挂上
    w3 = load(probe.W3_PATH, "w4_reanalyze_w3")
    w3.OUT = OUT
    probe.w3 = w3

    base = jread("baseline_14412.json")
    grabs = [jread("%s.json" % lab)
             for lab in ("D0", "D1a", "D1b", "D1c", "D2")
             if (OUT / ("%s.json" % lab)).exists()]
    # 若有补充趟（D1x）也纳入对比表，保持与运行时一致
    for lab in ("D1x",):
        if (OUT / ("%s.json" % lab)).exists():
            grabs.append(jread("%s.json" % lab))
    ana = jread("summary.json")
    meta = jread("run_meta.json")
    triggers = jread("triggers.json")

    budget_ms = float((meta.get("args") or {}).get("budget_ms", 50.0))
    exit_code = 0
    started_utc = meta.get("started_utc")
    ended_utc = meta.get("ended_utc")
    cmdline = meta.get("cmdline")
    hold_abort = bool(meta.get("hold_abort"))

    (W4 / "VERDICT.md").write_text(
        probe.render_verdict(base, grabs, ana, meta), encoding="utf-8")
    (W4 / "SAFETY.md").write_text(
        probe.render_safety(grabs, budget_ms, meta, hold_abort), encoding="utf-8")
    (W4 / "RUNLOG.md").write_text(
        probe.render_runlog(meta, exit_code, started_utc, ended_utc,
                            cmdline, triggers), encoding="utf-8")
    (W4 / "UNCOVERED.md").write_text(
        probe.render_uncovered(meta, grabs, ana), encoding="utf-8")

    print("[reanalyze] grabs=%d tier=%s P1=%s P2=%s P3=%s P4=%s" %
          (len(grabs), ana["tier"], ana["p1"]["status"], ana["p2"]["status"],
           ana["p3"]["status"], ana["p4"]["status"]))
    print("[reanalyze] 4 份 MD 已刷新；out/*.json 未改动；CONFIG_RESTORE.md 保持运行时版本")
    return 0


if __name__ == "__main__":
    sys.exit(main())
