# -*- coding: utf-8 -*-
"""§543 全量口径（子目录 + 根目录）：窗分类 / fps 分档 / 计分屏证据 / 独立指纹。

本件是 §543 的权威口径（§543 首版漏了根目录层级，已勘误）。
只读 measure_w*.json 与 measure_w*_end_*.png。零真机。
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


def trip_of(path):
    d = os.path.dirname(path)
    return os.path.basename(d) if os.path.basename(d) != os.path.basename(BASE) else "<root>"


# ---------- 1. 全量 json ----------
wins = []
paths = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json"))) + \
        sorted(glob.glob(os.path.join(BASE, "measure_w*.json")))
for p in paths:
    try:
        j = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    ed = j.get("frame_edges") or []
    if not ed:
        continue
    f0, f1 = ed[0][0], ed[-1][0]
    wins.append(dict(trip=trip_of(p), tid=j.get("trip_id"), w=j.get("window"),
                     f0=f0, f1=f1, df=f1 - f0, span=j.get("span_s") or 0.0,
                     dur=ed[-1][1] - ed[0][1],
                     fps=(j.get("stats") or {}).get("fps_avg"),
                     stall=(j.get("stats") or {}).get("max_stall_s"),
                     verd=j.get("verdict"),
                     png=os.path.join(os.path.dirname(p), "measure_w%d_end_x.png" % j.get("window"))))

print("=== 1. 全量窗分类（%d 窗，%d 趟，含 <root>）===" % (len(wins), len({w["trip"] for w in wins})))
adv = [w for w in wins if w["df"] > 0]
frz = [w for w in wins if w["df"] == 0 and w["f0"] != 0]
lz = [w for w in wins if w["df"] == 0 and w["f0"] == 0]
neg = [w for w in wins if w["df"] < 0]
print("  有推进 df>0        : %3d" % len(adv))
print("  冻结 df==0 & f0!=0 : %3d" % len(frz))
print("  加载段 df==0 & f0==0: %3d" % len(lz))
print("  帧号回退 df<0      : %3d" % len(neg))
print("  合计               : %3d" % (len(adv) + len(frz) + len(lz) + len(neg)))
print()

# ---------- 2. 有推进窗 fps 分档 ----------
print("=== 2. 有推进窗按 fps_avg 分档（目标① 数据面）===")
hi = [w for w in adv if (w["fps"] or 0) >= 28]
lo = [w for w in adv if (w["fps"] or 0) < 28]
nodef = [w for w in adv if w["fps"] is None]
print("  fps_avg >= 28（贴 31 帽，健康）: %d" % len(hi))
print("  fps_avg <  28（慢/卡）        : %d" % len(lo))
print("  fps_avg 为 None（有推进但无统计）: %d" % len(nodef))
print()
print("  == fps<28 明细（目标① 候选样本）==")
print("  %-20s %3s %6s %8s %8s %8s" % ("trip", "w", "df", "fps_avg", "dur", "max_stall"))
for w in sorted(lo, key=lambda x: (x["fps"] if x["fps"] is not None else 99)):
    print("  %-20s %3s %6d %8.2f %8.2f %8.2f" % (
        w["trip"], w["w"], w["df"], w["fps"] or -1, w["dur"], w["stall"] or -1))
print()
print("  == fps 为 None 明细 ==")
for w in nodef:
    print("  %-20s w%s df=%d dur=%.2f verdict=%s" % (w["trip"], w["w"], w["df"], w["dur"], w["verd"]))
print()

# ---------- 3. 计分屏证据 ----------
print("=== 3. 末截图全量（子目录 + 根目录）===")
print("  %-20s %3s %6s %7s %-18s %s" % ("trip", "w", "df", "p", "pixhash", "判读"))
pnghashes = {}
rows = []
seen_png = set()
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png"))) + \
         sorted(glob.glob(os.path.join(BASE, "measure_w*_end_*.png"))):
    if p in seen_png:
        continue
    seen_png.add(p)
    im = Image.open(p)
    im.load()
    pv = panel_p(im)
    ph = hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()[:16]
    pnghashes.setdefault(ph, []).append(os.path.basename(os.path.dirname(p)) + "/" + os.path.basename(p))
    rows.append((trip_of(p), os.path.basename(p), pv, ph))
    # 关联 df
    wn = p.split("measure_w")[-1].split("_")[0]
    dfv = next((w["df"] for w in wins if w["trip"] == trip_of(p) and str(w["w"]) == wn), None)
    verdict = "计分屏(待目视)" if pv >= 0.30 else ("无面板" if pv >= 0.02 else "非游戏画面")
    print("  %-20s %3s %6s %7.3f %-18s %s" % (trip_of(p), wn, dfv, pv, ph, verdict))

print()
print("  唯一整幅指纹: %d / %d" % (len(pnghashes), len(rows)))
dups = {k: v for k, v in pnghashes.items() if len(v) > 1}
print("  重复组:")
for k, v in dups.items():
    print("    %s (%d): %s" % (k, len(v), v))
print()
print("  p>=0.30 张数: %d / %d" % (sum(1 for _, _, pv, _ in rows if pv >= 0.30), len(rows)))

# ---------- 4. 冻结窗与证据的对应 ----------
print()
print("=== 4. %d 个 f0!=0 的 df==0 窗：有无计分屏证据 ===" % len(frz))
have = 0
missing = []
for w in frz:
    p = os.path.join(os.path.dirname(w["png"]), os.path.basename(w["png"]))
    ok = os.path.exists(p)
    if ok:
        im = Image.open(p)
        im.load()
        pv = panel_p(im)
        if pv >= 0.30:
            have += 1
            continue
    missing.append((w["trip"], w["w"], w["f0"], w["df"], w["png"] if ok else "无截图"))
print("  有计分屏证据: %d / %d" % (have, len(frz)))
print("  无证据（须挂账）:")
for m in missing:
    print("    %-20s w%s f0=%s df=%s -> %s" % m)
