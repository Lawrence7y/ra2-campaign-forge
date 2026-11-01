# -*- coding: utf-8 -*-
"""XVERIFY H8 探针 P6：H8 绑帧等待循环是否**顺路消费** QC213 / QC213P2 探针。

★ 背景（亲读代码所得）：
  - `main()` 在 `_measure_run` **之前**就把 `_QC213_PROBE["on"]` / `_QC213P2_PROBE["on"]`
    置 True（harness8 :8236-8246，条件 = `--measure` ∧ nav OK ⇒ 本批必然为 on）。
  - `_rpm_u32` 被 QC213P2→QC213 两层同名包装，凡 `va==MEASURE_CURRENT_FRAME_VA`
    的读数都会驱动 `_qc213_tick` / `_qc213p2_tick`（:4249、:4536）。
  ⇒ H8 等待循环里的每一次 `_rpm_u32(handle, MEASURE_CURRENT_FRAME_VA)`
    都不是"纯读帧钟"，而是会触发探针闩锁/冻结看门与快照。
★ 本探针把两层 tick 与快照函数换成计数器（其余保持原件），用**桩帧序列**跑
  `_measure_run` 的 H8 分支，统计等待期内触发了多少次 early / latch / frozen。
★ 用例：
  T1 帧钟在等待期冻结（模拟"引擎未推帧"，设计件 §1 明说短路臂 entry 后 frame≈0）
  T2 帧钟正常推进到 N（跨过 QC213P2 阶梯 10 / 250..312 与 QC213 闩锁 300）
"""
import json
import importlib.util
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"D:\Project\ra2-campaign-forge")
H8 = ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8.py"


def load(path, name):
    sp = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m


class FakeHandle:
    pass


def run_case(label, seq, n, advance_each_poll=True, dt=0.002):
    m = load(H8, "p6_%s" % label)
    out = HERE / ("p6_out_%s" % label)
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob("measure_w*.json"):
        p.unlink()

    calls = {"qc213_snap": [], "qc213p2_snap": [], "ticks": 0}

    # 保留原 tick 逻辑，只把快照换成计数桩
    m._qc213_snapshot = lambda handle, frame, tag: calls["qc213_snap"].append(
        (tag, frame, round(time.perf_counter() - t_wall, 4)))
    m._qc213p2_snapshot = lambda handle, frame, tag: calls["qc213p2_snap"].append(
        (tag, frame, round(time.perf_counter() - t_wall, 4)))

    state = {"i": 0}
    t_wall = time.perf_counter()

    m._rpm_open = lambda pid: FakeHandle()
    m._rpm_close = lambda h: None
    m._rpm_counters = lambda h: {"units": 1342}

    def _rpm_u32_base(handle, va):
        """最底层桩：直接命中 QC213 包装的锚（替换 :3915 那层实现）。"""
        if va != m.MEASURE_CURRENT_FRAME_VA:
            return 0
        i = state["i"]
        state["i"] += 1
        if i < len(seq):
            return seq[i]
        return seq[-1]

    m._rpm_u32_qc213_base = _rpm_u32_base   # ← 两层包装的公共锚

    def _span(handle, span_s, hz):
        t0 = 1000.0
        samples = [(t0 + k * 0.5, 400 + k) for k in range(9)]
        return t0, samples, [{"units": 1342, "t_rel": 0.0}], None

    m._measure_poll_span = _span
    m._measure_window_forensics = lambda *a, **k: None
    m._measure_focus_regrab = lambda *a, **k: None

    m.H8_MEASURE_START_FRAME = int(n)
    m.H8_FRAME_WAIT_TIMEOUT_S = 0.12          # 压短，避免本探针真等 120s
    rec = m.Recorder()
    budget = m.TripBudget(rec)
    m.ACTIVE_REC[0] = rec
    m._QC213_PROBE["on"] = True
    m._QC213P2_PROBE["on"] = True
    t_wall = time.perf_counter()
    m._measure_run(rec, budget, 5555, out, "sha" * 16, None)

    fw = [r["value"] for r in rec.rows if r["key"] == "h7_frame_wait"]
    vrows = [r["value"] for r in rec.rows
             if r["group"] == "MEASURE" and r["key"] == "verdict"]
    return {
        "n": n, "polls": fw[0]["poll_count"] if fw else None,
        "verdict_rec": vrows,
        "qc213_latched": dict(m._QC213_PROBE["latched"]),
        "qc213_latched_n": m._QC213_PROBE["latched_n"],
        "qc213_done_after_measure": m._QC213_PROBE["done"],
        "qc213_frozen_done": m._QC213_PROBE["frozen_done"],
        "qc213p2_early_done": m._QC213P2_PROBE["early_done"],
        "qc213p2_latched_n": m._QC213P2_PROBE["latched_n"],
        "qc213p2_done": m._QC213P2_PROBE["done"],
        "qc213p2_frozen_done": m._QC213P2_PROBE["frozen_done"],
        "snap_qc213": calls["qc213_snap"][:12],
        "snap_qc213p2": calls["qc213p2_snap"][:12],
        "snap_qc213_n": len(calls["qc213_snap"]),
        "snap_qc213p2_n": len(calls["qc213p2_snap"]),
        "LADDER_n": len(m.QC213P2_LADDER),
        "LADDER_head": list(m.QC213P2_LADDER)[:6],
        "LATCH_FRAMES": list(m._QC213_PROBE["latch_frames"] or
                             m.QC213_LATCH_FRAMES),
    }


