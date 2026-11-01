# -*- coding: utf-8 -*-
"""XVERIFY H8 探针 P4：H8-2 越界判定只在**首拍**做 ⇒ 首拍 RPM 失败(None) 时
   入口相位越界是否被漏检（误当「达标」放行、且 rec 宣称「绑帧等待达标」）。

★ 用例：
  G1 frames=[None, 900] n=400  ⇒ 首拍读失败、次拍已 900 (>N 500 帧)
  G2 frames=[10, 900]  n=400  ⇒ 首拍 10 (<N 合法) 后跳到 900（帧钟本身不会倒退/跳，
     但 RPM 半读/进程重启等场景可类比；同时给出轮询期间的 overshoot 行为）
  G3 frames=[399, 401] n=400  ⇒ 正常 1 帧量化过冲（预期可接受，看留痕）
"""
import json
import importlib.util
import sys
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


def arm(m, frames):
    seq = list(frames)
    st = {"i": 0}

    m._rpm_open = lambda pid: FakeHandle()
    m._rpm_close = lambda h: None
    m._rpm_counters = lambda h: {"units": 1342}

    def _rpm_u32(handle, va):
        if va == m.MEASURE_CURRENT_FRAME_VA:
            i = st["i"]
            st["i"] += 1
            return seq[i] if i < len(seq) else seq[-1]
        return 0

    def _span(handle, span_s, hz):
        t0 = 1000.0
        # 合成一个能过 gate 且 units 满员的 settle（若走到 settle 就说明没被拒采）
        samples = [(t0 + k * 0.5, 400 + k) for k in range(9)]
        return t0, samples, [{"units": 1342, "t_rel": 0.0}], None

    m._rpm_u32 = _rpm_u32
    m._measure_poll_span = _span
    m._measure_window_forensics = lambda *a, **k: None
    m._measure_focus_regrab = lambda *a, **k: None
    return st


def run(frames, n):
    m = load(H8, "p4_%s_%s" % (frames[0], n))
    out = HERE / ("p4_out_%s_%s" % (str(frames[0]).replace("None", "N"), n))
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob("measure_w*.json"):
        p.unlink()
    m.H8_MEASURE_START_FRAME = int(n)
    m.H8_FRAME_WAIT_TIMEOUT_S = 0.2
    rec = m.Recorder()
    budget = m.TripBudget(rec)
    arm(m, frames)
    m._measure_run(rec, budget, 9999, out, "sha" * 16, None)
    fw = [r for r in rec.rows if r["key"] == "h7_frame_wait"]
    vd = [r["value"] for r in rec.rows if r["group"] == "MEASURE" and r["key"] == "verdict"]
    note = [r["note"] for r in rec.rows if r["key"] == "h7_frame_wait"]
    w0 = out / "measure_w0.json"
    j = json.loads(w0.read_text(encoding="utf-8")) if w0.exists() else None
    return {"frames": frames, "n": n,
            "verdict_rec": vd,
            "frame_wait": fw[0]["value"] if fw else None,
            "note_head": (note[0][:40] if note else None),
            "reached_f0_in_json": ((j or {}).get("samples", {}).get("f") or [None])[0],
            "w1_exists": (out / "measure_w1.json").exists()}


def main():
    res = {
        "G1_first_read_None_then_overrun": run([None, 900], 400),
        "G2_low_then_jump": run([10, 900], 400),
        "G3_normal_1frame_overshoot": run([399, 401], 400),
        "G4_exact_N": run([400], 400),
    }
    print(json.dumps(res, ensure_ascii=False, indent=1))
    (HERE / "probe_overrun_first_read.stdout.txt").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
