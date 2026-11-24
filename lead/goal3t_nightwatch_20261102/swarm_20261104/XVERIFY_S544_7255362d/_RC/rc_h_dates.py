# -*- coding: utf8 -*-
"""RC-H：日期口径核实（目录名 vs fields ts vs t_abs0 vs mtime）+ 趟内负载/live 同降计数。"""
import csv, json, os, time, statistics
from collections import defaultdict

ROOT = r"D:\Project\ra2-campaign-forge"
MIRROR = ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(OUT, "rc_census.csv"), encoding="utf-8")))

print("== 1) L3 各趟日期四路核对 ==")
seen = {}
for r in rows:
    if r["base_tag"] != "mirror" or not (r["map_sha256"] or "").startswith("f3bb0a4e"):
        continue
    seen.setdefault(r["dir"], r)
for d, r in sorted(seen.items(), key=lambda x: x[1]["ts"] or ""):
    dp = os.path.join(MIRROR, d)
    files = [f for f in os.listdir(dp) if f.startswith("measure_w")]
    j = json.load(open(os.path.join(dp, files[0]), encoding="utf-8"))
    ta = j.get("t_abs0")
    abs_dt = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ta)) if ta else "-"
    mt = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(os.path.getmtime(
        os.path.join(dp, sorted(files)[-1])))) if files else "-"
    print("  %-16s fields_ts=%-20s t_abs0本地=%-20s 文件mtime=%-20s 目录名含=%s" % (
        d, (r["ts"] or "-")[:19], abs_dt, mt, "".join(ch for ch in d if ch.isdigit())[:8] or "-"))

print("\n== 2) 趟内负载 vs live 同向变化（报告 §4 称 8/9）==")
for r in rows:
    for k in ("live", "span_s", "c_units", "units0"):
        try:
            r[k] = float(r[k])
        except (TypeError, ValueError):
            r[k] = None
P3 = [r for r in rows if r["base_tag"] == "mirror" and r["verdict"] == "ok" and r["span_s"] == 25.0
      and r["live"] and r["live"] > 0 and (r["map_sha256"] or "").startswith("f3bb0a4e")]
g = defaultdict(list)
for r in P3:
    g[r["dir"]].append(r)
n_both = n_dec_load = 0
for d, rs in sorted(g.items()):
    rs.sort(key=lambda x: int(x["window"]))
    if len(rs) < 2:
        continue
    cu = [r["c_units"] for r in rs]
    lv = [r["live"] for r in rs]
    dec_load = cu[0] > cu[-1]
    n_dec_load += dec_load
    print("  %-16s c_units %s -> live %s  负载降=%s live降=%s" % (
        d, [round(x) for x in cu], [round(x, 2) for x in lv], dec_load, lv[0] > lv[-1]))
    if dec_load and lv[0] > lv[-1]:
        n_both += 1
print("  ⇒ L3 多窗趟 n=%d；负载降的趟=%d；负载与 live 同降=%d" % (len(g), n_dec_load, n_both))

print("\n== 3) 全库严格窗：趟内 c_units 首末 与 live 首末（不限图）==")
S = [r for r in rows if r["base_tag"] == "mirror" and r["verdict"] == "ok" and r["span_s"] == 25.0
     and r["live"] and r["live"] > 0 and r["c_units"]]
gg = defaultdict(list)
for r in S:
    gg[r["dir"]].append(r)
both = decli = 0
for d, rs in gg.items():
    if len(rs) < 2:
        continue
    rs.sort(key=lambda x: int(x["window"]))
    if rs[0]["c_units"] > rs[-1]["c_units"]:
        decli += 1
        if rs[0]["live"] > rs[-1]["live"]:
            both += 1
print("  多窗趟 n=%d 负载降=%d 其中 live 也降=%d" % (len([1 for rs in gg.values() if len(rs) >= 2]), decli, both))
