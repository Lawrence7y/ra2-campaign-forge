#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RE-N01 / replay_re_n01.py —— 只读 NDJSON 的离线重算器。

严格边界：
  * 本模块**只读磁盘上的 NDJSON 文本文件**；
  * 不 import ctypes / 不加载任何 Win32 DLL / 不打开任何进程句柄 /
    不调用 ReadProcessMemory / SuspendThread / StackWalk64；
  * 不写 NDJSON（只在 --out 显式给出时写一份摘要 JSON）。

重算内容（任务卡 §4）：
  1. 段统计（segments）
  2. 零Δ连续段（含缺测感知：读失败/超长真实间隔都会打断，见 _scan_zero_delta_runs）
  3. 停滞事件（events）
  4. 读状态直方图（read_status_hist）
  5. 计时分项汇总（cost_ns_sum / cost_ns_max）

用法：
  python -X utf8 replay_re_n01.py <ndjson> [--out summary.json] [--quiet]

摘要 schema = "re_n01_summary_v1"，与驱动候选件 _run_hl_match_candidate.py
内的 OnlineAccumulator（独立实现）逐字段一致；T-C4 对此做硬校验。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCHEMA = "re_n01_summary_v1"

# 缺测/分段标记（与驱动候选件、make_fixture.py 共用同一组字符串常量）
SEGMENT_MARKERS = ("frame_regression", "new_game", "load_game", "pid_change",
                   "read_failed_gap", "resume_after_gap", "run_start")
DEFAULT_MIN_OBS = 6
DEFAULT_STALL_N_NS = 1_000_000_000
DEFAULT_NOMINAL_INTERVAL_NS = 200_000_000
DEFAULT_GAP_MAX_NS = 600_000_000      # 3 × 0.2 s；真实间隔超过此值视为缺测证据

COST_FIELDS = ("detect_ns", "preflight_ns", "ownership_ns", "context_ns",
               "walk_ns", "resume_ns", "suspend_held_ns", "end_to_end_ns",
               "event_total_ns", "overhead_ns")


# ---------------------------------------------------------------- 读文件

def load_records(path):
    """逐行解析 NDJSON；返回 list[dict]。空行/非法行抛 ValueError（不静默过滤）。"""
    out = []
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception as e:                            # noqa: BLE001
                raise ValueError("NDJSON line %d is not valid JSON: %s" % (i, e))
            if not isinstance(obj, dict):
                raise ValueError("NDJSON line %d is not an object" % i)
            out.append(obj)
    return out


def _meta_of(records):
    for r in records:
        if r.get("kind") == "meta":
            return r
    return {}


def _sorted_hist(d):
    return {k: int(d[k]) for k in sorted(d)}


# ---------------------------------------------------------------- 零Δ连续段

