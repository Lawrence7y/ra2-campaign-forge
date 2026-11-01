# -*- coding: utf-8 -*-
"""_h8_waittrace_decomp.py - H8-7 等待环逐拍轨迹分解（v4-b 超时趟 vs v4-c 达标趟）。

离线、零真机、零 E3。输入=两趟 h8_wait_trace.json（[t_rel_s, frame] 逐拍）。
stdout 由 Bash 重定向落盘（tee 语义由重定向承担）。口径：
  - beat = 一次 poll；delta = 相邻拍 frame 差；None=读败拍。
  - 相位切分：首推进（frame 0→1）前=装载段；其后=战斗段（终局=最后拍）。
  - 停滞episode=战斗段内连续 delta==0 且时长>=100ms；读败段单列不计入停滞。
"""

import json
import statistics as st

TRIPS = {
    "v4b": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4b/h8_wait_trace.json",
    "v4c": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/h8_wait_trace.json",
}


def P(s):
    print(s)


def runs_of(seq, pred):
    """[(start_i, end_i_exclusive)] of maximal runs where pred(x) True."""
    out = []
    i = 0
    n = len(seq)
    while i < n:
        if pred(seq[i]):
            j = i
            while j < n and pred(seq[j]):
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


for tag, path in TRIPS.items():
    d = json.load(open(path, encoding="utf-8"))
    S = d["samples"]
    ts = [s[0] for s in S]
    fs = [s[1] for s in S]
    wait_s = d["wait_s"]
    P("")
    P("=" * 78)
    P("## %s  (%s)" % (tag, path.rsplit("/", 1)[-1]))
    P("   n=%s verdict=%s wait_s=%s beats=%d last_t=%.3fs last_frame=%s"
      % (d["n"], d["verdict"], wait_s, len(S), ts[-1], fs[-1]))
    # 拍节律
    ivs = [b - a for a, b in zip(ts, ts[1:])]
    P("   拍率=%.1fHz 中位间隔=%.4fs p90=%.4fs max=%.4fs"
      % (len(S) / wait_s, st.median(ivs),
         sorted(ivs)[int(0.9 * (len(ivs) - 1))], max(ivs)))
    # delta 直方
    dh = {"None": 0, "p0": 0, "p1": 0, "p2": 0, "pgt2": 0}
    deltas = []
    for a, b in zip(fs, fs[1:]):
        if a is None or b is None:
            dh["None"] += 1
            deltas.append(None)
        else:
            k = b - a
            deltas.append(k)
            if k == 0:
                dh["p0"] += 1
            elif k == 1:
                dh["p1"] += 1
            elif k == 2:
                dh["p2"] += 1
            else:
                dh["pgt2"] += 1
    P("   delta直方(相邻拍): " + "  ".join("%s=%d" % (k, v) for k, v in dh.items()))
    # 相位切分：首推进
    first_adv = None
    for i in range(1, len(fs)):
        if fs[i] is not None and fs[i - 1] is not None and fs[i] > fs[i - 1]:
            first_adv = i
            break
    if first_adv is None:
        P("   !! 全程零推进")
        continue
    P("   首推进: i=%d t=%.3fs (frame %s->%s) —— 装载段=%.3fs"
      % (first_adv, ts[first_adv], fs[first_adv - 1], fs[first_adv], ts[first_adv]))
    bts = ts[first_adv:]
    bfs = fs[first_adv:]
    bdl = deltas[first_adv - 1:]
    b_span = bts[-1] - bts[0]
    P("   战斗段: t=%.3fs..%.3fs 跨度=%.3fs 拍数=%d 首/末帧=%s/%s"
      % (bts[0], bts[-1], b_span, len(bts), bfs[0], bfs[-1]))
    adv_frames = bfs[-1] - bfs[0]
    P("   战斗段净推进=%d帧 等效平均=%.1f帧/s" % (adv_frames, adv_frames / b_span))
    # 读败段
    nf = runs_of(bdl, lambda x: x is None)
    if nf:
        tot = sum(bts[e] - bts[s] for s, e in nf)
        P("   读败段(delta=None): %d 段 合计=%.3fs" % (len(nf), tot))
    else:
        P("   读败段(delta=None): 0")
    # 跳帧(delta>2)
    jumps = [i for i in range(len(bdl)) if bdl[i] is not None and bdl[i] > 2]
    P("   跳帧拍(delta>2): %d 处" % len(jumps) + ("  " + str(jumps[:5]) if jumps else ""))
    # 停滞episode（delta==0 连续段，时长>=0.1s）
    stalls = []
    for s0, e0 in runs_of(bdl, lambda x: x == 0):
        end_t = bts[e0] if e0 < len(bts) else bts[-1]
        dur = end_t - bts[s0]
        if dur >= 0.1:
            stalls.append((bts[s0], end_t, dur, bfs[s0], bfs[e0 - 1]))
    stall_tot = sum(x[2] for x in stalls)
    P("   停滞episode(>=100ms): %d 段 合计=%.3fs 占战斗段=%.1f%%"
      % (len(stalls), stall_tot, 100.0 * stall_tot / b_span))
    if stalls:
        top = sorted(stalls, key=lambda x: -x[2])[:10]
        P("   Top10(起点s,终点s,时长s,持帧):")
        for x in top:
            P("     %.3f -> %.3f  dur=%.3f  frame=%s..%s" % x)
        gaps = [b[0] - a[0] for a, b in zip(stalls, stalls[1:])]
        if len(gaps) >= 2:
            P("   停滞起始间隔: n=%d 中位=%.3fs p25=%.3fs p75=%.3fs"
              % (len(gaps), st.median(gaps), sorted(gaps)[len(gaps) // 4],
                 sorted(gaps)[(3 * len(gaps)) // 4]))
    # 突发节律：推进拍（delta>=1）之间的间隔
    adv_idx = [i for i in range(len(bdl)) if bdl[i] is not None and bdl[i] >= 1]
    if len(adv_idx) >= 2:
        ag = [bts[b] - bts[a] for a, b in zip(adv_idx, adv_idx[1:])]
        P("   推进拍间隔: n=%d 中位=%.4fs p10=%.4fs p90=%.4fs（中位小=爆发节律）"
          % (len(ag), st.median(ag), sorted(ag)[len(ag) // 10],
             sorted(ag)[(9 * len(ag)) // 10]))
    # 尾段（超时趟重点）
    last_adv = max(i for i in range(len(bdl)) if bdl[i] is not None and bdl[i] >= 1)
    P("   末推进: t=%.3fs（其后至末拍 %.3fs 无推进）"
      % (bts[last_adv], bts[-1] - bts[last_adv]))

P("")
P("## 口径脚注（如实）")
P("   1) Δ=0>=100ms 停滞口径不区分『均匀慢』与『真停滞』：v4-b 推进间隔中位 343ms ⇒")
P("      单是慢节律即产生 ~340ms 的 Δ=0 段；89.6%/20.5% 应读作『非推进占比』上界口径。")
P("      更稳的跨趟不变量：推进拍间隔中位 343ms vs 66ms、拍节律饥饿（p90/max）、读败=0、")
P("      v4-c Top 停滞 0.19-0.24s=其中位推进间隔(66ms)的 ~3 倍（真停滞性质较实）。")
P("   2) 装载段=等待起点→首推进（frame=0 段），含菜单/读图；非纯读图时长。")
P("   3) 两趟等待段读败=0 ⇒ 停滞非读通道伪影（harness 侧与 A 席游戏侧 occ_a 双独立同向）。")
