# -*- coding: utf-8 -*-
"""W93 ABBA 观测器扰动标定分析脚本（只读离线分析，严禁输出 p 值与置信区间）。

输入：
  1. `switch_log.ndjson`（由 `abba_driver.py` 生成）
  2. 被测逐拍 NDJSON（含 `t_perf_ns`、`win_cpu_ms`、`elapsed_ingame_s`）

计算口径（依据 `OBSERVER_ABBA_PROTOCOL.md`）：
  - 按 `switch` / `seg_end` 边界切分每段，丢弃每段前 `--warm-sec` 秒（默认取 switch_log 元数据或 10.0s）
  - 每段有效窗内算 `CPU 消耗率 (%) = (Δwin_cpu_ms / 墙钟ms) * 100`
  - 区组内配对：`d_block = mean(A_block) - mean(B_block)`（单位：百分点 pp）
  - 汇总完整区组 `d_block` 的均值、最小值、最大值与极差 (`max - min`)
  - 三档判决（默认预算 0.5 个百分点，要求至少 3 个完整区组，除非显式调整 `--expected-blocks`）：
      1) |d 均值| <= 0.5 pp 且各区组方向一致  => 扰动可接受
      2) |d 均值| >  0.5 pp                   => 不可接受
      3) |d 均值| <= 0.5 pp 但区组方向不一致  => 未分辨（或完整区组数不足 => 未分辨）
  - 按协议规定：绝不输出任何假设检验显著性指标或区间估计。
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def load_switch_log(path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    meta: Dict[str, Any] = {}
    segments: List[Dict[str, Any]] = []
    crashes: List[Dict[str, Any]] = []
    finished: Optional[Dict[str, Any]] = None
    open_segs: Dict[int, Dict[str, Any]] = {}

    with path.open("r", encoding="utf-8") as fp:
        for line_no, raw in enumerate(fp, start=1):
            text = raw.strip()
            if not text:
                continue
            row = json.loads(text)
            ev = row.get("event")
            if ev == "meta":
                meta = row
            elif ev == "switch":
                seg_id = int(row["seg_id"])
                seg = {
                    "seg_id": seg_id,
                    "block": int(row["block"]),
                    "pos_in_block": int(row.get("pos_in_block", seg_id % 4)),
                    "phase": str(row["phase"]),
                    "observer_pid": row.get("observer_pid"),
                    "t_start_ns": int(row["t_perf_ns"]),
                    "t_end_ns": None,
                    "seg_status": "unclosed",
                    "line_no": line_no,
                }
                open_segs[seg_id] = seg
                segments.append(seg)
            elif ev == "seg_end":
                seg_id = int(row["seg_id"])
                if seg_id in open_segs:
                    open_segs[seg_id]["t_end_ns"] = int(row["t_perf_ns"])
                    open_segs[seg_id]["seg_status"] = "completed"
                    open_segs[seg_id]["observer_exit_code"] = row.get("observer_exit_code")
            elif ev == "crash":
                crashes.append(row)
                seg_id = row.get("seg_id")
                if seg_id is not None and int(seg_id) in open_segs:
                    open_segs[int(seg_id)]["t_end_ns"] = int(row["t_perf_ns"])
                    open_segs[int(seg_id)]["seg_status"] = "crash"
            elif ev == "finished":
                finished = row

    # 若 Ctrl-C 中断时某段尚未收到 seg_end，则以 finished 时间截尾并标记为 interrupted
    if finished is not None:
        fin_ns = int(finished["t_perf_ns"])
        for seg in segments:
            if seg["t_end_ns"] is None:
                seg["t_end_ns"] = fin_ns
                seg["seg_status"] = str(finished.get("status", "interrupted"))

    return meta, segments, crashes, finished


def load_run_samples(path: Path) -> List[Dict[str, Any]]:
    samples: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fp:
        for raw in fp:
            text = raw.strip()
            if not text:
                continue
            row = json.loads(text)
            if "kind" in row and row["kind"] != "sample":
                continue
            if "t_perf_ns" not in row:
                continue
            samples.append(row)
    samples.sort(key=lambda r: int(r["t_perf_ns"]))
    return samples


def is_valid_sample(row: Dict[str, Any]) -> bool:
    if row.get("win_cpu_ms") is None:
        return False
    if "read_status" in row and row["read_status"] != "ok":
        return False
    if "elapsed_ingame_s" in row and row["elapsed_ingame_s"] is None:
        return False
    return True


def evaluate_segment(seg: Dict[str, Any], samples: List[Dict[str, Any]], warm_sec: float) -> Dict[str, Any]:
    out = dict(seg)
    t_start = seg["t_start_ns"]
    t_end = seg["t_end_ns"]
    if t_end is None or t_end <= t_start:
        out.update({"valid": False, "reason": "段无有效结束时间戳"})
        return out

    warm_ns = int(round(warm_sec * 1e9))
    win_start = t_start + warm_ns
    if t_end <= win_start:
        out.update({"valid": False, "reason": f"段总时长 {(t_end - t_start) / 1e9:.2f}s <= 预热 {warm_sec:.2f}s"})
        return out

    in_window = [r for r in samples if win_start <= int(r["t_perf_ns"]) <= t_end]
    valid_rows = [r for r in in_window if is_valid_sample(r)]

    out["raw_sample_count"] = len(in_window)
    out["valid_sample_count"] = len(valid_rows)
    out["seg_wall_s"] = (t_end - t_start) / 1e9

    if seg["seg_status"] != "completed":
        out.update({"valid": False, "reason": f"段未完整结束 (status={seg['seg_status']})"})
        return out

    if len(valid_rows) < 2:
        out.update({"valid": False, "reason": f"丢弃预热后有效样本不足 2 点 (count={len(valid_rows)})"})
        return out

    first = valid_rows[0]
    last = valid_rows[-1]
    wall_s = (int(last["t_perf_ns"]) - int(first["t_perf_ns"])) / 1e9
    delta_cpu_ms = float(last["win_cpu_ms"]) - float(first["win_cpu_ms"])

    if wall_s <= 0:
        out.update({"valid": False, "reason": "有效首尾样本墙钟差 <= 0"})
        return out
    if delta_cpu_ms < 0:
        out.update({"valid": False, "reason": f"win_cpu_ms 出现回退 ({delta_cpu_ms:.3f} ms)"})
        return out

    cpu_pct = (delta_cpu_ms / (wall_s * 1000.0)) * 100.0
    ingame_delta: Optional[float] = None
    if first.get("elapsed_ingame_s") is not None and last.get("elapsed_ingame_s") is not None:
        ingame_delta = float(last["elapsed_ingame_s"]) - float(first["elapsed_ingame_s"])

    out.update(
        {
            "valid": True,
            "reason": "ok",
            "effective_wall_s": wall_s,
            "delta_win_cpu_ms": delta_cpu_ms,
            "cpu_rate_pct": cpu_pct,
            "delta_elapsed_ingame_s": ingame_delta,
        }
    )
    return out


def analyze_abba(
    switch_log: Path,
    run_ndjson: Path,
    warm_sec_override: Optional[float] = None,
    budget_pp: float = 0.5,
    expected_blocks_override: Optional[int] = None,
) -> Dict[str, Any]:
    meta, raw_segments, crashes, finished = load_switch_log(switch_log)
    samples = load_run_samples(run_ndjson)

    warm_sec = float(warm_sec_override) if warm_sec_override is not None else float(meta.get("warm_sec", 10.0))
    expected_blocks = (
        int(expected_blocks_override) if expected_blocks_override is not None else int(meta.get("blocks", 3))
    )

    seg_results = [evaluate_segment(seg, samples, warm_sec) for seg in raw_segments]

    by_block: Dict[int, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: {"A": [], "B": []})
    for sr in seg_results:
        if sr["valid"] and sr["phase"] in ("A", "B"):
            by_block[sr["block"]][sr["phase"]].append(sr)

    block_summaries: List[Dict[str, Any]] = []
    all_block_ids = sorted(set(sr["block"] for sr in seg_results) | set(range(1, expected_blocks + 1)))
    for b in all_block_ids:
        a_list = by_block[b]["A"]
        b_list = by_block[b]["B"]
        complete = len(a_list) == 2 and len(b_list) == 2
        if complete:
            mean_a = sum(x["cpu_rate_pct"] for x in a_list) / 2.0
            mean_b = sum(x["cpu_rate_pct"] for x in b_list) / 2.0
            d_block = mean_a - mean_b
        else:
            mean_a = sum(x["cpu_rate_pct"] for x in a_list) / len(a_list) if a_list else None
            mean_b = sum(x["cpu_rate_pct"] for x in b_list) / len(b_list) if b_list else None
            d_block = None
        block_summaries.append(
            {
                "block": b,
                "valid_A_count": len(a_list),
                "valid_B_count": len(b_list),
                "complete": complete,
                "mean_A_pct": mean_a,
                "mean_B_pct": mean_b,
                "d_block_pp": d_block,
            }
        )

    complete_blocks = [bs for bs in block_summaries if bs["complete"]]
    d_values = [float(bs["d_block_pp"]) for bs in complete_blocks]

    if not d_values:
        d_mean = None
        d_min = None
        d_max = None
        d_range = None
        direction_consistent = False
        direction_label = "无完整区组"
    else:
        d_mean = sum(d_values) / len(d_values)
        d_min = min(d_values)
        d_max = max(d_values)
        d_range = d_max - d_min
        if all(d > 0.0 for d in d_values):
            direction_consistent = True
            direction_label = "全为正 (A > B)"
        elif all(d < 0.0 for d in d_values):
            direction_consistent = True
            direction_label = "全为负 (A < B)"
        elif all(d == 0.0 for d in d_values):
            direction_consistent = True
            direction_label = "全为零 (A == B)"
        else:
            direction_consistent = False
            direction_label = "正负混杂（方向不一致）"

    # 三档判决
    if len(complete_blocks) < expected_blocks or d_mean is None:
        verdict_code = "UNRESOLVED"
        verdict_text = f"未分辨：完整 ABBA 区组数不足 ({len(complete_blocks)}/{expected_blocks})"
    elif abs(d_mean) > budget_pp:
        verdict_code = "UNACCEPTABLE"
        verdict_text = (
            f"不可接受：|d均值|={abs(d_mean):.4f} pp > 预算 {budget_pp:.4f} pp"
            + ("" if direction_consistent else "（且区组方向不一致）")
        )
    elif not direction_consistent:
        verdict_code = "UNRESOLVED"
        verdict_text = (
            f"未分辨：|d均值|={abs(d_mean):.4f} pp <= 预算 {budget_pp:.4f} pp，但 {len(complete_blocks)} 个区组方向不一致"
        )
    else:
        verdict_code = "ACCEPTABLE"
        verdict_text = (
            f"扰动可接受：|d均值|={abs(d_mean):.4f} pp <= 预算 {budget_pp:.4f} pp 且 {len(complete_blocks)} 个区组方向一致"
        )

    warnings: List[str] = []
    if crashes:
        warnings.append(f"switch_log 记录了 {len(crashes)} 次观测器段中崩溃事件")
    if finished is None:
        warnings.append("switch_log 缺少 finished 结束标记（可能被强杀）")
    elif finished.get("status") != "completed":
        warnings.append(f"switch_log 结束状态为 {finished.get('status')!r}")
    for sr in seg_results:
        if sr.get("valid") and sr.get("delta_elapsed_ingame_s") is not None and sr["delta_elapsed_ingame_s"] <= 0:
            warnings.append(f"seg={sr['seg_id']} 游戏内时间未前进 (Δelapsed_ingame_s={sr['delta_elapsed_ingame_s']})")

    return {
        "switch_log": str(switch_log),
        "run_ndjson": str(run_ndjson),
        "warm_sec": warm_sec,
        "budget_pp": budget_pp,
        "expected_blocks": expected_blocks,
        "complete_blocks_count": len(complete_blocks),
        "total_samples_loaded": len(samples),
        "segments": seg_results,
        "blocks": block_summaries,
        "summary": {
            "d_mean_pp": d_mean,
            "d_min_pp": d_min,
            "d_max_pp": d_max,
            "d_range_pp": d_range,
            "direction_consistent": direction_consistent,
            "direction_label": direction_label,
        },
        "verdict_code": verdict_code,
        "verdict_text": verdict_text,
        "warnings": warnings,
    }


def format_report(res: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("=== W93 ABBA 观测器 CPU 扰动标定报告 ===")
    lines.append(f"switch_log : {res['switch_log']}")
    lines.append(f"run_ndjson : {res['run_ndjson']} (有效 sample 条数={res['total_samples_loaded']})")
    lines.append(
        f"参数       : warm_sec={res['warm_sec']:.2f}s, budget={res['budget_pp']:.3f} pp, "
        f"完整区组={res['complete_blocks_count']}/{res['expected_blocks']}"
    )
    if res["warnings"]:
        lines.append("警告       :")
        for w in res["warnings"]:
            lines.append(f"  - {w}")

    lines.append("")
    lines.append("--- 逐段明细（已丢弃每段前 warm-sec） ---")
    for sr in res["segments"]:
        if sr["valid"]:
            ig = (
                f"{sr['delta_elapsed_ingame_s']:.2f}s"
                if sr.get("delta_elapsed_ingame_s") is not None
                else "n/a"
            )
            lines.append(
                f"  seg={sr['seg_id']:02d} b={sr['block']} phase={sr['phase']} "
                f"wall={sr['effective_wall_s']:6.2f}s n={sr['valid_sample_count']:4d} "
                f"dCPU={sr['delta_win_cpu_ms']:9.3f}ms CPU%={sr['cpu_rate_pct']:6.3f}% dIngame={ig}"
            )
        else:
            lines.append(
                f"  seg={sr['seg_id']:02d} b={sr['block']} phase={sr['phase']} [INVALID] {sr['reason']}"
            )

    lines.append("")
    lines.append("--- 区组配对结果 d_block = mean(A) - mean(B) ---")
    for bs in res["blocks"]:
        if bs["complete"]:
            lines.append(
                f"  Block {bs['block']}: mean(A)={bs['mean_A_pct']:.4f}%  mean(B)={bs['mean_B_pct']:.4f}%  "
                f"d_block={bs['d_block_pp']:+.4f} pp"
            )
        else:
            lines.append(
                f"  Block {bs['block']}: [INCOMPLETE] valid_A={bs['valid_A_count']}/2, valid_B={bs['valid_B_count']}/2"
            )

    s = res["summary"]
    lines.append("")
    lines.append("--- 汇总与三档判决（按协议不计算显著性检验或区间估计） ---")
    if s["d_mean_pp"] is not None:
        lines.append(
            f"  d 均值   : {s['d_mean_pp']:+.4f} pp  (绝对值 {abs(s['d_mean_pp']):.4f} pp)"
        )
        lines.append(
            f"  d 极差   : {s['d_range_pp']:.4f} pp  (范围 [{s['d_min_pp']:+.4f}, {s['d_max_pp']:+.4f}] pp)"
        )
    else:
        lines.append("  d 均值   : N/A")
        lines.append("  d 极差   : N/A")
    lines.append(f"  方向一致 : {s['direction_label']}")
    lines.append(f"  最终判决 : [{res['verdict_code']}] {res['verdict_text']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="离线分析 ABBA 观测器扰动标定（switch_log.ndjson + 逐拍 run.ndjson），输出均值/极差与三档判决。"
    )
    p.add_argument("--switch-log", type=Path, required=True, help="abba_driver.py 输出的 switch_log.ndjson 路径")
    p.add_argument("--run-ndjson", type=Path, required=True, help="被测逐拍采集脚本输出的 run.ndjson 路径")
    p.add_argument(
        "--warm-sec",
        type=float,
        default=None,
        help="每段起始丢弃的预热秒数（默认读取 switch_log 的 meta.warm_sec，否则 10.0）",
    )
    p.add_argument("--budget-pp", type=float, default=0.5, help="CPU 消耗率差异预算（百分点，默认 0.5）")
    p.add_argument(
        "--expected-blocks",
        type=int,
        default=None,
        help="期望完整区组数（默认读取 switch_log 的 meta.blocks，否则 3）",
    )
    p.add_argument("--json-out", type=Path, default=None, help="可选：将结构化汇总结果写入 JSON 文件")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.switch_log.is_file():
        print(f"[FATAL] switch_log 不存在：{args.switch_log}", file=sys.stderr)
        return 2
    if not args.run_ndjson.is_file():
        print(f"[FATAL] run_ndjson 不存在：{args.run_ndjson}", file=sys.stderr)
        return 2
    if args.budget_pp <= 0:
        print(f"[FATAL] --budget-pp 必须 > 0，当前={args.budget_pp}", file=sys.stderr)
        return 2
    if args.warm_sec is not None and args.warm_sec < 0:
        print(f"[FATAL] --warm-sec 不能为负数，当前={args.warm_sec}", file=sys.stderr)
        return 2

    res = analyze_abba(
        switch_log=args.switch_log.resolve(),
        run_ndjson=args.run_ndjson.resolve(),
        warm_sec_override=args.warm_sec,
        budget_pp=args.budget_pp,
        expected_blocks_override=args.expected_blocks,
    )
    print(format_report(res))

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
