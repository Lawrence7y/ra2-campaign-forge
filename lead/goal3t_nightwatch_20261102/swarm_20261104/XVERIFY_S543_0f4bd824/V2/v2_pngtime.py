# -*- coding: utf-8 -*-
"""V2 截图时序核对（只用文件系统元数据 + JSON 时间戳，不解码任何像素）。

对每张 measure_w{k}_end_x.png：
  期望采图时刻 ≈ 该窗 t_abs0 + span_s（harness 在窗结束后立即取证）
  与 PNG 的 mtime 对比，差值 > 30s ⇒ 该 PNG 不可能是该窗的现场截图。
另外交叉核对 qc151_fields.json 里 harness 自记的 empty_window 标志与 df 的关系。
"""
import glob
import json
import os
import re
import time

BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
PNG = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png")))


def hm(t):
    return time.strftime("%m-%d %H:%M:%S", time.localtime(t))


print("### A. PNG mtime vs 窗时刻（t_abs0 + span_s）")
print("%-20s %2s %18s %18s %10s %10s %8s" % ("dir", "w", "窗末时刻(t_abs0+span)", "png mtime", "Δs", "df", "class"))
rows = []
for p in PNG:
    d = os.path.dirname(p)
    m = re.match(r"measure_w(\d+)_end", os.path.basename(p))
    w = int(m.group(1))
    jp = os.path.join(d, "measure_w%d.json" % w)
    j = json.load(open(jp, encoding="utf-8"))
    ed = j["frame_edges"]
    f0, f1 = ed[0][0], ed[-1][0]
    df = f1 - f0
    cls = "ADV" if df > 0 else ("BACK" if df < 0 else ("LOAD" if f0 == 0 else "FRZ"))
    exp = (j.get("t_abs0") or 0) + (j.get("span_s") or 0)
    mt = os.path.getmtime(p)
    delta = mt - exp
    rows.append((d, w, df, cls, exp, mt, delta, p))
    print("%-20s %2d %18s %18s %10.1f %10d %8s" %
          (os.path.basename(d), w, hm(exp), hm(mt), delta, df, cls))
print()
bad = [r for r in rows if abs(r[6]) > 30]
print("  |Δ| > 30s 的张数 = %d / %d" % (len(bad), len(rows)))
for r in bad:
    print("     %-20s w%s Δ=%.1fs" % (os.path.basename(r[0]), r[1], r[6]))
print()
print("  注：t_abs0 是 unix 秒（time.time 口径）。用 archive_T32 w0 t_abs0=%.3f ⇒ %s 校验时钟口径"
      % (json.load(open(os.path.join(BASE, "archive_T32", "measure_w0.json"), encoding="utf-8"))["t_abs0"],
         hm(json.load(open(os.path.join(BASE, "archive_T32", "measure_w0.json"), encoding="utf-8"))["t_abs0"])))
print()

print("### B. t_abs0 相对时刻（同一趟三窗）与 PNG mtime 的自洽性")
for d in sorted({r[0] for r in rows}):
    seq = []
    for w in (0, 1, 2):
        jp = os.path.join(d, "measure_w%d.json" % w)
        if os.path.exists(jp):
            j = json.load(open(jp, encoding="utf-8"))
            seq.append((w, j.get("t_abs0"), j.get("span_s"), (j["frame_edges"][0][0], j["frame_edges"][-1][0])))
    line = []
    for w, t0, sp, ff in seq:
        pngp = os.path.join(d, "measure_w%d_end_x.png" % w)
        mark = ""
        if os.path.exists(pngp):
            mark = " png_mtime=%s Δ=%.1f" % (hm(os.path.getmtime(pngp)),
                                             os.path.getmtime(pngp) - ((t0 or 0) + (sp or 0)))
        line.append("w%d t0=%.1f span=%s f=%s->%s%s" % (w, t0 or 0, sp, ff[0], ff[1], mark))
    print("  %-20s %s" % (os.path.basename(d), " | ".join(line)))
print()

print("### C. harness 自记 empty_window 与 df 的对应（从 qc151_fields.json 的 QC208-2 取证记录读）")
for dp in sorted(glob.glob(os.path.join(BASE, "*", "qc151_fields.json"))):
    d = os.path.dirname(dp)
    j = json.load(open(dp, encoding="utf-8"))
    if not isinstance(j, list):
        continue
    recs = [r for r in j if isinstance(r, dict) and "空窗另存" in str(r.get("note", ""))]
    if not recs:
        continue
    out = []
    for r in recs:
        v = r.get("value") or {}
        wn = v.get("window")
        jp = os.path.join(d, "measure_w%d.json" % wn)
        df = None
        if os.path.exists(jp):
            jj = json.load(open(jp, encoding="utf-8"))
            ed = jj["frame_edges"]
            df = ed[-1][0] - ed[0][0]
        out.append("w%s empty_window=%s df=%s frame=%s png=%s" %
                   (wn, v.get("empty_window"), df, v.get("current_frame"),
                    os.path.basename(str(v.get("forensics_png") or "-"))))
    print("  %-20s %s" % (os.path.basename(d), " ; ".join(out)))
