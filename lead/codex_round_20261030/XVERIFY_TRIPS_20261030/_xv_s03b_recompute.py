#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s03b：① 战斗趟 frame_ms / 停顿的**正确独立重算**（按 frame run 边界，即 frame_edges），
   并与文件 stats.* 逐字段比对；同时核 ≥0.5s 停顿的两种口径（frame 不变时长 / 帧间隔）。
"""
import json, io, sys, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = r"D:\Project\ra2-campaign-forge"
T = ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
DIRS = ["l3_20261023q", "l3_20261023r"]
CLAIM = {"l3_20261023q": dict(p50=31.9, p90=37.2, p99=44.4, mx=68.4, fps=31.12, stalls=0),
         "l3_20261023r": dict(p50=32.1, p90=36.0, p99=41.4, mx=45.7, fps=31.32, stalls=0)}

def quantile(srt, q, method):
    n = len(srt)
    if method == "nearest":
        return srt[min(n - 1, int(round((n - 1) * q)))]
    if method == "low":
        return srt[int((n - 1) * q)]
    if method == "high":
        return srt[int((n - 1) * q) + (1 if (n - 1) * q % 1 else 0)]
    idx = (n - 1) * q
    lo, hi = int(idx), min(int(idx) + 1, n - 1)
    return srt[lo] * (1 - (idx - lo)) + srt[hi] * (idx - lo)

def runs(t, f):
    """返回每个 frame 值的 run: (frame_value, t_start, t_end, dur_of_hold)。"""
    out, i, n = [], 0, len(t)
    while i < n:
        j = i
        while j + 1 < n and f[j + 1] == f[i]:
            j += 1
        out.append((f[i], t[i], t[j], t[j] - t[i]))
        i = j + 1
    return out

for d in DIRS:
    print("=" * 70); print("###", d)
    m = json.load(open(f"{T}\\{d}\\measure_w0.json", encoding="utf-8"))
    t, f = m["samples"]["t"], m["samples"]["f"]
    st = m["stats"]; cl = CLAIM[d]
    R = runs(t, f)
    # 口径A：帧间隔 = 相邻 run 起点之差（frame k 的显示时长）
    edge_starts = [r[1] for r in R]
    fi = [round(edge_starts[i+1]-edge_starts[i], 6) for i in range(len(edge_starts)-1)]
    # 口径B：run 时长（同值持续跨度，末样本-首样本，偏小一个采样周期）
    hold = [r[3] for r in R]
    srtA = sorted(fi)
    print(f"  run 数={len(R)} (文件 n_edges={st['n_edges']} logic_frames={st['logic_frames']})")
    print(f"  口径A 帧间隔(s): mean={round(statistics.mean(srtA)*1000,4)}ms p50 p90 p99 max:")
    for q, nm in ((0.5,'p50'),(0.9,'p90'),(0.99,'p99'),(1.0,'max')):
        v = srtA[min(len(srtA)-1,int(round((len(srtA)-1)*q)))] if nm=='max' else None
        val = max(srtA) if nm=='max' else quantile(srtA, q, "linear")
        key = {"p50":"frame_ms_p50","p90":"frame_ms_p90","p99":"frame_ms_p99","max":"frame_ms_max"}[nm]
        c = cl[{'p50':'p50','p90':'p90','p99':'p99','max':'mx'}[nm]]
        print(f"    {nm}: 自算A={round(val*1000,4)} ms | 文件 stats={round(st[key],4)} | 台账={c} -> {'MATCH' if abs(round(val*1000,1)-c)<0.15 else 'CHECK'}")
    print(f"  fps_avg 自算A=(帧数/总时长)={round((len(fi))/(t[-1]-t[0]),4)} | 1/mean={round(1/statistics.mean(srtA),4)} | 文件={round(st['fps_avg'],4)} | 台账={cl['fps']}")
    print(f"  口径B run 时长 max={round(max(hold),6)}s (≥0.5s 的 run 数={sum(1 for h in hold if h>=0.5)})")
    print(f"  口径A 帧间隔 ≥0.5s 的帧数={sum(1 for x in fi if x>=0.5)} | ≥0.2s={sum(1 for x in fi if x>=0.2)} | ≥0.1s={sum(1 for x in fi if x>=0.1)}")
    print(f"  文件 max_stall_s={st['max_stall_s']} (=frame_ms_max? {abs(st['max_stall_s']*1000-st['frame_ms_max'])<1e-6}) | tick_miss={st['tick_miss']} n_multi_advance={st['n_multi_advance']}")
    print(f"  hz_effective 文件={st['hz_effective']} 自算={round((len(t)-1)/(t[-1]-t[0]),2)}")
    # 采样轴是否有空洞
    dd = [round(t[i+1]-t[i],6) for i in range(len(t)-1)]
    print(f"  采样间隔 max={max(dd)} min={min(dd)} => 无 >0.1s 空洞: {max(dd)<0.1}")
    # counters 严格单调
    u = [c["units"] for c in m["counters"]]
    print(f"  units 逐秒: {u}")
    print(f"  严格递减(每步都降)? {all(u[i]>u[i+1] for i in range(len(u)-1))} | 首末降={u[0]-u[-1]} | 任一步持平/上升 idx={[i for i in range(1,len(u)) if u[i]>=u[i-1]]}")
    print(f"  counters 步进 t_rel 间隔中位={round(statistics.median([m['counters'][i]['t_rel']-m['counters'][i-1]['t_rel'] for i in range(1,len(m['counters']))]),4)}s")
