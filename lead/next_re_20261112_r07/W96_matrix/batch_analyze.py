#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W94 BATCH ANALYZE - summarize every trip's run.ndjson into SUMMARY.csv/md.

    python batch_analyze.py OUT_ROOT [--matrix MATRIX.json] [--out-dir DIR]

OUT_ROOT is the runner's out/ directory (default: <card>/out) holding
trip_*/ subdirectories, each with run.ndjson (+ TRIP_RESULT.json, archived
except*.txt copies from D1).  Cell grouping: from the trip dir name
trip_<cell>_r<k> (greedy; cell ids must NOT end with _r<digits>).

Per-trip metrics (FILETIME channel is PRIMARY, cycle channel is evidence
only - W90 U1 signed wording; NO significance language anywhere):
  * window-thread CPU consumption rate over the FULL sampled window
    (Sigma GetThreadTimes kernel+user / wall time, single-core occupancy %)
  * A8ED50 nonzero-tick ratio (+ first nonzero tick)
  * X87E8E0 change count (+ first value / first change)
  * read failures, foreground-loss samples, ingame duration, stop reason
  * D1 crash forensics: EIP list from archived except*.txt
    (regex "Bytes at CS:EIP (XXXXXXXX)")

SUMMARY.csv: one row per trip.
SUMMARY.md: per-cell aggregates (趟数, outcome 分布, CPU 消耗率均值/极差,
A8ED50 非零占比, X87E8E0 变化, 崩溃 EIP 列表) + caveats.

Wording discipline inherited from W88/W90: rates are descriptive only; the
paired-control verdict wording (ratio <1.10 / >=1.10) is a PAIRED analysis
rule and is deliberately NOT computed here - the matrix layer collects the
raw per-trip numbers, pairing decisions stay with the lead.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from pathlib import Path

NS_MS = 1e9
EIP_RE = re.compile(r"Bytes at CS:EIP \(([0-9A-Fa-f]{1,8})\)")
TRIP_RE = re.compile(r"^trip_(.+)_r(\d+)$")
# [Lead patch 2026-11-14] 兼容历史卡的 trip 命名（trip_<label>，无 _r<k> 后缀）：
# W85/W88/W90 的目录是 trip_C6_c / trip_C1 等，原正则会把它们全部漏掉
# （实测：对 W90 的 out_root 得 trips: 0）。
TRIP_RE_LEGACY = re.compile(r"^trip_(.+)$")


def load_ndjson(path: Path):
    rows = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
    except OSError:
        pass
    return rows


def samples_of(rows):
    return [r for r in rows if r.get("kind") == "sample"
            and r.get("elapsed_ingame_s") is not None]


def window_rates(win):
    """FILETIME-channel CPU consumption rate over the sample window (%)"""
    if len(win) < 5:
        return None
    t0, t1 = win[0]["t_perf_ns"], win[-1]["t_perf_ns"]
    wall = (t1 - t0) / NS_MS
    if wall <= 0:
        return None
    sum_ms = 0.0
    for i in range(1, len(win)):
        a, b = win[i - 1], win[i]
        if b.get("read_status") != "ok" or a.get("read_status") != "ok":
            continue
        if b.get("win_cpu_ms_delta") is not None:
            sum_ms += b["win_cpu_ms_delta"]
    return {"rate_pct_filetime": round(sum_ms / wall / 10.0, 4),
            "wall_s": round(wall, 3), "n": len(win),
            "sum_cpu_ms": round(sum_ms, 2)}


def anchors(samples):
    nz_idx = None
    x87_first = None
    x87_changes = 0
    prev = None
    for i, r in enumerate(samples):
        if r.get("read_status") != "ok":
            continue
        if nz_idx is None and (r.get("A8ED50") or 0) != 0:
            nz_idx = i
        xv = r.get("X87E8E0")
        if x87_first is None:
            x87_first = xv
            prev = xv
        elif xv != prev:
            x87_changes += 1
            prev = xv
    return {"a8ed50_first_nonzero_idx": nz_idx,
            "x87e8e0_first_value": x87_first,
            "x87e8e0_n_changes": x87_changes}


def eip_list(trip_dir: Path):
    eips = []
    for p in sorted(trip_dir.glob("archived_*.txt")):
        try:
            txt = p.read_text(encoding="latin-1", errors="replace")
        except OSError:
            continue
        for m in EIP_RE.finditer(txt):
            eips.append({"eip": m.group(1).upper(), "src": p.name})
    return eips


