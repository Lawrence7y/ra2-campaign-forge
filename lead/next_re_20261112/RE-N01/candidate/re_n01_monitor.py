# -*- coding: utf-8 -*-
"""RE-N01 / re_n01_monitor.py —— 可信测量所需的「流式原始记录 + 分段 + 在线摘要」。

严格边界（与任务卡 §授权边界一致）：
  * 本模块**纯 Python**：不 import ctypes、不加载任何 Win32 DLL、
    不打开进程句柄、不 ReadProcessMemory、不 SuspendThread / ResumeThread /
    StackWalk64、不 attach、不启动游戏。
  * 采样器、帧读取器、时钟、休眠、UTC 全部由调用方**注入**；离线测试给假对象。

它补齐的正是前代理只写在 docstring 里、没落到代码里的 P1 / P5 / P6：
  P1  run_monitor() 的两条路径严格互斥：
      --only-tid  → sampler.sample_single(tid, pid, timer=...)  （绝不 sample(pid)）
      全线程      → sampler.sample(pid, timer=...)              （绝不直接 sample_one_thread）
  P2  单一 perf_counter_ns 整数里程碑；端到端 event_total_ns / end_to_end_ns 与
      检测延迟 / 上下文 / 走栈 / 恢复 / 实际挂起时长等分项一起入事件，
      **不是**只记最后一次函数调用耗时。
  P5  逐条 NDJSON，每行 flush（可选 fsync）；异常退出靠 try/finally 关闭文件，
      此前各行已落盘，可由 replay_re_n01.py 单独重算。
  P6  读失败区间**保留真实时间间隔**（t_mono_ns / gap_ns 不改写），并切到
      read_failed_gap / resume_after_gap 段，段 verdict=missing_gap / undecidable，
      因此「帧100 → 长读失败 → 帧100」不会拼成一段已证实连续冻结。

OnlineAccumulator 是 replay_re_n01.summarize_records() 的**独立流式实现**；
两者输出 schema 都是 re_n01_summary_v1，T-C4 对同一份 NDJSON 逐字段硬比对。
"""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

SCHEMA = "re_n01_summary_v1"

# 与 replay_re_n01.py 完全相同的字段集合（顺序也保留，便于逐字段比对）
COST_FIELDS = ("detect_ns", "preflight_ns", "ownership_ns", "context_ns",
               "walk_ns", "resume_ns", "suspend_held_ns", "end_to_end_ns",
               "event_total_ns", "overhead_ns")
ALL_COST_FIELDS = COST_FIELDS + ("open_ns",)

SAMPLE_STATES = ("not_attempted", "ok", "resume_verified_ok",
                 "resume_failed", "error")

GAP_REASONS = ("read_failed_gap", "resume_after_gap")
BOUNDARY_REASONS = ("frame_regression", "new_game", "load_game", "pid_change")
SEGMENT_MARKERS = ("frame_regression", "new_game", "load_game", "pid_change",
                   "read_failed_gap", "resume_after_gap", "run_start")

DEFAULT_MIN_OBS = 6
DEFAULT_STALL_N_NS = 1_000_000_000
DEFAULT_NOMINAL_INTERVAL_NS = 200_000_000
DEFAULT_GAP_MAX_NS = 600_000_000


def default_cfg(run_id="NEXT_RE_20261112_R01", provenance="synthetic_fixture"):
    return {"run_id": run_id, "provenance": provenance,
            "min_obs": DEFAULT_MIN_OBS,
            "stall_n_ns": DEFAULT_STALL_N_NS,
            "nominal_interval_ns": DEFAULT_NOMINAL_INTERVAL_NS,
            "gap_max_ns": DEFAULT_GAP_MAX_NS}


def utc_now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ------------------------------------------------------------------ 时钟里程碑

class EventTimer(object):
    """与 r2 采样器 EventTimer 同 API（mark / get / .marks），便于传给
    sample_single(timer=...)。全部取值来自**同一个** now_ns 可调用对象。"""

    def __init__(self, now_ns=None):
        import time
        self._now = now_ns or time.perf_counter_ns
        self.marks = {}

    def mark(self, name):
        v = int(self._now())
        self.marks[name] = v
        return v

    def get(self, name):
        return self.marks.get(name)


