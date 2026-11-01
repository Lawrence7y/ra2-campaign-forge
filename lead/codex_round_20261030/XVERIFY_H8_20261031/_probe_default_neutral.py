# -*- coding: utf-8 -*-
"""XVERIFY H8 探针 P1：离线双跑 _measure_run，逐字节对账 rec 行与窗 JSON。

★ 零真机：不启动游戏、不开句柄。用桩替换 _rpm_open/_rpm_u32/_rpm_close/
  _measure_poll_span/_rpm_counters/_measure_window_forensics/_measure_focus_regrab，
  只检验 H8 新增块在「缺省 None」与「给定 N」两种状态下的行为与留痕。
★ 写域：本探针与其产物全部位于 lead/codex_round_20261030/XVERIFY_H8_20261031/。
"""
import ast
import hashlib
import json
import sys
import types
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"D:\Project\ra2-campaign-forge")
H7 = ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py"
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
    """装桩：handle 打开恒成功；CurrentFrame 依 `frames` 序列返回。

    frames 可以是标量（恒定值）或列表（每次 _rpm_u32(CurrentFrame) 依次取一个）。
    """
    seq = [frames] if isinstance(frames, int) else list(frames)
    state = {"i": 0}

    def _rpm_open(pid):
        return FakeHandle()

    def _rpm_close(h):
        return None

    def _rpm_u32(handle, va):
        if va == m.MEASURE_CURRENT_FRAME_VA:
            i = state["i"]
            state["i"] += 1
            return seq[i] if i < len(seq) else seq[-1]
        return 0

    def _rpm_counters(handle):
        return {"units": None}

    def _measure_poll_span(handle, span_s, hz):
        # 合成 4 个采样点 + 一行 counters（units=1342）
        t0 = 1000.0
        samples = [(t0 + k * 1.0, 400 + k) for k in range(4)]
        counters = [{"units": 1342, "t_rel": 0.0}]
        return t0, samples, counters, None

    def _forensics(rec, handle, hwnd, k, out_dir, stats):
        return None

    def _focus(rec, hwnd, k):
        return None

    m._rpm_open = _rpm_open
    m._rpm_close = _rpm_close
    m._rpm_u32 = _rpm_u32
    m._rpm_counters = _rpm_counters
    m._measure_poll_span = _measure_poll_span
    m._measure_window_forensics = _forensics
    m._measure_focus_regrab = _focus
    return state


