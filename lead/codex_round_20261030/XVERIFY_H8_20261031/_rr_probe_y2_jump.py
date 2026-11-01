# -*- coding: utf-8 -*-
"""RR-P2（Y-2 复验）：v2 跳帧拒采（H8-4）路径覆盖 + 边界 + 不误伤性。

用例如 ask 指定：
  J1 frames=[None, 900]  N=400 ⇒ 首拍读败后跳读 ⇒ 应拒（overrun_kind=jump）
  J2 frames=[399, 400]   N=400 ⇒ 正常 1 帧步进 ⇒ 应达标
  J3 frames=[398, 400]   N=400 ⇒ offset=2（容差上界）⇒ 应达标
  J4 frames=[403, 400]   ... 见下
  B1 frames=[402]        N=400 ⇒ offset=2 达标（若首拍即 >N 走 H8-2 分支，另计）
  B2 frames=[403]        N=400 ⇒ offset=3 ⇒ 应拒
  M1 frames=[10, 900]    N=400 ⇒ 中途跳读 ⇒ 应拒（jump）
  M2 frames=[None,399,402] ⇒ 首拍 None + 中途读败 + 末拍 offset=2 ⇒ 达标（不误伤）
  M3 frames=[None,None,403] ⇒ 首拍 None + 末拍 offset=3 ⇒ 拒
  T1 frames=[10]*5       N=400 ⇒ 帧钟不动 ⇒ 超时拒（frame_wait_timeout）
★ 零真机、零游戏进程：_rpm_open/_rpm_u32/_rpm_close/_measure_poll_span/取证/焦点全桩。
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
        samples = [(t0 + k * 0.5, 400 + k) for k in range(9)]
        return t0, samples, [{"units": 1342, "t_rel": 0.0}], None

    m._rpm_u32 = _rpm_u32
    m._measure_poll_span = _span
    m._measure_window_forensics = lambda *a, **k: None
    m._measure_focus_regrab = lambda *a, **k: None
    m._measure_check_isolated_process = lambda *a, **k: None
    return st


def run(tag, frames, n, *, timeout_s=0.2):
    m = load(H8, "rr_%s" % tag)
    out = HERE / ("rr_out_%s" % tag)
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob("measure_w*.json"):
        p.unlink()
    m.H8_MEASURE_START_FRAME = int(n)
    m.H8_FRAME_WAIT_TIMEOUT_S = timeout_s
    rec = m.Recorder()
    budget = m.TripBudget(rec)
    arm(m, frames)
    closed = {"v": None}
    orig_close = m._rpm_close

    def spy_close(h):
        closed["v"] = True
        return orig_close(h)
    m._rpm_close = spy_close
    m._measure_run(rec, budget, 9999, out, "sha" * 16, None)
    fw = [r for r in rec.rows if r["key"] == "h7_frame_wait"]
    vd = [r["value"] for r in rec.rows if r["group"] == "MEASURE" and r["key"] == "verdict"]
    note = [r["note"] for r in rec.rows if r["key"] == "h7_frame_wait"]
    w0 = out / "measure_w0.json"
    j = json.loads(w0.read_text(encoding="utf-8")) if w0.exists() else None
    return {
        "tag": tag, "frames": frames, "n": n,
        "verdict_rec": vd,
        "frame_wait": fw[0]["value"] if fw else None,
        "note_head": (note[0][:46] if note else None),
        "reject": bool(vd) and vd[0] in ("frame_overrun", "frame_wait_timeout"),
        "overrun_kind": (fw[0]["value"].get("overrun_kind") if fw else None),
        "offset_frames": (fw[0]["value"].get("offset_frames") if fw else None),
        "w0_verdict_json": (j or {}).get("verdict"),
        "w0_error": (j or {}).get("error"),
        "w1_exists": (out / "measure_w1.json").exists(),
        "handle_closed": closed["v"],
        "h8_state": json.loads(json.dumps(m._H8_STATE)),
    }


def main():
    res = {
        "J1_first_None_then_jump": run("J1", [None, 900], 400),
        "J2_normal_step_399_400": run("J2", [399, 400], 400),
        "J3_offset2_398_400": run("J3", [398, 400], 400),
        "B1_first_read_offset2": run("B1", [402], 400),
        "B2_first_read_offset3": run("B2", [403], 400),
        "K1_loop_exit_offset2": run("K1", [399, 402], 400),
        "K2_loop_exit_offset3": run("K2", [399, 403], 400),
        "K3_N398_reached400_offset2": run("K3", [398, 400], 398),
        "K4_N397_reached400_offset3": run("K4", [398, 400], 397),
        "M1_mid_jump": run("M1", [10, 900], 400),
        "M2_None_then_fail_then_offset2": run("M2", [None, 399, 402], 400),
        "M3_None_then_offset3": run("M3", [None, None, 403], 400),
        "T1_frozen_clock_timeout": run("T1", [10] * 5, 400),
        "E1_exact_N": run("E1", [400], 400),
        "E2_first_read_over": run("E2", [900], 400),
    }
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    print(txt)
    (HERE / "rr_p2_y2.stdout.txt").write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    main()
