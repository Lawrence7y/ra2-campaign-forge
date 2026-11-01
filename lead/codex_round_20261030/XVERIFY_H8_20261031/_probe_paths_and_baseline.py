# -*- coding: utf-8 -*-
"""XVERIFY H8 探针 P3：拒采路径完整 rec 行 + 既有真机趟的 samples.f[0] 基线。

★ 用途：
  1) 完整列出 frame_overrun / frame_wait_timeout 两条路径的 rec 行（含 handle_closed），
     与 harness7 late_start 先例的行形对照；
  2) 读既有真机趟 measure_w0.json 的 samples.f[0] / gate.units0，核卡片「预测」的
     经验基线（短路臂 entry frame≈0 ⇒ 绑帧等待需实际等多久）。
"""
import json
import glob
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"D:\Project\ra2-campaign-forge")
H8 = ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8.py"
TRIPS = ROOT / "lead/qc161_u0400_trip"


def load(path, name):
    sp = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m


class FakeHandle:
    pass


def arm(m, frames, settle_units=1342):
    seq = [frames] if isinstance(frames, int) else list(frames)
    st = {"i": 0}

    def _rpm_open(pid):
        return FakeHandle()

    m._rpm_open = _rpm_open
    m._rpm_close = lambda h: None
    m._rpm_counters = lambda h: {"units": settle_units}

    def _rpm_u32(handle, va):
        if va == m.MEASURE_CURRENT_FRAME_VA:
            i = st["i"]
            st["i"] += 1
            return seq[i] if i < len(seq) else seq[-1]
        return 0

    def _span(handle, span_s, hz):
        t0 = 1000.0
        samples = [(t0 + k, 400 + k) for k in range(4)]
        return t0, samples, [{"units": settle_units, "t_rel": 0.0}], None

    m._rpm_u32 = _rpm_u32
    m._measure_poll_span = _span
    m._measure_window_forensics = lambda *a, **k: None
    m._measure_focus_regrab = lambda *a, **k: None
    return st


def rows_for(frames, n, timeout=None):
    m = load(H8, "p3_h8_%s_%s" % (n, len(frames)))
    out = HERE / ("p3_out_%s_%s" % (n, frames[0]))
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob("measure_w*.json"):
        p.unlink()
    m.H8_MEASURE_START_FRAME = None if n is None else int(n)
    if timeout is not None:
        m.H8_FRAME_WAIT_TIMEOUT_S = float(timeout)
    rec = m.Recorder()
    budget = m.TripBudget(rec)
    arm(m, frames)
    m._measure_run(rec, budget, 7777, out, "sha" * 16, None)
    return [{k: r[k] for k in ("group", "key", "value", "source")} for r in rec.rows]


def main():
    res = {}
    res["OVERRUN_rows"] = rows_for([900], 400)
    res["TIMEOUT_rows"] = rows_for([10], 400, timeout=0.05)
    res["ACHIEVED_rows_first_read_eq_N"] = rows_for([400], 400)

    # 真机基线：既有趟 measure_w0 samples.f[0] / gate.units0 / verdict
    base = []
    for p in sorted(glob.glob(str(TRIPS / "*" / "measure_w0.json")))[:60]:
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        f = (d.get("samples") or {}).get("f") or []
        g = d.get("gate") or {}
        base.append({"trip": Path(p).parent.name,
                     "verdict": d.get("verdict"),
                     "f0": f[0] if f else None,
                     "units0": g.get("units0"),
                     "pre_fps15": g.get("pre_fps15")})
    res["real_trips_w0"] = base

    print(json.dumps(res, ensure_ascii=False, indent=1))
    (HERE / "probe_paths_and_baseline.stdout.txt").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
