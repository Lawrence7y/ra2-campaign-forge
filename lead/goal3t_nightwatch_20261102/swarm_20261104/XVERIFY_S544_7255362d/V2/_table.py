# -*- coding: utf-8 -*-
"""V2 时代效应核验：窗口级表 + 按 units0 分组 + 快慢对照。

数据源：本目录 census.csv（由 _census.py 从原始 measure_w*.json 逐份重算）。
只取 mirror 基（lead 下的 4 个目录经 _dupcheck.py 证明为逐字节重复件）。
"""
import csv
import os
from collections import defaultdict, Counter

OUT = os.path.dirname(os.path.abspath(__file__))


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


rows = []
with open(os.path.join(OUT, "census.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["base_tag"] != "mirror":
            continue
        rows.append(r)

# 补一个可用于排序的时间：fields_ts_first，若无则用 dir_mtime -> UTC 字符串
import datetime


def ts_of(r):
    if r["fields_ts_first"]:
        return r["fields_ts_first"]
    m = f(r["dir_mtime"])
    if m:
        # 本地时间 = UTC+8
        dt = datetime.datetime.utcfromtimestamp(m) + datetime.timedelta(hours=8)
        return dt.isoformat(timespec="seconds") + "+08:00*"
    return "?"


for r in rows:
    r["ts"] = ts_of(r)
    r["live"] = f(r["live_fps"])
    r["units0"] = f(r["units0"])
    r["pre"] = f(r["pre_fps15"])
    r["fps_avg"] = f(r["fps_avg_json"])
    r["fps_p50"] = f(r["fps_p50_json"])

print("=== 全部 mirror 窗 %d 个（含 lead 重复件则 115，已剔除）===" % len(rows))
print("有 frame_edges>=2 且 live 可算：%d" % sum(1 for r in rows if r["live"] is not None))
print("units0 非空：%d" % sum(1 for r in rows if r["units0"] is not None))
print("units0 非空 且 live 可算：%d" % sum(1 for r in rows if r["units0"] is not None and r["live"] is not None))

def harness_label(r):
    """harness_sha16 缺时退回 argv 里的脚本名，再退 UNKNOWN。"""
    if r["harness_sha16"]:
        return r["harness_sha16"]
    ap = r["argv_harness"] or r["harness_path"]
    if ap:
        return "name:" + os.path.basename(ap)
    return "UNKNOWN"


print("\n=== 窗口全表（按时间排序）===")
hdr = "%-20s %-14s %2s %7s %8s %8s %8s %8s %-18s %-18s %s"
print(hdr % ("ts", "dir", "w", "units0", "pre15", "fps_avg", "fps_p50", "live_fps", "harness", "map16", "trip_id"))
for r in sorted(rows, key=lambda x: x["ts"]):
    live = "  n/a" if r["live"] is None else "%7.2f" % r["live"]
    r["harness"] = harness_label(r)
    print(hdr % (
        r["ts"][:19], r["dir"][:20], r["window"],
        "-" if r["units0"] is None else "%7.0f" % r["units0"],
        "-" if r["pre"] is None else "%8.3f" % r["pre"],
        "-" if r["fps_avg"] is None else "%8.3f" % r["fps_avg"],
        "-" if r["fps_p50"] is None else "%8.3f" % r["fps_p50"],
        live, (r["harness"] or "-")[:18], (r["map_sha256"] or "-")[:18],
        (r["trip_id"] or "-")[:34]))

# ---- 按 units0 分组（精确值）----
print("\n=== 按 units0 精确分组，出现 >=3 次的档 ===")
g = defaultdict(list)
for r in rows:
    if r["units0"] is not None and r["live"] is not None:
        g[int(r["units0"])].append(r)
for u in sorted(g):
    if len(g[u]) >= 3:
        lives = [x["live"] for x in g[u]]
        print("units0=%d  n=%d  live_fps %.2f..%.2f (ratio %.2fx)" % (
            u, len(lives), min(lives), max(lives), max(lives) / min(lives)))
        for x in sorted(g[u], key=lambda y: y["ts"]):
            print("    %-19s %-14s w%s live=%6.2f pre15=%7.3f fps_avg=%7.3f harness=%-16s map=%s" % (
                x["ts"][:19], x["dir"], x["window"], x["live"], x["pre"] or float("nan"),
                x["fps_avg"] or float("nan"), harness_label(x)[:16],
                (x["map_sha256"] or "-")[:12]))

# ---- 关键对照：units0 1180..1360 ----
print("\n=== 关键对照带 units0 ∈ [1180,1360]（live 可算）===")
band = [r for r in rows if r["units0"] is not None and 1180 <= r["units0"] <= 1360]
print("该带窗数 = %d（其中 live 可算 %d）" % (len(band), sum(1 for r in band if r["live"] is not None)))
for r in sorted(band, key=lambda x: x["ts"]):
    print("  %-19s %-14s w%s units0=%4.0f pre15=%7.3f live=%s fps_avg=%7.3f fps_p50=%7.3f ne=%s harness=%-16s map=%s gamemd=%s" % (
        r["ts"][:19], r["dir"], r["window"], r["units0"], r["pre"] or float("nan"),
        "  n/a" if r["live"] is None else "%6.2f" % r["live"],
        r["fps_avg"] or float("nan"), r["fps_p50"] or float("nan"), r["n_edges"],
        (r["harness_sha16"] or "-")[:16], (r["map_sha256"] or "-")[:12],
        (r["gamemd_sha256"] or "-")[:12]))

# ---- 全部 units0 ∈ [1180,1360] 但 df==0 / 无 edges 的也列出来（含 verdict）
print("\n=== 同带不可算窗明细（df/edges/verdict）===")
for r in sorted(band, key=lambda x: x["ts"]):
    if r["live"] is None:
        print("  %-19s %-14s w%s units0=%4.0f n_edges=%s df=%s verdict=%s f0=%s f1=%s" % (
            r["ts"][:19], r["dir"], r["window"], r["units0"], r["n_edges"], r["df"],
            r["verdict"], r["f0"], r["f1"]))