def cost_from_marks(marks, t_candidate_ns=None):
    """由整数里程碑生成成本字典（单位 ns）。

    非重叠分项（望远镜求和）恰好等于 end_to_end_ns：
      preflight + ownership + open + context + walk + resume + overhead
        == end - verdict == end_to_end_ns
    detect_ns 在 verdict **之前**，属于 event_total_ns 而不是 end_to_end_ns；
    suspend_held_ns 是 suspend→resume 的**重叠子区间**，不可加入分项之和。
    """
    def g(k):
        v = marks.get(k)
        return int(v) if v is not None else 0

    def d(a, b):
        return max(0, int(b) - int(a)) if (a and b) else 0

    t_cand = g("candidate") if t_candidate_ns is None else int(t_candidate_ns)
    t_verd = g("verdict")
    t_pref = g("preflight")
    t_own = g("ownership")
    t_susp = g("suspend")
    t_ctx = g("context")
    t_walk = g("walk")
    t_res = g("resume")
    t_end = g("end")
    return {
        "detect_ns": d(t_cand, t_verd),
        "preflight_ns": d(t_verd, t_pref),
        "ownership_ns": d(t_pref, t_own),
        "open_ns": d(t_own, t_susp),
        "context_ns": d(t_susp, t_ctx),
        "walk_ns": d(t_ctx, t_walk),
        "resume_ns": d(t_walk, t_res),
        "overhead_ns": d(t_res, t_end),
        "suspend_held_ns": d(t_susp, t_res),
        "end_to_end_ns": d(t_verd, t_end),
        "event_total_ns": d(t_cand, t_end),
    }


def fill_missing_marks(timer):
    """补齐缺失里程碑（假采样器 / 前置拒绝路径），保证 T-D1 六字段恒存在。"""
    for name in ("candidate", "verdict", "preflight", "ownership",
                 "suspend", "context", "walk", "resume", "end"):
        if timer.get(name) is None:
            timer.mark(name)
    return timer.marks


# ------------------------------------------------------------------ NDJSON 落盘

class NDJSONSink(object):
    """逐条写 NDJSON；每行 flush。异常退出时此前数据已在磁盘上。"""

    def __init__(self, path, fsync=False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fsync = bool(fsync)
        self.f = self.path.open("w", encoding="utf-8", newline="\n")
        self.n_lines = 0

    def write(self, rec):
        line = json.dumps(rec, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), default=_json_default)
        self.f.write(line + "\n")
        self.f.flush()                       # P5：每行 flush
        if self.fsync:
            os.fsync(self.f.fileno())
        self.n_lines += 1
        return rec

    def close(self):
        if not self.f.closed:
            self.f.flush()
            self.f.close()


def _json_default(o):
    return {"__unserializable__": type(o).__name__}


# ------------------------------------------------------------------ 在线摘要（独立实现）

