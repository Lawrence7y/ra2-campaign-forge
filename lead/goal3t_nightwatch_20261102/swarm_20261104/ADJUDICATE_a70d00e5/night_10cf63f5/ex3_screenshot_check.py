# -*- coding: utf-8 -*-
# 复核 EX-3 抽查 2 窗 + 残留件：截图落盘与 mtime 对齐窗尾判据（+0.05 ~ +0.20 s）
#   抽查1 archive_T33/w0（EX-3 第2行：当窗无图；后续 w1/w2 图对各自窗尾 +0.084068/+0.089937）
#   抽查2 archive_T47/w0（EX-3 第8行：后续 w1/w2 图 exists=False，但 qc151_fields.json 声明 capture_ok=true）
#   附查 archive_T38/w1（EX-3 第5行：残留件 sha256 与 T36/w1 相同、mtime Δ=-4410.949692s）
import json, hashlib
from pathlib import Path

ROOT = Path(r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")

def tail(trip, fn):
    d = json.loads((ROOT / trip / fn).read_text(encoding="utf-8-sig"))
    return d["t_abs0"] + d["span_s"], d

def forensics(trip):
    q = ROOT / trip / "qc151_fields.json"
    if not q.exists():
        return "qc151_fields.json ABSENT"
    d = json.loads(q.read_text(encoding="utf-8-sig"))
    items = d if isinstance(d, list) else [d]
    out = {}
    for it in items:
        if not isinstance(it, dict):
            continue
        for k, v in it.items():
            if "forensics" in k and isinstance(v, dict):
                out[k] = {kk: v.get(kk) for kk in ("empty_window", "forensics_png", "capture_ok", "focus_ok") if kk in v}
    return out

for trip, fn, claim in [
    ("archive_T33", "measure_w0.json", "row#2: w0 无 end png; w1/w2 png 对各自窗尾 +0.084068/+0.089937"),
    ("archive_T47", "measure_w0.json", "row#8: w1/w2 end png 不在盘; qc151_fields 声明 capture_ok=true"),
    ("archive_T38", "measure_w1.json", "row#5: w1 end png 为残留件 Δ=-4410.949692s 且与 T36/w1 同 sha"),
]:
    print("==== %s  (%s)" % (trip, claim))
    for w in (0, 1, 2):
        f = ROOT / trip / ("measure_w%d.json" % w)
        if not f.exists():
            print("  w%d: json absent" % w)
            continue
        t, d = tail(trip, f.name)
        png = ROOT / trip / ("measure_w%d_end_x.png" % w)
        if png.exists():
            delta = png.stat().st_mtime - t
            print("  w%d: tail=%.6f end_png EXISTS mtime_delta=%+.6f s" % (w, t, delta))
        else:
            print("  w%d: tail=%.6f end_png ABSENT" % (w, t))
        # 该窗窗尾 +0.05~+0.20 内的任何 png
        near = []
        for q in sorted((ROOT / trip).glob("*.png")):
            dd = q.stat().st_mtime - t
            if 0.05 <= dd <= 0.20:
                near.append((q.name, round(dd, 6)))
        print("       pngs within +0.05..+0.20 of w%d tail: %s" % (w, near))
    print("  forensics:", json.dumps(forensics(trip), ensure_ascii=False))

a = ROOT / "archive_T38/measure_w1_end_x.png"
b = ROOT / "archive_T36/measure_w1_end_x.png"
if a.exists() and b.exists():
    ha = hashlib.sha256(a.read_bytes()).hexdigest()
    hb = hashlib.sha256(b.read_bytes()).hexdigest()
    print("T38/w1 sha256=%s size=%d" % (ha, a.stat().st_size))
    print("T36/w1 sha256=%s size=%d" % (hb, b.stat().st_size))
    print("identical =", ha == hb)
