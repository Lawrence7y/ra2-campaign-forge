# -*- coding: utf-8 -*-
"""XVERIFY H8 探针 P8：证明 P2 里 `rows_equal=False` 的那一行是**墙钟抖动**，
   不是 H8 引入的语义差 —— 办法：同一份 harness7 连跑两次互比（self-vs-self）。

★ 若 self-vs-self 也会出现同类 stage_seconds 抖动 ⇒ 该差异与补丁无关（缺省中性仍成立）。
★ 顺带对 v2 的 h7/vs-h8 多轮互跑，统计"差异行只落在 BUDGET 计时行"这一命题。
"""
import json
import importlib.util
import sys
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"D:\Project\ra2-campaign-forge")
H7 = str(ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py")
H8 = str(ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8.py")


class FH:
    pass


def load(path, name):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m


def arm(m):
    m._rpm_open = lambda pid: FH()
    m._rpm_close = lambda h: None
    m._rpm_u32 = lambda h, va: 500
    m._rpm_counters = lambda h: {"units": 1342}

    def _span(handle, span_s, hz):
        t0 = 1000.0
        n = 40
        dt = span_s / n
        return t0, [(t0 + k * dt, int(k * dt * 31)) for k in range(n + 1)], \
            [{"units": 1342, "t_rel": 0.0}], None
    m._measure_poll_span = _span
    m._measure_window_forensics = lambda *a, **k: None
    m._measure_focus_regrab = lambda *a, **k: None


def run(path, out, name, n=None):
    m = load(path, name)
    Path(out).mkdir(parents=True, exist_ok=True)
    for f in os.listdir(out):
        if f.startswith("measure_w"):
            os.remove(os.path.join(out, f))
    if hasattr(m, "H8_MEASURE_START_FRAME"):
        m.H8_MEASURE_START_FRAME = None if n is None else int(n)
    rec = m.Recorder()
    arm(m)
    m._measure_run(rec, m.TripBudget(rec), 1, Path(out), "shasmoke", None)
    return [{k: r[k] for k in ("group", "key", "value", "source", "note")}
            for r in rec.rows]


def compare(a, b):
    if len(a) != len(b):
        return [("LEN", len(a), len(b))]
    out = []
    for i, (x, y) in enumerate(zip(a, b)):
        for k in ("group", "key", "value", "source", "note"):
            if x[k] != y[k]:
                out.append((i, x["key"], k, repr(x[k])[:40], repr(y[k])[:40]))
    return out


def main():
    res = {}
    # 1) harness7 self-vs-self（三轮）
    self_diffs = []
    for i in range(3):
        r1 = run(H7, str(str(HERE / ("eq7_%d" % i))), "s7a%d" % i)
        r2 = run(H7, str(str(HERE / ("eq7b_%d" % i))), "s7b%d" % i)
        self_diffs.append(compare(r1, r2))
    res["h7_self_vs_self_rounds"] = [len(x) for x in self_diffs]
    res["h7_self_diff_samples"] = self_diffs

    # 2) h7 vs h8(v2, 缺省 None)（三轮）
    pair_diffs = []
    kinds = []
    for i in range(3):
        r7 = run(H7, str(str(HERE / ("eq7p_%d" % i))), "p7a%d" % i)
        r8 = run(H8, str(str(HERE / ("eq8p_%d" % i))), "p8a%d" % i, n=None)
        d = compare(r7, r8)
        pair_diffs.append(d)
        for row in d:
            kinds.append(row[1])
    res["h7_vs_h8v2_rounds"] = [len(x) for x in pair_diffs]
    res["h7_vs_h8v2_diff_keys"] = sorted(set(kinds))
    res["h7_vs_h8v2_samples"] = [d[:6] for d in pair_diffs]
    # 关键命题：差异键集合 ⊆ self-vs-self 会出现的键集合
    self_keys = set(x[1] for d in self_diffs for x in d)
    res["diff_keys_subset_of_wallclock_keys"] = (set(kinds) <= (self_keys | {
        "stage_seconds:measure_w0", "stage_seconds:measure_w1",
        "stage_seconds:measure_w2", "settle_seconds"}))
    res["self_seen_keys"] = sorted(self_keys)

    print(json.dumps(res, ensure_ascii=False, indent=1))
    (HERE / "probe_wallclock_jitter.stdout.txt").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