class _RunScanner(object):
    """流式零Δ连续段扫描器（独立实现，语义对齐 replay 的批式扫描器）。

    缺测证据：读失败记录、跨段、gap_ns > gap_max_ns、紧邻缺测之后的新 run。
    帧号变化是**正常推进**，不算缺测证据（replay 旧版把它误记成
    frame_change_or_gap，导致非末段冻结永远无法被 confirmed —— 已在
    replay_re_n01.py 同步修正）。
    """

    def __init__(self, min_obs, stall_n_ns, gap_max_ns):
        self.min_obs = int(min_obs)
        self.stall_n_ns = int(stall_n_ns)
        self.gap_max_ns = int(gap_max_ns)
        self.runs = []
        self.cur = None
        self.prev = None
        self.pending_gap = False

    def _close(self, reason):
        if self.cur is None:
            return
        c = self.cur
        adjacent = bool(c["adjacent_to_gap"])
        dur = max(0, int(c["t_last_ns"]) - int(c["t_first_ns"]))
        no_gap = (reason != "gap_interrupted" and not adjacent)
        self.runs.append({
            "segment": c["segment"], "frame": c["frame"],
            "start_seq": c["start_seq"], "end_seq": c["end_seq"],
            "n": c["n"], "duration_ns": dur,
            "confirmed": bool(no_gap and c["n"] >= self.min_obs
                              and dur >= self.stall_n_ns),
            "reason": "gap_interrupted" if adjacent else reason,
        })
        self.cur = None

    def push(self, r):
        ok = (r.get("read_status") == "ok" and r.get("frame") is not None)
        if not ok:
            self._close("gap_interrupted")
            self.pending_gap = True
            self.prev = r
            return
        gap = int(r.get("gap_ns") or 0)
        if self.prev is not None:
            if (self.prev.get("segment") != r.get("segment")
                    or self.prev.get("read_status") != "ok"
                    or gap > self.gap_max_ns):
                self._close("gap_interrupted")
                self.pending_gap = True
        if self.cur is not None:
            if (self.cur["segment"] != r.get("segment")
                    or gap > self.gap_max_ns):
                self._close("gap_interrupted")
                self.pending_gap = True
            elif self.cur["frame"] != r.get("frame"):
                self._close("frame_change")
        if self.cur is None:
            self.cur = {
                "segment": r.get("segment"), "frame": r.get("frame"),
                "start_seq": r.get("seq"), "end_seq": r.get("seq"), "n": 1,
                "adjacent_to_gap": bool(self.pending_gap),
                "t_first_ns": r.get("t_mono_ns"), "t_last_ns": r.get("t_mono_ns"),
            }
            self.pending_gap = False
        else:
            self.cur["end_seq"] = r.get("seq")
            self.cur["n"] += 1
            self.cur["t_last_ns"] = r.get("t_mono_ns")
        self.prev = r

    def finish(self):
        self._close("end_of_stream")
        return self.runs