def _scan_zero_delta_runs(reads, min_obs, stall_n_ns, gap_max_ns):
    """缺测感知的零Δ连续段扫描。

    规则（对应 C2 / T-C2）：
      * 只在**同一段内**、且 read_status == "ok" 的连续读数之间比较；
      * frame 相同才延续；frame 不同按**正常帧推进**收束（不是缺测证据）；
      * 任一 read_failed 记录（或跨段、或真实间隔 gap_ns > gap_max_ns）
        立即收束并把相邻 run 标成 gap_interrupted；
      * 因此「帧100 → 长读失败区间 → 帧100」不可能合并成一个长 run。
      * confirmed 需同时满足：n >= min_obs、duration_ns >= stall_n_ns、
        没有任何缺测证据（gap_interrupted / 未到阈值另计）。

    返回 list[dict]，字段：
      segment, frame, start_seq, end_seq, n, duration_ns, confirmed, reason

    RE-N01 修正（FACT_CHECK）：原版把「帧号变化」也记成
    ``frame_change_or_gap`` 并排除出 confirmed，导致**只有整条流的最后一段**
    才可能被证实为连续冻结。现改为 ``frame_change``（正常推进），与
    candidate/re_n01_monitor.py 的流式扫描器逐字段对齐（T-C4 硬校验）。
    """
    by_seq = {r.get("seq"): r for r in reads}
    raw_runs = []
    cur = None
    prev = None
    pending_gap = False          # 上一条是缺测 ⇒ 紧随的 run 也带缺测证据

    def close(reason):
        nonlocal cur
        if cur is None:
            return
        raw_runs.append((dict(cur), reason))
        cur = None

    for r in reads:
        ok = (r.get("read_status") == "ok" and r.get("frame") is not None)
        if not ok:
            # 读失败 / 缺测：收束当前 run（带缺测证据），并标记紧随的下一个 run
            close("gap_interrupted")
            pending_gap = True
            prev = r
            continue

        if prev is not None:
            if (prev.get("segment") != r.get("segment")
                    or prev.get("read_status") != "ok"
                    or int(r.get("gap_ns") or 0) > gap_max_ns):
                close("gap_interrupted")
                pending_gap = True

        if cur is not None:
            if (cur["segment"] != r.get("segment")
                    or int(r.get("gap_ns") or 0) > gap_max_ns):
                close("gap_interrupted")
                pending_gap = True
            elif cur["frame"] != r.get("frame"):
                close("frame_change")        # 正常帧推进，不是缺测证据

        if cur is None:
            cur = {"segment": r.get("segment"), "frame": r.get("frame"),
                   "start_seq": r.get("seq"), "end_seq": r.get("seq"),
                   "n": 1, "adjacent_to_gap": bool(pending_gap)}
            pending_gap = False
        else:
            cur["end_seq"] = r.get("seq")
            cur["n"] += 1
        prev = r
    close("end_of_stream")

    runs = []
    for c, reason in raw_runs:
        adjacent = bool(c.pop("adjacent_to_gap", False))
        a = by_seq.get(c["start_seq"])
        b = by_seq.get(c["end_seq"])
        dur = (int(b.get("t_mono_ns", 0)) - int(a.get("t_mono_ns", 0))) \
            if (a is not None and b is not None) else 0
        no_gap = (reason not in ("gap_interrupted", "frame_change_or_gap")
                  and not adjacent)
        runs.append({
            "segment": c["segment"], "frame": c["frame"],
            "start_seq": c["start_seq"], "end_seq": c["end_seq"],
            "n": int(c["n"]), "duration_ns": int(dur),
            "confirmed": bool(no_gap and c["n"] >= min_obs
                              and dur >= stall_n_ns),
            "reason": ("gap_interrupted" if adjacent else reason),
        })
    return runs


# ---------------------------------------------------------------- 主归约器

