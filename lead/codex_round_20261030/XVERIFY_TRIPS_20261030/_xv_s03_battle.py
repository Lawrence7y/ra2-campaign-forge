#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s03：① 战斗 2 趟 —— gate 字段回读 / 500Hz 原始序列自算 ≥0.5s frame 冻结区段 /
   frame_ms 分位数独立重算 / counters 单调性与变化点 / W1W2 冻结起点 vs units 停变点对齐。
"""
import json, io, sys, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = r"D:\Project\ra2-campaign-forge"
T = ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
DIRS = ["l3_20261023q", "l3_20261023r"]
CLAIM_STATS = {  # 台账 GOAL1_BATCH1_RESULT 自报
    "l3_20261023q": dict(fps_avg=31.12, p50=31.9, p90=37.2, p99=44.4, mx=68.4, stalls=0, units0_gate=974, pre_fps=31.34, u_first=953, u_last=854, span="2955->3733"),
    "l3_20261023r": dict(fps_avg=31.32, p50=32.1, p90=36.0, p99=41.4, mx=45.7, stalls=0, units0_gate=941, pre_fps=30.72, u_first=923, u_last=842, span="3100->3883"),
}
THRESH = 0.5  # 台账口径：frame 连续不变 ≥0.5s

def pct(sorted_vals, q):
    """文件里 frame_ms_* 用的是哪种分位法未知，故两种都算，报告区间。"""
    n = len(sorted_vals)
    lin = sorted_vals[min(n - 1, int(round((n - 1) * q)))]
    idx = (n - 1) * q
    lo, hi = int(idx), min(int(idx) + 1, n - 1)
    frac = idx - lo
    interp = sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac
    return lin, interp

def stalls_from(t, f, thr=THRESH):
    """返回 frame 值连续不变且时长 ≥thr 的区段列表 (start_idx, end_idx, t0, t1, dur, frame)。"""
    segs, i, n = [], 0, len(t)
    while i < n - 1:
        if f[i] == f[i + 1]:
            j = i
            while j + 1 < n and f[j + 1] == f[i]:
                j += 1
            dur = t[j] - t[i]
            if dur >= thr:
                segs.append((i, j, t[i], t[j], round(dur, 4), f[i]))
            i = j + 1
        else:
            i += 1
    return segs

for d in DIRS:
    print("=" * 70)
    print("###", d)
    m = json.load(open(f"{T}\\{d}\\measure_w0.json", encoding="utf-8"))
    cl = CLAIM_STATS[d]
    print(f"(8) gate 字段回读: {json.dumps(m['gate'], ensure_ascii=False)}")
    print(f"    pre_fps15 实际={m['gate']['pre_fps15']} claim={cl['pre_fps']} | units0 实际={m['gate']['units0']} claim={cl['units0_gate']}")
    print(f"    注意 gate_fps15_min 字段值={m['gate']['gate_fps15_min']}（台账/派单称『门 25』⇒ 需甄别该 25 不是件内 gate 常量）")
    print(f"    ok={m['gate']['ok']} verdict={m['verdict']} error={m['error']} map_sha={m['map_sha256'][:8]} gamemd_sha={m['gamemd_sha256'][:8]} hz={m['hz']} span_s={m['span_s']} window={m['window']}")
    t, f = m["samples"]["t"], m["samples"]["f"]
    print(f"(9) 原始序列: len(t)={len(t)} len(f)={len(f)} t跨度={round(t[-1]-t[0],4)}s 实际采样率={round((len(t)-1)/(t[-1]-t[0]),2)}Hz")
    print(f"    frame 首={f[0]} 末={f[-1]} (claim span {cl['span']})")
    segs = stalls_from(t, f)
    print(f"    自算 ≥{THRESH}s frame 不变区段数 = {len(segs)} (claim {cl['stalls']})  -> {'MATCH' if len(segs)==cl['stalls'] else 'DIFF'}")
    if segs: print(f"      区段={segs[:10]}")
    # 敏感阈值扫描：证明结论不依赖 0.5s 这个取值
    for thr in (0.2, 0.3, 0.5, 1.0):
        print(f"      阈值 {thr}s -> 区段数 {len(stalls_from(t,f,thr))}")
    df = [round(t[i+1]-t[i], 6) for i in range(len(t)-1) if f[i+1] != f[i]]
    nonadvance = [round(t[i+1]-t[i], 6) for i in range(len(t)-1) if f[i+1] == f[i]]
    print(f"    帧推进间隔: n={len(df)} max={max(df)} p50={round(statistics.median(df),4)}")
    print(f"    帧不推进(相邻同值)间隔: n={len(nonadvance)} max={max(nonadvance)} => 单样本级最大 gap")
    # frame_ms 重算（帧间隔 = 相邻 frame 变化点的 t 差）
    fm = [round(t[i+1]-t[i], 6) for i in range(len(t)-1) if f[i+1] != f[i]]
    srt = sorted(fm)
    for q, nm in ((0.5, "p50"), (0.9, "p90"), (0.99, "p99"), (1.0, "max")):
        lin, interp = pct(srt, q)
        key = {"p50": "frame_ms_p50", "p90": "frame_ms_p90", "p99": "frame_ms_p99", "max": "frame_ms_max"}[nm]
        ck = {"p50": "p50", "p90": "p90", "p99": "p99", "max": "mx"}[nm]
        print(f"    [错法-相邻样本差] frame_ms {nm}: 自算 nearest={round(lin*1000,4)} interp={round(interp*1000,4)} | 文件 stats={round(m['stats'][key],4)} | 台账 claim={cl[ck]}  << 正确重算见 s03b（按帧 run 边界）")
    fps = [1/x for x in fm if x > 0]
    print(f"    fps_avg 自算={round(sum(fps)/len(fps),4)} | 文件={round(m['stats']['fps_avg'],4)} | claim={cl['fps_avg']}")
    print(f"    文件 max_stall_s={m['stats']['max_stall_s']} logic_frames={m['stats']['logic_frames']} n_edges={m['stats']['n_edges']} samples={m['stats']['samples']} hz_effective={m['stats']['hz_effective']} tick_miss={m['stats']['tick_miss']}")
    # (10) counters 单调性与变化点
    cs = m["counters"]
    u = [c["units"] for c in cs]
    print(f"(10) counters n={len(cs)} units 轨迹={u}")
    print(f"    首={u[0]}(claim {cl['u_first']}) 末={u[-1]}(claim {cl['u_last']}) 净变化={u[-1]-u[0]} claim=-{cl['u_first']-cl['u_last']}")
    inc = [i for i in range(1, len(u)) if u[i] > u[i-1]]
    eq = [i for i in range(1, len(u)) if u[i] == u[i-1]]
    print(f"    严格逐秒下降? {'YES' if not inc and not eq else 'NO'} 上升步={inc} 持平步={eq}")
    print(f"    变化点数(相邻不等)={sum(1 for i in range(1,len(u)) if u[i]!=u[i-1])}/{len(u)-1} => 非静态在场")
    other = {k: [c.get(k) for c in cs] for k in ("infantry", "aircraft", "g", "b", "techno")}
    for k, v in other.items():
        print(f"    {k}: first={v[0]} last={v[-1]} 变化点数={sum(1 for i in range(1,len(v)) if v[i]!=v[i-1])}/{len(v)-1}")
    print(f"    末 counter t_rel={cs[-1]['t_rel']} (span_s={m['span_s']}) => W0 内全程 units 单调（无转平/归零）")

print("\n" + "=" * 70 + "\n### (11) W1/W2 终局定性")
for d in DIRS:
    print("---", d)
    for w in ("w0", "w1", "w2"):
        p = f"{T}\\{d}\\measure_{w}.json"
        try:
            x = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            print(f"  measure_{w}: 缺文件/读败 {e}"); continue
        t, f = x["samples"]["t"], x["samples"]["f"]
        segs = stalls_from(t, f)
        last = segs[-1] if segs else None
        print(f"  {w}: verdict={x.get('verdict')} span={round(t[-1]-t[0],3)}s samples={len(t)} frame {f[0]}->{f[-1]} "
              f"≥0.5s 冻结区段数={len(segs)} 末段(冻结帧={last[5] if last else None}, dur={last[4] if last else None}s, 起于 t={last[2] if last else None})")
        if segs:
            print(f"      全部区段={[ (s[5], s[4]) for s in segs ][:12]}")
        cs = x.get("counters") or []
        if cs:
            u = [c["units"] for c in cs]
            bb = [c.get("b") for c in cs]
            print(f"      counters units={u[:30]} b={[c.get('b') for c in cs][:30]}")
            flat = [i for i in range(1, len(u)) if u[i] == u[i-1]]
            print(f"      units 持平步 idx={flat}")
        st = x.get("stats") or {}
        print(f"      stats frame_ms_max={st.get('frame_ms_max')} max_stall_s={st.get('max_stall_s')} fps_avg={st.get('fps_avg')} logic_frames={st.get('logic_frames')}")

print("\n### qc151_fields.json（终局/胜负字段回读）")
for d in DIRS:
    x = json.load(open(f"{T}\\{d}\\qc151_fields.json", encoding="utf-8"))
    print("---", d, "type", type(x).__name__, "len", len(x) if isinstance(x, list) else "")
    if isinstance(x, list):
        keys = set()
        for r in x:
            if isinstance(r, dict): keys |= set(r.keys())
        print("   字段名=", sorted(keys))
        for r in x[:6]:
            print("   ", json.dumps(r, ensure_ascii=False)[:300])
        for r in x[-4:]:
            print("   TAIL", json.dumps(r, ensure_ascii=False)[:300])
