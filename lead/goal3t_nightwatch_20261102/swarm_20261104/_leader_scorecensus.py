# -*- coding: utf-8 -*-
"""§542 汇总普查：窗分类 + 屏幕计时器对账 + 面板判据三者合一。

只读 measure_w*.json 与 measure_w*_end_*.png。零真机。

输出三块：
  A. 全窗分类（有推进 / 冻结 / 加载段冻结），给出健康窗占比
  B. 有截图窗的「面板判据 p」与「屏幕计时器隐含 fps」
  C. 判据阈值分离度（战斗帧对照 vs 冻结窗末）
"""
import glob
import hashlib
import json
import os

from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
PANEL = (85, 108, 630, 275)


def panel_p(im):
    c = im.convert("RGB").crop(PANEL)
    px = list(c.getdata())
    n = len(px)
    hit = sum(1 for r, g, b in px if b > r + 18 and b > g + 10 and 40 <= b <= 190 and r < 150)
    return hit / n if n else 0.0


# ---------- A ----------
wins = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json"))):
    try:
        j = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    ed = j.get("frame_edges") or []
    if not ed:
        continue
    trip = os.path.basename(os.path.dirname(p))
    f0, f1 = ed[0][0], ed[-1][0]
    wins.append(dict(trip=trip, w=j.get("window"), f0=f0, f1=f1, df=f1 - f0,
                     span=j.get("span_s") or 0.0,
                     dur=(ed[-1][1] - ed[0][1]),
                     fpsavg=(j.get("stats") or {}).get("fps_avg"),
                     png=os.path.join(os.path.dirname(p), "measure_w%d_end_x.png" % j.get("window"))))

adv = [w for w in wins if w["df"] > 0]
frz = [w for w in wins if w["df"] == 0 and w["f0"] != 0]
loadfrz = [w for w in wins if w["df"] == 0 and w["f0"] == 0]
neg = [w for w in wins if w["df"] < 0]

print("=== A. 全窗分类（共 %d 窗，%d 趟）===" % (len(wins), len({w["trip"] for w in wins})))
print("  有推进      : %3d" % len(adv))
print("  冻结(f0!=0) : %3d  <- §538 称之为「战斗段完全冻结」" % len(frz))
print("  加载段冻结  : %3d" % len(loadfrz))
print("  帧号回退    : %3d" % len(neg))
print()
healthy = [w for w in adv if (w["fpsavg"] or 0) >= 28]
print("  有推进窗中 fps_avg>=28（贴 31 帽）: %d / %d" % (len(healthy), len(adv)))
print()

# ---------- B ----------
print("=== B. 有末截图的窗：面板判据 p + 截图指纹 ===")
print("%-20s %3s %6s %7s %8s %6s %s" % ("trip", "w", "df", "p", "pixgrp", "dur", "判读"))
groups = {}
rows = []
for w in wins:
    png = w["png"]
    if not os.path.exists(png):
        continue
    try:
        im = Image.open(png)
        im.load()
    except Exception:
        continue
    p = panel_p(im)
    ph = hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()[:8]
    groups.setdefault(ph, []).append("%s/w%s" % (w["trip"], w["w"]))
    rows.append((w, p, ph))

for w, p, ph in rows:
    verdict = "计分屏" if p >= 0.30 else ("无面板" if p >= 0.02 else "非游戏画面")
    print("%-20s %3s %6d %7.3f %8s %6.2f %s" % (w["trip"], w["w"], w["df"], p, ph, w["dur"], verdict))

print()
print("=== B2. 截图指纹重复组（同组=逐像素相同，非同一次采集）===")
for ph, v in groups.items():
    if len(v) > 1:
        print("  %s (%d): %s" % (ph, len(v), v))
print()
uniq = len(groups)
print("  唯一整幅指纹 %d / %d 张" % (uniq, len(rows)))
n_score = sum(1 for _, p, _ in rows if p >= 0.30)
print("  计分屏判定 %d / %d 张" % (n_score, len(rows)))

# ---------- C ----------
print()
print("=== C. 判据分离度对照（战斗帧 vs 冻结窗末）===")
ctrls = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "frame_target_01.png"))):
    try:
        im = Image.open(p)
        im.load()
    except Exception:
        continue
    ctrls.append((os.path.basename(os.path.dirname(p)), panel_p(im)))
for t, p in ctrls[:10]:
    print("  战斗帧 %-18s p=%.3f" % (t, p))
if ctrls:
    vals = sorted(p for _, p in ctrls)
    print("  战斗帧 p 范围: %.3f .. %.3f (n=%d)" % (vals[0], vals[-1], len(vals)))
if rows:
    vals = sorted(p for _, p, _ in rows)
    print("  冻结窗末 p 范围: %.3f .. %.3f (n=%d)" % (vals[0], vals[-1], len(rows)))
    print("  ★ 已知最低「计分屏」p=0.347，已知最高「战斗帧」p=%.3f ⇒ 间隔 %.3f" % (
        max(p for _, p in ctrls) if ctrls else -1,
        0.347 - (max(p for _, p in ctrls) if ctrls else 0)))
