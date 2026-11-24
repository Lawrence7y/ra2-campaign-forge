# -*- coding: utf-8 -*-
"""V3 独立复算 #12：三件收尾核对。

 (1) D-13 相关：把「停滞段」按 §538 的两种人口分开——
     A 人口 = 窗内段间空隙（df>0 的窗），B 人口 = 整窗冻结窗。
     若 N=1.0s 触发器只在 A 人口上还有意义，D-13 的采点前提就能保住；
     若 A 人口里几乎没有 >=1s 的空隙，则「停滞段内采栈」在慢窗上也基本打不着。
 (2) §536 的行为学前提「帧号严格 +1 推进、不丢帧」在全量窗上是否成立。
 (3) archive_T42 三窗结构 + 那张无表图片到底是开局简报还是终局结算。
"""
import collections
import glob
import hashlib
import json
import os
import time

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")

wins = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json"))):
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    if not ed:
        continue
    wins.append(dict(trip=os.path.basename(os.path.dirname(p)), w=j.get("window"),
                     ed=ed, j=j, st=j.get("stats") or {},
                     span=j.get("span_s") or 25.0))

print("=" * 90)
print("(1) 窗内「段间空隙」普查（只统计 df>0 的窗，即 S543 新口径的目标①数据面）")
print("=" * 90)
adv = [x for x in wins if x["ed"][-1][0] - x["ed"][0][0] > 0]
gaps = []
for x in adv:
    e = x["ed"]
    for i in range(1, len(e)):
        dt = e[i][1] - e[i - 1][1]
        if dt > 0:
            gaps.append((dt, x["trip"], x["w"]))
buckets = collections.Counter()
for dt, _, _ in gaps:
    if dt < 0.1:
        buckets["<0.1s"] += 1
    elif dt < 0.2:
        buckets["0.1-0.2s"] += 1
    elif dt < 0.5:
        buckets["0.2-0.5s"] += 1
    elif dt < 1.0:
        buckets["0.5-1.0s"] += 1
    elif dt < 2.0:
        buckets["1.0-2.0s"] += 1
    elif dt < 5.0:
        buckets["2-5s"] += 1
    else:
        buckets[">=5s"] += 1
print("  df>0 窗数 %d，窗内空隙总数 %d" % (len(adv), len(gaps)))
for k in ["<0.1s", "0.1-0.2s", "0.2-0.5s", "0.5-1.0s", "1.0-2.0s", "2-5s", ">=5s"]:
    print("    %-9s %6d  (%.2f%%)" % (k, buckets[k], 100.0 * buckets[k] / max(len(gaps), 1)))
ge1 = [g for g in gaps if g[0] >= 1.0]
print("  ★ N=1.0s 触发器在 df>0 窗内可命中的空隙数：%d（占 %.2f%%）" % (
    len(ge1), 100.0 * len(ge1) / max(len(gaps), 1)))
for dt, t, w in sorted(ge1, reverse=True)[:15]:
    print("      %.3fs  %s/w%s" % (dt, t, w))
print()
frozen = [x for x in wins if x["ed"][-1][0] == x["ed"][0][0] and x["ed"][0][0] != 0]
print("  整窗冻结窗（§538 的 29）: %d —— 这些窗每窗只贡献 1 个「整窗空隙」，"
      "与上面的人口是**两回事**" % len(frozen))

print()
print("=" * 90)
print("(2) 帧号是否严格 +1 推进（§536/§535 的行为学前提 n_multi_advance）")
print("=" * 90)
c = collections.Counter()
bad = []
for x in wins:
    v = x["st"].get("n_multi_advance")
    c[v] += 1
    if v:
        ed = x["ed"]
        steps = collections.Counter(ed[i][0] - ed[i - 1][0] for i in range(1, len(ed)))
        bad.append((x["trip"], x["w"], v, dict(steps)))
print("  n_multi_advance 取值分布: %s" % dict(c))
for t, w, v, s in bad:
    print("      %s/w%s n_multi_advance=%d 步长分布=%s" % (t, w, v, s))
if bad:
    print("  ★ 存在一次推进多帧的窗 -> 「严格 +1 不丢帧」在全量窗上不成立")
else:
    print("  全部窗 n_multi_advance==0 -> +1 严格成立")

print()
print("=" * 90)
print("(3) archive_T42 三窗 + 「无表」那张图的定位")
print("=" * 90)
for x in [y for y in wins if y["trip"] == "archive_T42"]:
    print("  w%s f=[%d,%d] df=%d max_stall=%.3f fps_avg=%.2f units0=%s gate=%s" % (
        x["w"], x["ed"][0][0], x["ed"][-1][0], x["ed"][-1][0] - x["ed"][0][0],
        x["st"].get("max_stall_s") or -1, x["st"].get("fps_avg") or -1,
        (x["j"].get("gate") or {}).get("units0"), (x["j"].get("gate") or {}).get("ok")))
print()
# 无表那张图 = 2f5ddc60；它在 navsig_burst_04_x（开局导航段）里也出现
ref = None
for p in glob.glob(os.path.join(BASE, "archive_T42", "measure_w1_end_x.png")):
    ref = hashlib.sha256(open(p, "rb").read()).hexdigest()[:10]
where = collections.Counter()
for p in glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True):
    if os.path.getsize(p) < 2000:
        continue
    if hashlib.sha256(open(p, "rb").read()).hexdigest()[:10] == ref:
        where[collections.Counter([os.path.basename(p).split("_")[0] + "_" +
                                   os.path.basename(p).split("_")[1]])] += 1
hits = []
for p in glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True):
    if os.path.getsize(p) < 2000:
        continue
    if hashlib.sha256(open(p, "rb").read()).hexdigest()[:10] == ref:
        hits.append(os.path.relpath(p, BASE))
print("  同一张「无表」图（sha %s）在仓内出现在：" % ref)
for h in sorted(hits):
    print("      " + h)
print("  ⇒ 它同时出现在 **开局导航段 navsig_*** 与 **窗末 measure_*** ——")
print("    同图既可能是开局简报、也可能是终局无表画面，单张图无法定向。")
