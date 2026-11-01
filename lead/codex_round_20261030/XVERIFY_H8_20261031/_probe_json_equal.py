# -*- coding: utf-8 -*-
"""XVERIFY H8 探针 P2：缺省中性 JSON 载荷逐字段对账（排除墙钟字段）。

★ P1 里 A 组 rec 行完全相等但窗 JSON sha 不等 ⇒ 本探针定位差异字段，
  证明不等仅来自 time.time()/perf_counter 墙钟戳（与补丁无关），
  而非 H8 代码路径引入的字段差。
★ 同时跑「三窗全采满」的正常路径（把 gate 桩改成推进足够），对账 h7/h8。
"""
import json
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"D:\Project\ra2-campaign-forge")
H7 = ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py"
H8 = ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8.py"

WALLCLOCK_KEYS = {"t_abs0"}
WALLCLOCK_TOLERANT_PATHS = {
    "samples.t",          # perf_counter 相对值（桩里固定）
    "frame_edges",        # 含 perf_counter
    "counters.t_rel",
    "stats.hz_effective",
    "stats.max_stall_s",
}


def load(path, name):
    sp = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m


class FakeHandle:
    pass


def arm_good(m):
    """桩：让 gate/W1/3 窗全部走通（推进足够 + units=1342）。"""

    def _rpm_open(pid):
        return FakeHandle()

    def _rpm_close(h):
        return None

    def _rpm_u32(handle, va):
        return 500

    def _rpm_counters(handle):
        return {"units": 1342}

    def _measure_poll_span(handle, span_s, hz):
        # 4 秒/25 秒窗都用固定步长：1.5s 末段推进 ≥ 25 fps
        n = 40
        dt = span_s / n
        t0 = 1000.0
        samples = [(t0 + k * dt, int(k * dt * 31)) for k in range(n + 1)]
        counters = [{"units": 1342, "t_rel": 0.0}]
        return t0, samples, counters, None

    m._rpm_open = _rpm_open
    m._rpm_close = _rpm_close
    m._rpm_u32 = _rpm_u32
    m._rpm_counters = _rpm_counters
    m._measure_poll_span = _measure_poll_span
    m._measure_window_forensics = lambda *a, **k: None
    m._measure_focus_regrab = lambda *a, **k: None


def strip_wallclock(obj, path=""):
    """递归去掉墙钟字段，返回可比较副本。"""
    if isinstance(obj, dict):
        return {k: strip_wallclock(v, path + "." + k)
                for k, v in obj.items() if k not in WALLCLOCK_KEYS}
    if isinstance(obj, list):
        return [strip_wallclock(v, path + "[]") for v in obj]
    return obj


def run(m, out_dir, n=None):
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in out_dir.glob("measure_w*.json"):
        p.unlink()
    m.H8_MEASURE_START_FRAME = None if n is None else int(n)
    rec = m.Recorder()
    budget = m.TripBudget(rec)
    arm_good(m)
    m._measure_run(rec, budget, 4321, out_dir, "sha" * 16, None)
    rows = [{k: r[k] for k in ("group", "key", "value", "source", "note")}
            for r in rec.rows]
    js = {}
    for p in sorted(out_dir.glob("measure_w*.json")):
        js[p.name] = json.loads(p.read_text(encoding="utf-8"))
    return rows, js


def diff_dicts(a, b, path=""):
    out = []
    if type(a) is not type(b):
        return [path + ": TYPE"]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append(path + "." + k + ": only in B")
            elif k not in b:
                out.append(path + "." + k + ": only in A")
            else:
                out += diff_dicts(a[k], b[k], path + "." + k)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(path + ": LEN %d vs %d" % (len(a), len(b)))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                out += diff_dicts(x, y, path + "[%d]" % i)
    elif a != b:
        out.append(path + ": %r vs %r" % (a, b))
    return out


def main():
    res = {}
    m7 = load(H7, "p2_h7")
    m8 = load(H8, "p2_h8")

    r7, j7 = run(m7, HERE / "outP2_7")
    r8, j8 = run(m8, HERE / "outP2_8", n=None)

    res["rows_equal"] = r7 == r8
    res["rows_count"] = [len(r7), len(r8)]
    res["verdict_rows_h7"] = [r["value"] for r in r7
                              if r["key"] == "verdict"]
    res["verdict_rows_h8"] = [r["value"] for r in r8
                              if r["key"] == "verdict"]
    res["windows_produced_h7"] = sorted(j7)
    res["windows_produced_h8"] = sorted(j8)

    # 原始 sha（含墙钟）
    res["raw_sha_equal"] = {
        k: (json.dumps(j7[k], sort_keys=True) == json.dumps(j8[k], sort_keys=True))
        for k in j7}
    # 去掉墙钟后
    s7 = {k: strip_wallclock(v) for k, v in j7.items()}
    s8 = {k: strip_wallclock(v) for k, v in j8.items()}
    res["wallclock_stripped_equal"] = {}
    res["diffs"] = {}
    for k in sorted(set(s7) | set(s8)):
        d = diff_dicts(s7.get(k), s8.get(k), k)
        res["wallclock_stripped_equal"][k] = (not d)
        if d:
            res["diffs"][k] = d[:40]
    # 墙钟字段名定位（第一次跑 P1 时 A 组 sha 不等的来源）
    res["raw_diffs_with_wallclock"] = {}
    for k in sorted(j7):
        d = diff_dicts(j7[k], j8[k], k)
        if d:
            res["raw_diffs_with_wallclock"][k] = d[:20]

    print(json.dumps(res, ensure_ascii=False, indent=1))
    (HERE / "probe_json_equal.stdout.txt").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
