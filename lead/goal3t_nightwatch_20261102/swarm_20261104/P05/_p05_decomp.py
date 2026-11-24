# -*- coding: utf-8 -*-
"""P05：wait-trace 4 份逐拍分解（只读 4 份 h8_wait_trace.json + 4 份 qc151_fields.json；stdout-only；零真机）。

口径（与台账对齐）：
  战斗段 = 首个推进样本(新帧值首见) → 末样本（复刻 analyze_waittrace.py 的 bts=ts[first:]）
  停滞 episode 阈值 = 0.1s
  A = 发布实现口径：复刻 analyze_waittrace.episodes(bts, deltas[first-1:])（入边对齐下标直用 ts）
  B = 钉死口径（§508 复算/D-12②）：卡住帧值首末拍跨度 = ts[b]-ts[a]
  C = 到下一帧值首见 = ts[b+1]-ts[a]（=B+gap_out；§514 的 C；末段裁剪到末样本）
  p90 = analyze_waittrace 同式 ordered[int(.9*(len-1))]（floor）
"""
import json
import statistics
import hashlib
from pathlib import Path

BASE = Path(r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
TAGS = ("b", "c", "d", "e")
THR = 0.1
BUCKETS = ((0.0, 0.1, "<0.1"), (0.1, 0.5, "0.1-0.5"), (0.5, 1.0, "0.5-1"),
           (1.0, 5.0, "1-5"), (5.0, float("inf"), ">5"))


def runs_pred(seq, pred):
    start = None
    for i in range(len(seq) + 1):
        hit = i < len(seq) and pred(seq[i])
        if hit and start is None:
            start = i
        elif not hit and start is not None:
            yield start, i
            start = None


def p_floor(vals, q):
    if not vals:
        return None
    return sorted(vals)[int(q * (len(vals) - 1))]


def med(vals):
    return statistics.median(vals) if vals else None


def bucketize(durs):
    out = {}
    for lo, hi, name in BUCKETS:
        sel = [d for d in durs if lo <= d < hi]
        out[name] = (len(sel), sum(sel))
    return out


def fmt(v, nd=3):
    if v is None:
        return "None"
    return f"{v:.{nd}f}"


def measure_fields(qpath):
    """qc151_fields.json 里抽 h8_frame_wait 相关 MEASURE 键。"""
    want = ("poll_count", "reached_frame", "timed_out", "wait_s", "offset_frames",
            "h8_wait_trace", "h8_wait_verdict")
    got = {}
    try:
        rows = json.loads(qpath.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_error": str(e)}
    for row in rows:
        if not isinstance(row, dict):
            continue
        k = str(row.get("key", ""))
        if k in want or "wait" in k or "poll" in k:
            got[k] = row.get("value")
    return got


def analyze(tag, path):
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    d = json.loads(raw)
    samples = d["samples"]
    n = len(samples)
    ts = [r[0] for r in samples]
    fs = [r[1] for r in samples]
    L = []
    P = L.append
    P(f"### v4-{tag}  {path.name}")
    P(f"sha256[:16]={sha[:16]}  n(json)={d.get('n')}  len(samples)={n}  verdict={d.get('verdict')}  wait_s(json)={d.get('wait_s')}")
    P(f"帧号: 首={fs[0]} 末={fs[-1]}  t: 首={ts[0]} 末={ts[-1]}  跨度={ts[-1]-ts[0]:.3f}s")
    mf = measure_fields(BASE / f"l3_1101v4{tag}" / "qc151_fields.json")
    P(f"qc151 MEASURE 字段: {mf}")

    # ---- 读失败 / 回退 / 直方图 ----
    bad = [i for i, f in enumerate(fs) if f is None]
    deltas = [None if (fs[i] is None or fs[i + 1] is None) else fs[i + 1] - fs[i]
              for i in range(n - 1)]
    neg = [i for i, v in enumerate(deltas) if v is not None and v < 0]
    hist = {"zero": 0, "one": 0, "two": 0, "gt2": 0, "neg": 0, "none": 0}
    for v in deltas:
        if v is None:
            hist["none"] += 1
        elif v < 0:
            hist["neg"] += 1
        elif v == 0:
            hist["zero"] += 1
        elif v == 1:
            hist["one"] += 1
        elif v == 2:
            hist["two"] += 1
        else:
            hist["gt2"] += 1
    P(f"读失败拍={len(bad)}  回退(Δf<0)={len(neg)}  Δf直方图(共{n-1}边): {hist}")

    # ---- 拍节律 ----
    ivs = [b - a for a, b in zip(ts, ts[1:])]
    gaps10 = [x for x in ivs if x > 0.01]
    P(f"拍间隔: med={fmt(med(ivs)*1000,1)}ms  p90={fmt(p_floor(ivs,.9)*1000,1)}ms  max={fmt(max(ivs)*1000,1)}ms  "
      f"Hz(全程)={ (n-1)/(ts[-1]-ts[0]) :.1f}  采样缺口>10ms: {len(gaps10)}处/{sum(gaps10):.3f}s")

    # ---- 首推进 / 战斗段 ----
    first = next((i + 1 for i, v in enumerate(deltas) if v is not None and v > 0), None)
    if first is None:
        P("无推进 → 战斗段分析跳过")
        return "\n".join(L), None
    bts, bfs = ts[first:], fs[first:]
    span = bts[-1] - bts[0]
    net = bfs[-1] - bfs[0]
    advances = [ts[i + 1] for i, v in enumerate(deltas)
                if i + 1 >= first and v is not None and v > 0]
    aivs = [b - a for a, b in zip(advances, advances[1:])]
    P(f"首推进: 样本idx={first} t={ts[first]:.3f}s (帧值{bfs[0]}，前置平台={fmt(ts[first]-ts[0])}s@帧{fs[0]})  "
      f"末推进 t={advances[-1]:.3f}s  尾静默={fmt(ts[-1]-advances[-1])}s")
    P(f"战斗段: 跨度={span:.3f}s  净推进={net}帧  平均={net/span:.2f}帧/s  推进次数={len(advances)}")
    if aivs:
        P(f"推进间隔: med={fmt(med(aivs)*1000,1)}ms  p90={fmt(p_floor(aivs,.9)*1000,1)}ms  "
          f"max={fmt(max(aivs)*1000,1)}ms  std/mean={ (statistics.pstdev(aivs)/statistics.mean(aivs)) if len(aivs)>1 else 0 :.2f}")

    # ---- 三口径 episode（复刻 analyze_waittrace 结构）----
    dl_legacy = deltas[first - 1:]   # 入边对齐（A 口径）
    dl_canon = deltas[first:]        # 出边对齐（B 口径）
    # B 段（含段身份信息）：runs of 出边==0 → 平台 = 样本 first+s .. first+e
    plats = []  # (a_abs, b_abs, B, C, clipC)
    for s, e in runs_pred(dl_canon, lambda v: v == 0):
        a_abs = first + s
        b_abs = first + e
        b_dur = ts[min(b_abs, n - 1)] - ts[a_abs]
        if b_abs + 1 <= n - 1:
            c_dur = ts[b_abs + 1] - ts[a_abs]
            clip = False
        else:
            c_dur = ts[n - 1] - ts[a_abs]
            clip = True
        plats.append((a_abs, b_abs, b_dur, c_dur, clip))
    # A 段：入边对齐，下标直用 bts
    leg = []
    for s, e in runs_pred(dl_legacy, lambda v: v == 0):
        stop = min(e, len(bts) - 1)
        dur = bts[stop] - bts[s]
        if dur >= THR:
            leg.append((s, stop, dur))
    b_eps = [(a, b, bd) for (a, b, bd, cd, cl) in plats if bd >= THR]
    c_eps = [(a, b, cd) for (a, b, bd, cd, cl) in plats if cd >= THR]
    totA = sum(x[2] for x in leg)
    totB = sum(x[2] for x in b_eps)
    totC = sum(x[2] for x in c_eps)
    P(f"[对账] A口径(发布实现): {len(leg)}段/{totA:.3f}s/{100*totA/span:.2f}%   "
      f"B口径(钉死): {len(b_eps)}段/{totB:.3f}s/{100*totB/span:.2f}%   "
      f"C口径(到下一帧首见): {len(c_eps)}段/{totC:.3f}s/{100*totC/span:.2f}%   (战斗段span={span:.3f}s)")
    P(f"  全部平台数(战斗段,不限阈值)={len(plats)}  阈值下: A/B/C 如上  "
      f"med平台B时长={fmt(med([x[2] for x in plats])*1000,1)}ms")

    # ---- 任务2：Δf==0 区段时长分档（B 口径，战斗段；头平台单列）----
    allB = [x[2] for x in plats]
    P("分档(战斗段全部平台, B口径):  档: 段数/合计s")
    for _, _, name in BUCKETS:
        cnt, tot = bucketize(allB)[name]
        P(f"  {name:>7}: {cnt} / {tot:.3f}")
    epsB = [x[2] for x in b_eps]
    if epsB:
        P("分档(≥0.1s 的 B 段):")
        for _, _, name in BUCKETS:
            sel = [x for x in epsB if (name == "<0.1" and x < 0.1) or
                   (name == "0.1-0.5" and 0.1 <= x < 0.5) or
                   (name == "0.5-1" and 0.5 <= x < 1.0) or
                   (name == "1-5" and 1.0 <= x < 5.0) or
                   (name == ">5" and x >= 5.0)]
            P(f"  {name:>7}: {len(sel)} / {sum(sel):.3f}")
    head_dur = ts[first] - ts[0]
    P(f"头平台(战斗段外, 帧{fs[0]}): {head_dur:.3f}s  → 归档 {'<0.1' if head_dur<0.1 else '0.1-0.5' if head_dur<0.5 else '0.5-1' if head_dur<1 else '1-5' if head_dur<5 else '>5'}")

    # ---- 任务3：分型判据 ----
    maxB = max(allB) if allB else 0.0
    maxC = max([x[3] for x in plats], default=0.0)
    topB = sorted(epsB, reverse=True)[:10]
    dominant = (max(maxB / totB, 0) if totB else 0.0)
    P(f"[分型] 最长完全静止窗(B)={fmt(maxB)}s  最长完全静止窗(C口径=相邻推进最大间隔)={fmt(maxC)}s  "
      f"Top5 B段={[fmt(x) for x in sorted(epsB, reverse=True)[:5]]}")
    # ≥0.1s B 段内部采样缺口（饥饿导致内部漏拍 → 内部并非完全观测）
    gappy = 0
    gap_total_in_eps = 0.0
    max_in_eps_gap = 0.0
    for (a, b, bd) in b_eps:
        inner = [ts[i + 1] - ts[i] for i in range(a, b) if ts[i + 1] - ts[i] > 0.01]
        if inner:
            gappy += 1
            gap_total_in_eps += sum(inner)
            max_in_eps_gap = max(max_in_eps_gap, max(inner))
    P(f"  ≥0.1s B段含内部>10ms缺口的段数={gappy}/{len(b_eps)}  内部缺口合计={gap_total_in_eps:.3f}s  "
      f"段内最大单缺口={fmt(max_in_eps_gap)}s")
    P(f"  单段主导度 max(B段)/Σ(B段) = {fmt(dominant*100,1)}%")
    P(f"  推进间隔 med/p90/max = {fmt(med(aivs)*1000,1)}/{fmt(p_floor(aivs,.9)*1000,1)}/{fmt(max(aivs)*1000,1)}ms")

    # ---- 跳帧（Δf>1）----
    jumps = [(ts[i + 1], fs[i], fs[i + 1], deltas[i]) for i, v in enumerate(deltas)
             if v is not None and v > 1]
    if jumps:
        for (t, f0, f1, dv) in jumps:
            P(f"  跳帧: t={t:.3f}s  {f0}→{f1} (Δf={dv})")
    else:
        P("  跳帧(Δf>1): 0 处")

    # ---- 任务6：速率时间序列（5s 窗 + 1s 窗突变）----
    def rate_at(tq):
        # 返回 tq 时刻的帧值（<=tq 的最后样本）
        lo, hi = 0, n - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if ts[mid] <= tq:
                lo = mid
            else:
                hi = mid - 1
        return fs[lo]

    t0 = ts[first]
    t1 = ts[-1]
    W = 5.0
    w = []
    cur = t0
    while cur < t1:
        nxt = min(cur + W, t1)
        f0 = rate_at(cur)
        f1 = rate_at(nxt)
        w.append(((cur - ts[0], nxt - ts[0]), (f1 - f0) / (nxt - cur)))
        cur = nxt
    rates = [r for _, r in w]
    P("5s窗速率(帧/s, 相对t0): " + " ".join(f"{fmt(r,1)}" for r in rates))
    P(f"  5s窗速率 min={fmt(min(rates),2)} max={fmt(max(rates),2)} med={fmt(med(rates),2)}")
    # 1s 窗 + 突变时刻（相邻窗比 >2x 或 <0.5x，且两侧窗都有推进）
    w1 = []
    cur = t0
    while cur < t1:
        nxt = min(cur + 1.0, t1)
        f0 = rate_at(cur)
        f1 = rate_at(nxt)
        w1.append(((cur - ts[0], nxt - ts[0]), (f1 - f0) / (nxt - cur)))
        cur = nxt
    r1 = [r for _, r in w1]
    changes = []
    for i in range(1, len(r1)):
        a, b = r1[i - 1], r1[i]
        if a > 0 and b > 0 and (b >= 2 * a or b <= 0.5 * a) and abs(b - a) > 1.0:
            changes.append((w1[i][0][0], a, b))
    # 合并相邻突变
    merged = []
    for t, a, b in changes:
        if merged and t - merged[-1][0] < 1.5:
            merged[-1] = (t, merged[-1][1], b)
        else:
            merged.append((t, a, b))
    P(f"1s窗速率突变点(合并<1.5s): {len(merged)} 处")
    for t, a, b in merged[:25]:
        P(f"  t≈{t:.0f}s  {fmt(a,1)}→{fmt(b,1)} 帧/s")
    # 慢期/快期 regime（1s窗，阈值=战斗段中位速率的 50%）
    rmed = med([r for r in r1 if r > 0]) if any(r > 0 for r in r1) else 0
    if rmed:
        lows = [i for i, r in enumerate(r1) if r < 0.5 * rmed]
        runs_low = []
        for i in lows:
            if runs_low and i == runs_low[-1][1] + 1:
                runs_low[-1][1] = i
            else:
                runs_low.append([i, i])
        if runs_low:
            seg = ", ".join(f"[{w1[s][0][0]:.0f}-{w1[e][0][0]+1:.0f}s]" for s, e in runs_low[:12])
            P(f"低速率期(<50%中位{fmt(rmed,1)}): {len(runs_low)} 段  {seg}{' …' if len(runs_low)>12 else ''}")
        else:
            P(f"低速率期(<50%中位{fmt(rmed,1)}): 0 段（速率全程≥中位一半）")
    return "\n".join(L), {"plats": plats, "advances": advances, "ts": ts, "fs": fs,
                          "first": first, "span": span, "leg": leg}


def main():
    out = []
    for tag in TAGS:
        path = BASE / f"l3_1101v4{tag}" / "h8_wait_trace.json"
        txt, _extra = analyze(tag, path)
        out.append(txt)
        out.append("")
    print("\n".join(out))


if __name__ == "__main__":
    main()
