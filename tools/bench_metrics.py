#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_metrics.py — 验收指标的唯一计算器（Q3）。

为什么单独成文件：指标定义散落在 bench_replay（真机采样）与 bench_filter（噪声口径）里，
判据又写在文档里，三处口径一旦漂移，数字就不可比。本文件把「计算式 + 阈值 + 判定」收敛成
**一个可离线复算的函数**：喂它任何一次采样的 JSON（bench_replay run JSON 或 ra2re perf JSON），
它给出逐指标的值、计算式、门禁与 PASS/FAIL/NOT_MEASURABLE。

三条铁律（写在代码里，防止"没数据也算达标"）：
  1. 没有帧序列的输入 → 帧率类指标一律 **NOT_MEASURABLE**，绝不默认 0 分或"通过"；
  2. 有效样本占比 < 10% 的输入 → 整体判定 **INVALID_SAMPLE**（无论其它指标多好看）；
  3. 输出里必须带 `formula` 与 `threshold` 原文，禁止只给结论。

用法：
  python tools/bench_metrics.py --selftest
  python tools/bench_metrics.py --run out/loadbench/bench_U0800_20260927_101500_run1.json
  python tools/bench_metrics.py --historical      # 判定历史基线是否可作为达标证据
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "out" / "loadbench"
HARNESS = PROJECT / "out" / "re_work" / "bench_harness"

# ---- 门禁阈值（与 out/loadbench/PROTOCOL.md §4 一一对应；改这里必须同步改文档） ----
THRESHOLDS = {
    200: {"fps_avg_min": 20.0, "fps_1low_min": 10.0, "tick_miss_rate_max": 0.05,
          "cpu_pct_min": 10.0, "valid_min": 300, "coverage_min": 70.0, "uniformity_ratio": 0.30},
    800: {"fps_avg_min": 8.0, "fps_1low_min": 4.0, "tick_miss_rate_max": 0.25,
          "cpu_pct_min": 15.0, "valid_min": 500, "coverage_min": 70.0, "uniformity_ratio": 0.30},
}
VALID_PCT_FLOOR = 10.0        # 有效样本占比下限（低于此值：不是对局，是菜单/暂停）
SAMPLING_COVERAGE_FLOOR = 90.0  # 采样器保真度下限（实际样本 / 计划样本）

FORMULAS = {
    "fps_avg": "FPS_avg = (CurrentFrame_end - CurrentFrame_start) / (t_end - t_start)",
    "fps_1pct_low": "FPS_1%low = 1 / P99(dt_i)，dt_i = 相邻帧推进所耗墙钟秒数",
    "cpu_single_core_pct": "CPU% = (ΔT_user + ΔT_kernel) / Δt_span * 100%（相对单核）",
    "tick_miss_rate": "TickMissRate = #{dt_i > 1.5 * P50(dt)} / M",
    "valid_samples": "N_valid = N_gamemd + N_hooks；ValidPct = N_valid / N_total * 100%",
    "coverage_pct": "Coverage = (N_gamemd - N_gamemd_other) / N_gamemd * 100%",
    "sampling_coverage": "SamplingCoverage = N_samples / (target_hz * duration) * 100%",
}


def _pct(x, n):
    return round(100.0 * x / n, 2) if n else 0.0


