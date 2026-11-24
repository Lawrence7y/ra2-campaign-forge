#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W12 —— RE-N04 基线离线重算（只从 NDJSON 重算，可重复）。

口径（红线）：
  * 区间推进速率 = Δframe / 实测 Δt（真实 t_mono_ns 差，不用名义 30ms×拍数）；
    另报 10 s 分段速率（漂移检查）。**不是逐帧 FPS**。
  * 相邻采样 frame 增量分布：min/中位/p90/max + Δframe==0 占比；
    **注明「增量分布 ≠ 帧时间分布」**（30ms 轮询采样，非逐帧）。
  * 缺测：read_status=fail 拍数与最长连续段；停推：连续 ≥1s frame 不变的段
    （在 ok 拍上判定）计数与最长段，段落在非局内状态的标注（无局内判别器，
    以 win_foreground 与相位时间给线索，不确定写「未定」）。
  * 重复性：R1/R2/R3 的区间速率 / 增量分布（中位、p90）/ 停推段数对比与偏离幅度。
  * R4 对比：与 R1-R3 中位的速率差与增量分布差。**只描述，不归因负载**。

用法：
  python -X utf8 analyze_baseline.py --ndjson out/R1.ndjson out/R2.ndjson out/R3.ndjson out/R4.ndjson
  python -X utf8 analyze_baseline.py --ndjson out/R1.ndjson            # 单趟
输出：out\analysis_summary.json（结构化）+ 控制台摘要。
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from pathlib import Path

WIN_S = 10.0          # 分段速率窗宽（秒）
STALL_S = 1.0         # 停推段判定阈（秒）
LOAD_TAIL_HINT_S = 35.0   # StartGame 后该时刻之前可能含加载尾（R4 门控 ~35s；R1-3 ~20s）


def load_ndjson(path):
    samples, events = [], []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            k = rec.get("kind")
            if k == "sample":
                samples.append(rec)
            elif k in ("event", "meta", "meta_end"):
                events.append(rec)
    return samples, events


