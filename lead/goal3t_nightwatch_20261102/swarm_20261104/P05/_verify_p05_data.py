# -*- coding: utf-8 -*-
"""VERIFY-P05 主数据复核：自写探针，从 4 份 h8_wait_trace.json 原始字节重算全部 keyFact。

独立性声明：不 import _p05_decomp/_p05_probe；口径定义从 analyze_waittrace.py（发布定义源，
本会话直读）与台账 §508/§513 文本取来；平台枚举用「直扫帧值序列」规范方式（非 delta 零游程），
天然包含单样本平台。零真机、只读、stdout-only。
"""
import json, statistics, hashlib, sys
from pathlib import Path

BASE = Path(r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
TAGS = ("b", "c", "d", "e")
THR = 0.1
OUT = []
P = OUT.append


def p_floor(vals, q):
    return sorted(vals)[int(q * (len(vals) - 1))] if vals else None


def med(vals):
    return statistics.median(vals) if vals else None


def fmt(v, nd=3):
    return "None" if v is None else f"{v:.{nd}f}"


def analyze(tag):
    path = BASE / f"l3_1101v4{tag}" / "h8_wait_trace.json"
    raw = path.read_bytes()
    sha16 = hashlib.sha256(raw).hexdigest()[:16]
    d = json.loads(raw)
    S = d["samples"]
    n = len(S)
    ts = [r[0] for r in S]
    fs = [r[1] for r in S]
    span_all = ts[-1] - ts[0]
    P(f"######## v4-{tag}  sha16={sha16}  n(json)={d.get('n')}  len(samples)={n}  "
      f"verdict={d.get('verdict')}  wait_s(json)={d.get('wait_s')}  "
      f"frame 首={fs[0]} 末={fs[-1]}  t跨度={span_all:.3f}s  "
      f"拍率(n-1/span)={(n-1)/span_all:.2f}Hz")

    # ---- 数据完整性：读失败 / 回退 / Δf 直方图 ----
    bad = sum(1 for f in fs if f is None)
    neg = sum(1 for i in range(n - 1)
              if fs[i] is not None and fs[i + 1] is not None and fs[i + 1] - fs[i] < 0)
    hist = {"zero": 0, "one": 0, "two": 0, "gt2": 0, "other": 0}
    for i in range(n - 1):
        if fs[i] is None or fs[i + 1] is None:
            hist["other"] += 1
            continue
        dv = fs[i + 1] - fs[i]
        k = "zero" if dv == 0 else "one" if dv == 1 else "two" if dv == 2 else "gt2" if dv > 2 else "other"
        hist[k] += 1
    P(f"完整性: 读失败={bad} 回退={neg} Δf直方图(边数{n-1})={hist}")

    # ---- 拍节律 / 采样缺口 ----
    ivs = [ts[i + 1] - ts[i] for i in range(n - 1)]
    gaps = [x for x in ivs if x > 0.01]
    P(f"拍间隔 med/p90/max = {fmt(med(ivs)*1000,1)}/{fmt(p_floor(ivs,.9)*1000,1)}/{fmt(max(ivs)*1000,1)}ms  "
      f"缺口>10ms: {len(gaps)}处/{sum(gaps):.3f}s = {100*sum(gaps)/span_all:.1f}%轨迹跨度")

    # ---- qc151_fields h7_frame_wait ----
    q = json.loads((BASE / f"l3_1101v4{tag}" / "qc151_fields.json").read_text(encoding="utf-8"))
    hw = None
    for row in q:
        if isinstance(row, dict) and row.get("key") == "h7_frame_wait":
            hw = row.get("value")
    if isinstance(hw, dict):
        P(f"qc151 h7_frame_wait: poll_count={hw.get('poll_count')} reached_frame={hw.get('reached_frame')} "
          f"timed_out={hw.get('timed_out')} wait_s={hw.get('wait_s')} offset_frames={hw.get('offset_frames')} "
          f"| len(samples)==poll_count? {n == hw.get('poll_count')}  "
          f"| 末样本t={ts[-1]:.4f}  json.wait_s={d.get('wait_s')}")
    else:
        P("qc151 h7_frame_wait: 未找到!")

    # ---- 首推进 / 战斗段 / 规范平台枚举（直扫帧值序列）----
    adv_edge = [i for i in range(n - 1)
                if fs[i] is not None and fs[i + 1] is not None and fs[i + 1] > fs[i]]
    if not adv_edge:
        P("无推进"); return
    first = adv_edge[0] + 1          # 首推进拍 = 新帧值首见样本
    bts, bfs = ts[first:], fs[first:]
    m = len(bts)
    span = bts[-1] - bts[0]
    net = bfs[-1] - bfs[0]
    # advances：每个新帧值首见拍的绝对时刻（战斗段内）
    advances = [ts[i + 1] for i in adv_edge if i + 1 >= first]
    aivs = [b - a for a, b in zip(advances, advances[1:])]
    P(f"首推进 idx={first} t={ts[first]:.3f}s  头平台={ts[first]-ts[0]:.3f}s@帧{fs[0]}  "
      f"末推进 t={advances[-1]:.4f}s  尾静默={ts[-1]-advances[-1]:.3f}s")
    P(f"战斗段: 跨度={span:.4f}s(4位)  净推进={net}  平均={net/span:.2f}帧/s  推进次数={len(advances)}")
    P(f"推进间隔 med/p90/max = {fmt(med(aivs)*1000,1)}/{fmt(p_floor(aivs,.9)*1000,1)}/{fmt(max(aivs)*1000,1)}ms  (n={len(aivs)})")

    # 平台直扫：战斗段内连续等帧值样本组；p0=首见拍,p1=末见拍;尾平台 p1=m-1
    plats = []  # (p0,p1,B,C,clip,single)
    p0 = 0
    for i in range(1, m + 1):
        if i == m or bfs[i] != bfs[p0]:
            p1 = i - 1
            single = (p1 == p0)
            Bdur = ts[first + p1] - ts[first + p0]
            if first + p1 + 1 <= n - 1:
                Cdur = ts[first + p1 + 1] - ts[first + p0]
                clip = False
            else:
                Cdur = None
                clip = True
            plats.append((p0, p1, Bdur, Cdur, clip, single))
            p0 = i
    n_plat = len(plats)
    n_single = sum(1 for x in plats if x[5])
    tail = plats[-1]
    P(f"平台直扫: 战斗段平台总数={n_plat}  单样本平台={n_single}  "
      f"尾平台: p0={tail[0]} B={fmt(tail[2])}s C={'None(clip)' if tail[4] else fmt(tail[3])}")

    # 三口径（§513 定义；阈值 ≥0.1s 含端点）
    Asegs, Bsegs, Csegs = [], [], []
    for (p0, p1, Bdur, Cdur, clip, single) in plats:
        gap_out = None if clip else ts[first + p1 + 1] - ts[first + p1]
        # A(发布实现)=legacy dur=bts[p1+1]-bts[p0+1]=B+gap_out-内部首拍间隔；尾平台裁剪为 ts[p1]-ts[p0+1]
        # 单样本平台：无零入边游程 → legacy 不成段 → None
        if clip:
            Adur = ts[n - 1] - ts[first + p0 + 1] if p1 > p0 else None
        elif single:
            Adur = None
        else:
            inner_first = ts[first + p0 + 1] - ts[first + p0]   # 平台内首两拍间隔（§513 记号的 d_in）
            Adur = Bdur + gap_out - inner_first if gap_out is not None else None
        if Adur is not None and Adur >= THR:
            Asegs.append(Adur)
        if Bdur >= THR:
            Bsegs.append(Bdur)
        if (not clip) and Cdur is not None and Cdur >= THR:
            Csegs.append(Cdur)
    totA, totB, totC = sum(Asegs), sum(Bsegs), sum(Csegs)
    P(f"[三口径] A={len(Asegs)}段/{totA:.4f}s/{100*totA/span:.2f}%  "
      f"B={len(Bsegs)}段/{totB:.4f}s/{100*totB/span:.2f}%  "
      f"C={len(Csegs)}段/{totC:.4f}s/{100*totC/span:.2f}%  (span={span:.4f})")
    # C 分解：零游程平台（非单样本）C≥0.1 不含尾 + 单样本平台 C≥0.1
    c_reg = sum(1 for x in plats if (not x[5]) and (not x[4]) and x[3] is not None and x[3] >= THR)
    c_single = sum(1 for x in plats if x[5] and (not x[4]) and x[3] is not None and x[3] >= THR)
    c_tail_clip = sum(1 for x in plats if x[4] and x[3] is None)
    P(f"[C分解] 零游程平台C≥0.1(不含尾)={c_reg} + 单样本平台C≥0.1={c_single} = {c_reg+c_single}"
      f"  (尾平台不计={c_tail_clip}；C<0.1不计={n_plat-c_reg-c_single-c_tail_clip})")
    # 逐段 A=直算(legacy 位移) vs A=B+gap_out-内部首拍 恒等式残差
    maxres = 0.0
    for (p0, p1, Bdur, Cdur, clip, single) in plats:
        if clip or single:
            continue
        a_direct = ts[first + p1 + 1] - ts[first + p0 + 1]
        a_ident = (ts[first + p1] - ts[first + p0]) + (ts[first + p1 + 1] - ts[first + p1]) \
            - (ts[first + p0 + 1] - ts[first + p0])
        maxres = max(maxres, abs(a_direct - a_ident))
    P(f"[A恒等式残差] max={maxres:.12f} ms→{maxres*1000:.10f}ms")

    # 分档（B 口径，战斗段全部平台）
    buckets = {"<0.1": (0.0, 0.1), "0.1-0.5": (0.1, 0.5), "0.5-1": (0.5, 1.0),
               "1-5": (1.0, 5.0), ">5": (5.0, 1e9)}
    bl = [x[2] for x in plats]
    P("分档(B,全部平台): " + "  ".join(
        f"{k}:{sum(1 for x in bl if lo<=x<hi)}/{sum(x for x in bl if lo<=x<hi):.3f}s"
        for k, (lo, hi) in buckets.items()))
    P(f"分档(B,≥0.1s段): " + "  ".join(
        f"{k}:{sum(1 for x in Bsegs if lo<=x<hi)}/{sum(x for x in Bsegs if lo<=x<hi):.3f}s"
        for k, (lo, hi) in buckets.items() if k != "<0.1"))
    top5B = sorted(Bsegs, reverse=True)[:5]
    P(f"Top5 B段 = {[fmt(x) for x in top5B]}")
    P(f"头平台: {ts[first]-ts[0]:.3f}s@帧{fs[0]}")

    # 分型判据
    maxB = max(bl) if bl else 0.0
    maxC = max([x[3] for x in plats if not x[4] and x[3] is not None], default=0.0)
    dom = maxB / totB if totB else 0.0
    P(f"[判据] 最长完全静止窗 B={maxB:.4f}s  C口径(=相邻推进最大间隔)={maxC:.4f}s  "
      f"≥2s静止窗存在? B:{any(x>=2 for x in bl)} C:{maxC>=2}  "
      f"单段主导度 maxB/ΣB={100*dom:.2f}%  maxB/ΣA={100*maxB/totA:.2f}%")
    # 推进间隔直方图（0.05s 桶，判据③宽连续分布）
    hb = {}
    for x in aivs:
        lo = int(x / 0.05) * 0.05
        key = f"{lo:.2f}-{lo+0.05:.2f}"
        hb[key] = hb.get(key, 0) + 1
    top_hb = sorted(hb.items(), key=lambda kv: -kv[1])[:6]
    P("推进间隔直方图 top 桶(占266): " + "  ".join(f"{k}:{v}({100*v/len(aivs):.1f}%)" for k, v in top_hb))
    hi = [k for k, v in hb.items() if float(k.split("-")[0]) >= 0.75 and float(k.split("-")[0]) < 1.0]
    P(f"  0.75-1.0s 桶合计: {sum(hb.get(k,0) for k in hi)}({100*sum(hb.get(k,0) for k in hi)/len(aivs):.1f}%)  "
      f">1.5s: {sum(1 for x in aivs if x>1.5)}处")

    # 跳帧
    jumps = [(ts[i + 1], fs[i], fs[i + 1], fs[i + 1] - fs[i], ivs[i]) for i in adv_edge
             if fs[i + 1] - fs[i] > 1]
    for (t, f0, f1, dv, g) in jumps:
        P(f"跳帧: t={t:.4f}s {f0}→{f1} Δf={dv} 该边拍间隔={g*1000:.1f}ms")
    if not jumps:
        P("跳帧(Δf>1): 0 处")

    # 速率时间序列
    def f_at(tq):
        lo, hi2 = 0, n - 1
        while lo < hi2:
            mid = (lo + hi2 + 1) // 2
            if ts[mid] <= tq:
                lo = mid
            else:
                hi2 = mid - 1
        return fs[lo]
    t0, t1 = ts[first], ts[-1]
    # 四分位
    q4 = []
    for k in range(4):
        a = t0 + span * k / 4
        b = t0 + span * (k + 1) / 4
        q4.append((f_at(b) - f_at(a)) / (b - a))
    P(f"四分位速率(净推进/时长) = {'/'.join(fmt(x,2) for x in q4)} 帧/s")
    # 5s 窗
    w5, cur = [], t0
    while cur < t1:
        nxt = min(cur + 5.0, t1)
        w5.append(((cur - ts[0], nxt - ts[0]), (f_at(nxt) - f_at(cur)) / (nxt - cur)))
        cur = nxt
    r5 = [r for _, r in w5]
    wmin = min(r5); wmax = max(r5)
    tmin = w5[r5.index(wmin)][0]; tmax = w5[r5.index(wmax)][0]
    P(f"5s窗速率: {len(w5)}窗  min={wmin:.2f}@abs[{tmin[0]:.1f}-{tmin[1]:.1f}s]  "
      f"max={wmax:.2f}@abs[{tmax[0]:.1f}-{tmax[1]:.1f}s]  序列=" + " ".join(fmt(x,1) for x in r5))
    P(f"  5s窗范围: {min(r5):.2f}~{max(r5):.2f}  零速率窗={sum(1 for x in r5 if x==0)}")
    # 1s 窗低速率期
    w1, cur = [], t0
    while cur < t1:
        nxt = min(cur + 1.0, t1)
        w1.append((cur - ts[0], (f_at(nxt) - f_at(cur)) / (nxt - cur)))
        cur = nxt
    r1 = [r for _, r in w1]
    rmed = med([r for r in r1 if r > 0]) if any(r > 0 for r in r1) else 0
    lows = [i for i, r in enumerate(r1) if r < 0.5 * rmed]
    runs_low = []
    for i in lows:
        if runs_low and i == runs_low[-1][1] + 1:
            runs_low[-1][1] = i
        else:
            runs_low.append([i, i])
    P(f"1s窗低速率期(<50%中位{fmt(rmed,1)}): {len(runs_low)} 段  " +
      ", ".join(f"[{w1[s][0]:.0f}-{w1[e][0]+1:.0f}s]" for s, e in runs_low[:12]))

    # A 段起点间距中位（§507 术语解码；A段起点=bts[s]=ts[p0+1]）
    astarts = []
    for (p0, p1, Bdur, Cdur, clip, single) in plats:
        if clip:
            Ad = ts[n - 1] - ts[first + p0 + 1] if p1 > p0 else None
        elif single:
            Ad = None
        else:
            Ad = Bdur + (ts[first + p1 + 1] - ts[first + p1]) \
                - (ts[first + p0 + 1] - ts[first + p0])
        if Ad is not None and Ad >= THR:
            astarts.append(ts[first + p0 + 1])
    astarts.sort()
    agaps = [b - a for a, b in zip(astarts, astarts[1:])]
    P(f"A段起点间距: n={len(astarts)}  med={fmt(med(agaps)*1000,1)}ms ({fmt(med(agaps),4)}s)")
    OUT.append("")
    return dict(tag=tag, first=first, span=span, t0=t0, advances=advances, plats=plats,
                ts=ts, fs=fs, n=n, astarts=astarts, w5=w5, r5=r5, aivs=aivs, Bsegs=Bsegs,
                Csegs=Csegs, jumps=jumps, ivs=ivs)


def main():
    R = {}
    for tag in TAGS:
        R[tag] = analyze(tag)
    # ---- 跨趟对比：跳帧法医细节（v4-b 两处）----
    b = R["b"]
    ts = b["ts"]; n = b["n"]; ivs = b["ivs"]; fs = b["fs"]
    maxgap = max(ivs)
    gi = ivs.index(maxgap)
    P(f"[跳帧法医] v4-b 最大拍间隔={maxgap*1000:.1f}ms @样本{gi} (t={ts[gi]:.3f}→{ts[gi+1]:.3f}, "
      f"帧{fs[gi]}→{fs[gi+1]})  缺口内推进{fs[gi+1]-fs[gi]}帧 → 均摊速率={ (fs[gi+1]-fs[gi])/maxgap :.2f}帧/s")
    jm = med([x for i, x in enumerate(b["aivs"])])
    P(f"[跳帧法医] v4-b 推进间隔中位={fmt(jm*1000,1)}ms  缺口均摊>中位? {(fs[gi+1]-fs[gi])/maxgap > jm}")
    for (t, f0, f1, dv, g) in b["jumps"]:
        P(f"  跳帧 t={t:.3f}s Δf={dv} 边间隔={g*1000:.1f}ms (同拍连跳? {g<0.005})")
    # 邻域推进间隔（跳帧①）
    j1 = b["jumps"][0]
    near = [fmt(x*1000,0) for x in b["aivs"] if abs(x - 0) < 9]
    # 找跳帧附近的推进间隔：直接列 advances 中距 j1±2s 的间隔
    adv = b["advances"]
    idx = min(range(len(adv)), key=lambda i: abs(adv[i] - j1[0]))
    lo, hi2 = max(0, idx - 3), min(len(adv) - 1, idx + 2)
    P(f"  跳帧①邻域推进间隔: {[fmt((adv[i+1]-adv[i])*1000,0) for i in range(lo,hi2)]}ms")
    # v4-e 战斗段口径差（§516 33.882 vs 本线 33.879）
    e = R["e"]
    first_e = e["first"]
    span_pre = e["ts"][-1] - e["ts"][first_e - 1]
    P(f"[v4-e口径] span(首推进拍起)={e['span']:.4f}s  span(推进边前拍起)={span_pre:.4f}s  (§516 写 33.882)")
    print("\n".join(OUT))


if __name__ == "__main__":
    main()