class OnlineAccumulator(object):
    """由已写出的记录流增量生成 re_n01_summary_v1。

    与 replay_re_n01.summarize_records() **没有共用代码**：那边是「读文件 →
    批式归约」，这边是「逐行 push → 增量计数器」。T-C4 逐字段比对二者输出。
    """

    def __init__(self, cfg):
        self.cfg = dict(cfg)
        self.n_records = 0
        self.n_frame_reads = 0
        self.n_events = 0
        self.read_status_hist = {}
        self.state_label_hist = {}
        self.sample_flag_true = 0
        self.markers = {k: 0 for k in
                        ("frame_regression", "new_game", "load_game",
                         "pid_change", "read_failed_gap")}
        self.seg_order = []
        self.segment_rows = {}
        self.scanner = _RunScanner(cfg.get("min_obs", DEFAULT_MIN_OBS),
                                   cfg.get("stall_n_ns", DEFAULT_STALL_N_NS),
                                   cfg.get("gap_max_ns", DEFAULT_GAP_MAX_NS))
        self.ev_state_hist = {}
        self.event_rows = []
        self.cost_sum = {c: 0 for c in COST_FIELDS}
        self.cost_max = {c: 0 for c in COST_FIELDS}

    def push(self, rec):
        self.n_records += 1
        sid = rec.get("segment")
        if sid is not None:
            self._push_segment(sid, rec)
        kind = rec.get("kind")
        if kind == "frame_read":
            self._push_read(rec)
        elif kind == "event":
            self._push_event(rec)

    def _push_segment(self, sid, rec):
        if sid not in self.segment_rows:
            self.seg_order.append(sid)
            self.segment_rows[sid] = {
                "segment": sid,
                "reason": str(rec.get("segment_reason", "")),
                "n_records": 0, "n_read_ok": 0, "n_read_failed": 0,
                "first_seq": rec.get("seq"), "last_seq": rec.get("seq"),
                "_t_first_ns": rec.get("t_mono_ns"),
                "_t_last_ns": rec.get("t_mono_ns"),
                "frame_first": None, "frame_last": None,
                "verdict": "measurable", "undecidable": False,
            }
        s = self.segment_rows[sid]
        s["n_records"] += 1
        s["last_seq"] = rec.get("seq")
        s["_t_last_ns"] = rec.get("t_mono_ns")
        if rec.get("kind") == "frame_read":
            if rec.get("read_status") == "ok":
                s["n_read_ok"] += 1
                f = rec.get("frame")
                if f is not None:
                    if s["frame_first"] is None:
                        s["frame_first"] = f
                    s["frame_last"] = f
            else:
                s["n_read_failed"] += 1
        # 与 replay 一致：每条记录都按自己的 segment_reason 刷新 verdict
        reason = str(rec.get("segment_reason", ""))
        if reason in GAP_REASONS:
            s["verdict"] = "missing_gap"
            s["undecidable"] = True
        elif reason in BOUNDARY_REASONS:
            s["verdict"] = "boundary"

    def _push_read(self, rec):
        self.n_frame_reads += 1
        s = str(rec.get("read_status", "unknown"))
        self.read_status_hist[s] = self.read_status_hist.get(s, 0) + 1
        lab = str(rec.get("state_label", "UNKNOWN"))
        self.state_label_hist[lab] = self.state_label_hist.get(lab, 0) + 1
        if rec.get("sample_flag"):
            self.sample_flag_true += 1
        m = rec.get("marker")
        if m in self.markers:
            self.markers[m] += 1
        self.scanner.push(rec)

    def _push_event(self, rec):
        self.n_events += 1
        st = str(rec.get("sample_state", "missing"))
        self.ev_state_hist[st] = self.ev_state_hist.get(st, 0) + 1
        cn = rec.get("cost_ns") or {}
        row_cost = {c: int(cn.get(c, 0)) for c in COST_FIELDS}
        self.event_rows.append({
            "event_id": rec.get("event_id"),
            "segment": rec.get("segment"),
            "mode": rec.get("mode"),
            "sample_state": st,
            "resume_state": rec.get("resume_state"),
            "n_threads_sampled": rec.get("n_threads_sampled"),
            "budget_exceeded": bool(rec.get("budget_exceeded")),
            "errors_n": len(rec.get("errors") or []),
            "cost_ns": row_cost,
        })
        for c in COST_FIELDS:
            self.cost_sum[c] += row_cost[c]
            if row_cost[c] > self.cost_max[c]:
                self.cost_max[c] = row_cost[c]

    def summary(self):
        rows = []
        for sid in self.seg_order:
            s = dict(self.segment_rows[sid])
            s["duration_ns"] = (int(s.pop("_t_last_ns") or 0)
                                - int(s.pop("_t_first_ns") or 0))
            rows.append(s)
        runs = self.scanner.finish()
        # 多次调用 summary() 必须幂等：finish() 已清空 cur，重复调用不再追加
        return {
            "schema": SCHEMA,
            "run_id": str(self.cfg.get("run_id", "")),
            "provenance": str(self.cfg.get("provenance", "")),
            "n_records": self.n_records,
            "n_frame_reads": self.n_frame_reads,
            "n_events": self.n_events,
            "n_segments": len(rows),
            "segment_ids": [int(x) for x in self.seg_order],
            "read_status_hist": _sorted_hist(self.read_status_hist),
            "state_label_hist": _sorted_hist(self.state_label_hist),
            "sample_flag_true": int(self.sample_flag_true),
            "segments": rows,
            "zero_delta_runs": runs,
            "n_zero_delta_runs": len(runs),
            "n_confirmed_continuous_freezes": sum(1 for c in runs if c["confirmed"]),
            "n_gap_interrupted_runs": sum(1 for c in runs
                                          if c["reason"] in ("gap_interrupted",
                                                             "frame_change_or_gap")),
            "n_events_by_state": _sorted_hist(self.ev_state_hist),
            "events": self.event_rows,
            "cost_ns_sum": {c: int(self.cost_sum[c]) for c in COST_FIELDS},
            "cost_ns_max": {c: int(self.cost_max[c]) for c in COST_FIELDS},
            "n_frame_regressions": self.markers["frame_regression"],
            "n_new_game_markers": self.markers["new_game"],
            "n_load_game_markers": self.markers["load_game"],
            "n_pid_change_markers": self.markers["pid_change"],
            "n_read_fail_gaps": self.markers["read_failed_gap"],
        }