def evaluate(record: dict, tier: "int | None" = None) -> dict:
    """对一次采样的 JSON 逐指标求值。record 可以是 bench_replay run JSON 或 ra2re perf JSON。"""
    tier = int(tier or record.get("tier") or 0)
    th = THRESHOLDS.get(tier) or THRESHOLDS[800]
    frames = record.get("frames") or {}
    by_bucket = record.get("by_bucket") or {}
    by_module = record.get("by_module") or {}
    n_total = int(record.get("samples") or sum(by_module.values()) or 0)
    span = float(record.get("span_s") or record.get("seconds") or 0.0)

    gamemd_n = int(record.get("gamemd_samples") or 0)
    if not gamemd_n and by_module:
        gamemd_n = sum(v for k, v in by_module.items() if k.lower().startswith("gamemd"))
    hooks_n = int(record.get("hooks_samples") or 0)
    if not hooks_n and by_module:
        hooks_n = sum(v for k, v in by_module.items() if k.lower().startswith("ra2render"))
    valid_n = int(record.get("valid_samples") or (gamemd_n + hooks_n))

    m: dict = {}

    def put(key, value, verdict, threshold, note=""):
        m[key] = {"value": value, "verdict": verdict, "threshold": threshold,
                  "formula": FORMULAS[key], "note": note}

    # 1) 平均逻辑帧率
    has_frames = bool(frames) and frames.get("note") != "insufficient"
    fps_avg = frames.get("fps_avg")
    logic_frames = frames.get("logic_frames")
    if has_frames and fps_avg is not None:
        if logic_frames == 0:
            put("fps_avg", fps_avg, "FAIL", f">= {th['fps_avg_min']} fps",
                "CurrentFrame 零推进：卡死/假死/未进入对局")
        else:
            v = "PASS" if fps_avg >= th["fps_avg_min"] else "FAIL"
            put("fps_avg", fps_avg, v, f">= {th['fps_avg_min']} fps")
    else:
        put("fps_avg", None, "NOT_MEASURABLE", f">= {th['fps_avg_min']} fps",
            "输入 JSON 无帧序列（历史 perf_*.json 属于此类）：必须先真机采样")

    # 2) 1% low
    fps1 = frames.get("fps_1pct_low")
    if has_frames and fps1 is not None:
        v = "PASS" if fps1 >= th["fps_1low_min"] else "FAIL"
        note = ""
        if fps_avg and fps1 < th["uniformity_ratio"] * fps_avg:
            v = "FAIL"
            note = f"1%low < {th['uniformity_ratio']}×FPS_avg：帧生成均匀度严重劣化"
        put("fps_1pct_low", fps1, v, f">= {th['fps_1low_min']} fps 且 >= {th['uniformity_ratio']}×FPS_avg", note)
    else:
        put("fps_1pct_low", None, "NOT_MEASURABLE", f">= {th['fps_1low_min']} fps",
            "输入 JSON 无逐帧时间序列")

    # 3) 单核 CPU 占用（也是"是否真的在对局里"的旁证）
    cpu = record.get("cpu_pct_of_one_core")
    if cpu is None and record.get("cpu_seconds") is not None and span:
        cpu = round(100.0 * float(record["cpu_seconds"]) / span, 2)
    if cpu is not None:
        v = "PASS" if cpu >= th["cpu_pct_min"] else "FAIL"
        put("cpu_single_core_pct", cpu, v, f">= {th['cpu_pct_min']}%（低于则视作不在对局中）")
    else:
        put("cpu_single_core_pct", None, "NOT_MEASURABLE", f">= {th['cpu_pct_min']}%",
            "输入 JSON 无 GetProcessTimes 首尾差分")

    # 4) TickMiss
    tm = frames.get("tick_miss_rate")
    if has_frames and tm is not None:
        put("tick_miss_rate", tm, "PASS" if tm <= th["tick_miss_rate_max"] else "FAIL",
            f"<= {100.0 * th['tick_miss_rate_max']:.0f}%")
    else:
        put("tick_miss_rate", None, "NOT_MEASURABLE", f"<= {100.0 * th['tick_miss_rate_max']:.0f}%",
            "输入 JSON 无逐帧时间序列")

    # 5) 有效样本数 / 有效占比
    vp = record.get("valid_pct")
    if vp is None and n_total:
        vp = _pct(valid_n, n_total)
    if n_total:
        v = "PASS" if (vp or 0) >= VALID_PCT_FLOOR and valid_n >= th["valid_min"] else "FAIL"
        put("valid_samples", {"count": valid_n, "pct": vp, "total": n_total}, v,
            f">= {th['valid_min']} 个且占比 >= {VALID_PCT_FLOOR}%")
    else:
        put("valid_samples", None, "NOT_MEASURABLE", f">= {th['valid_min']} 个")

    # 6) 归因覆盖率（区间表命中率；诚实口径由 bench_filter 的 anchored_range_pct 补充）
    cov = record.get("coverage_pct")
    if cov is None and gamemd_n and by_bucket:
        other = sum(v for k, v in by_bucket.items() if k == "game_other")
        cov = _pct(gamemd_n - other, gamemd_n)
    if cov is not None and gamemd_n:
        put("coverage_pct", cov, "PASS" if cov >= th["coverage_min"] else "FAIL",
            f">= {th['coverage_min']}%",
            "覆盖率=落进 VA 区间表的比例，不等于归因正确性（见 bench_filter 证据等级）")
    else:
        put("coverage_pct", None, "NOT_MEASURABLE", f">= {th['coverage_min']}%")

    # 7) 采样覆盖率（采样器保真度，不等于场景覆盖率）
    hz = float(record.get("hz") or record.get("hz_actual") or 0.0)
    planned = hz * span if hz and span else 0.0
    if planned and n_total:
        sc = round(100.0 * n_total / planned, 2)
        put("sampling_coverage", sc, "PASS" if sc >= SAMPLING_COVERAGE_FLOOR else "FAIL",
            f">= {SAMPLING_COVERAGE_FLOOR}%",
            "只说明采样频率达标；不说明采到了对局（场景有效性看 valid_samples）")
    else:
        put("sampling_coverage", None, "NOT_MEASURABLE", f">= {SAMPLING_COVERAGE_FLOOR}%")

    verdicts = [v["verdict"] for v in m.values()]
    if (vp or 0) < VALID_PCT_FLOOR:
        overall = "INVALID_SAMPLE"
        reason = f"有效样本占比 {vp}% < {VALID_PCT_FLOOR}%：本次采样不在对局中，所有指标不得引用"
    elif "FAIL" in verdicts:
        overall = "FAIL"
        reason = "存在不达标指标：" + ", ".join(k for k, v in m.items() if v["verdict"] == "FAIL")
    elif "NOT_MEASURABLE" in verdicts:
        overall = "PARTIAL"
        reason = "部分指标不可测量：" + ", ".join(k for k, v in m.items() if v["verdict"] == "NOT_MEASURABLE")
    else:
        overall = "PASS"
        reason = f"U{tier} 全部指标达标（样本口径有效）"

    return {
        "source": record.get("_source", ""),
        "tier": tier,
        "metrics": m,
        "overall": overall,
        "overall_reason": reason,
        "scope": "本结果仅描述本次采样的数值与门禁判定，不构成任何补丁的收益结论",
    }