def trip_stats(trip_dir: Path, run_id_hint=None):
    name_m = TRIP_RE.match(trip_dir.name)
    if name_m:
        cell, rep = name_m.group(1), int(name_m.group(2))
    else:
        # [Lead patch] 历史卡命名兼容：trip_C6_c / trip_C1 -> cell=全名, r=1
        legacy = TRIP_RE_LEGACY.match(trip_dir.name)
        if not legacy:
            return None
        cell, rep = legacy.group(1), 1
    res = {"trip": trip_dir.name, "cell": cell, "r": rep,
           "run_id": run_id_hint or "", "outcome": None, "ok": None,
           "terminal": None, "stop_reason": None, "ingame_s": None,
           "n_samples": None, "n_read_fail": None, "n_fg_loss": None,
           "rate_pct_filetime": None, "wall_s": None, "sum_cpu_ms": None,
           "a8ed50_nonzero_ratio": None, "a8ed50_nz_n": None, "a8ed50_n": None,
           "a8ed50_first_nonzero_idx": None,
           "x87e8e0_changes": None, "x87e8e0_first_value": None,
           "d1_captured": None, "eips": ""}
    rp = trip_dir / "TRIP_RESULT.json"
    if rp.is_file():
        try:
            r = json.loads(rp.read_text(encoding="utf-8"))
            res["outcome"] = r.get("outcome")
            res["ok"] = r.get("ok")
            res["terminal"] = (r.get("terminal") or {}).get("kind")
            s = r.get("sampling") or {}
            res["stop_reason"] = s.get("stop_reason")
            res["ingame_s"] = s.get("ingame_duration_s")
            res["n_read_fail"] = s.get("n_read_fail")
            res["n_fg_loss"] = s.get("n_fg_loss_samples")
            res["d1_captured"] = bool(r.get("d1_forensics"))
        except Exception:
            pass
    rows = load_ndjson(trip_dir / "run.ndjson")
    s = samples_of(rows)
    res["n_samples"] = len(s)
    if s:
        wr = window_rates(s)
        if wr:
            res["rate_pct_filetime"] = wr["rate_pct_filetime"]
            res["wall_s"] = wr["wall_s"]
            res["sum_cpu_ms"] = wr["sum_cpu_ms"]
        n_ok = sum(1 for r in s if r.get("read_status") == "ok")
        nzn = sum(1 for r in s if (r.get("A8ED50") or 0) != 0
                  and r.get("read_status") == "ok")
        res["a8ed50_nz_n"] = nzn
        res["a8ed50_n"] = n_ok
        res["a8ed50_nonzero_ratio"] = round(nzn / n_ok, 5) if n_ok else None
        an = anchors(s)
        res["a8ed50_first_nonzero_idx"] = an["a8ed50_first_nonzero_idx"]
        res["x87e8e0_first_value"] = an["x87e8e0_first_value"]
        res["x87e8e0_changes"] = an["x87e8e0_n_changes"]
    eips = eip_list(trip_dir)
    res["eip_details"] = eips
    res["eips"] = ";".join(dict.fromkeys(e["eip"] for e in eips))
    return res


def agg(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"mean": None, "min": None, "max": None,
                "range": None, "n": 0}
    return {"mean": round(sum(vals) / len(vals), 4),
            "min": round(min(vals), 4), "max": round(max(vals), 4),
            "range": round(max(vals) - min(vals), 4), "n": len(vals)}