def _sorted_hist(d):
    return {k: int(d[k]) for k in sorted(d)}


def write_summary(path, summary):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(summary, ensure_ascii=False, indent=1,
                            sort_keys=True), encoding="utf-8")
    return p


# ------------------------------------------------------------------ 监测会话

class MonitoringSession(object):
    """把「读数 → 分段 → 流式落盘 → 在线摘要」收在一处。"""

    def __init__(self, sink, cfg, *, now_ns=None, utc_fn=None, pid=0):
        import time
        self.sink = sink
        self.cfg = dict(cfg)
        self.now_ns = now_ns or time.perf_counter_ns
        self.utc_fn = utc_fn or utc_now_iso
        self.pid = int(pid)
        self.seq = 0
        self.segment = 0
        self.segment_reason = "run_start"
        self.prev_t_ns = None
        self.last_frame = None
        self.in_gap = False
        self.event_id = 0
        self.acc = OnlineAccumulator(self.cfg)
        self._write_meta()

    # ---- 公共字段（P5：每行都有单调时钟 ns / UTC / 读取状态 / 帧值 /
    #      状态标签 / 采样标记 / 段号）----
    def _stamp(self):
        t = int(self.now_ns())
        gap = 0 if self.prev_t_ns is None else max(0, t - self.prev_t_ns)
        self.prev_t_ns = t
        self.seq += 1
        return {"seq": self.seq, "t_mono_ns": t, "t_utc": self.utc_fn(),
                "gap_ns": gap, "kind": "meta", "read_status": "meta",
                "frame": None, "state_label": "META", "sample_flag": False,
                "segment": self.segment, "segment_reason": self.segment_reason,
                "marker": None, "pid": self.pid,
                "run_id": self.cfg.get("run_id", ""),
                "provenance": self.cfg.get("provenance", "")}

    def _emit(self, rec):
        self.sink.write(rec)
        self.acc.push(rec)
        return rec

    def _write_meta(self):
        m = self._stamp()
        m["kind"] = "meta"
        m["schema"] = SCHEMA
        m.update({k: self.cfg[k] for k in
                  ("min_obs", "stall_n_ns", "nominal_interval_ns", "gap_max_ns")})
        m["note"] = "meta: 以下每行均为独立 NDJSON 记录；异常退出后此前各行仍可解析"
        self._emit(m)

    def _new_segment(self, reason):
        self.segment += 1
        self.segment_reason = reason

    def observe(self, reading, detector, timer=None):
        """写一条 frame_read 记录；返回 (fired, rec)。

        reading 可以是 int / None / dict。dict 支持：
          frame, read_status, marker, pid, note
        """
        if isinstance(reading, dict):
            frame = reading.get("frame")
            rs = reading.get("read_status") or (
                "ok" if frame is not None else "read_failed")
            marker = reading.get("marker")
            pid = int(reading.get("pid", self.pid))
            note = reading.get("note", "")
        else:
            frame = reading
            rs = "ok" if reading is not None else "read_failed"
            marker, pid, note = None, self.pid, ""
        rec = self._stamp()
        rec["kind"] = "frame_read"
        rec["note"] = note

        # --- PID 变化：自动分段 ---
        if pid != self.pid:
            marker = marker or "pid_change"
            self.pid = pid
        rec["pid"] = self.pid

        # --- 显式边界标记：帧号回退 / 新局 / 读档 ---
        if marker in BOUNDARY_REASONS:
            self._new_segment(marker)
            self.in_gap = False
            self.last_frame = None
            if detector is not None and hasattr(detector, "reset"):
                detector.reset()
            rec["state_label"] = "BOUNDARY_" + marker
        elif rs != "ok":
            # --- 读失败区间：保留原时间间隔，不改写 t_mono_ns / gap_ns ---
            if not self.in_gap:
                self._new_segment("read_failed_gap")
                marker = marker or "read_failed_gap"
            self.in_gap = True
            rec["state_label"] = "MISSING_GAP"
        else:
            if self.in_gap:
                self._new_segment("resume_after_gap")
                self.in_gap = False
                self.last_frame = None
                if detector is not None and hasattr(detector, "reset"):
                    detector.reset()
                rec["state_label"] = "RESUME_AFTER_GAP"
            elif (self.last_frame is not None and frame is not None
                  and frame < self.last_frame):
                marker = "frame_regression"
                self._new_segment("frame_regression")
                self.last_frame = None
                if detector is not None and hasattr(detector, "reset"):
                    detector.reset()
                rec["state_label"] = "BOUNDARY_frame_regression"
            elif self.last_frame is None:
                rec["state_label"] = "OK_FIRST"
            elif frame == self.last_frame:
                rec["state_label"] = "OK_SAME"
            else:
                rec["state_label"] = "OK_ADVANCING"

        if rs != "ok":
            frame = None                      # 读失败行不携带帧值
        rec["frame"] = frame
        rec["read_status"] = rs
        rec["marker"] = marker
        rec["segment"] = self.segment
        rec["segment_reason"] = self.segment_reason

        fired = False
        if detector is not None and rs == "ok":
            fired = bool(detector.observe(rec["t_mono_ns"] / 1e9, frame))
        rec["sample_flag"] = bool(fired)
        if frame is not None:
            self.last_frame = frame
        if timer is not None and fired:
            timer.mark("verdict")
        return fired, self._emit(rec)

    def emit_event(self, ev, cost_ns):
        rec = self._stamp()
        rec["kind"] = "event"
        rec["read_status"] = "event"
        rec["state_label"] = "EVENT_" + str(ev.get("sample_state", "missing"))
        rec["sample_flag"] = True
        rec["segment"] = self.segment
        rec["segment_reason"] = self.segment_reason
        rec["marker"] = None
        self.event_id += 1
        rec["event_id"] = "E%04d" % self.event_id
        rec.update(ev)
        rec["cost_ns"] = cost_ns
        rec["ns_marks"] = dict(ev.get("ns_marks") or {})
        return self._emit(rec)

    def summary(self):
        return self.acc.summary()


