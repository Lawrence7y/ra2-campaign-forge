# -*- coding: utf-8 -*-
"""V3 独立复算 #6：
 (A) 6 个「无末截图」的冻结窗，其所属趟的任何 PNG 是否命中计分屏签名。
 (B) S543 声称 38 慢窗「含 v4-b 的 2.9fps 慢爬」——逐条核对 v4-b 在不在 38 里。
 (C) 38 慢窗与「本趟已证明终局」的重叠度；38 里有多少其实是「长停拖低均值」。
"""
import collections
import glob
import hashlib
import json
import os

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
X0, X1 = 85, 630
Y0, Y1 = 100, 290
SIG_ROWS = list(range(100, 290))


def load(p):
    try:
        im = Image.open(p).convert("RGB")
    except Exception:
        return None
    return im if im.size == (800, 600) else None


def rows(im):
    return [hashlib.sha256(im.crop((X0, y, X1, y + 1)).tobytes()).hexdigest()
            for y in range(Y0, Y1)]


# 参考：archive_T34/w1 与 archive_T40/w1 已目视确认是计分屏
ref = {}
for t, n in [("archive_T34", "measure_w1_end_x.png"),
             ("archive_T40", "measure_w1_end_x.png")]:
    im = load(os.path.join(BASE, t, n))
    rr = rows(im)
    ref[(t, n)] = rr


def class_of(im):
    if im is None:
        return None
    rr = rows(im)
    out = []
    for k, v in ref.items():
        m = sum(1 for a, b in zip(rr, v) if a == b)
        out.append("%s:%d/%d" % (k[0], m, len(v)))
    return out


print("=== (A) 无末截图的 6 个冻结窗所属趟：其它 PNG 的计分屏同带行数 ===")
for t in ["archive_T32", "archive_T47", "l1_20261023", "l1_20261023b"]:
    d = os.path.join(BASE, t)
    if not os.path.isdir(d):
        print("  %s  -- 目录不存在" % t)
        continue
    print("  --- %s" % t)
    for p in sorted(glob.glob(os.path.join(d, "*.png"))):
        im = load(p)
        if im is None:
            continue
        rr = rows(im)
        best = 0
        for k, v in ref.items():
            best = max(best, sum(1 for a, b in zip(rr, v) if a == b))
        print("      %-42s 同带行 %3d/%d" % (os.path.basename(p), best, len(rr)))

print()
print("=== (B) v4-b 是否落在 38 慢窗里 ===")
wins = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json"))):
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    trip = os.path.basename(os.path.dirname(p))
    if not ed:
        if "v4b" in trip:
            print("  %s w%s : frame_edges 为空 -> 不进任何分类" % (trip, j.get("window")))
        continue
    st = j.get("stats") or {}
    wins.append(dict(trip=trip, w=j.get("window"), f0=ed[0][0], df=ed[-1][0] - ed[0][0],
                     st=st, span=j.get("span_s") or 25.0))
for x in wins:
    if "v4b" in x["trip"]:
        print("  v4b 有边的窗: %s w%s df=%s fps_avg=%s" % (
            x["trip"], x["w"], x["df"], x["st"].get("fps_avg")))
adv = [x for x in wins if x["df"] > 0]
slow = [x for x in adv if (x["st"].get("fps_avg") or 0) < 28]
print("  df>0 %d, 其中 fps_avg<28 -> %d" % (len(adv), len(slow)))
print("  ★ 38 慢窗里 trip 含 'v4b' 者：%s" % [x["trip"] for x in slow if "v4b" in x["trip"]])

print()
print("=== (C) 38 慢窗的形态构成 ===")
cliff = [x for x in slow if (x["st"].get("max_stall_s") or 0) / x["span"] >= 0.50]
crawl = [x for x in slow if (x["st"].get("max_stall_s") or 0) / x["span"] < 0.50]
print("  单段停摆 >= 50%% 窗长（=一个长停拖垮均值，形态同冻结窗）: %d" % len(cliff))
print("  其余（无长单段停，形态接近真慢爬）: %d" % len(crawl))
print()
print("  真慢爬侧明细：")
for x in sorted(crawl, key=lambda y: y["st"].get("fps_avg") or 0):
    print("    %-18s w%-1s df=%-5d fps_avg=%-6.2f p50=%-6.2f stall=%-6.3f span=%.0f" % (
        x["trip"], x["w"], x["df"], x["st"].get("fps_avg") or -1,
        x["st"].get("fps_p50") or -1, x["st"].get("max_stall_s") or -1, x["span"]))
print()
# 38 里有多少属于「本趟已有计分屏证据」的趟
score_trips = {"archive_T33", "archive_T34", "archive_T36", "archive_T38", "archive_T39",
               "archive_T40", "archive_T41", "archive_T43", "archive_T44", "archive_T45",
               "archive_T49_u0800", "l3_20261023r"}
ins = [x for x in slow if x["trip"] in score_trips]
print("  ★ 38 慢窗中，属于「本趟已出现计分屏末截图」的趟者：%d / %d -> %s" % (
    len(ins), len(slow), sorted(set(x["trip"] + "/w%d" % x["w"] for x in ins))))
print("  ★ 其中长停型(cliff) 又占 %d 个" % len([x for x in ins if x in cliff]))
