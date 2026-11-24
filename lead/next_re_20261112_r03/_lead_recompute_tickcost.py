#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead 独立复算器：只吃 tickcost.csv（逐拍扁平表），不 import 任何子代理的分析器。

口径（与 r02 已签发口径对齐，任何偏离都会打印出来）：
- "局内有效窗" = 从**首个 frame>0** 的拍起，到**最后一个 frame>0** 的拍止（含两端）。
  理由：记录开头含加载期（frame==0，约 13 s），尾含结算/退出退化窗；两者都不是被测对象。
- 每拍 CPU 取 `cyc_est_ms`（窗口线程 cycle 自标定）。`cyc_est_ms_A_factor` 只作旁证。
- 统计量：n / 中位 / 均值 / p90 / p95 / p99 / max。
- 副作用量：≥64 ms 且 Δframe==0 的"饿死"拍数；Δframe≥2 的跳多拍数；读失败（note 非空）计数。
- 按 A8ED50 分组（0/1/2/3+）给中位，用于剂量反应判断。

用法：
  python _lead_recompute_tickcost.py <tickcost.csv> [--label NAME] [--json OUT]
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path


def pct(sorted_vals, q):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = k - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def num(row, key, cast=float):
    v = row.get(key)
    if v is None or v == "":
        return None
    try:
        return cast(v)
    except (TypeError, ValueError):
        return None


def load(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows


def summarize(rows, label, filename=""):
    # 1) 定位局内窗
    first_gt = last_gt = None
    for i, r in enumerate(rows):
        fr = num(r, "frame", int)
        if fr is not None and fr > 0:
            if first_gt is None:
                first_gt = i
            last_gt = i
    if first_gt is None:
        return {"label": label, "error": "no frame>0 rows"}

    win = rows[first_gt : last_gt + 1]
    cpus = []
    by_evt = {}
    gaps = []
    jumps = 0
    starve = 0
    readfail = 0
    zero_adv = 0
    prev_frame = None
    for r in win:
        c = num(r, "cyc_est_ms")
        if c is not None and c > 0:
            cpus.append(c)
            ev = num(r, "A8ED50", int)
            key = "3+" if (ev is not None and ev >= 3) else str(ev)
            by_evt.setdefault(key, []).append(c)
        g = num(r, "interval_ms")
        if g is not None:
            gaps.append(g)
        fr = num(r, "frame", int)
        if prev_frame is not None and fr is not None:
            d = fr - prev_frame
            if d >= 2:
                jumps += 1
            if d == 0:
                zero_adv += 1
                if g is not None and g >= 64.0:
                    starve += 1
        prev_frame = fr if fr is not None else prev_frame
        note = (r.get("note") or "").strip()
        if note:
            readfail += 1

    cpus_sorted = sorted(cpus)
    gaps_sorted = sorted(gaps)
    # 采样缺测单列：cyc_est_ms 为空 = 该拍没有 CPU 读数（采样器漏采），
    # 它的 interval_ms 仍然很大且 Δframe 可能 >=2，若与"游戏停顿"混算会造出伪饿死拍。
    valid_gaps = []
    valid_jumps = 0
    true_jumps = 0
    prev_frame_valid = None
    prev_valid_pos = None
    missing_cyc = 0
    for pos, r in enumerate(win):
        c = num(r, "cyc_est_ms")
        has_cyc = c is not None and c > 0
        fr = num(r, "frame", int)
        if not has_cyc:
            missing_cyc += 1
        if has_cyc:
            g = num(r, "interval_ms")
            if g is not None:
                valid_gaps.append(g)
            if prev_frame_valid is not None and fr is not None and (fr - prev_frame_valid) >= 2:
                valid_jumps += 1
                # 真跳拍：两次有效采样在记录里相邻（中间无缺测），Δframe 仍 >=2
                if prev_valid_pos is not None and pos - prev_valid_pos == 1:
                    true_jumps += 1
            prev_frame_valid = fr if fr is not None else prev_frame_valid
            prev_valid_pos = pos
    valid_gaps_sorted = sorted(valid_gaps)
    out = {
        "label": label,
        "file": filename,
        "rows_total": len(rows),
        "window_rows": len(win),
        "window_first_index": first_gt,
        "window_last_index": last_gt,
        "t_start_s": num(win[0], "t_rel_s") if win else None,
        "t_end_s": num(win[-1], "t_rel_s") if win else None,
        "frame_start": num(win[0], "frame", int) if win else None,
        "frame_end": num(win[-1], "frame", int) if win else None,
        "cpu_n": len(cpus_sorted),
        "cpu_median_ms": round(statistics.median(cpus_sorted), 6) if cpus_sorted else None,
        "cpu_mean_ms": round(statistics.fmean(cpus_sorted), 6) if cpus_sorted else None,
        "cpu_p90_ms": round(pct(cpus_sorted, 0.90), 6) if cpus_sorted else None,
        "cpu_p95_ms": round(pct(cpus_sorted, 0.95), 6) if cpus_sorted else None,
        "cpu_p99_ms": round(pct(cpus_sorted, 0.99), 6) if cpus_sorted else None,
        "cpu_max_ms": round(cpus_sorted[-1], 6) if cpus_sorted else None,
        "gap_median_ms": round(statistics.median(gaps_sorted), 6) if gaps_sorted else None,
        "gap_p99_ms": round(pct(gaps_sorted, 0.99), 6) if gaps_sorted else None,
        "gap_ge64_ms_n": sum(1 for g in gaps_sorted if g >= 64.0),
        "zero_advance_ticks": zero_adv,
        "starve_ticks_ge64_and_no_advance": starve,
        "frame_jump_ge2": jumps,
        "missing_cyc_rows": missing_cyc,
        "gap_ge64_valid_n": sum(1 for g in valid_gaps_sorted if g >= 64.0),
        "gap_median_valid_ms": round(statistics.median(valid_gaps_sorted), 6)
        if valid_gaps_sorted
        else None,
        "gap_p99_valid_ms": round(pct(valid_gaps_sorted, 0.99), 6) if valid_gaps_sorted else None,
        "frame_jump_ge2_valid": valid_jumps,
        "frame_jump_ge2_true": true_jumps,
        "readfail_notes": readfail,
        "by_A8ED50": {
            k: {
                "n": len(v),
                "median_ms": round(statistics.median(sorted(v)), 6),
            }
            for k, v in sorted(by_evt.items())
        },
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="+")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    results = []
    for p in args.csv:
        path = Path(p)
        rows = load(path)
        res = summarize(rows, path.stem, path.name)
        results.append(res)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    if args.json:
        Path(args.json).write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    main()

