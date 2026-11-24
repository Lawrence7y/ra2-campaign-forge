# -*- coding: utf-8 -*-
"""V3 独立复算 #5：三件事一次做完。

 (1) 29 个冻结窗的「窗末取证」逐条读数：empty_window / focus_ok / fg_title /
     current_frame / forensics_png —— 与磁盘上是否真有 png 对账。
 (2) df>0 的 63 窗污染度：fps_avg<28 的 38 窗里有多少其实「几乎全程停住」
     （max_stall 接近窗长 / df 极小 / fps_p50 仍贴 31）。
 (3) 6 个无 png 的冻结窗，目录里到底有什么文件；各趟退出码。
"""
import glob
import json
import os
import time

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")


def mt(p):
    return time.strftime("%m-%d %H:%M:%S", time.localtime(os.path.getmtime(p)))


print("=" * 96)
print("(1) 29 冻结窗的 measure_forensics 读数（直接来自 harness 自己的 fields json）")
print("=" * 96)
wins = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json"))):
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    if not ed:
        continue
    wins.append(dict(trip=os.path.basename(os.path.dirname(p)), w=j.get("window"),
                     f0=ed[0][0], f1=ed[-1][0], df=ed[-1][0] - ed[0][0],
                     st=j.get("stats") or {}, dirn=os.path.dirname(p), j=j))
frozen = [w for w in wins if w["df"] == 0 and w["f0"] != 0]
print("%-20s %-3s %6s %8s %8s %10s %6s %s" % (
    "trip", "w", "df", "f0", "stall", "focus_ok", "png", "fg_title"))
n_nopng = []
nfocus = 0
for w in frozen:
    fp = os.path.join(w["dirn"], "qc151_fields.json")
    foc = pngfield = cur = fg = None
    if os.path.exists(fp):
        for r in json.load(open(fp, encoding="utf-8")):
            v = r.get("value")
            if (r.get("group") == "MEASURE" and isinstance(v, dict)
                    and "empty_window" in v and v.get("window") == w["w"]):
                foc = v.get("focus_ok")
                fg = v.get("fg_title")
                cur = v.get("current_frame")
                pngfield = v.get("forensics_png")
                if v.get("empty_window") is False:
                    pngfield = "NO(empty_window=False)"
    disk = os.path.exists(os.path.join(w["dirn"], "measure_w%d_end_x.png" % w["w"]))
    if foc is False:
        nfocus += 1
    if not disk:
        n_nopng.append("%s/w%d" % (w["trip"], w["w"]))
    print("%-20s w%-1d %6d %8d %8.2f %10s %6s %-12s rpm_frame=%s rec_png=%s" % (
        w["trip"], w["w"], w["df"], w["f0"],
        w["st"].get("max_stall_s") or -1, foc, "on" if disk else "**NONE**",
        fg, cur, pngfield))
print()
print("  冻结窗共 %d；其中 focus_ok==False 者 %d；磁盘无 png 者 %d -> %s" % (
    len(frozen), nfocus, len(n_nopng), n_nopng))

print()
print("=" * 96)
print("(2) df>0 的 63 窗：S543 的「38 个 fps_avg<28 = 目标①真正数据面」污染度")
print("=" * 96)
adv = [w for w in wins if w["df"] > 0]
slow = [w for w in adv if (w["st"].get("fps_avg") or 0) < 28]
print("  df>0 共 %d；fps_avg<28 共 %d；fps_avg>=28 共 %d" % (
    len(adv), len(slow), len(adv) - len(slow)))
print()
print("%-20s %-3s %6s %9s %9s %9s %9s %8s" % (
    "trip", "w", "df", "fps_avg", "fps_p50", "max_stall", "span", "停摆占比"))
cont = 0
for w in sorted(slow, key=lambda x: x["st"].get("fps_avg") or 0):
    st = w["st"]
    span = w["j"].get("span_s") or 25.0
    ms = st.get("max_stall_s") or 0.0
    ratio = ms / span if span else 0
    if ratio >= 0.5:
        cont += 1
    print("%-20s w%-1d %6d %9.2f %9.2f %9.3f %9.1f %7.1f%% %s" % (
        w["trip"], w["w"], w["df"], st.get("fps_avg") or -1,
        st.get("fps_p50") or -1, ms, span, 100 * ratio,
        "<< 单段停摆过半" if ratio >= 0.5 else ""))
print()
print("  ★ 38 慢窗中「最长单段停摆 >= 窗长 50%%」者 %d 个" % cont)
lo = [w for w in slow if w["df"] <= 60]
print("  ★ 38 慢窗中 df<=60（25s 窗里推进不足 60 帧，即整窗几乎没动）者 %d 个：%s" % (
    len(lo), ["%s/w%d df=%d" % (x["trip"], x["w"], x["df"]) for x in lo]))
p50hi = [w for w in slow if (w["st"].get("fps_p50") or 0) >= 28]
print("  ★ 38 慢窗中 fps_p50 仍 >=28（中位帧率健康、均值被单个长停拖低）者 %d 个" % len(p50hi))

print()
print("=" * 96)
print("(3) §539 断崖那一条（archive_T32）现场到底有什么")
print("=" * 96)
for t in ["archive_T32", "archive_T47", "l1_20261023", "l1_20261023b"]:
    d = os.path.join(BASE, t)
    print("  --- %s" % t)
    for f in sorted(os.listdir(d)):
        if f.endswith(".png"):
            print("      PNG %-40s %s" % (f, mt(os.path.join(d, f))))
    fp = os.path.join(d, "qc151_fields.json")
    if os.path.exists(fp):
        for r in json.load(open(fp, encoding="utf-8")):
            k = str(r.get("key", ""))
            if "forensic" in k or k in ("rc", "exit", "verdict") or "measure_window" in k:
                print("      REC %s = %s" % (k, json.dumps(r.get("value"), ensure_ascii=False)[:180]))
