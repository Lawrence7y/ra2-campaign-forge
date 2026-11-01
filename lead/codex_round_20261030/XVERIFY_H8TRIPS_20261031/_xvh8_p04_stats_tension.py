#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 对账探针 p04：窗统计独立重算（不采信 stats 字段）+ frame↔units 轨迹 + q/r 早相可行性。

(A) 由 samples.{t,f} 原始数组按 harness _measure_stats 口径（:4741-4811，帧沿差分）独立重算
    fps_avg / logic_frames / frame_ms p50/p90/max / max_stall_s / n_edges / n_multi_advance /
    tick_miss，与落盘 stats 逐位比（差>1e-6 记 DIFF）。
(B) counters（1Hz）× frame_edges（帧沿时刻）⇒ 每窗 (t_rel→frame) 与 (frame→units) 内插：
    给 q/r 与 hb 各自的「frame→units」采样曲线，检验两族的战斗进度是否可用同一 frame 轴描述。
(C) 可行性上界：若 frame 计数器 battle 起零（e1/hb/k 三趟实证 f≈0 at nav_end+0.1s），
    则 q 的 0→f0 平均 fps = f0/n2w；与同趟窗内 max fps（沿差分帧时的 min 的倒数）与族内
    观察上限 31.4 比较 ⇒ 判定「q 早相是否可能同 hb 早相一样慢」。
