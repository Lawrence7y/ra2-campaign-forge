# -*- coding: utf-8 -*-
"""V1 补充2：零推进窗普查（对齐 §543 的 29）、窗口分层、以及「跨会话/跨负载」对照是否被口径混淆。"""
import collections
import glob
import json
import os

TRIP = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
files = sorted(glob.glob(os.path.join(TRIP, "*", "measure_w*.json")))
files += sorted(glob.glob(os.path.join(TRIP, "measure_w*.json")))

root_level = [p for p in files if os.path.dirname(p) == TRIP]
print("total=%d  root-level(trip 直下)=%d  subdir=%d" % (len(files), len(root_level), len(files) - len(root_level)))
print("root-level files:", [os.path.basename(p) + "/" + json.load(open(p, encoding="utf-8"))["trip_id"] for p in root_level])

zero = []
for p in files:
    d = json.load(open(p, encoding="utf-8"))
    st = d["stats"]
    if st.get("fps_avg") is None:
        t = d["samples"]["t"]
        zero.append((os.path.relpath(p, TRIP).replace("\\", "/"), st.get("note"),
                     (t[-1] - t[0]) if len(t) >= 2 else None, d.get("span_s"),
                     len(d.get("frame_edges") or []), d.get("trip_id"), d.get("verdict")))
print("\n=== 零推进/不可测窗 普查: %d ===" % len(zero))
c = collections.Counter((z[1], round(z[2], 1) if z[2] is not None else None) for z in zero)
for k, v in sorted(c.items(), key=lambda x: str(x[0])):
    print("   note=%-28s span≈%-6s  n=%d" % (k[0], k[1], v))
n25 = [z for z in zero if z[1] == "frame not advancing" and z[2] is not None and z[2] > 20]
print("   → 「frame not advancing」且 span>20s 的窗: %d  （§543 曾报 29）" % len(n25))
for z in n25:
    print("      ", z[0], z[5], z[6])
print("   → span==4s 短窗的零推进: %d" % sum(1 for z in zero if z[2] is not None and z[2] < 5))

print("\n=== 「同负载跨时段」原始对照（不做因果解释，只列口径可混性） ===")
import datetime
groups = collections.defaultdict(list)
for p in files:
    d = json.load(open(p, encoding="utf-8"))
    st = d["stats"]
    if st.get("fps_avg") is None:
        continue
    t = d["samples"]["t"]
    ej = d.get("frame_edges") or []
    live_s = (ej[-1][1] - ej[0][1]) if len(ej) >= 2 else None
    tail = (t[-1] - ej[-1][1]) if ej else None
    groups[d["trip_id"]].append((os.path.relpath(p, TRIP).replace("\\", "/"),
                                 d["gate"].get("units0"), st["fps_avg"], st.get("fps_p50"),
                                 live_s, tail,
                                 datetime.datetime.fromtimestamp(d["t_abs0"]).strftime("%m-%d %H:%M"),
                                 (d.get("map_sha256") or "")[:8], (d.get("gamemd_sha256") or "")[:8],
                                 d.get("schema")))
for trip in sorted(groups):
    for g in sorted(groups[trip], key=lambda x: x[0]):
        print("  %-32s u0=%-5s avg=%6.2f p50=%6s live_s=%7s tail=%6s %s map=%s gm=%s %s" %
              (trip, g[1], g[2], ("%.2f" % g[3]) if g[3] else "None",
               ("%.2f" % g[4]) if g[4] else "None", ("%.2f" % g[5]) if g[5] is not None else "None",
               g[6], g[7], g[8], g[9]))

print("\n=== units0 相近但 fps 差 >2× 的跨趟对照（列活段长度，看是否可比） ===")
flat = [(trip, g) for trip in sorted(groups) for g in groups[trip]]
for i in range(len(flat)):
    for j in range(i + 1, len(flat)):
        (t1, a), (t2, b) = flat[i], flat[j]
        if t1 == t2 or a[1] is None or b[1] is None:
            continue
        if abs(a[1] - b[1]) > 120:
            continue
        hi, lo = max(a[2], b[2]), min(a[2], b[2])
        if lo > 0 and hi / lo >= 2.0:
            print("  %-30s u=%5d avg=%6.2f p50=%6s live_s=%6s tail=%6s %s" % (a[0], a[1], a[2], ("%.1f" % a[3]) if a[3] else "None", ("%.2f" % a[4]) if a[4] else "None", ("%.2f" % a[5]) if a[5] is not None else "None", t1))
            print("  %-30s u=%5d avg=%6.2f p50=%6s live_s=%6s tail=%6s %s  → ratio %.2f" % (b[0], b[1], b[2], ("%.1f" % b[3]) if b[3] else "None", ("%.2f" % b[4]) if b[4] else "None", ("%.2f" % b[5]) if b[5] is not None else "None", t2, hi / lo))