# ------------------------------------------------------------------ 事件级采样

def _event_from_single(ev, timer):
    """把 sample_single 的返回整合成 NDJSON event 字段（不丢任何证据）。"""
    return {
        "mode": "single_thread",
        "sample_state": str(ev.get("sample_state", "error")),
        "resume_state": str(ev.get("resume_state", "unknown")),
        "resume_ret": ev.get("resume_ret"),
        "resume_ret_present": ev.get("resume_ret_present"),
        "resume_ok": ev.get("resume_ok"),
        "prev": ev.get("prev"),
        "errors": list(ev.get("errors") or []),
        "exception": str(ev.get("exception") or ""),
        "budget_exceeded": bool(ev.get("budget_exceeded")),
        "budget_state": str(ev.get("budget_state") or "unknown"),
        "budget_ms": ev.get("budget_ms"),
        "n_threads_sampled": ev.get("n_threads_sampled"),
        "n_threads_attempted": ev.get("n_threads_attempted"),
        "preflight": ev.get("preflight") or {},
        "ownership": ev.get("ownership") or {},
        "frames_n": len(ev.get("frames") or []),
        "suspend_held_ms": ev.get("suspend_held_ms"),
        "sample_called": bool(ev.get("sample_called")),
        "sample_one_thread_calls": ev.get("sample_one_thread_calls"),
        "ns_marks": dict(timer.marks),
    }


