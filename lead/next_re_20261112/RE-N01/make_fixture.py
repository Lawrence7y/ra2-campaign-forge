# -*- coding: utf-8 -*-
"""RE-N01 / make_fixture.py —— 可重复生成 raw/ 下的原始记录样例。

零真机：只用纯 Python 假时钟 + 假对象；不 import ctypes、不碰任何进程。
每个 fixture_*.ndjson 的 meta 行都标 provenance=synthetic_fixture。

derived_from_14412.ndjson 由只读原件
lead/re_d13_ruling_20261112/_hl_match_14412.json 的那一条**真实事件**派生，
标 provenance=derived_from_recorded_event，并在 meta/事件行里明写：
  **不含全量 3493 样本序列，故不能重算 3493 样本统计**。

用法：python -X utf8 make_fixture.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAND = ROOT / "candidate"
RAW = ROOT / "raw"
for p in (str(ROOT), str(CAND)):
    if p not in sys.path:
        sys.path.insert(0, p)

import re_n01_monitor as mon       # noqa: E402
import replay_re_n01 as replay     # noqa: E402

RUN_ID = "NEXT_RE_20261112_R01"
UTC = "2026-11-12T07:00:00+00:00"


class ManualClock(object):
    def __init__(self):
        self.t = 0

    def __call__(self):
        return self.t

    def set(self, t):
        self.t = int(t)


class NeverFire(object):
    def observe(self, t, frame):
        return False

    def reset(self):
        pass


class FireAt(object):
    def __init__(self, at):
        self.at = set(at)
        self.n = 0

    def observe(self, t, frame):
        self.n += 1
        return self.n in self.at

    def reset(self):
        pass


def _scripted(name, script, *, provenance="synthetic_fixture",
              cfg=None, events=None):
    """script: [(t_ns, reading)]；events: {index: event_dict}（可选）。"""
    clock = ManualClock()
    nd = RAW / (name + ".ndjson")
    sink = mon.NDJSONSink(nd)
    base = mon.default_cfg(run_id=RUN_ID, provenance=provenance)
    if cfg:
        base.update(cfg)
    sess = mon.MonitoringSession(sink, base, now_ns=clock,
                                 utc_fn=lambda: UTC, pid=14412)
    det = FireAt((events or {}).keys()) if events else NeverFire()
    for i, (t_ns, reading) in enumerate(script):
        clock.set(t_ns)
        fired, _rec = sess.observe(reading, det)
        if fired and events and i in events:
            timer = mon.EventTimer(now_ns=clock)
            marks = {}
            for k, v in (("candidate", 0), ("verdict", 2_000_000),
                         ("preflight", 3_000_000), ("ownership", 4_000_000),
                         ("suspend", 5_000_000), ("context", 7_000_000),
                         ("walk", 11_000_000), ("resume", 13_000_000),
                         ("end", 15_000_000)):
                marks[k] = int(t_ns) + v
                timer.marks[k] = marks[k]
            cost = mon.cost_from_marks(marks)
            ev = dict(events[i])
            ev["ns_marks"] = marks
            sess.emit_event(ev, cost)
    summary = sess.summary()
    sink.close()
    mon.write_summary(ROOT / "out" / (name + ".summary.json"), summary)
    replayed = replay.summarize(nd)
    assert not _diff(summary, replayed), "%s: online != replay: %s" % (
        name, _diff(summary, replayed)[:3])
    return nd, replayed


def _diff(a, b, path="$"):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(path + "." + k)
            else:
                out.extend(_diff(a[k], b[k], path + "." + k))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(path + ".len")
        for x, y in zip(a, b):
            out.extend(_diff(x, y, path + "[]"))
    elif a != b:
        out.append("%s:%r!=%r" % (path, a, b))
    return out


def _ev(state="resume_verified_ok", mode="single_thread", **kw):
    e = {
        "mode": mode, "sample_state": state,
        "resume_state": ("verified_ok" if state == "resume_verified_ok"
                         else "failed" if state == "resume_failed" else "unknown"),
        "resume_ret": 0, "resume_ret_present": True,
        "resume_ok": state != "resume_failed",
        "errors": [] if state != "resume_failed" else ["resume_fail:tid=30668"],
        "exception": "", "budget_exceeded": False, "budget_state": "within",
        "budget_ms": 50.0, "n_threads_sampled": 1, "n_threads_attempted": 1,
        "preflight": {"ok": True, "reason": "ok"},
        "ownership": {"pid": 14412, "tid": 30668,
                      "tid_belongs_to_pid": True, "validated": True},
        "frames_n": 7, "suspend_held_ms": 8.0,
        "sample_called": False, "sample_one_thread_calls": 1,
    }
    e.update(kw)
    return e


def _ok(frame, **kw):
    d = {"frame": frame, "read_status": "ok", "pid": 14412}
    d.update(kw)
    return d


def _fail():
    return {"frame": None, "read_status": "read_failed", "pid": 14412}


def build_fixtures():
    RAW.mkdir(parents=True, exist_ok=True)
    made = []

    # 1) 正常推进：每 0.2s 帧号 +1，无停滞、无缺测
    script = [(i * 200_000_000, _ok(100 + i)) for i in range(20)]
    nd, s = _scripted("fixture_normal_advance", script)
    made.append((nd.name, s["n_frame_reads"], s["n_confirmed_continuous_freezes"]))

    # 2) 长停：帧号 12 次不变，跨 2.2s（>1.0s），随后恢复推进
    script = [(i * 200_000_000, _ok(200)) for i in range(12)]
    script += [(2_400_000_000 + i * 200_000_000, _ok(201 + i))
               for i in range(5)]
    nd, s = _scripted("fixture_long_stall", script,
                      events={7: _ev("resume_verified_ok")})
    made.append((nd.name, s["n_frame_reads"], s["n_confirmed_continuous_freezes"]))

    # 3) 短停：帧号 3 次不变（0.4s < 1.0s），不足以证实长停
    script = [(i * 200_000_000, _ok(300 if i < 3 else 300 + i - 2))
              for i in range(10)]
    nd, s = _scripted("fixture_short_stall", script)
    made.append((nd.name, s["n_frame_reads"], s["n_confirmed_continuous_freezes"]))

    # 4) 读失败区间：帧100 → 长读失败（真实间隔 2s）→ 帧100
    script = [(i * 200_000_000, _ok(100)) for i in range(8)]
    script += [(1_600_000_000, _fail()), (3_600_000_000, _fail()),
               (5_600_000_000, _fail())]
    script += [(5_800_000_000 + i * 200_000_000, _ok(100)) for i in range(8)]
    nd, s = _scripted("fixture_read_failed_gap", script)
    made.append((nd.name, s["n_frame_reads"], s["n_confirmed_continuous_freezes"]))

    # 5) 帧号回退：100→101→102→90（回退）→91
    script = [(i * 200_000_000, _ok(f)) for i, f in
              enumerate((100, 101, 102, 90, 91, 92))]
    nd, s = _scripted("fixture_frame_regression", script)
    made.append((nd.name, s["n_frame_reads"], s["n_segments"]))

    # 6) 新局 / 读档：显式 marker 分段 + 一次读失败分段
    script = [
        (0, _ok(10)), (200_000_000, _ok(11)),
        (400_000_000, _ok(1, marker="new_game")),
        (600_000_000, _ok(2)),
        (800_000_000, _ok(7, marker="load_game")),
        (1_000_000_000, _ok(8)),
        (1_200_000_000, _fail()),
        (1_400_000_000, _ok(9)),
        (1_600_000_000, _ok(10, marker="frame_regression")),
    ]
    nd, s = _scripted("fixture_new_game_load_game", script)
    made.append((nd.name, s["n_frame_reads"], s["n_segments"]))
    return made


def build_derived():
    """由 _hl_match_14412.json 的单条真实事件派生的**极小**样例。"""
    src = Path(r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112"
               r"\_hl_match_14412.json")
    raw = src.read_bytes()
    d = json.loads(raw.decode("utf-8"))
    ev = d["events"][0]
    nd = RAW / "derived_from_14412.ndjson"
    sink = mon.NDJSONSink(nd)
    clock = ManualClock()
    base_t = 471_266_000_000          # 记录里 t=471.266 s
    sink.write({
        "kind": "meta", "schema": mon.SCHEMA, "run_id": RUN_ID,
        "provenance": "derived_from_recorded_event",
        "source_file": src.name,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_pid": d.get("pid"), "source_pattern": d.get("pattern"),
        "source_n_samples": d.get("n_samples"),
        "source_n_readable": d.get("n_readable"),
        "seq": 0, "t_mono_ns": base_t, "t_utc": UTC, "gap_ns": 0,
        "read_status": "meta", "frame": None, "state_label": "META",
        "sample_flag": False, "segment": 0, "segment_reason": "run_start",
        "marker": None, "pid": d.get("pid"),
        "min_obs": 6, "stall_n_ns": 1_000_000_000,
        "nominal_interval_ns": 200_000_000, "gap_max_ns": 600_000_000,
        "note": (
            "只由 _hl_match_14412.json 中的 1 条真实事件派生，"
            "**不含全量 3493 样本序列**，因此**不能**用它重算 3493 样本统计"
            "（帧率、零Δ段分布、P95/P99 等一概不可重算）。"
            "本文件只演示 NDJSON 字段布局与可重放性。"),
        "limitation": (
            "源事件 paused_ms=0.0 是**低于当时测量精度**，不是零开销；"
            "源事件 errors=null 是旧记录的状态表达，不满足 RE-N01 五态契约，"
            "故本派生事件用显式字符串 unknown_from_source_record 表达「源未记录」，"
            "不冒充 not_attempted/ok/resume_verified_ok/resume_failed/error 之一。"),
    })
    # 3 条围绕事件的读数（合成时间戳，标明是派生的布局演示）
    for i in range(3):
        t = base_t - 400_000_000 + i * 200_000_000
        clock.set(t)
        sink.write({
            "kind": "frame_read", "seq": 1 + i, "t_mono_ns": t, "t_utc": UTC,
            "gap_ns": 0 if i == 0 else 200_000_000,
            "read_status": "ok", "frame": ev["frame"],
            "state_label": "OK_SAME", "sample_flag": False,
            "segment": 0, "segment_reason": "run_start", "marker": None,
            "pid": d.get("pid"), "run_id": RUN_ID,
            "provenance": "derived_from_recorded_event",
            "note": "synthetic_layout_row: 仅演示字段布局，不是原始 3493 样本",
        })
    marks = {"candidate": base_t, "verdict": base_t + 2_000_000,
             "preflight": base_t + 3_000_000, "ownership": base_t + 4_000_000,
             "suspend": base_t + 5_000_000, "context": base_t + 7_000_000,
             "walk": base_t + 11_000_000, "resume": base_t + 13_000_000,
             "end": base_t + 15_000_000}
    sink.write({
        "kind": "event", "seq": 4, "t_mono_ns": base_t, "t_utc": UTC,
        "gap_ns": 200_000_000, "read_status": "event",
        "frame": ev["frame"], "state_label": "EVENT_unknown_from_source_record",
        "sample_flag": True, "segment": 0, "segment_reason": "run_start",
        "marker": None, "pid": d.get("pid"), "run_id": RUN_ID,
        "provenance": "derived_from_recorded_event",
        "event_id": "E0001", "mode": ev.get("mode"),
        "sample_state": "unknown_from_source_record",
        "resume_state": "unknown_from_source_record",
        "resume_ret": None, "resume_ok": None, "errors": [],
        "exception": "", "budget_exceeded": False, "budget_state": "unknown",
        "n_threads_sampled": 1, "n_threads_attempted": 1,
        "preflight": {}, "ownership": {"pid": d.get("pid"),
                                       "tid": ev["stack"]["tid"]},
        "frames_n": ev["stack"]["n"], "suspend_held_ms": None,
        "source_event": ev,
        "source_paused_ms": ev.get("paused_ms"),
        "note": "源事件字段原样保留在 source_event；paused_ms=0.0 不是零开销证据",
        "cost_ns": mon.cost_from_marks(marks), "ns_marks": marks,
    })
    sink.close()
    recs = replay.load_records(nd)
    assert len(recs) == 5, len(recs)
    s = replay.summarize(nd)
    mon.write_summary(ROOT / "out" / "derived_from_14412.summary.json", s)
    return nd, s


def main():
    made = build_fixtures()
    nd, s = build_derived()
    print("run_id=%s 生成 %d 个 fixture + 1 个派生样例" % (RUN_ID, len(made)))
    for name, reads, extra in made:
        print("  %-42s frame_reads=%-3s extra=%s" % (name, reads, extra))
    print("  %-42s records=%d n_events=%d provenance=%s"
          % (nd.name, s["n_records"], s["n_events"], s["provenance"]))
    print("  每个 fixture 的在线摘要与 replay_re_n01.py 离线重算逐字段一致（已断言）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