def render_markdown(res: dict) -> str:
    lines = [
        f"### 指标判定 — {res['source'] or '(内存记录)'}",
        "",
        f"- 档位：U{res['tier'] or '(未知)'}　**总判定：`{res['overall']}`**",
        f"- 依据：{res['overall_reason']}",
        "",
        "| 指标 | 值 | 计算式 | 门禁 | 判定 | 备注 |",
        "|---|---:|---|---|---|---|",
    ]
    for k, v in res["metrics"].items():
        val = v["value"]
        if isinstance(val, dict):
            val = f"{val['count']} 个 / {val['pct']}%（总 {val['total']}）"
        elif val is None:
            val = "—"
        lines.append(f"| `{k}` | {val} | `{v['formula']}` | {v['threshold']} | "
                     f"**{v['verdict']}** | {v['note']} |")
    lines += ["", f"> {res['scope']}", ""]
    return "\n".join(lines)


def _synth(tier: int = 800, **over) -> dict:
    rec = {
        "_source": "synthetic",
        "tier": tier,
        "samples": 5000, "span_s": 20.0, "hz_actual": 250.0,
        "gamemd_samples": 1700, "hooks_samples": 300,
        "valid_samples": 2000, "valid_pct": 40.0,
        "coverage_pct": 92.0,
        "cpu_pct_of_one_core": 61.5,
        "frames": {"fps_avg": 14.2, "fps_1pct_low": 5.4, "tick_miss_rate": 0.08,
                   "tick_miss": 400, "logic_frames": 284},
    }
    rec.update(over)
    return rec