def _event_from_all(res, timer):
    """全线程路径：驱动只调 sample(pid)，绝不直接调 sample_one_thread。"""
    threads = res.get("threads") or []
    errs = list(res.get("errors") or [])
    got = [x for x in threads if isinstance(x, dict) and x.get("frames")]
    if errs:
        state = "error"
    elif any("resume_fail" in str(e) for e in errs):
        state = "resume_failed"
    else:
        state = "ok"
    return {
        "mode": "all_threads",
        "sample_state": state,
        "resume_state": "unknown",
        "resume_ret": None,
        "resume_ret_present": False,
        "resume_ok": None,
        "prev": None,
        "errors": errs,
        "exception": "",
        "budget_exceeded": bool(res.get("aborted")),
        "budget_state": "exceeded" if res.get("aborted") else "within",
        "budget_ms": res.get("budget_ms"),
        "n_threads_sampled": len(got),
        "n_threads_attempted": res.get("n_threads"),
        "preflight": {},
        "ownership": {"pid": res.get("pid"), "tid": None,
                      "validated": False, "reason": "full_thread_path"},
        "frames_n": sum(len(x.get("frames") or []) for x in got),
        "suspend_held_ms": res.get("paused_ms"),
        "sample_called": True,
        "sample_one_thread_calls": 0,
        "paused_ms": res.get("paused_ms"),
        "ns_marks": dict(timer.marks),
    }


def build_event(only_tid, sampler, pid, want_tid, timer):
    """P1：两条路径严格互斥。返回 (event_dict, path_tag)。

    --only-tid 路径**绝不**调用 sample(pid)；全线程路径**不直接**调用
    sample_one_thread（它只在 sampler.sample() 内部发生，由采样器自己负责）。
    """
    if only_tid:
        raw = sampler.sample_single(int(want_tid), int(pid), timer=timer)
        ev = _event_from_single(raw or {}, timer)
        path = "single"
    else:
        try:
            res = sampler.sample(int(pid), timer=timer)
        except TypeError:
            # 兼容不接受 timer 的采样器（仍不直接调单线程入口）
            res = sampler.sample(int(pid))
        ev = _event_from_all(res or {}, timer)
        path = "all"
    return ev, path


def run_monitor(*, pid, want_tid, only_tid, sampler, detector, rd, sink, cfg,
                now_ns=None, utc_fn=None, sleep_fn=None,
                interval_s=0.2, max_ticks=None, post_hook=None,
                fail_hook=None, on_event=None, summary_path=None,
                provenance=None):
    """RE-N01 的可注入监测循环（离线测试的全部依赖都是假对象）。

    rd(i) → int / None / dict（见 MonitoringSession.observe）。
    fail_hook(i) 若抛异常，异常向外传播；finally 关闭 sink，此前 NDJSON 保留。
    post_hook(ev) 用于注入「恢复完成后仍然很慢」的后续步骤（T-A3）。
    """
    import time
    cfg = dict(cfg)
    if provenance is not None:
        cfg["provenance"] = provenance
    clock = now_ns or time.perf_counter_ns
    session = MonitoringSession(sink, cfg, now_ns=clock, utc_fn=utc_fn, pid=pid)
    emitted = []
    i = 0
    try:
        while max_ticks is None or i < max_ticks:
            if fail_hook is not None:
                fail_hook(i)                     # 故意让异常穿透（T-C1）
            timer = EventTimer(now_ns=clock)
            timer.mark("candidate")              # 检测开始
            reading = rd(i)
            fired, _rec = session.observe(reading, detector, timer=timer)
            if fired:
                ev, _path = build_event(only_tid, sampler, pid, want_tid, timer)
                if post_hook is not None:
                    post_hook(ev)                # 恢复完成后的慢步骤
                fill_missing_marks(timer)
                timer.mark("end")                # 整事件结束（含收尾）
                cost = cost_from_marks(timer.marks)
                ev["ns_marks"] = dict(timer.marks)
                rec = session.emit_event(ev, cost)
                emitted.append(rec)
                if on_event is not None:
                    on_event(rec)
            if sleep_fn is not None:
                sleep_fn(interval_s)
            i += 1
    finally:
        # P5：异常退出也保留此前逐行 flush 的数据；摘要同样落盘供离线比对
        summary = session.summary()
        sink.close()
        if summary_path is not None:
            write_summary(summary_path, summary)
    return {"n_ticks": i, "events": emitted, "summary": summary}
