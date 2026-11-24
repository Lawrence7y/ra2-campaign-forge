# -*- coding: utf-8 -*-
"""V2 反证与专查：口径复现 / 被丢弃文件 / 冻结窗「对局已结束」量级检验 /
   e4 深查 / T42 深查 / 慢窗独立性 / 窗末 PNG 的**字节级**同一性（不解码图像）。

只读。零真机。PNG 只做文件字节 sha256 + 尺寸 + mtime，不调用 PIL，不读像素。
"""
import glob
import hashlib
import json
import os
import time

BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

SUB = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))
ROOT = sorted(glob.glob(os.path.join(BASE, "measure_w*.json")))


def J(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def windows(paths, label):
    out = []
    for p in paths:
        j = J(p)
        ed = j.get("frame_edges") or []
        d = os.path.basename(os.path.dirname(p))
        out.append(dict(p=p, dir=d, j=j, ed=ed))
    return out


print("### Q1  在 ask 点名的 glob（BASE/*/measure_w*.json）下复现本线口径")
rows = []
dropped = []
for p in SUB:
    j = J(p)
    ed = j.get("frame_edges") or []
    d = os.path.basename(os.path.dirname(p))
    if not ed:
        dropped.append((d, j))
        continue
    f0, f1 = ed[0][0], ed[-1][0]
    rows.append((d, j.get("window"), f0, f1, f1 - f0, j))
adv = [r for r in rows if r[4] > 0]
frz = [r for r in rows if r[4] == 0 and r[2] != 0]
ld = [r for r in rows if r[4] == 0 and r[2] == 0]
bk = [r for r in rows if r[4] < 0]
print("  文件 %d 份 -> 参与分类 %d 窗 / %d 趟目录 ；丢弃 %d 份"
      % (len(SUB), len(rows), len({r[0] for r in rows}), len(dropped)))
print("  ADV=%d  FRZ=%d  LOAD=%d  BACK=%d   （本线报：63 / 29 / 1 / 1，94 窗 / 36 趟）"
      % (len(adv), len(frz), len(ld), len(bk)))
print("  结论：%s" % ("逐位复现" if (len(rows), len(adv), len(frz), len(ld), len(bk)) == (94, 63, 29, 1, 1) else "未复现"))
print()
print("### Q1b 被 frame_edges 判空而丢弃的 4 份（§538/§543 均未提）")
for d, j in dropped:
    st = j.get("stats") or {}
    sm = j.get("samples") or {}
    print("  %-16s w%s trip_id=%s verdict=%r span=%s n_samples_t=%s error=%r gate=%s" %
          (d, j.get("window"), j.get("trip_id"), j.get("verdict"), j.get("span_s"),
           len(sm.get("t") or []), j.get("error"), json.dumps(j.get("gate"), ensure_ascii=False)))
    cs = j.get("counters") or []
    print("       counters_n=%d 首=%s 末=%s" %
          (len(cs), json.dumps(cs[0], ensure_ascii=False)[:150] if cs else None,
           json.dumps(cs[-1], ensure_ascii=False)[:150] if cs else None))
print()
print("### Q1c 根目录 3 份（本线 glob 漏）")
for p in ROOT:
    j = J(p)
    ed = j.get("frame_edges") or []
    st = j.get("stats") or {}
    print("  %s w%s trip_id=%s f=%s->%s span=%s pre_fps15=%s ok=%s verdict=%r samples=%s error=%r" %
          (os.path.basename(p), j.get("window"), j.get("trip_id"),
           ed[0][0] if ed else None, ed[-1][0] if ed else None, j.get("span_s"),
           (j.get("gate") or {}).get("pre_fps15"), (j.get("gate") or {}).get("ok"),
           j.get("verdict"), st.get("samples"), j.get("error")))
    print("      t_abs0=%.3f  map=%s  counters[0]=%s" %
          (j.get("t_abs0") or 0, (j.get("map_sha256") or "")[:8],
           json.dumps((j.get("counters") or [])[:1], ensure_ascii=False)[:170]))
print()

print("### Q2 冻结窗「对局已结束」的量级检验：游戏时长 = f/31.2，与场上单位数")
print("  %-20s %2s %6s %8s %8s %7s %7s %6s %6s %6s %8s" %
      ("dir", "w", "f", "秒@31.2", "秒@30", "units0", "units冻", "Δunits", "g冻", "b冻", "units_uniq"))
tot = dict()
for d, w, f0, f1, df, j in sorted(frz, key=lambda x: (x[0], x[1])):
    ed = j["frame_edges"]
    g = j.get("gate") or {}
    cs = j.get("counters") or []
    u = [c.get("units") for c in cs]
    gv = [c.get("g") for c in cs]
    bv = [c.get("b") for c in cs]
    print("  %-20s %2s %6d %8.2f %8.2f %7s %7s %6s %6s %6s %8s" %
          (d, w, f0, f0 / 31.2, f0 / 30.0, g.get("units0"),
           u[0] if u else None,
           (u[0] - g.get("units0")) if (u and g.get("units0") is not None) else None,
           gv[0] if gv else None, bv[0] if bv else None, len(set(u))))
gt = [ (f0/31.2) for d,w,f0,f1,df,j in frz ]
print("  游戏时长(秒@31.2) 分布: min=%.1f max=%.1f ；<=30s 的窗 %d/%d" %
      (min(gt), max(gt), sum(1 for v in gt if v <= 30.0), len(gt)))
print()

print("### Q2b 冻结时刻前一窗（同趟）末秒计数器 -> 冻结窗首秒计数器 是否连续")
bytrip = {}
for d, w, f0, f1, df, j in rows:
    bytrip.setdefault(d, []).append((w, f0, f1, df, j))
for d, rs in sorted(bytrip.items()):
    rs.sort()
    for i in range(1, len(rs)):
        w, f0, f1, df, j = rs[i]
        if df != 0 or f0 == 0:
            continue
        pw, pf0, pf1, pdf, pj = rs[i - 1]
        cs_prev = (pj.get("counters") or [])
        cs_now = (j.get("counters") or [])
        if not cs_prev or not cs_now:
            continue
        a = cs_prev[-1]
        b = cs_now[0]
        keys = ("units", "infantry", "g", "b", "techno", "g_items", "b_items")
        diff = {k: (a.get(k), b.get(k)) for k in keys if a.get(k) != b.get(k)}
        print("  %-20s w%d(冻 f=%d) <- w%d(末 f=%d)  差异字段=%s  本窗帧推进=%s" %
              (d, w, f0, pw, pf1, json.dumps(diff, ensure_ascii=False), pdf))
print()

print("### Q3 连续性谱系：全部窗按 df 升序（df==0 与 df 小者之间有没有缝）")
allw = sorted([(r[4], r[0], r[1], r[5]) for r in rows])
prev = None
for df, d, w, j in allw:
    st = j.get("stats") or {}
    if df <= 40:
        print("  df=%6d  %-20s w%s  fps_avg=%s  max_stall=%s  span=%s  n_edges=%s" %
              (df, d, w, st.get("fps_avg"), st.get("max_stall_s"), j.get("span_s"), len(j["frame_edges"])))
print()
print("  df 正数区间的最小值 / 最大值分布：")
pos = sorted(x[0] for x in allw if x[0] > 0)
print("   最小 12 个正 df:", pos[:12])
print("   df==0 窗数=%d，df 在 1..40 的窗数=%d，df>700 的窗数=%d" %
      (sum(1 for x in allw if x[0] == 0), sum(1 for v in pos if v <= 40), sum(1 for v in pos if v > 700)))
print()

print("### Q4 慢窗（fps_avg<28 的 ADV 窗）独立性：同趟贡献几个窗")
lo = [(d, w, f0, f1, df, (j.get("stats") or {}).get("fps_avg")) for d, w, f0, f1, df, j in adv
      if ((j.get("stats") or {}).get("fps_avg") or 99) < 28]
from collections import Counter
cnt = Counter(x[0] for x in lo)
print("  慢窗总数=%d ，来自 %d 个趟目录" % (len(lo), len(cnt)))
for k, v in cnt.most_common():
    print("     %-20s %d 窗" % (k, v))
print("  同一 map_sha256 的慢窗分布：")
mc = Counter((J(os.path.join(BASE, x[0], "measure_w%d.json" % x[1])).get("map_sha256") or "")[:8] for x in lo)
for k, v in mc.most_common():
    print("     map %s : %d 窗" % (k, v))
print()

print("### Q5 archive 系列冻结窗的 map 与「游戏时长」聚类")
arc = {}
for d, w, f0, f1, df, j in rows:
    if df != 0:
        continue
    arc.setdefault(d, []).append((w, f0, (j.get("map_sha256") or "")[:8], (j.get("gate") or {}).get("units0"),
                                  (j.get("counters") or [{}])[0].get("units"), j.get("span_s"),
                                  (j.get("gate") or {}).get("pre_fps15"), (j.get("gate") or {}).get("ok")))
for k in sorted(arc):
    print("  %-20s %s" % (k, json.dumps(arc[k])))
print()

print("### Q6 l1_20261023e4 深查（唯一 df<0 与唯一 LOAD 窗）")
j = J(os.path.join(BASE, "l1_20261023e4", "measure_w1.json"))
ed = j["frame_edges"]
s = j["samples"]
print("  w1: trip_id=%s t_abs0=%.3f span=%s hz=%s" % (j.get("trip_id"), j.get("t_abs0"), j.get("span_s"), j.get("hz")))
print("  w1 frame_edges 前 3: %s" % ed[:3])
print("  w1 frame_edges 后 4: %s" % ed[-4:])
print("  w1 最后一个非零边 t=%.3f f=%d ；随后第一个 0 边 t=%.3f ；间隔 %.3f s" %
      (ed[-2][1], ed[-2][0], ed[-1][1], ed[-1][1] - ed[-2][1]))
fs, ts = s["f"], s["t"]
nz = max(i for i, v in enumerate(fs) if v != 0)
print("  w1 samples: 最后一个非零帧的下标 %d / %d ；其 t=%.3f f=%d ；此后到窗尾 %.3f s 全为 0" %
      (nz, len(fs), ts[nz], fs[nz], ts[-1] - ts[nz]))
first0 = min(i for i, v in enumerate(fs) if v == 0)
print("  w1 samples: 第一个 0 的下标 %d ，t=%.3f ，相对最后非零 %.3f s" % (first0, ts[first0], ts[first0] - ts[nz]))
print("  w1 counters 逐秒 units/g/ws_kb：")
for c in j.get("counters") or []:
    print("     t=%7.3f units=%s g=%s b=%s techno=%s ws=%s pf=%s" %
          (c.get("t_rel"), c.get("units"), c.get("g"), c.get("b"), c.get("techno"), c.get("ws_kb"), c.get("pf_kb")))
j2 = J(os.path.join(BASE, "l1_20261023e4", "measure_w2.json"))
print("  w2: error=%r stats.samples=%s n_edges=%s f 唯一值=%s" %
      (j2.get("error"), (j2.get("stats") or {}).get("samples"), len(j2["frame_edges"]),
       sorted(set((j2.get("samples") or {}).get("f") or []))))
print("  w2 counters 逐秒（注意 null 与 ws_kb）：")
for c in j2.get("counters") or []:
    print("     t=%7.3f units=%s g=%s b=%s ws=%s pf=%s" %
          (c.get("t_rel"), c.get("units"), c.get("g"), c.get("b"), c.get("ws_kb"), c.get("pf_kb")))
j0 = J(os.path.join(BASE, "l1_20261023e4", "measure_w0.json"))
print("  w0: f=%s->%s fps_avg=%s counters 末秒=%s" %
      (j0["frame_edges"][0][0], j0["frame_edges"][-1][0], (j0.get("stats") or {}).get("fps_avg"),
       json.dumps((j0.get("counters") or [])[-1], ensure_ascii=False)[:220]))
for nm in ("measure_w0.json", "measure_w1.json", "measure_w2.json"):
    jj = J(os.path.join(BASE, "l1_20261023e4", nm))
    print("     %s t_abs0=%.3f verdict=%r" % (nm, jj.get("t_abs0") or 0, jj.get("verdict")))
print()

print("### Q7 archive_T42 深查（本线称无计分屏证据的 df==0 窗）")
for w in (0, 1, 2):
    jj = J(os.path.join(BASE, "archive_T42", "measure_w%d.json" % w))
    st = jj.get("stats") or {}
    cs = jj.get("counters") or []
    print("  w%d f=%s->%s fps_avg=%s max_stall=%s samples=%s n_edges=%s error=%r t_abs0=%.3f" %
          (w, jj["frame_edges"][0][0], jj["frame_edges"][-1][0], st.get("fps_avg"),
           st.get("max_stall_s"), st.get("samples"), len(jj["frame_edges"]), jj.get("error"), jj.get("t_abs0") or 0))
    if w >= 1:
        wsv = [c.get("ws_kb") for c in cs]
        print("      ws_kb 逐秒: %s" % wsv)
        print("      units 逐秒: %s" % [c.get("units") for c in cs])
print("  T42 w0 与 w1 的绝对时间差 = %.3f s（窗长 25.0 ⇒ 无空档）" %
      (J(os.path.join(BASE, "archive_T42", "measure_w1.json"))["t_abs0"] -
       J(os.path.join(BASE, "archive_T42", "measure_w0.json"))["t_abs0"]))
print()

print("### Q8 窗末取证 PNG 的**文件字节**同一性（不解码；字节级指纹）")
pngs = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png")))
print("  measure_w*_end_*.png 共 %d 张" % len(pngs))
info = []
for p in pngs:
    with open(p, "rb") as fh:
        h = hashlib.sha256(fh.read()).hexdigest()
    sz = os.path.getsize(p)
    mt = os.path.getmtime(p)
    info.append((p, h, sz, mt))
groups = {}
for p, h, sz, mt in info:
    groups.setdefault(h, []).append(p)
dup = {h: v for h, v in groups.items() if len(v) > 1}
print("  字节级不同的指纹 %d / 字节级相同的组 %d" % (len(groups), len(dup)))
for h, v in sorted(dup.items(), key=lambda x: -len(x[1])):
    print("   [%s] %d 张：" % (h[:8], len(v)))
    for p in v:
        mt = os.path.getmtime(p)
        print("      %-96s %7d B  mtime=%s" % (p.replace(BASE + os.sep, ""), os.path.getsize(p),
                                               time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mt))))
print()
print("  全部窗末 PNG 清单（含 mtime，便于时序核对）：")
for p, h, sz, mt in info:
    print("     %-92s %7d B %s %s" % (p.replace(BASE + os.sep, ""), sz, h[:8],
                                      time.strftime("%m-%d %H:%M:%S", time.localtime(mt))))