def run_selftest() -> int:
    """四类判定各构造一个输入，证明计算器不会「没数据也算达标」。"""
    print("=== bench_metrics 离线自检（不启动游戏、不读实时进程） ===")
    cases = [
        ("全部达标(U800)", _synth(), "PASS"),
        ("帧率不达标(U800)", _synth(frames={"fps_avg": 5.0, "fps_1pct_low": 2.0,
                                              "tick_miss_rate": 0.31, "tick_miss": 1550,
                                              "logic_frames": 100}), "FAIL"),
        ("无帧序列(历史 JSON 形态)", _synth(frames={}, cpu_pct_of_one_core=None,
                                            coverage_pct=None), "PARTIAL"),
        ("菜单误采(有效占比 1.2%)", _synth(valid_pct=1.2, valid_samples=171,
                                           gamemd_samples=171, hooks_samples=0,
                                           samples=22500, coverage_pct=None,
                                           cpu_pct_of_one_core=None, frames={}), "INVALID_SAMPLE"),
    ]
    ok = True
    for name, rec, expect in cases:
        res = evaluate(rec, rec.get("tier"))
        got = res["overall"]
        flag = "[PASS]" if got == expect else "[FAIL]"
        if got != expect:
            ok = False
        detail = ", ".join(f"{k}={v['verdict']}" for k, v in res["metrics"].items())
        print(f"  {flag} {name:26s} 期望 {expect:16s} 实得 {got:16s} | {detail}")
    print("=== bench_metrics 自检 " + ("4/4 通过" if ok else "存在失败项") + " ===")
    return 0 if ok else 1


def historical(out_json: "Path | None" = None, out_md: "Path | None" = None) -> int:
    """判定历史基线（out/loadbench/perf_U0800.json、perf-profile.json）能否作为达标证据。"""
    files = [OUT / "perf_U0800.json", OUT / "perf-profile.json"]
    results = []
    for p in files:
        if not p.is_file():
            print(f"[SKIP] 缺文件 {p}")
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        rec["_source"] = str(p.relative_to(PROJECT)).replace("\\", "/")
        rec.setdefault("tier", 800 if "U0800" in p.name else 0)
        results.append(evaluate(rec, rec.get("tier")))
    md = ["## 历史基线指标判定（Q3 反向自证）", ""]
    for r in results:
        md.append(render_markdown(r))
    md += ["### 结论：历史基线不能作为性能达标证据", "",
           "- 两个历史 JSON 都**没有帧序列 / CPU 差分 / 桶表**：平均帧、1% low、TickMiss、CPU、归因覆盖率",
           "  五项在结构上就无法计算（NOT_MEASURABLE），不存在「跑一下就算达标」的路径。",
           "- `perf-profile.json` 有效样本占比 0.76% -> 直接 `INVALID_SAMPLE`（主菜单空闲态）。",
           "- 因此任何性能结论必须由 `tools/bench_replay.py` 真机采样后，再喂本计算器判定。", ""]
    text = "\n".join(md)
    print(text)
    if out_json:
        Path(out_json).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] JSON 落盘: {out_json}")
    if out_md:
        Path(out_md).write_text(text, encoding="utf-8")
        print(f"[OK] Markdown 落盘: {out_md}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bench_metrics", description="验收指标计算与门禁判定（Q3）")
    ap.add_argument("--run", default=None, help="单次采样 JSON（bench_replay run JSON）")
    ap.add_argument("--tier", type=int, default=None, help="档位 200 / 800（缺省取 JSON 内 tier）")
    ap.add_argument("--selftest", action="store_true", help="离线自检四类判定")
    ap.add_argument("--historical", action="store_true", help="判定历史基线能否作为达标证据")
    ap.add_argument("--out-json", default=None)
    ap.add_argument("--out-md", default=None)
    args = ap.parse_args(argv)

    if args.selftest:
        return run_selftest()
    if args.historical:
        return historical(args.out_json or (HARNESS / "metrics_historical.json"),
                          args.out_md or (HARNESS / "metrics_historical.md"))
    if not args.run:
        ap.print_help()
        return 2
    p = Path(args.run)
    if not p.is_file():
        print(f"[FAIL] 文件不存在: {p}", file=sys.stderr)
        return 1
    rec = json.loads(p.read_text(encoding="utf-8"))
    rec["_source"] = str(p)
    res = evaluate(rec, args.tier)
    md = render_markdown(res)
    print(md)
    if args.out_json:
        Path(args.out_json).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.out_md:
        Path(args.out_md).write_text(md, encoding="utf-8")
    return 0 if res["overall"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())