def load_meta(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def pctl(sorted_vals, q):
    """线性插值分位（sorted_vals 已排序，q∈[0,1]）。"""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def analyze_run(ndjson_path, meta_path=None):
    if meta_path is None:
        meta_path = str(Path(ndjson_path).with_name(
            Path(ndjson_path).stem.replace("R", "R") + "_meta.json"))
    samples, events = load_ndjson(ndjson_path)
    meta = load_meta(meta_path)
    ig = [s for s in samples
          if s.get("phase") == "ingame" and s.get("read_status") == "ok"]
    ig_all = [s for s in samples if s.get("phase") == "ingame"]
    fails = [s for s in ig_all if s.get("read_status") != "ok"]

    res = {
        "ndjson": str(ndjson_path),
        "n_ingame_samples": len(ig_all),
        "n_ok": len(ig),
        "n_read_fail": len(fails),
        "read_fail_longest_consecutive": 0,
    }

    # ---- 读失败最长连续段（在 ingame 序列上）
    cur = 0
    for s in ig_all:
        if s.get("read_status") != "ok":
            cur += 1
            res["read_fail_longest_consecutive"] = max(
                res["read_fail_longest_consecutive"], cur)
        else:
            cur = 0
    res["read_fail_fail_fields"] = sorted({f2 for s in fails
                                           for f2 in (s.get("read_fail_detail") or [])})

    if len(ig) < 2:
        res["insufficient"] = True
        return res

    t0 = ig[0]["t_mono_ns"]
    t_end = ig[-1]["t_mono_ns"]
    dur = (t_end - t0) / 1e9
    f_first, f_last = ig[0]["frame"], ig[-1]["frame"]
    rate = (f_last - f_first) / dur if dur > 0 else None

    # ---- 10s 分段速率（真实 Δt）
    windows = []
    w_start_idx = 0
    w_start_t = t0
    w_idx = 0
    for i in range(1, len(ig) + 1):
        if i == len(ig) or (ig[i]["t_mono_ns"] - w_start_t) / 1e9 >= WIN_S:
            seg = ig[w_start_idx:i]
            if len(seg) >= 2:
                sd = (seg[-1]["t_mono_ns"] - seg[0]["t_mono_ns"]) / 1e9
                sf = seg[-1]["frame"] - seg[0]["frame"]
                windows.append({
                    "window": w_idx,
                    "start_elapsed_s": round((seg[0]["t_mono_ns"] - t0) / 1e9, 3),
                    "span_s": round(sd, 3),
                    "n_ok": len(seg),
                    "rate": round(sf / sd, 3) if sd > 0 else None,
                    "df": sf,
                })
            else:
                windows.append({"window": w_idx,
                                "start_elapsed_s": round((seg[0]["t_mono_ns"] - t0) / 1e9, 3)
                                if seg else None,
                                "span_s": None, "n_ok": len(seg), "rate": None,
                                "df": None})
            w_start_idx = i
            w_start_t = ig[i]["t_mono_ns"] if i < len(ig) else t_end
            w_idx += 1
    wrates = [w["rate"] for w in windows if w["rate"] is not None]

    # ---- 相邻 ok 采样 frame 增量分布（相邻 = ingame 序列中紧邻且均为 ok）
    deltas = []
    fail_interrupted_pairs = 0
    for i in range(1, len(ig_all)):
        a, b = ig_all[i - 1], ig_all[i]
        if a.get("read_status") == "ok" and b.get("read_status") == "ok":
            deltas.append(b["frame"] - a["frame"])
        elif a.get("read_status") == "ok" or b.get("read_status") == "ok":
            fail_interrupted_pairs += 1
    ds = sorted(deltas)
    dist = dict(collections.Counter(deltas).most_common(12))
    zero_n = sum(1 for x in deltas if x == 0)

    # ---- 停推段（连续 ok 且 frame 不变 ≥1s）
    stalls = []
    run_start = 0
    for i in range(1, len(ig) + 1):
        if i == len(ig) or ig[i]["frame"] != ig[run_start]["frame"]:
            seg = ig[run_start:i]
            if len(seg) >= 2:
                sd = (seg[-1]["t_mono_ns"] - seg[0]["t_mono_ns"]) / 1e9
                if sd >= STALL_S:
                    fg = [bool(s.get("win_foreground")) for s in seg]
                    stalls.append({
                        "start_elapsed_s": round((seg[0]["t_mono_ns"] - t0) / 1e9, 3),
                        "end_elapsed_s": round((seg[-1]["t_mono_ns"] - t0) / 1e9, 3),
                        "duration_s": round(sd, 3),
                        "frame": seg[0]["frame"],
                        "n_ticks": len(seg),
                        "win_foreground_all_true": all(fg),
                        "possible_load_tail": (
                            (seg[0]["t_mono_ns"] - t0) / 1e9 < LOAD_TAIL_HINT_S),
                        "state_label": "未定",
                    })
            run_start = i
    stall_total = sum(s["duration_s"] for s in stalls)

    # ---- 候选代理量现象（只描述；语义未定）
    proxies = {}
    for key in ("A8ED50", "B0CE88", "87E8E0"):
        vals = [s.get(key) for s in ig]
        if vals and all(v is not None for v in vals):
            proxies[key] = {"min": min(vals), "max": max(vals),
                            "n_distinct": len(set(vals)),
                            "n_nonzero": sum(1 for v in vals if v != 0)}
    fields = {}
    for key in ("mode_A8B238", "A8E9A0", "ABCD58", "exitstate",
                "g1", "g2", "g3", "g4"):
        vals = [s.get(key) for s in ig]
        fields[key] = dict(collections.Counter(vals).most_common(6))

    fg_ratio = (sum(1 for s in ig if s.get("win_foreground")) / len(ig))
    res.update({
        "insufficient": False,
        "duration_s": round(dur, 3),
        "frame_first": f_first, "frame_last": f_last,
        "frame_net_delta": f_last - f_first,
        "interval_rate_counts_per_s": round(rate, 4) if rate is not None else None,
        "n_10s_windows": len(windows),
        "window_rates": windows,
        "window_rate_min": round(min(wrates), 3) if wrates else None,
        "window_rate_max": round(max(wrates), 3) if wrates else None,
        "window_rate_spread": round(max(wrates) - min(wrates), 3) if wrates else None,
        "delta_stats": {
            "n_pairs": len(deltas),
            "min": min(deltas) if deltas else None,
            "median": round(statistics.median(deltas), 3) if deltas else None,
            "p90": round(pctl(ds, 0.90), 3) if deltas else None,
            "max": max(deltas) if deltas else None,
            "zero_count": zero_n,
            "zero_ratio": round(zero_n / len(deltas), 4) if deltas else None,
            "dist_top": dist,
            "fail_interrupted_pairs": fail_interrupted_pairs,
            "note": "相邻采样增量分布 ≠ 帧时间分布（30ms 轮询，非逐帧采样）；"
                    "Δframe==0 可能是闲置停推也可能是采样快于帧周期",
        },
        "stalls": stalls,
        "stall_count": len(stalls),
        "stall_max_s": round(max((s["duration_s"] for s in stalls), default=0.0), 3),
        "stall_total_s": round(stall_total, 3),
        "win_foreground_true_ratio": round(fg_ratio, 4),
        "fields_dist": fields,
        "proxies": proxies,
        "meta_map": (meta.get("map") or {}),
        "meta_gate": (meta.get("battle_gate") or {}),
        "meta_phase_stop": meta.get("phase_stop"),
        "meta_error": meta.get("error"),
        "meta_residual_after": meta.get("residual_after"),
        "meta_restore_ok": all(
            r.get("sha_match") and r.get("byte_identical_to_baseline")
            for r in (meta.get("restore_rows") or [])
            if r.get("file") in ("RA2MD.INI", "ddraw.ini", "RA2MD.INI.benchbak")),
        "meta_prelaunch_match": all(
            v.get("match") for v in (meta.get("prelaunch_hashes") or {}).values()),
        "meta_conditions": meta.get("conditions"),
        "meta_carrier": meta.get("carrier"),
    })
    return res


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--ndjson", nargs="+", required=True,
                    help="NDJSON 路径列表（meta 取同目录 <stem>_meta.json）")
    ap.add_argument("--meta", nargs="*", default=None,
                    help="可选：与 --ndjson 一一对应的 meta 路径")
    ap.add_argument("--out", default=None,
                    help="输出 JSON 路径（默认 <首个 ndjson 所在目录>/analysis_summary.json）")
    a = ap.parse_args()
    metas = a.meta or [None] * len(a.ndjson)
    if a.meta and len(a.meta) != len(a.ndjson):
        raise SystemExit("--meta 与 --ndjson 数量不一致")
    runs = [analyze_run(p, m) for p, m in zip(a.ndjson, metas)]

    # ---- 重复性：R1-R3（取前三个以 Proving Grounds 为载体的趟）
    comp = {}
    for r in runs:
        comp[r["ndjson"]] = r

    def trio_summary():
        rates = [r.get("interval_rate_counts_per_s") for r in runs[:3]
                 if r.get("interval_rate_counts_per_s") is not None]
        meds = [r["delta_stats"]["median"] for r in runs[:3]
                if r.get("delta_stats") and r["delta_stats"]["median"] is not None]
        p90s = [r["delta_stats"]["p90"] for r in runs[:3]
                if r.get("delta_stats") and r["delta_stats"]["p90"] is not None]
        stalls = [r.get("stall_count") for r in runs[:3]]
        out = {"rates": rates, "delta_medians": meds, "delta_p90s": p90s,
               "stall_counts": stalls}
        if len(rates) >= 2:
            med = statistics.median(rates)
            out["rate_median"] = round(med, 4)
            out["rate_max_abs_dev"] = round(max(abs(x - med) for x in rates), 4)
            out["rate_max_abs_dev_pct"] = round(
                100.0 * max(abs(x - med) for x in rates) / med, 3)
            out["rate_min"] = round(min(rates), 4)
            out["rate_max"] = round(max(rates), 4)
        return out

    trio = trio_summary()

    # ---- R4 对比（若存在第 4 趟）
    r4 = runs[3] if len(runs) >= 4 else None
    r4_cmp = None
    if r4 and not r4.get("insufficient") and trio.get("rate_median"):
        r4_cmp = {
            "r4_rate": r4.get("interval_rate_counts_per_s"),
            "r13_median_rate": trio["rate_median"],
            "rate_diff": round(r4["interval_rate_counts_per_s"]
                               - trio["rate_median"], 4),
            "rate_diff_pct": round(100.0 * (r4["interval_rate_counts_per_s"]
                                            - trio["rate_median"])
                                   / trio["rate_median"], 3),
            "r4_delta_median": r4["delta_stats"]["median"],
            "r13_delta_median": trio["delta_medians"],
            "r4_delta_p90": r4["delta_stats"]["p90"],
            "r13_delta_p90": trio["delta_p90s"],
            "r4_zero_ratio": r4["delta_stats"]["zero_ratio"],
            "r4_stall_count": r4.get("stall_count"),
            "note": "只描述差异；负载未经验证，不归因",
        }

    summary = {
        "generated_note": "离线重算自 NDJSON；口径见 analyze_baseline.py 头注",
        "runs": runs,
        "repeatability_r1_r3": trio,
        "r4_vs_r13": r4_cmp,
    }
    out_path = a.out or str(Path(a.ndjson[0]).parent / "analysis_summary.json")
    Path(out_path).write_text(json.dumps(summary, ensure_ascii=False, indent=1,
                                         sort_keys=True, default=str),
                              encoding="utf-8")

    # ---- 控制台摘要
    for r in runs:
        if r.get("insufficient"):
            print("%s: 不足（ok=%d, fail=%d, err=%s）" %
                  (Path(r["ndjson"]).name, r.get("n_ok"), r.get("n_read_fail"),
                   r.get("meta_error")))
            continue
        print("%s: dur=%.1fs rate=%.4f/s 10s窗[%.3f..%.3f] Δ(min/med/p90/max)=%s/%s/%s/%s "
              "zero=%.2f%% fail=%d stall=%d(max %.2fs) fg=%.2f map=%r gate=%s" %
              (Path(r["ndjson"]).name, r["duration_s"], r["interval_rate_counts_per_s"],
               r["window_rate_min"], r["window_rate_max"],
               r["delta_stats"]["min"], r["delta_stats"]["median"],
               r["delta_stats"]["p90"], r["delta_stats"]["max"],
               100 * r["delta_stats"]["zero_ratio"], r["n_read_fail"],
               r["stall_count"], r["stall_max_s"], r["win_foreground_true_ratio"],
               (r["meta_map"] or {}).get("display_name"),
               (r["meta_gate"] or {}).get("gate_kind")))
        for st in r["stalls"]:
            print("    stall @%.1fs dur=%.2fs frame=%d fg_all=%s load_tail_hint=%s %s" %
                  (st["start_elapsed_s"], st["duration_s"], st["frame"],
                   st["win_foreground_all_true"], st["possible_load_tail"],
                   st["state_label"]))
    print("R1-R3 重复性: rates=%s median=%s maxdev=%.4f(%.2f%%)  medians=%s p90s=%s stalls=%s"
          % (trio.get("rates"), trio.get("rate_median"),
             trio.get("rate_max_abs_dev", 0), trio.get("rate_max_abs_dev_pct", 0),
             trio.get("delta_medians"), trio.get("delta_p90s"),
             trio.get("stall_counts")))
    if r4_cmp:
        print("R4 对比: %s" % json.dumps(r4_cmp, ensure_ascii=False))
    print("已写出 %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
