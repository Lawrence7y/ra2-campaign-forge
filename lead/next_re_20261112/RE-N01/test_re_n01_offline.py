# -*- coding: utf-8 -*-
"""RE-N01 / test_re_n01_offline.py —— 有区分力的离线测试（不是复跑作者自检器）。

严格零真机：
  * 不启动游戏、不 attach、不 ReadProcessMemory 活进程、不 SuspendThread /
    ResumeThread / StackWalk64 / MiniDump / 断点 / 注入 / taskkill；
  * 所有 Win32 通道都是**注入的纯 Python stub / 假对象**；
  * 唯一被真实 import 的候选件是 r2 采样器，但它的 OPS 被整套替换成 stub，
    因此**没有任何一次真实 Win32 调用**。

用计数 spy 断言驱动的两条路径互斥，用假时钟构造「采样慢 + 后续也慢」，
用手工时钟构造长读失败区间 / 帧号回退 / 新局 / 读档，并把在线摘要与
replay_re_n01.py 的离线重算逐字段硬比对。

用法（从 RE-N01 目录运行）：
  python -X utf8 test_re_n01_offline.py
退出码 0 = 全绿；1 = 有 RED。
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAND = ROOT / "candidate"
TMP = ROOT / "out" / "_offline_tests"
for p in (str(ROOT), str(CAND)):
    if p not in sys.path:
        sys.path.insert(0, p)

import replay_re_n01 as replay          # noqa: E402
import re_n01_monitor as mon           # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


r2 = _load("re_n01_sampler_r2", CAND / "e3_stack_sampler_candidate_r2.py")
drv = _load("re_n01_driver", CAND / "_run_hl_match_candidate.py")

TMP.mkdir(parents=True, exist_ok=True)

_RESULTS = []


def check(name, cond, evidence=""):
    ok = bool(cond)
    _RESULTS.append((name, ok, str(evidence)))
    print("[%s] %-58s %s" % ("OK" if ok else "RED", name, evidence))
    return ok


def deep_diff(a, b, path="$"):
    """逐字段比对两个 JSON 结构，返回差异路径列表（空 = 完全一致）。"""
    out = []
    if type(a) is not type(b) and not (isinstance(a, (int, float))
                                       and isinstance(b, (int, float))):
        return ["%s: type %s != %s" % (path, type(a).__name__, type(b).__name__)]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append("%s.%s: missing in %s" %
                           (path, k, "a" if k not in a else "b"))
            else:
                out.extend(deep_diff(a[k], b[k], "%s.%s" % (path, k)))
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append("%s: len %d != %d" % (path, len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(deep_diff(x, y, "%s[%d]" % (path, i)))
    elif a != b:
        out.append("%s: %r != %r" % (path, a, b))
    return out


# ---------------------------------------------------------------- 假对象

class StepClock(object):
    """每调用一次前进 step ns 的单调假时钟（可注入 now_ns）。"""

    def __init__(self, step=1_000_000, start=0):
        self.step = int(step)
        self.t = int(start)
        self.calls = 0

    def __call__(self):
        self.t += self.step
        self.calls += 1
        return self.t

    def burn(self, n):
        for _ in range(int(n)):
            self()


class ManualClock(object):
    """手工设定 t_mono_ns 的时钟（构造长间隔 / 缺测区间用）。"""

    def __init__(self, t=0):
        self.t = int(t)

    def __call__(self):
        return self.t

    def set(self, t):
        self.t = int(t)


class NeverFire(object):
    def __init__(self):
        self.n = 0

    def observe(self, t, frame):
        self.n += 1
        return False

    def reset(self):
        pass


class FireOnce(object):
    def __init__(self):
        self.n = 0

    def observe(self, t, frame):
        self.n += 1
        return self.n == 1

    def reset(self):
        pass


class SpySampler(object):
    """计数 spy：三个入口各自计数，且 sample() 不调 sample_one_thread。"""

    def __init__(self, clock=None, state="resume_verified_ok", burn=0):
        self.clock = clock
        self.state = state
        self.burn_n = int(burn)
        self.counts = {"sample": 0, "sample_single": 0,
                       "sample_one_thread": 0}
        self.last_sample_single_ns = 0

    def _burn(self, timer=None):
        if self.clock is not None and self.burn_n:
            self.clock.burn(self.burn_n)
        if timer is not None:
            for k in ("preflight", "ownership", "suspend",
                      "context", "walk", "resume"):
                timer.mark(k)

    def sample(self, pid, timer=None):
        self.counts["sample"] += 1
        self._burn(timer)
        return {"pid": pid, "threads": [{"tid": 1, "frames": [0x401000],
                                         "ctx": {"bits": 32}}],
                "errors": [], "paused_ms": 1.0, "n_threads": 1,
                "aborted": False, "budget_ms": 50.0}

    def sample_single(self, tid, pid, timer=None, **kw):
        self.counts["sample_single"] += 1
        t0 = self.clock() if self.clock is not None else 0
        self._burn(timer)
        t1 = self.clock() if self.clock is not None else 0
        self.last_sample_single_ns = max(0, t1 - t0)
        return {
            "mode": "single_thread", "sample_state": self.state,
            "resume_state": ("verified_ok" if self.state == "resume_verified_ok"
                             else "failed" if self.state == "resume_failed"
                             else "unknown"),
            "resume_ret": 0, "resume_ret_present": True,
            "resume_ok": (self.state != "resume_failed"),
            "errors": (["resume_fail:tid=%d" % tid]
                       if self.state == "resume_failed" else []),
            "exception": "", "budget_exceeded": False, "budget_state": "within",
            "budget_ms": 50.0, "n_threads_sampled": 1,
            "n_threads_attempted": 1, "preflight": {"ok": True, "reason": "ok"},
            "ownership": {"tid_belongs_to_pid": True}, "frames": [0x401000],
            "suspend_held_ms": 1.0, "sample_called": False,
            "sample_one_thread_calls": 1,
        }

    def sample_one_thread(self, tid, timer=None):
        self.counts["sample_one_thread"] += 1
        return {"tid": tid, "frames": [0x401000]}


def _cfg(**kw):
    c = mon.default_cfg(run_id="NEXT_RE_20261112_R01",
                        provenance="synthetic_fixture")
    c.update(kw)
    return c


def _new_case(name, *, clock=None, cfg=None, detector=None):
    clock = clock or StepClock()
    nd = TMP / (name + ".ndjson")
    sm = TMP / (name + ".online.json")
    sink = mon.NDJSONSink(nd)
    session = mon.MonitoringSession(sink, cfg or _cfg(), now_ns=clock,
                                    utc_fn=lambda: "2026-11-12T00:00:00+00:00",
                                    pid=14412)
    return {"clock": clock, "nd": nd, "sm": sm, "sink": sink,
            "session": session, "detector": detector or NeverFire()}


# ---------------------------------------------------------------- 真候选 + stub

def make_real_sampler(clock, *, tids=(30668,), pid=14412,
                      resume_fail=False, ctx_bound=True):
    """用**纯 Python stub** 填满 r2 采样器的 OPS；任何真实 Win32 都不会被调用。"""
    st = {"suspend_calls": 0, "resume_calls": 0, "open_calls": 0}
    idx = {"i": -1}

    def _tf(_snap, ptr):
        e = ctypes_cast(ptr)
        e.dwSize = r2.ctypes.sizeof(r2._ThreadEntry32)
        idx["i"] = 0
        if not tids:
            return 0
        e.th32ThreadID = tids[0]
        e.th32OwnerProcessID = pid
        return 1

    def _tn(_snap, ptr):
        e = ctypes_cast(ptr)
        idx["i"] += 1
        if idx["i"] >= len(tids):
            return 0
        e.dwSize = r2.ctypes.sizeof(r2._ThreadEntry32)
        e.th32ThreadID = tids[idx["i"]]
        return 1

    def ctypes_cast(ptr):
        return r2.ctypes.cast(ptr, r2.ctypes.POINTER(r2._ThreadEntry32)).contents

    ops = {
        "now": lambda: clock() / 1e9,
        "now_ns": clock,
        "create_snapshot": lambda a, b: 4242,
        "thread_first": _tf,
        "thread_next": _tn,
        "close_handle": lambda h: 1,
        "close_thread_handle": lambda h: 1,
        "open_process": lambda a, p: 9999,
        "is_wow64": lambda h: True,
        "open_thread": lambda a, b, tid: (st.__setitem__(
            "open_calls", st["open_calls"] + 1), 10000 + tid)[1],
        "suspend_thread": lambda h: (st.__setitem__(
            "suspend_calls", st["suspend_calls"] + 1), 0)[1],
        "resume_thread": lambda h: (st.__setitem__(
            "resume_calls", st["resume_calls"] + 1),
            (0xFFFFFFFF if resume_fail else 0))[1],
    }
    if ctx_bound:
        ops["get_context_stub"] = lambda h: {
            "bits": 32, "ip": 0x401000, "sp": 0x1000, "bp": 0x1100,
            "eflags": 0x202, "cs": 0x1b}
        ops["walk_stub"] = lambda c, depth: [c["ip"], c["ip"] + 4]
    r2.OPS.clear()
    r2.OPS.update(ops)
    return r2.StackSampler(), st


def _run_with_real_sampler(name, *, tids=(30668,), resume_fail=False,
                           ctx_bound=True, want_tid=30668, pid=14412):
    clock = StepClock(step=1_000_000)
    sampler, st = make_real_sampler(clock, tids=tids, pid=pid,
                                    resume_fail=resume_fail,
                                    ctx_bound=ctx_bound)
    nd, sm = TMP / (name + ".ndjson"), TMP / (name + ".online.json")
    sink = mon.NDJSONSink(nd)
    out = mon.run_monitor(
        pid=pid, want_tid=want_tid, only_tid=True, sampler=sampler,
        detector=FireOnce(), rd=lambda i: {"frame": 15042, "pid": pid},
        sink=sink, cfg=_cfg(), now_ns=clock,
        utc_fn=lambda: "2026-11-12T00:00:00+00:00",
        max_ticks=1, summary_path=sm)
    return out, st, nd, sm


# ================================================================ T-A 组

def test_T_A1():
    """--only-tid 模式下全线程 sample() 调用次数 == 0（计数 spy）。"""
    clock = StepClock()
    spy = SpySampler(clock=clock, burn=4)
    nd, sm = TMP / "a1.ndjson", TMP / "a1.online.json"
    sink = mon.NDJSONSink(nd)
    mon.run_monitor(pid=14412, want_tid=30668, only_tid=True,
                    sampler=spy, detector=FireOnce(),
                    rd=lambda i: {"frame": 100, "pid": 14412},
                    sink=sink, cfg=_cfg(), now_ns=clock,
                    utc_fn=lambda: "2026-11-12T00:00:00+00:00",
                    max_ticks=1, summary_path=sm)
    check("T-A1 --only-tid ⇒ sample(pid) 调用数 == 0",
          spy.counts["sample"] == 0 and spy.counts["sample_single"] == 1,
          "counts=%s" % spy.counts)


def test_T_A2():
    """全线程模式下驱动不直接调单线程入口（计数 spy）。"""
    clock = StepClock()
    spy = SpySampler(clock=clock, burn=4)
    nd, sm = TMP / "a2.ndjson", TMP / "a2.online.json"
    sink = mon.NDJSONSink(nd)
    mon.run_monitor(pid=14412, want_tid=30668, only_tid=False,
                    sampler=spy, detector=FireOnce(),
                    rd=lambda i: {"frame": 100, "pid": 14412},
                    sink=sink, cfg=_cfg(), now_ns=clock,
                    utc_fn=lambda: "2026-11-12T00:00:00+00:00",
                    max_ticks=1, summary_path=sm)
    check("T-A2 全线程 ⇒ 驱动不直接调 sample_one_thread",
          spy.counts["sample_one_thread"] == 0
          and spy.counts["sample"] == 1
          and spy.counts["sample_single"] == 0,
          "counts=%s" % spy.counts)


def test_T_A3():
    """整事件时长：采样函数本身慢 + 后续步骤也慢 ⇒ 记录值 > 最后一次调用耗时。"""
    clock = StepClock(step=1_000_000)
    spy = SpySampler(clock=clock, burn=6)       # 采样函数内部慢
    nd, sm = TMP / "a3.ndjson", TMP / "a3.online.json"
    sink = mon.NDJSONSink(nd)
    last = {"ns": 0}

    def post_hook(ev):
        # 恢复完成之后的「后续步骤也慢」；这是本事件最后一次函数调用
        t0 = clock()
        clock.burn(4)
        last["ns"] = clock() - t0

    out = mon.run_monitor(
        pid=14412, want_tid=30668, only_tid=True, sampler=spy,
        detector=FireOnce(), rd=lambda i: {"frame": 100, "pid": 14412},
        sink=sink, cfg=_cfg(), now_ns=clock,
        utc_fn=lambda: "2026-11-12T00:00:00+00:00",
        max_ticks=1, post_hook=post_hook, summary_path=sm)
    rec = out["events"][0]
    c = rec["cost_ns"]
    e2e, total = c["end_to_end_ns"], c["event_total_ns"]
    check("T-A3 整事件时长 > 最后一次函数调用耗时",
          total > last["ns"] and e2e > last["ns"]
          and total > spy.last_sample_single_ns
          and total >= (c["detect_ns"] + spy.last_sample_single_ns
                        + last["ns"]),
          "event_total=%d e2e=%d last_call=%d sampler=%d detect=%d"
          % (total, e2e, last["ns"], spy.last_sample_single_ns,
             c["detect_ns"]))


# ================================================================ T-B 组

def test_T_B1():
    """恢复失败时事件里出现恢复失败（不是 null、不是空）。"""
    out, st, nd, _sm = _run_with_real_sampler("b1", resume_fail=True)
    ev = out["events"][0]
    check("T-B1 恢复失败进事件：resume_failed / failed / errors 非空",
          ev["sample_state"] == "resume_failed"
          and ev["resume_state"] == "failed"
          and ev["sample_state"] is not None
          and isinstance(ev["errors"], list) and len(ev["errors"]) > 0
          and all("resume_fail" in e for e in ev["errors"]),
          "state=%s resume=%s errors=%s"
          % (ev["sample_state"], ev["resume_state"], ev["errors"]))


def test_T_B2():
    """五态两两不同：未采集 / 无错误 / 恢复成功 / 恢复失败 / 一般错误。"""
    states = ("not_attempted", "ok", "resume_verified_ok",
              "resume_failed", "error")
    got = []
    for i, s in enumerate(states):
        clock = StepClock()
        spy = SpySampler(clock=clock, state=s, burn=2)
        sink = mon.NDJSONSink(TMP / ("b2_%d.ndjson" % i))
        out = mon.run_monitor(
            pid=14412, want_tid=30668, only_tid=True, sampler=spy,
            detector=FireOnce(), rd=lambda j: {"frame": 100, "pid": 14412},
            sink=sink, cfg=_cfg(), now_ns=clock,
            utc_fn=lambda: "2026-11-12T00:00:00+00:00", max_ticks=1)
        got.append(out["events"][0]["sample_state"])
    check("T-B2 五态两两不同且均非 null/空",
          len(set(got)) == 5
          and all(isinstance(x, str) and x for x in got)
          and all(x in mon.SAMPLE_STATES for x in got)
          and len(set(mon.SAMPLE_STATES)) == 5
          and all(x for x in mon.SAMPLE_STATES),
          "states=%s SAMPLE_STATES_distinct=%d"
          % (tuple(got), len(set(mon.SAMPLE_STATES))))


def test_T_B3():
    """单线程入口 preflight 失败 ⇒ 零线程被挂起，事件写明失败原因。"""
    out, st, nd, _sm = _run_with_real_sampler("b3", ctx_bound=False)
    ev = out["events"][0]
    reason = json.dumps(ev["preflight"], ensure_ascii=False)
    check("T-B3 preflight 失败：零挂起 + not_attempted + 原因",
          st["suspend_calls"] == 0
          and ev["sample_state"] == "not_attempted"
          and "context_not_bound" in reason
          and len(ev["errors"]) > 0,
          "susp=%d state=%s preflight=%s errors=%s"
          % (st["suspend_calls"], ev["sample_state"], reason, ev["errors"]))


def test_T_B4():
    """TID 不属于该 PID 时拒绝并记录。"""
    out, st, nd, _sm = _run_with_real_sampler(
        "b4", tids=(30668, 30669), want_tid=77777)
    ev = out["events"][0]
    blob = json.dumps(ev, ensure_ascii=False)
    check("T-B4 TID∉PID 被拒绝且写入事件",
          st["suspend_calls"] == 0
          and ev["sample_state"] == "not_attempted"
          and "tid_not_in_pid" in blob
          and ev["ownership"].get("tid_belongs_to_pid") is False,
          "susp=%d state=%s ownership=%s"
          % (st["suspend_calls"], ev["sample_state"], ev["ownership"]))


# ================================================================ T-C 组

def test_T_C1():
    """循环中途抛异常 ⇒ 已写 NDJSON 仍可解析且含此前记录。"""
    clock = StepClock()
    spy = SpySampler(clock=clock, burn=2)
    nd, sm = TMP / "c1.ndjson", TMP / "c1.online.json"
    sink = mon.NDJSONSink(nd)

    def fail_hook(i):
        if i == 3:
            raise RuntimeError("injected_mid_loop_failure")

    raised = None
    try:
        mon.run_monitor(pid=14412, want_tid=30668, only_tid=True,
                        sampler=spy, detector=NeverFire(),
                        rd=lambda i: {"frame": 100 + i, "pid": 14412},
                        sink=sink, cfg=_cfg(), now_ns=clock,
                        utc_fn=lambda: "2026-11-12T00:00:00+00:00",
                        max_ticks=9, fail_hook=fail_hook, summary_path=sm)
    except RuntimeError as e:
        raised = str(e)
    recs = replay.load_records(nd)           # 非法行会抛 ValueError ⇒ 测试红色
    n_reads = sum(1 for r in recs if r.get("kind") == "frame_read")
    online = json.loads(sm.read_text(encoding="utf-8"))
    replayed = replay.summarize(nd)
    check("T-C1 异常退出后 NDJSON 可解析且含此前记录",
          raised == "injected_mid_loop_failure"
          and sink.f.closed and n_reads == 3
          and replayed["n_frame_reads"] == 3
          and not deep_diff(online, replayed),
          "raised=%s lines=%d closed=%s frame_reads=%d"
          % (raised, len(recs), sink.f.closed, n_reads))


def _drive_scripted(name, script):
    """script: list of (t_ns, reading)。手工时钟，保留真实时间间隔。"""
    case = _new_case(name, clock=ManualClock())
    case["clock"].set(0)
    for t_ns, reading in script:
        case["clock"].set(t_ns)
        case["session"].observe(reading, case["detector"])
    online = case["session"].summary()
    case["sink"].close()
    mon.write_summary(case["sm"], online)
    replayed = replay.summarize(case["nd"])
    return online, replayed, case


def test_T_C2():
    """帧100 → 长读失败区间 → 帧100 ⇒ 无已证实连续冻结，段标缺测/不可判。"""
    script = []
    for i in range(8):
        script.append((i * 200_000_000, {"frame": 100, "pid": 14412}))
    # 长读失败区间：真实时间间隔 0.2s / 2.0s / 2.0s 原样保留
    script.append((1_600_000_000, {"frame": None, "read_status": "read_failed",
                                   "pid": 14412}))
    script.append((3_600_000_000, {"frame": None, "read_status": "read_failed",
                                   "pid": 14412}))
    script.append((5_600_000_000, {"frame": None, "read_status": "read_failed",
                                   "pid": 14412}))
    for i in range(8):
        script.append((5_800_000_000 + i * 200_000_000,
                       {"frame": 100, "pid": 14412}))
    online, replayed, case = _drive_scripted("c2", script)
    recs = replay.load_records(case["nd"])
    failed = [r for r in recs if r.get("read_status") == "read_failed"]
    max_gap = max((r.get("gap_ns") or 0) for r in recs)
    runs = replayed["zero_delta_runs"]
    merged = any(r["start_seq"] <= 9 and r["end_seq"] >= 11 for r in runs)
    missing = [s for s in replayed["segments"]
               if s["verdict"] == "missing_gap" and s["undecidable"]]
    ok = (online["n_confirmed_continuous_freezes"] == 0
          and replayed["n_confirmed_continuous_freezes"] == 0
          and replayed["n_gap_interrupted_runs"] >= 2
          and not merged and len(runs) >= 2
          and len(missing) >= 2
          and len(failed) == 3 and max_gap >= 2_000_000_000
          and not deep_diff(online, replayed))
    check("T-C2 帧100→长读失败→帧100 不产生已证实连续冻结",
          ok,
          "online_conf=%d replay_conf=%d gap_runs=%d merged=%s "
          "missing_segs=%d read_failed=%d max_gap_ns=%d"
          % (online["n_confirmed_continuous_freezes"],
             replayed["n_confirmed_continuous_freezes"],
             replayed["n_gap_interrupted_runs"], merged, len(missing),
             len(failed), max_gap))


def test_T_C2b():
    """阳性对照：无缺测的长停必须**能**被证实（防 T-C2 空壳全绿）。"""
    script = []
    for i in range(8):
        script.append((i * 200_000_000, {"frame": 100, "pid": 14412}))
    script.append((1_600_000_000, {"frame": 101, "pid": 14412}))  # 帧推进
    for i in range(3):
        script.append((1_800_000_000 + i * 200_000_000,
                       {"frame": 101 + i, "pid": 14412}))
    online, replayed, _case = _drive_scripted("c2b", script)
    check("T-C2b 阳性对照：无缺测长停 ⇒ confirmed >= 1",
          online["n_confirmed_continuous_freezes"] >= 1
          and replayed["n_confirmed_continuous_freezes"] >= 1
          and not deep_diff(online, replayed),
          "online=%d replay=%d runs=%s"
          % (online["n_confirmed_continuous_freezes"],
             replayed["n_confirmed_continuous_freezes"],
             [(r["frame"], r["n"], r["duration_ns"], r["reason"], r["confirmed"])
              for r in replayed["zero_delta_runs"]]))


def test_T_C3():
    """帧号回退 / 新局 / 读档 / PID 变化能正确分段（段号改变）。"""
    script = [
        (0, {"frame": 100, "pid": 14412}),
        (200_000_000, {"frame": 101, "pid": 14412}),
        (400_000_000, {"frame": 90, "pid": 14412}),     # 自动 frame_regression
        (600_000_000, {"frame": 91, "pid": 14412, "marker": "new_game"}),
        (800_000_000, {"frame": 92, "pid": 14412, "marker": "load_game"}),
        (1_000_000_000, {"frame": 93, "pid": 20001}),   # 自动 pid_change
        (1_200_000_000, {"frame": None, "read_status": "read_failed",
                         "pid": 20001}),
        (1_400_000_000, {"frame": 94, "pid": 20001}),
    ]
    online, replayed, case = _drive_scripted("c3", script)
    recs = replay.load_records(case["nd"])
    reads = [r for r in recs if r.get("kind") == "frame_read"]
    segs = [r["segment"] for r in reads]
    switched = sum(1 for a, b in zip(segs, segs[1:]) if a != b)
    counts_ok = (replayed["n_frame_regressions"] >= 1
                 and replayed["n_new_game_markers"] >= 1
                 and replayed["n_load_game_markers"] >= 1
                 and replayed["n_pid_change_markers"] >= 1
                 and replayed["n_read_fail_gaps"] >= 1)
    check("T-C3 帧号回退/新局/读档/PID 变化正确分段",
          switched >= 5 and replayed["n_segments"] >= 6
          and len(set(segs)) >= 6 and counts_ok
          and not deep_diff(online, replayed),
          "segments=%s switches=%d n_segments=%d markers=(%d,%d,%d,%d,%d)"
          % (segs, switched, replayed["n_segments"],
             replayed["n_frame_regressions"], replayed["n_new_game_markers"],
             replayed["n_load_game_markers"],
             replayed["n_pid_change_markers"], replayed["n_read_fail_gaps"]))


def test_T_C4():
    """同一 NDJSON 经 replay_re_n01.py 重算的摘要与在线摘要逐字段一致。"""
    clock = StepClock(step=1_000_000)
    spy = SpySampler(clock=clock, burn=5)
    nd, sm = TMP / "c4.ndjson", TMP / "c4.online.json"
    sink = mon.NDJSONSink(nd)
    fired = {"n": 0}

    class FireTwice(object):
        def __init__(self):
            self.n = 0

        def observe(self, t, frame):
            self.n += 1
            return self.n in (2, 5)

        def reset(self):
            pass

    mon.run_monitor(pid=14412, want_tid=30668, only_tid=True,
                    sampler=spy, detector=FireTwice(),
                    rd=lambda i: {"frame": 100 + (i // 4), "pid": 14412},
                    sink=sink, cfg=_cfg(), now_ns=clock,
                    utc_fn=lambda: "2026-11-12T00:00:00+00:00",
                    max_ticks=9, summary_path=sm)
    online = json.loads(sm.read_text(encoding="utf-8"))
    recs = replay.load_records(nd)
    replayed = replay.summarize_records(recs)
    diff = deep_diff(online, replayed)

    def n_leaves(x):
        if isinstance(x, dict):
            return sum(n_leaves(v) for v in x.values())
        if isinstance(x, list):
            return sum(n_leaves(v) for v in x) if x else 1
        return 1

    check("T-C4 在线摘要 vs replay 离线重算逐字段一致",
          not diff and online["schema"] == replay.SCHEMA
          and online["n_events"] == 2
          and json.dumps(online, sort_keys=True, ensure_ascii=False)
          == json.dumps(replayed, sort_keys=True, ensure_ascii=False),
          "fields=%d diff=%s n_records=%d n_events=%d"
          % (n_leaves(online), diff[:3], online["n_records"],
             online["n_events"]))


# ================================================================ T-D 组

def test_T_D1():
    """六计时字段齐全，且端到端 ≥ 分项之和；时钟容差 0 ns（同一整数时钟）。"""
    clock = StepClock(step=1_000_000)
    spy = SpySampler(clock=clock, burn=6)
    nd = TMP / "d1.ndjson"
    sink = mon.NDJSONSink(nd)
    out = mon.run_monitor(pid=14412, want_tid=30668, only_tid=True,
                          sampler=spy, detector=FireOnce(),
                          rd=lambda i: {"frame": 100, "pid": 14412},
                          sink=sink, cfg=_cfg(), now_ns=clock,
                          utc_fn=lambda: "2026-11-12T00:00:00+00:00",
                          max_ticks=1)
    recs = replay.load_records(nd)
    events = [r for r in recs if r.get("kind") == "event"]
    six = ("detect_ns", "context_ns", "walk_ns", "resume_ns",
           "suspend_held_ns", "end_to_end_ns")
    parts = ("preflight_ns", "ownership_ns", "open_ns", "context_ns",
             "walk_ns", "resume_ns", "overhead_ns")
    # 容差 0 ns：全部里程碑来自同一个 perf_counter_ns 整数时钟（离线为 StepClock
    # 注入），望远镜求和恒等；跨进程/跨时钟域时不适用此等式。
    tolerance_ns = 0
    all_ok = True
    ev_lines = []
    for e in events:
        c = e.get("cost_ns") or {}
        present = all(k in c for k in six)
        s = sum(int(c.get(k, 0)) for k in parts)
        ok = (present and c["end_to_end_ns"] + tolerance_ns >= s
              and c["suspend_held_ns"] <= c["end_to_end_ns"]
              and c["event_total_ns"] >= c["end_to_end_ns"]
              and e.get("ns_marks", {}).get("end") is not None)
        all_ok = all_ok and ok
        ev_lines.append("e2e=%d parts=%d held=%d" %
                        (c.get("end_to_end_ns", -1), s,
                         c.get("suspend_held_ns", -1)))
    check("T-D1 六计时字段 + e2e ≥ 分项之和（容差 0ns）",
          len(events) >= 1 and all_ok,
          "events=%d %s" % (len(events), "; ".join(ev_lines)))


ALL_TESTS = [
    ("T-A1", test_T_A1), ("T-A2", test_T_A2), ("T-A3", test_T_A3),
    ("T-B1", test_T_B1), ("T-B2", test_T_B2), ("T-B3", test_T_B3),
    ("T-B4", test_T_B4),
    ("T-C1", test_T_C1), ("T-C2", test_T_C2), ("T-C2b", test_T_C2b),
    ("T-C3", test_T_C3), ("T-C4", test_T_C4),
    ("T-D1", test_T_D1),
]


def main():
    print("=" * 78)
    print("RE-N01 离线测试（零真机 · 全部 Win32 为 stub / 假对象）")
    print("run_id=NEXT_RE_20261112_R01  root=%s" % ROOT)
    print("=" * 78)
    for name, fn in ALL_TESTS:
        try:
            fn()
        except Exception as e:                              # noqa: BLE001
            check(name + " 未捕获异常", False,
                  "%s:%s" % (type(e).__name__, e))
    reds = [n for n, ok, _ in _RESULTS if not ok]
    print("=" * 78)
    print("结果：%d 项检查，%d 项失败%s" %
          (len(_RESULTS), len(reds), "" if not reds else "：%s" % reds))
    print("=" * 78)
    return 0 if not reds else 1


if __name__ == "__main__":
    sys.exit(main())