只读。
"""
import json, io, sys, os, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

def pctl(vals, q):
    """同 harness _measure_pctl（线性插值口径，需与源件一致）。"""
    if not vals:
        return None
    s = sorted(vals)
    i = q * (len(s) - 1)
    lo = math.floor(i); hi = math.ceil(i)
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (i - lo)

def recompute(m0, hz=500, tick_factor=1.5):
    ts, fs = m0["samples"]["t"], m0["samples"]["f"]
    samples = list(zip(ts, fs))
    st = {}
    t_a, f_a = samples[0]; t_b, f_b = samples[-1]
    span = t_b - t_a
    logic = int(f_b) - int(f_a)
    st["logic_frames"] = logic
    st["hz_effective"] = round(len(samples) / span, 1) if span > 0 else None
    edges = []
    prev = None
    for t, f in samples:
        fi = int(f)
        if prev is None or fi != prev:
            edges.append((fi, t)); prev = fi
    st["n_edges"] = len(edges)
    run_t0, run_f = samples[0]; best = 0.0
    for t, f in samples[1:]:
        if f != run_f:
            if t - run_t0 > best: best = t - run_t0
            run_t0, run_f = t, f
    if samples[-1][0] - run_t0 > best:
        best = samples[-1][0] - run_t0
    st["max_stall_s"] = round(best, 6)
    fms = []; nmulti = 0
    for (fa, ta), (fb, tb) in zip(edges, edges[1:]):
        df = fb - fa
        if df == 1: fms.append((tb - ta) * 1000.0)
        elif df > 1: nmulti += 1
    st["n_multi_advance"] = nmulti
    if fms:
        p50 = pctl(fms, .5); p90 = pctl(fms, .9); p99 = pctl(fms, .99)
        st["frame_ms_p50"] = p50; st["frame_ms_p90"] = p90; st["frame_ms_p99"] = p99
        st["frame_ms_max"] = max(fms); st["frame_ms_min"] = min(fms)
        st["fps_avg"] = logic / span
        st["fps_p50"] = 1000.0 / p50
        st["tick_miss"] = sum(1 for v in fms if v > p50 * tick_factor)
    st["_span"] = span
    return st

def cmp_trip(d, wins):
    print(f"\n--- {d} ---")
    out = {}
    for w in wins:
        p = f"{ROOT}/{d}/measure_w{w}.json"
        if not os.path.isfile(p): continue
        m0 = json.load(open(p, encoding="utf-8"))
        if not isinstance(m0.get("samples"), dict) or not m0["samples"].get("f"):
            print(f"  w{w}: 零样（短路趟）verdict={m0.get('verdict')}"); continue
        st = m0["stats"] or {}
        rc = recompute(m0)
        diffs = []
        for k in ("fps_avg", "logic_frames", "frame_ms_p50", "frame_ms_p90", "frame_ms_max",
                  "max_stall_s", "n_edges", "n_multi_advance", "tick_miss", "fps_p50"):
            a, b = st.get(k), rc.get(k)
            if a is None or b is None:
                diffs.append(f"{k}:落盘={a}/本算={b}"); continue
            if abs(a - b) > 1e-6 if isinstance(a, (int, float)) else a != b:
                diffs.append(f"{k}:落盘={a}/本算={round(b,6)}")
        print(f"  w{w} f[{m0['samples']['f'][0]}→{m0['samples']['f'][-1]}] "
              f"{'逐位一致' if not diffs else 'DIFF: ' + '; '.join(diffs)}")
        if rc.get("frame_ms_min") is None:
            print(f"      本算：零推进窗（主指标 null）stall={rc['max_stall_s']} edges={rc['n_edges']}")
            out[w] = (m0, rc)
            continue
        print(f"      本算 fps_avg={rc['fps_avg']:.4f} p50ms={rc['frame_ms_p50']:.3f} "
              f"p90ms={rc['frame_ms_p90']:.3f} max={rc['frame_ms_max']:.3f} min={rc['frame_ms_min']:.3f} "
              f"(⇒ 本窗瞬时上限 {1000.0/rc['frame_ms_min']:.2f} fps) stall={rc['max_stall_s']} "
              f"edges={rc['n_edges']} multi={rc['n_multi_advance']} tick_miss={rc['tick_miss']}")
        out[w] = (m0, rc)
    return out

print("=" * 78)
print("(A) 窗统计独立重算 vs 落盘 stats")
print("=" * 78)
data = {}
for d, wins in [("l3_20261031ha", [0]), ("l3_20261031hb", [0, 1, 2]),
               ("l3_20261023q", [0, 1, 2]), ("l3_20261023r", [0, 1, 2]),
               ("l3_20261021", [0, 1, 2]), ("l1_20261023e1", [0]),
               ("l1_20261023hb", [0]), ("l1_20261023k", [0]), ("l1_20261023hc", [0])]:
    data[d] = cmp_trip(d, wins)

print("\n" + "=" * 78)
print("(B) frame↔units 轨迹（counters 1Hz 内插到 frame 轴，用同窗 frame_edges 做 t→frame 映射）")
print("=" * 78)
def curve(d, w):
    m0, rc = data[d][w]
    if not m0.get("frame_edges"):
        return None, None
    edges = [(int(f), t) for f, t in m0["frame_edges"]]
    cs = m0["counters"]
    def t2f(t):
        if t <= edges[0][1]: return edges[0][0]
        for (fa, ta), (fb, tb) in zip(edges, edges[1:]):
            if ta <= t <= tb:
                if tb == ta: return fb
                return fa + (fb - fa) * (t - ta) / (tb - ta)
        return edges[-1][0]
    pts = [(t2f(c["t_rel"]), c["units"]) for c in cs]
    return pts, edges

for d, w in [("l3_20261031hb", 0), ("l3_20261031hb", 1), ("l3_20261031hb", 2),
             ("l3_20261023q", 0), ("l3_20261023r", 0), ("l3_20261021", 0)]:
    if d not in data or w not in data[d]:
        print(f"  {d} w{w}: 无件"); continue
    pts, edges = curve(d, w)
    if pts is None:
        print(f"  {d} w{w}: 零推进窗，无沿表"); continue
    print(f"  {d} w{w}: frame {round(pts[0][0])}→{round(pts[-1][0])}  units {pts[0][1]}→{pts[-1][1]}"
          f"  Δu/Δf={(pts[-1][1]-pts[0][1])/(pts[-1][0]-pts[0][0]):.4f}")
    print(f"      units 序列(前8): {[u for _f,u in pts[:8]]}")

print("\n" + "=" * 78)
print("(C) q/r 早相可行性：0→f0 平均 fps 与同趟窗内瞬时上限/族内 cap")
print("=" * 78)
hdr = "{:<16}{:>7}{:>9}{:>10}{:>11}{:>10}{:>12}{:>14}"
print(hdr.format("trip", "f0", "nav→w0", "avg0→f0", "窗内min_ms", "窗内峰值", "族内cap", "早相可否=慢"))
FAM_CAP = 31.4
for d in ("l3_20261023q", "l3_20261023r", "l3_20261021", "l3_20261031ha", "l3_20261031hb"):
    if d not in data or 0 not in data[d]:
        print(f"  {d}: 无 w0 样"); continue
    m0, rc = data[d][0]
    f0 = m0["samples"]["f"][0]
    qf = json.load(open(f"{ROOT}/{d}/qc151_fields.json", encoding="utf-8"))
    def gv(grp, key):
        v = [e["value"] for e in qf if e.get("group") == grp and e.get("key") == key]
        return v[-1] if v else None
    fr_s = gv("BUDGET", "stage_seconds:frame"); setl = gv("MEASURE", "settle_seconds")
    fw = gv("MEASURE", "h7_frame_wait")
    n2w = (fr_s or 0) + (setl or 0)
    avg = f0 / n2w if n2w else None
    peak = 1000.0 / rc["frame_ms_min"] if rc.get("frame_ms_min") else None
    if fw:
        avg2 = fw["n"] / fw["wait_s"]
        print(f"  {d:<16}{f0:>7}{n2w:>9.2f}{avg2:>10.2f}{rc['frame_ms_min']:>11.2f}"
              f"{peak:>10.2f}{FAM_CAP:>12}"
              f"{'★ H8 实测 0→%d 用 %s s = %.2f fps（绑帧等待本体）' % (fw['n'], fw['wait_s'], avg2)}")
    else:
        verdict = "不可（需 >cap）" if avg and avg > FAM_CAP else "可能"
        print(hdr.format(d, f0, round(n2w, 2), round(avg, 2), round(rc["frame_ms_min"], 2),
                         round(peak, 2), FAM_CAP, verdict))

print("""
  推理口径（判定用，写在 stdout 以免误读）：
   frame 计数器 battle 起零的实证 = l1_20261023e1 / hb / k 三趟（短路臂，nav_end+0.1s 进 measure，
   f[0]=0，4s settle 内 0→8/0→40/0→18）⇒ f0 即「battle 起累计帧数」，非进程起累计。
   ∴ q/r 的 0→f0 平均 fps = f0 / (frame 段 + settle)，为「早相平均」的**上界时长口径**。""")
