# -*- coding: utf-8 -*-
"""独立复核 RC：从原始 measure_w*.json 重建普查，不读 V2/census.csv。

零真机、只读。所有量自己算：
  live_fps = (frame_edges[-1][0]-frame_edges[0][0]) / (frame_edges[-1][1]-frame_edges[0][1])
  版本 = 趟目录 _launch_result.json 的 harness_sha16（+ argv[0] 文件名）
  协议 = argv 中 --h7-measure-start-frame 的后随值
  时刻 = qc151_fields.json 首条 ts；负载均值 = counters[].units / .infantry
"""
import csv
import glob
import json
import os
import statistics

ROOT = r"D:\Project\ra2-campaign-forge"
MIRROR = ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
LEAD = ROOT + r"\lead\qc161_u0400_trip"
OUT = os.path.dirname(os.path.abspath(__file__))


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def win_of(path):
    b = os.path.basename(path)
    return int(b.split("measure_w")[1].split(".json")[0])


def build(base, tag):
    files = sorted(glob.glob(os.path.join(base, "*", "measure_w*.json")))
    files += sorted(glob.glob(os.path.join(base, "measure_w*.json")))
    rows = []
    for p in files:
        d = jload(p)
        dp = os.path.dirname(p)
        rel = os.path.relpath(dp, base).replace("\\", "/") if dp != base else "."
        e = d.get("frame_edges") or []
        live = None
        if len(e) >= 2 and e[-1][1] > e[0][1]:
            live = (e[-1][0] - e[0][0]) / (e[-1][1] - e[0][1])
        gate = d.get("gate") or {}
        s = d.get("samples") or {}
        t = s.get("t") or []
        gap = sum((t[i + 1] - t[i]) for i in range(len(t) - 1) if t[i + 1] - t[i] > 0.010)
        cs = d.get("counters") or []
        def cmean(k):
            v = [c[k] for c in cs if isinstance(c.get(k), int)]
            return sum(v) / len(v) if v else None
        lr_path = os.path.join(dp, "_launch_result.json")
        sha = argv = sf = None
        if os.path.exists(lr_path):
            lr = jload(lr_path)
            sha = lr.get("harness_sha16")
            argv = lr.get("argv") or []
            argv = argv[0] if argv else None
            for i, x in enumerate(lr.get("argv") or []):
                if x == "--h7-measure-start-frame":
                    sf = (lr.get("argv") or [])[i + 1]
        ts = None
        fp = os.path.join(dp, "qc151_fields.json")
        if os.path.exists(fp):
            fd = jload(fp)
            if isinstance(fd, list):
                for x in fd:
                    if isinstance(x, dict) and isinstance(x.get("ts"), str) and x["ts"]:
                        ts = x["ts"]
                        break
        rows.append(dict(base_tag=tag, dir=rel, file=os.path.relpath(p, base).replace("\\", "/"),
                         trip_id=d.get("trip_id"), window=win_of(p), verdict=d.get("verdict"),
                         span_s=d.get("span_s"), units0=gate.get("units0"),
                         pre_fps15=gate.get("pre_fps15"), live=live,
                         map_sha256=d.get("map_sha256"), gamemd=d.get("gamemd_sha256"),
                         hz=d.get("hz"), t_clock=d.get("t_clock"), schema=d.get("schema"),
                         t_abs0=d.get("t_abs0"), ts=ts, sha16=sha, argv=argv, sf=sf,
                         gap_s=gap, c_units=cmean("units"), c_inf=cmean("infantry"),
                         n_edges=len(e), f0=e[0][0] if e else None, f1=e[-1][0] if e else None,
                         t0=e[0][1] if e else None, t1=e[-1][1] if e else None))
    return rows


rows = build(MIRROR, "mirror") + build(LEAD, "lead")
with open(os.path.join(OUT, "rc_census.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print("total rows=%d (mirror=%d lead=%d) dirs=%d trips=%d" % (
    len(rows), sum(r["base_tag"] == "mirror" for r in rows), sum(r["base_tag"] == "lead" for r in rows),
    len(set(r["dir"] for r in rows)), len(set(r["trip_id"] for r in rows))))
S = [r for r in rows if r["base_tag"] == "mirror" and r["verdict"] == "ok"
     and r["span_s"] == 25.0 and r["live"] and r["live"] > 0]
print("strict 25s ok windows=%d over trips=%d" % (len(S), len(set(r["dir"] for r in S))))
print("settle pseudo windows (span=4.0): %d  -> %s" % (
    sum(1 for r in rows if r["base_tag"] == "mirror" and r["span_s"] == 4.0),
    sorted(set(r["dir"] for r in rows if r["base_tag"] == "mirror" and r["span_s"] == 4.0))))
print("negative/zero live rows: %s" % [(r["dir"], r["window"], round(r["live"], 2) if r["live"] else None)
                                       for r in rows if r["base_tag"] == "mirror" and r["live"] is not None and r["live"] <= 0])
print("units0 distinct maps in strict=%d ; gamemd set=%s ; hz=%s ; clock=%s ; schema=%s" % (
    len(set(r["map_sha256"] for r in S)), set((r["gamemd"] or "")[:16] for r in S),
    set(r["hz"] for r in S), set(r["t_clock"] for r in S), set(r["schema"] for r in S)))