def main() -> int:
    ap = argparse.ArgumentParser(description="W94 batch analyzer")
    ap.add_argument("out_root", nargs="?",
                    default=str(Path(__file__).resolve().parent / "out"))
    ap.add_argument("--matrix", default=None,
                    help="matrix JSON (only used to record run_id in output)")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    root = Path(args.out_root)
    out_dir = Path(args.out_dir) if args.out_dir else root
    run_id = None
    if args.matrix:
        try:
            run_id = json.loads(Path(args.matrix).read_text(
                encoding="utf-8-sig")).get("run_id")
        except Exception:
            pass
    trip_dirs = sorted([p for p in root.glob("trip_*") if p.is_dir()],
                       key=lambda p: p.name.lower())
    stats = [s for s in (trip_stats(d, run_id) for d in trip_dirs) if s]

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "SUMMARY.csv"
    md_path = out_dir / "SUMMARY.md"

    cols = ["run_id", "cell", "r", "trip", "outcome", "ok", "terminal",
            "stop_reason", "ingame_s", "n_samples", "n_read_fail", "n_fg_loss",
            "rate_pct_filetime", "wall_s", "sum_cpu_ms",
            "a8ed50_nonzero_ratio", "a8ed50_nz_n", "a8ed50_n",
            "a8ed50_first_nonzero_idx", "x87e8e0_changes",
            "x87e8e0_first_value", "d1_captured", "eips"]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for s in stats:
            w.writerow(s)

    # ---- per-cell aggregates ----
    cells = {}
    for s in stats:
        cells.setdefault(s["cell"], []).append(s)
    lines = []
    lines.append("# W94 MATRIX SUMMARY (batch_analyze)")
    lines.append("")
    lines.append("- out_root: `%s`" % root)
    lines.append("- run_id: %s" % (run_id or "(not supplied)"))
    lines.append("- trips found: %d (cells: %d)" % (len(stats), len(cells)))
    lines.append("- 口径: CPU 消耗率 = 窗口线程 CPU(GetThreadTimes kernel+user) "
                 "/ 墙钟，单核占用百分比，全采样窗；FILETIME 主通道。")
    lines.append("- 措辞纪律: 本表只做描述统计（均值/极差/占比），"
                 "不做显著性表述；配对判定措辞属 Lead 层，不在此计算。")
    lines.append("")
    for cell in sorted(cells):
        ts = sorted(cells[cell], key=lambda s: s["r"])
        rate = agg([t["rate_pct_filetime"] for t in ts])
        a8r = agg([t["a8ed50_nonzero_ratio"] for t in ts])
        x87 = agg([float(t["x87e8e0_changes"]) if t["x87e8e0_changes"]
                   is not None else None for t in ts])
        dist = {}
        for t in ts:
            dist[t["outcome"] or "(no TRIP_RESULT)"] = \
                dist.get(t["outcome"] or "(no TRIP_RESULT)", 0) + 1
        eips = sorted({e["eip"] for t in ts for e in t["eip_details"]})
        n_complete = sum(1 for t in ts if t["outcome"])
        lines.append("## cell `%s`" % cell)
        lines.append("")
        lines.append("| 趟 | trip | outcome | ok | ingame_s | CPU%% | "
                     "A8ED50 非零比 | X87E8E0 变化 | EIP |")
        lines.append("|---|---|---|---|---:|---:|---:|---:|---|")
        for t in ts:
            lines.append("| r%d | %s | %s | %s | %s | %s | %s | %s | %s |"
                         % (t["r"], t["trip"], t["outcome"] or "-",
                            t["ok"] if t["ok"] is not None else "-",
                            t["ingame_s"] if t["ingame_s"] is not None else "-",
                            t["rate_pct_filetime"] if t["rate_pct_filetime"]
                            is not None else "-",
                            t["a8ed50_nonzero_ratio"]
                            if t["a8ed50_nonzero_ratio"] is not None else "-",
                            t["x87e8e0_changes"]
                            if t["x87e8e0_changes"] is not None else "-",
                            t["eips"] or "-"))
        lines.append("")
        lines.append("- 趟数: %d（TRIP_RESULT 完整: %d）" % (len(ts), n_complete))
        lines.append("- outcome 分布: %s" % json.dumps(dist, ensure_ascii=False))
        lines.append("- CPU 消耗率%%: 均值 %s / 极差 %s（min %s, max %s）"
                     % (rate["mean"], rate["range"], rate["min"], rate["max"]))
        lines.append("- A8ED50 非零占比: 均值 %s（min %s, max %s）"
                     % (a8r["mean"], a8r["min"], a8r["max"]))
        lines.append("- X87E8E0 变化次数: 均值 %s / 极差 %s"
                     % (x87["mean"], x87["range"]))
        lines.append("- 崩溃 EIP 列表: %s" % (", ".join(eips) if eips
                                              else "（无归档 except 命中）"))
        lines.append("")
    if not stats:
        lines.append("(no trip_* directories with parseable names found under "
                     "`%s`)" % root)
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("SUMMARY.csv : %s" % csv_path)
    print("SUMMARY.md  : %s" % md_path)
    print("trips: %d cells: %d" % (len(stats), len(cells)))
    return 0


if __name__ == "__main__":
    sys.exit(main())


