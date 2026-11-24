# -*- coding: utf-8 -*-
"""_wtr_v4e.py - v4-e 等待段轨迹分解（V4E 卡 §4 轨1 钉死口径）。

口径（V4E_PERSIST_CARD §4 轨1 / V4D_RECOMPUTE §三-1 §四-2 钉死）：
  停滞 episode = 战斗段（首推进拍→末拍）内 Δframe=0 连续段
  时长 = 卡住帧值首末拍跨度（t(段内末拍) − t(段内首拍)，不含段尾至下一推进拍间隔）
  ≥100ms 计入；占比 = 合计 / 战斗段跨度

同时输出：
  - 替代口径 C（算到下一推进拍）作为已登记陷阱的对照，单列不混算
  - 拍节律 / 采样缺口（harness 侧饥饿侧证，§507 新观察①）
  - 读败段（delta=None）单列，不计入停滞

用法：python -I -X utf8 _wtr_v4e.py > _wtr_v4e_out.txt
"""

import json
import os

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
T = 0.100


def P(s=""):
    print(s)


def median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return 0.0
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def analyze(trip):
    p = os.path.join(BASE, trip, "h8_wait_trace.json")
    with open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    # 结构自适应：找 (t, frame) 序列
    keys = list(d.keys())
    P("   [trace keys] %s" % keys)
    raw = None
    for k in ("trace", "samples", "beats", "data", "polls"):
        if k in d and isinstance(d[k], list) and d[k] and isinstance(d[k][0], (list, dict)):
            raw = d[k]
            P("   [trace list key] %s  n=%d" % (k, len(raw)))
            break
    if raw is None:
        P("   !! 无法定位轨迹序列")
        return None
    if isinstance(raw[0], dict):
        ts = [float(r.get("t", r.get("t_rel", 0.0))) for r in raw]
        fs = [r.get("f", r.get("frame")) for r in raw]
    else:
        ts = [float(r[0]) for r in raw]
        fs = [r[1] for r in raw]

    n = len(ts)
    # 读败段
    bad = sum(1 for x in fs if x is None)
    # 有效推进点（f 非 None）
    valid = [(ts[i], fs[i]) for i in range(n) if fs[i] is not None]
    if len(valid) < 2:
        P("   !! 有效样本不足")
        return None
    vt = [v[0] for v in valid]
    vf = [v[1] for v in valid]
    # 战斗段 = 首推进拍到末拍（推进 = f 改变）
    first_adv = None
    for i in range(1, len(vf)):
        if vf[i] != vf[i - 1]:
            first_adv = i - 1
            break
    if first_adv is None:
        P("   !! 全程无推进")
        return None
    bt = vt[first_adv:]
    bf = vf[first_adv:]
    battle_span = bt[-1] - bt[0]

    # 找 Δf=0 的连续平台段
    segs = []
    i = 0
    while i < len(bf) - 1:
        if bf[i + 1] == bf[i]:
            j = i
            while j + 1 < len(bf) and bf[j + 1] == bf[j]:
                j += 1
            # 平台 [i..j]
            dur_b = bt[j] - bt[i]          # 口径 B：首末拍跨度（钉死）
            dur_c = bt[j + 1] - bt[i] if j + 1 < len(bf) else bt[j] - bt[i]
            segs.append((bt[i], bf[i], dur_b, dur_c))
            i = j + 1
        else:
            i += 1

    hitB = [s for s in segs if s[2] >= T]
    hitC = [s for s in segs if s[3] >= T]
    totB = sum(s[2] for s in hitB)
    totC = sum(s[3] for s in hitC)

    # 拍节律
    allgap = [ts[i] - ts[i - 1] for i in range(1, n)]
    biggap = [g for g in allgap if g > 0.010]
    hz = (n - 1) / (ts[-1] - ts[0]) if ts[-1] > ts[0] else 0.0

    # 推进拍间隔谱
    advt = [vt[i] for i in range(1, len(vt)) if vf[i] != vf[i - 1]]
    advgap = [advt[i] - advt[i - 1] for i in range(1, len(advt))]

    return dict(n=n, bad=bad, span=ts[-1] - ts[0], battle_span=battle_span,
                nseg=len(segs), hitB=len(hitB), totB=totB,
                pctB=100 * totB / battle_span if battle_span else 0.0,
                hitC=len(hitC), totC=totC,
                pctC=100 * totC / battle_span if battle_span else 0.0,
                top=sorted(hitB, key=lambda x: -x[2])[:5],
                hz=hz, medgap=median(allgap) * 1000,
                p90=sorted(allgap)[int(len(allgap) * 0.9)] * 1000 if allgap else 0.0,
                maxgap=max(allgap) * 1000 if allgap else 0.0,
                nbig=len(biggap), bigsum=sum(biggap),
                adv_med=median(advgap) * 1000 if advgap else 0.0)


P("=" * 88)
P("## v4-e / v4-d 等待段轨迹分解（V4E 卡 §4 轨1 钉死口径 + 口径 C 对照）")
P("=" * 88)
res = {}
for trip in ("l3_1101v4d", "l3_1101v4e"):
    P()
    P("### %s" % trip)
    r = analyze(trip)
    if not r:
        continue
    res[trip] = r
    P("   样本=%d  读败=%d  跨度=%.3fs  战斗段=%.3fs" % (r["n"], r["bad"], r["span"], r["battle_span"]))
    P("   停滞段(全部平台)=%d" % r["nseg"])
    P("   ★ 钉死口径B：%d 段 / %.3fs / %.2f%%" % (r["hitB"], r["totB"], r["pctB"]))
    P("     替代口径C：%d 段 / %.3fs / %.2f%%  （已登记陷阱，单列不混算）"
      % (r["hitC"], r["totC"], r["pctC"]))
    P("   Top5 停滞段（口径B）：")
    for s in r["top"]:
        P("      t=%8.3fs frame=%-8s dur=%.3fs" % (s[0], s[1], s[2]))
    P("   拍节律：%.1f Hz  拍间隔 中位=%.2fms p90=%.2fms max=%.2fms" % (r["hz"], r["medgap"], r["p90"], r["maxgap"]))
    P("   采样缺口(>10ms)：%d 处 / 合计 %.3fs" % (r["nbig"], r["bigsum"]))
    P("   推进拍间隔 中位=%.2fms" % r["adv_med"])

if len(res) == 2:
    a, b = res["l3_1101v4d"], res["l3_1101v4e"]
    P()
    P("=" * 88)
    P("## 对照（v4-d=BOOT#6 0.93h → v4-e=BOOT#8 现）")
    P("=" * 88)
    P("   钉死口径B 占比：v4-d %.2f%%  →  v4-e %.2f%%   （%.2f 倍）" % (a["pctB"], b["pctB"], b["pctB"] / a["pctB"] if a["pctB"] else float("inf")))
    P("   段数：v4-d %d  →  v4-e %d" % (a["hitB"], b["hitB"]))
    P("   合计时长：v4-d %.3fs  →  v4-e %.3fs" % (a["totB"], b["totB"]))
    P("   拍率：v4-d %.1f Hz  →  v4-e %.1f Hz" % (a["hz"], b["hz"]))
    P()
    P("   历史锚（同口径B，供判读）：v4-c 90 段/11.844s/20.5%；v4-b 224 段/82.079s/79.41%")