def main():
    res = {}
    # T1: 帧钟冻结在 12（模拟引擎未推帧）——等待期会撞 QC213_FREEZE_S=2.0 吗？
    #     用少量不同帧值 + 让 tick 的 monotonic 差足够：桩里 tick 用真时间，
    #     等待循环每拍 _doze(0.002) ⇒ 120ms 帽内约 60 拍 ≈0.12s < 2s ⇒ 不冻结；
    #     故另设 T1b：把超时帽放大到 2.4s 以真实跨越 2s 冻结阈。
    res["T1_frozen_short_wait"] = run_case("T1", [12], 400)
    res["T1b_frozen_over_2s"] = run_case_frozen()
    # T2: 帧钟逐拍推进 1..401（跨过阶梯 10 / 250..312 与 QC213 闩锁 300/600）
    res["T2_advance_to_N"] = run_case("T2", list(range(1, 402)), 400)

    print(json.dumps(res, ensure_ascii=False, indent=1))
    (HERE / "probe_probe_interference.stdout.txt").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


def run_case_frozen():
    """等待期跨越 QC213/QC213P2 的 2s 冻结阈：帧钟恒 12，超时帽 2.4s。"""
    m = load(H8, "p6_T1b")
    out = HERE / "p6_out_T1b"
    out.mkdir(parents=True, exist_ok=True)
    calls = {"qc213": [], "qc213p2": []}
    tw = time.perf_counter()
    m._qc213_snapshot = lambda h, f, tag: calls["qc213"].append(
        (tag, f, round(time.perf_counter() - tw, 3)))
    m._qc213p2_snapshot = lambda h, f, tag: calls["qc213p2"].append(
        (tag, f, round(time.perf_counter() - tw, 3)))
    state = {"i": 0}
    m._rpm_open = lambda pid: FakeHandle()
    m._rpm_close = lambda h: None
    m._rpm_counters = lambda h: {"units": 1342}

    def base(handle, va):
        if va != m.MEASURE_CURRENT_FRAME_VA:
            return 0
        state["i"] += 1
        return 12
    m._rpm_u32_qc213_base = base
    m._measure_poll_span = lambda h, s, z: (1000.0, [], [], None)
    m._measure_window_forensics = lambda *a, **k: None
    m._measure_focus_regrab = lambda *a, **k: None
    m.H8_MEASURE_START_FRAME = 400
    m.H8_FRAME_WAIT_TIMEOUT_S = 2.4
    rec = m.Recorder()
    m.ACTIVE_REC[0] = rec
    m._QC213_PROBE["on"] = True
    m._QC213P2_PROBE["on"] = True
    tw = time.perf_counter()
    m._measure_run(rec, m.TripBudget(rec), 5555, out, "sha" * 16, None)
    fw = [r["value"] for r in rec.rows if r["key"] == "h7_frame_wait"]
    return {
        "polls": fw[0]["poll_count"] if fw else None,
        "wait_s": fw[0]["wait_s"] if fw else None,
        "verdict": [r["value"] for r in rec.rows
                    if r["group"] == "MEASURE" and r["key"] == "verdict"],
        "qc213_snap": calls["qc213"], "qc213p2_snap": calls["qc213p2"],
        "qc213_done": m._QC213_PROBE["done"],
        "qc213_frozen_done": m._QC213_PROBE["frozen_done"],
        "qc213p2_done": m._QC213P2_PROBE["done"],
        "qc213p2_early_done": m._QC213P2_PROBE["early_done"],
        "qc213p2_frozen_done": m._QC213P2_PROBE["frozen_done"],
    }


if __name__ == "__main__":
    main()