def run(m, out_dir, frames, n=None):
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in out_dir.glob("measure_w*.json"):
        p.unlink()
    if n is None:
        m.H8_MEASURE_START_FRAME = None
    else:
        m.H8_MEASURE_START_FRAME = int(n)
    if hasattr(m, "_H8_STATE"):
        m._H8_STATE["frame_wait"] = None
    rec = m.Recorder()
    budget = m.TripBudget(rec)
    st = arm(m, frames)
    m._measure_run(rec, budget, 1234, out_dir, "sha" * 16, None)
    rows = [{k: r[k] for k in ("group", "key", "value", "source", "note")}
            for r in rec.rows]
    jreld = {}
    for p in sorted(out_dir.glob("measure_w*.json")):
        jreld[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {"rows": rows, "json": jreld, "polls_consumed": st["i"],
            "h8_state": (dict(m._H8_STATE) if hasattr(m, "_H8_STATE") else None)}


def main():
    results = {}
    m7 = load(H7, "xv_h7")
    m8 = load(H8, "xv_h8")

    # --- A. 缺省中性：harness7 vs harness8(N=None)，同帧序列（正常三窗路径）
    frames_ok = [10]            # late-start 不触发（nav_end_t 缺省 None）
    a7 = run(m7, HERE / "outA7", frames_ok)
    a8 = run(m8, HERE / "outA8", frames_ok, n=None)
    results["A_default_neutral_rows_equal"] = a7["rows"] == a8["rows"]
    results["A_default_neutral_json_equal"] = a7["json"] == a8["json"]
    results["A_rowcount"] = [len(a7["rows"]), len(a8["rows"])]
    results["A_json7"] = a7["json"]
    results["A_json8"] = a8["json"]
    results["A_h8_state"] = a8["h8_state"]

    # --- B. 越界拒采：等待起点 frame 已 > N
    b = run(m8, HERE / "outB", [900], n=400)
    results["B_rows_new"] = [r for r in b["rows"] if r["key"] not in
                             [x["key"] for x in a8["rows"]]]
    results["B_verdict_rec"] = [r["value"] for r in b["rows"]
                                if r["group"] == "MEASURE" and r["key"] == "verdict"]
    results["B_frame_wait"] = [r["value"] for r in b["rows"]
                               if r["key"] == "h7_frame_wait"]
    results["B_json"] = b["json"]
    results["B_polls"] = b["polls_consumed"]
    results["B_h8_state"] = b["h8_state"]
    w0 = HERE / "outB" / "measure_w0.json"
    results["B_w0_verdict"] = json.loads(w0.read_text(encoding="utf-8")).get("verdict")
    results["B_w0_stats"] = json.loads(
        w0.read_text(encoding="utf-8")).get("stats", {}).get("fps_avg")
    results["B_w1_exists"] = (HERE / "outB" / "measure_w1.json").exists()

    # --- C. 达标路径（frame==N 首读即达标）
    c = run(m8, HERE / "outC", [400], n=400)
    results["C_verdict_rec"] = [r["value"] for r in c["rows"]
                                if r["group"] == "MEASURE" and r["key"] == "verdict"]
    results["C_frame_wait"] = [r["value"] for r in c["rows"]
                               if r["key"] == "h7_frame_wait"]
    results["C_json"] = c["json"]
    results["C_rows_extra_vs_A"] = len(c["rows"]) - len(a8["rows"])

    # --- D. 超时拒采（把超时帽临时压到 0.05s，避免本探针真等 120s）
    old_to = m8.H8_FRAME_WAIT_TIMEOUT_S
    m8.H8_FRAME_WAIT_TIMEOUT_S = 0.05
    d = run(m8, HERE / "outD", [10], n=400)
    m8.H8_FRAME_WAIT_TIMEOUT_S = old_to
    results["D_verdict_rec"] = [r["value"] for r in d["rows"]
                                if r["group"] == "MEASURE" and r["key"] == "verdict"]
    results["D_frame_wait"] = [r["value"] for r in d["rows"]
                               if r["key"] == "h7_frame_wait"]
    results["D_polls"] = d["polls_consumed"]
    results["D_json"] = d["json"]
    w0d = HERE / "outD" / "measure_w0.json"
    dd = json.loads(w0d.read_text(encoding="utf-8"))
    results["D_w0_verdict"] = dd.get("verdict")
    results["D_w0_fps_avg"] = dd.get("stats", {}).get("fps_avg")
    results["D_w1_exists"] = (HERE / "outD" / "measure_w1.json").exists()

    # --- E. RPM 读失败（None）⇒ 应走超时支而非崩溃
    m8.H8_FRAME_WAIT_TIMEOUT_S = 0.05
    e = run(m8, HERE / "outE", [None], n=400)
    m8.H8_FRAME_WAIT_TIMEOUT_S = old_to
    results["E_verdict_rec"] = [r["value"] for r in e["rows"]
                                if r["group"] == "MEASURE" and r["key"] == "verdict"]
    results["E_frame_wait"] = [r["value"] for r in e["rows"]
                               if r["key"] == "h7_frame_wait"]

    # --- F. 句柄关闭：拒采路径是否仍 finally 关句柄
    closed = [r for r in d["rows"] if r["key"] == "handle_closed"]
    results["F_handle_closed_on_reject"] = bool(closed)

    print(json.dumps(results, ensure_ascii=False, indent=1))
    (HERE / "probe_default_neutral.stdout.txt").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