def summarize_records(records):
    """纯函数：由 NDJSON 记录列表重算完整摘要。不触碰任何进程。"""
    meta = _meta_of(records)
    run_id = str(meta.get("run_id", ""))
    provenance = str(meta.get("provenance", ""))
    min_obs = int(meta.get("min_obs", DEFAULT_MIN_OBS))
    stall_n_ns = int(meta.get("stall_n_ns", DEFAULT_STALL_N_NS))
    gap_max_ns = int(meta.get("gap_max_ns", DEFAULT_GAP_MAX_NS))

    reads = [r for r in records if r.get("kind") == "frame_read"]
    events = [r for r in records if r.get("kind") == "event"]

    read_status_hist, state_label_hist = {}, {}
    sample_flag_true = 0
    for r in reads:
        s = str(r.get("read_status", "unknown"))
        read_status_hist[s] = read_status_hist.get(s, 0) + 1
        lab = str(r.get("state_label", "UNKNOWN"))
        state_label_hist[lab] = state_label_hist.get(lab, 0) + 1
        if r.get("sample_flag"):
            sample_flag_true += 1

    # ---- 段统计（按记录里已写死的 segment / segment_reason 聚合）----
    seg_order, seg_map = [], {}
    for r in records:
        sid = r.get("segment")
        if sid is None:
            continue
        if sid not in seg_map:
            seg_map[sid] = {
                "segment": sid,
                "reason": str(r.get("segment_reason", "")),
                "n_records": 0, "n_read_ok": 0, "n_read_failed": 0,
                "first_seq": r.get("seq"), "last_seq": r.get("seq"),
                "t_first_ns": r.get("t_mono_ns"), "t_last_ns": r.get("t_mono_ns"),
                "frame_first": None, "frame_last": None,
                "verdict": "measurable", "undecidable": False,
            }
            seg_order.append(sid)
        s = seg_map[sid]
        s["n_records"] += 1
        s["last_seq"] = r.get("seq")
        s["t_last_ns"] = r.get("t_mono_ns")
        if r.get("kind") == "frame_read":
            if r.get("read_status") == "ok":
                s["n_read_ok"] += 1
                f = r.get("frame")
                if f is not None:
                    if s["frame_first"] is None:
                        s["frame_first"] = f
                    s["frame_last"] = f
            else:
                s["n_read_failed"] += 1
        if s["reason"] in ("read_failed_gap", "resume_after_gap"):
            s["verdict"] = "missing_gap"
            s["undecidable"] = True
        elif s["reason"] in ("frame_regression", "new_game", "load_game", "pid_change"):
            s["verdict"] = "boundary"
    segments = []
    for sid in seg_order:
        s = seg_map[sid]
        s["duration_ns"] = int(s["t_last_ns"] or 0) - int(s["t_first_ns"] or 0)
        del s["t_first_ns"], s["t_last_ns"]
        segments.append(s)

    # ---- 零Δ连续段（含缺测感知）----
    runs = _scan_zero_delta_runs(reads, min_obs, stall_n_ns, gap_max_ns)

    # ---- 事件聚合 ----
    ev_state_hist = {}
    ev_rows, cost_sum, cost_max = [], {}, {}
    for c in COST_FIELDS:
        cost_sum[c] = 0
        cost_max[c] = 0
    for e in events:
        st = str(e.get("sample_state", "missing"))
        ev_state_hist[st] = ev_state_hist.get(st, 0) + 1
        ev_rows.append({
            "event_id": e.get("event_id"),
            "segment": e.get("segment"),
            "mode": e.get("mode"),
            "sample_state": st,
            "resume_state": e.get("resume_state"),
            "n_threads_sampled": e.get("n_threads_sampled"),
            "budget_exceeded": bool(e.get("budget_exceeded")),
            "errors_n": len(e.get("errors") or []),
            "cost_ns": {c: int((e.get("cost_ns") or {}).get(c, 0)) for c in COST_FIELDS},
        })
        for c in COST_FIELDS:
            v = int((e.get("cost_ns") or {}).get(c, 0))
            cost_sum[c] += v
            if v > cost_max[c]:
                cost_max[c] = v

    n_markers = {k: 0 for k in ("frame_regression", "new_game", "load_game",
                                "pid_change", "read_failed_gap")}
    for r in reads:
        m = r.get("marker")
        if m in n_markers:
            n_markers[m] += 1

    return {
        "schema": SCHEMA,
        "run_id": run_id,
        "provenance": provenance,
        "n_records": len(records),
        "n_frame_reads": len(reads),
        "n_events": len(events),
        "n_segments": len(segments),
        "segment_ids": [int(x) for x in seg_order],
        "read_status_hist": _sorted_hist(read_status_hist),
        "state_label_hist": _sorted_hist(state_label_hist),
        "sample_flag_true": int(sample_flag_true),
        "segments": segments,
        "zero_delta_runs": runs,
        "n_zero_delta_runs": len(runs),
        "n_confirmed_continuous_freezes": sum(1 for c in runs if c["confirmed"]),
        "n_gap_interrupted_runs": sum(1 for c in runs
                                      if c["reason"] in ("gap_interrupted",
                                                         "frame_change_or_gap")),
        "n_events_by_state": _sorted_hist(ev_state_hist),
        "events": ev_rows,
        "cost_ns_sum": {c: int(cost_sum[c]) for c in COST_FIELDS},
        "cost_ns_max": {c: int(cost_max[c]) for c in COST_FIELDS},
        "n_frame_regressions": n_markers["frame_regression"],
        "n_new_game_markers": n_markers["new_game"],
        "n_load_game_markers": n_markers["load_game"],
        "n_pid_change_markers": n_markers["pid_change"],
        "n_read_fail_gaps": n_markers["read_failed_gap"],
    }


def summarize(path):
    """从 NDJSON 文件重算摘要（只调用 load_records + summarize_records）。"""
    return summarize_records(load_records(path))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="RE-N01 offline NDJSON replay (read-only, no Win32, no process)")
    ap.add_argument("ndjson", help="path to input .ndjson")
    ap.add_argument("--out", default=None, help="optional path to write summary JSON")
    ap.add_argument("--quiet", action="store_true", help="do not print summary to stdout")
    a = ap.parse_args(argv)
    s = summarize(a.ndjson)
    if a.out:
        Path(a.out).write_text(json.dumps(s, ensure_ascii=False, indent=1,
                                          sort_keys=True), encoding="utf-8")
    if not a.quiet:
        print(json.dumps(s, ensure_ascii=False, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
