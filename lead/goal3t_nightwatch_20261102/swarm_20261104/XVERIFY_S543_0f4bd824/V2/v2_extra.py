# -*- coding: utf-8 -*-
"""V2 补充核对：健康档成色 / 「全程最慢」说法 / 冻结窗的截图可得性 / 重复指纹组的跨趟性。

路径一律由 measure json 的目录 + 固定窗号拼出，不从文件名反解路径成分。
"""
import glob
import hashlib
import json
import os

BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
SUB = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))

rows = []
for p in SUB:
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    if not ed:
        continue
    d = os.path.basename(os.path.dirname(p))
    st = j.get("stats") or {}
    f0, f1 = ed[0][0], ed[-1][0]
    rows.append(dict(dir=d, w=int(j.get("window")), f0=f0, df=f1 - f0, st=st, j=j, p=p,
                     dirdir=os.path.dirname(p)))

adv = [r for r in rows if r["df"] > 0]
hi = [r for r in adv if (r["st"].get("fps_avg") or 0) >= 28]
print("### D. 「fps_avg>=28 = 健康」这 25 窗的成色")
print("  n=%d ；其中 max_stall_s>=1.0s 的：%d" % (len(hi), sum(1 for r in hi if (r["st"].get("max_stall_s") or 0) >= 1.0)))
for r in sorted(hi, key=lambda x: -(x["st"].get("max_stall_s") or 0))[:8]:
    print("    %-20s w%s fps=%6.3f max_stall=%7.3f tick_miss=%s n_multi=%s" %
          (r["dir"], r["w"], r["st"]["fps_avg"], r["st"].get("max_stall_s") or 0,
           r["st"].get("tick_miss"), r["st"].get("n_multi_advance")))
print("  fps_avg 范围: %.3f .. %.3f" % (min(r["st"]["fps_avg"] for r in hi), max(r["st"]["fps_avg"] for r in hi)))
print()

print("### E. §543 称 l3_20261023r「是全程最慢的一趟」——按 stats.fps_avg 核对")
lr = [r for r in adv if r["st"].get("fps_avg") is not None]
target = [r for r in adv if r["dir"] == "l3_20261023r" and r["w"] == 1]
tv = target[0]["st"]["fps_avg"]
slower = [r for r in lr if r["st"]["fps_avg"] < tv]
print("  l3_20261023r w1 fps_avg = %.3f" % tv)
print("  全部 %d 个有推进窗中 fps_avg 低于它的：%d 个" % (len(lr), len(slower)))
for r in sorted(slower, key=lambda x: x["st"]["fps_avg"])[:12]:
    print("    %-20s w%s fps=%8.3f" % (r["dir"], r["w"], r["st"]["fps_avg"]))
mn = min(lr, key=lambda x: x["st"]["fps_avg"])
print("  真正最低的窗: %s w%d fps_avg=%.3f" % (mn["dir"], mn["w"], mn["st"]["fps_avg"]))
per_trip_min = {}
for r in lr:
    per_trip_min[r["dir"]] = min(per_trip_min.get(r["dir"], 9e9), r["st"]["fps_avg"])
rank = sorted(per_trip_min.items(), key=lambda x: x[1])
names = [k for k, v in rank]
print("  按「该趟最慢窗」升序排序，l3_20261023r 的名次 = %d / %d" %
      (names.index("l3_20261023r") + 1 if "l3_20261023r" in names else -1, len(rank)))
for k, v in rank[:8]:
    print("    %-20s %8.3f" % (k, v))
print("  l3_20261023r 全部窗：%s" % json.dumps(
    [(r["w"], r["df"], r["st"].get("fps_avg"), r["st"].get("max_stall_s"))
     for r in rows if r["dir"] == "l3_20261023r"]))
print()

print("### F. 29 个冻结窗的「窗末截图可得性」（文件存在 + harness 自记 empty_window）")
frz = [r for r in rows if r["df"] == 0 and r["f0"] != 0]
have = 0
for r in sorted(frz, key=lambda x: (x["dir"], x["w"])):
    png = os.path.join(r["dirdir"], "measure_w%d_end_x.png" % r["w"])
    ex = os.path.exists(png)
    fields = os.path.join(r["dirdir"], "qc151_fields.json")
    rec = None
    if os.path.exists(fields):
        try:
            jj = json.load(open(fields, encoding="utf-8"))
            for x in jj:
                if isinstance(x, dict) and "空窗另存" in str(x.get("note", "")):
                    v = x.get("value") or {}
                    if v.get("window") == r["w"]:
                        rec = (v.get("empty_window"), v.get("current_frame"))
        except Exception:
            rec = "fields_unreadable"
    tag = ""
    if ex and rec and rec[0] is False:
        tag = "★★ 文件存在但 harness 记 empty_window=False ⇒ 该文件不该存在"
    elif ex and rec is None:
        tag = "文件存在，但该趟 fields 无 QC208-2 取证记录"
    elif not ex:
        tag = "无截图"
    if ex:
        have += 1
    print("  %-20s w%s f=%-5s png=%-5s harness_empty_window=%s %s" %
          (r["dir"], r["w"], r["f0"], ex, rec, tag))
print("  有 PNG 的冻结窗 = %d / %d ；无 PNG = %d" % (have, len(frz), len(frz) - have))
print()

print("### G. 字节级重复组：同组内的趟 / map / 冻结帧号")
groups = {}
for r in rows:
    png = os.path.join(r["dirdir"], "measure_w%d_end_x.png" % r["w"])
    if not os.path.exists(png):
        continue
    h = hashlib.sha256(open(png, "rb").read()).hexdigest()[:8]
    groups.setdefault(h, []).append((png, r))
for h, v in groups.items():
    if len(v) < 2:
        continue
    print("  组 %s (%d 张)" % (h, len(v)))
    for png, r in v:
        print("     %-14s w%s trip_id=%-30s map=%s f=%s->%s df=%s 大小=%d mtime=%.0f" %
              (r["dir"], r["w"], r["j"].get("trip_id"), (r["j"].get("map_sha256") or "")[:8],
               r["f0"], r["f0"] + r["df"], r["df"], os.path.getsize(png), os.path.getmtime(png)))
print()
print("  同组内 map 是否相同（不同 map 出同一张图 ⇒ 该图与地形无关）：")
for h, v in groups.items():
    if len(v) < 2:
        continue
    maps = {(r["j"].get("map_sha256") or "")[:8] for _, r in v}
    trips = {r["dir"] for _, r in v}
    print("     组 %s: 张数=%d 趟=%s map=%s ⇒ map 全同? %s" %
          (h, len(v), sorted(trips), sorted(maps), len(maps) == 1))
