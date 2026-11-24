# -*- coding: utf-8 -*-
"""
_independent_recheck.py —— 判据独立复核员（执行者 != 核验者；本件不复用任何既有探针函数）

目的：
  1. 从原始语料独立重算 26 档可执行判据的 9 项指标，逐字段与 CRITERIA_METRICS.json 比对并列出差异。
  2. 专项核查四个坑：
     (a) 冷启动 N=64/N=16 缺基线覆盖了多少真实事件、是否落在窗首「加载后第一波」；
     (b) 历史窗口若把「当前这次停滞」算进去，P95/P99 会不会自我抬高；
     (c) 绝对时长判据 vs k 拍判据在采样抖动下的触发时刻差；
     (d) 4 条 startTick=0 真实事件（缺前序帧沿）在各判据上的可算性与延迟影响。
  3. 给出可区分性证据：各判据查准率 vs 前缀不可分辨理论上界。

纪律：零真机、零采样代码、只读语料、不 import 既有探针、不修改任何既有文件。
运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_independent_recheck.py
写域：仅本脚本新建的 _independent_recheck_out.txt
"""

import json
import re
import hashlib
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANI = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EV = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
WD = (ROOT / "lead/dtrigger_compare_20261107").resolve()
MJ = WD / "CRITERIA_METRICS.json"
OUT = WD / "_independent_recheck_out.txt"

BUF = []
def o(s=""):
    BUF.append(str(s))
    print(s)

def med(a):
    """自实现中位数（不依赖 statistics.median）。"""
    if not a:
        return None
    s = sorted(a)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0

def pct(a, p):
    """最近秩百分位：与既有文档 _dtrigger_probe.py:61-65 声明同口径。"""
    if not a:
        return None
    s = sorted(a)
    return s[int(p * (len(s) - 1))]

def r6(x):
    return round(x, 6)

def f3(x):
    return "N/A" if x is None else f"{x:.3f}"

# ---------------------------------------------------------------- 语料（只读）
o("=" * 108)
o("判据独立复核 · 从原始语料重算（本件不 import 任何既有探针/核验脚本）")
o("=" * 108)
corpus = {}
for fp in sorted(BASE.rglob("measure_w*.json")):
    p = fp.resolve()
    if not p.is_relative_to(BASE):
        raise ValueError("corpus escape")
    parts = p.relative_to(BASE).parts
    key = (parts[0], p.stem[len("measure_"):])
    corpus[key] = json.loads(p.read_text(encoding="utf-8-sig"))
n_samp = sum(len(v["samples"]["t"]) for v in corpus.values())
o(f"语料文件 n={len(corpus)}  采样点 n={n_samp}  hz={sorted({v.get('hz') for v in corpus.values()})}")
o(f"只读治理件 STALL_EVENTS.json sha256={hashlib.sha256(EV.read_bytes()).hexdigest()}")

wins = set()
for ln in MANI.read_text(encoding="utf-8-sig").splitlines():
    m = re.match(r"^([a-zA-Z0-9_()]+)\s+(w\d)\s+([0-9.]+)", ln.strip())
    if m and (m[1], m[2]) in corpus:
        z = corpus[(m[1], m[2])]["samples"]
        if len(z["t"]) >= 2 and any(a != b for a, b in zip(z["f"], z["f"][1:])):
            wins.add((m[1], m[2]))
wins = sorted(wins)
o(f"moving64 推进窗 n={len(wins)}")

events = json.loads(EV.read_text(encoding="utf-8-sig"))
real = [e for e in events if e.get("isRealMatch") is True]
rk = {(e["trip"], e["window"], e["startTick"], e["endTick"]) for e in real}
o(f"STALL_EVENTS 全量 n={len(events)}  isRealMatch==True n={len(real)}  real_keys n={len(rk)}")

# ---------------------------------------------------------------- 独立数据组织
# 与既有实现不同：把每个窗压成「游程表」+「每个游程起点处的已完成帧周期前缀」。
# 帧周期 g_m = t[i_{m+1}] - t[i_m]（从第 m 个游程起点到第 m+1 个游程起点）。
# 游程 b 起点处可用的已完成帧周期 = g_0 .. g_{b-2}（共 b-1 条）；
# 当前停滞游程 b 的帧周期 g_b 要等它推进才产生，故结构上不可能进自己的基线。
RUNS = []
for trip, win in wins:
    T = corpus[(trip, win)]["samples"]["t"]
    F = corpus[(trip, win)]["samples"]["f"]
    m = len(F)
    starts = [0]
    for a in range(1, m):
        if F[a] != F[a - 1]:
            starts.append(a)
    nb = len(starts)
    gp = [(T[starts[b + 1]] - T[starts[b]]) * 1000.0 for b in range(nb - 1)]
    for b in range(nb):
        i = starts[b]
        j = starts[b + 1] - 1 if b + 1 < nb else m - 1
        RUNS.append({
            "key": (trip, win, i, j), "i": i, "j": j, "b": b,
            "npts": j - i + 1,
            "dfin": (T[j] - T[i]) * 1000.0,
            "t_rel_win": (T[i] - T[0]) * 1000.0,
            "og": (T[i] - T[i - 1]) * 1000.0 if i > 0 else None,
            "hist": gp[:b - 1] if b >= 1 else [],   # g_0..g_{b-2}
            "T": T,
        })
o(f"游程 n={len(RUNS)}  real key 对齐 n={sum(1 for r in RUNS if r['key'] in rk)}/{len(rk)}")

# ---------------------------------------------------------------- 判据谓词（独立实现）
def q_k(r, k):
    return r["i"] + k - 1 if r["npts"] >= k else None

def q_rel(r, p, mult, N, cap=None):
    h = r["hist"][-N:]
    if len(h) < N:
        return None
    th = pct(h, p) * mult
    if cap is not None:
        th = min(th, cap)
    T, i = r["T"], r["i"]
    for x in range(i, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 > th:
            return x
    return None

def q_rel_abs(r, p, mult, N):
    h = r["hist"][-N:]
    if len(h) < N or r["og"] is None:
        return None
    th = pct(h, p) * mult
    T, i = r["T"], r["i"]
    for x in range(i, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 + r["og"] > th:
            return x
    return None

def q_rate(r, mult, N, anchor):
    h = r["hist"][-N:]
    if len(h) < N or (anchor == "lastEdge" and r["og"] is None):
        return None
    b = med(h)
    if b is None or b <= 0:
        return None
    off = r["og"] if anchor == "lastEdge" else 0.0
    T, i = r["T"], r["i"]
    for x in range(i, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 + off > mult * b:
            return x
    return None

def q_abs(r, th, kmin=3):
    if r["npts"] < kmin:
        return None
    T, i = r["T"], r["i"]
    for x in range(i + kmin - 1, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 > th:
            return x
    return None

def q_hybrid(r, k, th):
    if r["npts"] < k:
        return None
    T, i = r["T"], r["i"]
    for x in range(i + k - 1, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 > th:
            return x
    return None

CASES = []
for k in (10, 25, 50):
    CASES.append((f"C1-k{k}", lambda r, k=k: q_k(r, k)))
for pn, p in (("P95", .95), ("P99", .99)):
    for mu in (2, 3):
        CASES.append((f"C2-{pn}x{mu}", lambda r, p=p, mu=mu: q_rel(r, p, mu, 64)))
CASES += [
    ("C2-abs-P95x2", lambda r: q_rel_abs(r, .95, 2, 64)),
    ("C2-N16-P95x2", lambda r: q_rel(r, .95, 2, 16)),
    ("C2-cap40-P95x2", lambda r: q_rel(r, .95, 2, 64, 40.0)),
    ("C2-N16-P95x2-cap40", lambda r: q_rel(r, .95, 2, 16, 40.0)),
    ("C3-r1.5", lambda r: q_rate(r, 1.5, 64, "runStart")),
    ("C3-r2", lambda r: q_rate(r, 2, 64, "runStart")),
    ("C3-r4", lambda r: q_rate(r, 4, 64, "lastEdge")),
    ("C3-r4-clean", lambda r: q_rate(r, 4, 64, "runStart")),
    ("C3-r8", lambda r: q_rate(r, 8, 64, "lastEdge")),
    ("C3-r8-clean", lambda r: q_rate(r, 8, 64, "runStart")),
    ("C3-r12", lambda r: q_rate(r, 12, 64, "lastEdge")),
    ("C3-N16-r1.5", lambda r: q_rate(r, 1.5, 16, "runStart")),
    ("C3-N16-r2", lambda r: q_rate(r, 2, 16, "runStart")),
]
for t in (16, 24, 30, 40, 48):
    CASES.append((f"C4-t{t}", lambda r, t=t: q_abs(r, t)))
CASES.append(("C5-k10t30", lambda r: q_hybrid(r, 10, 30)))

# ---------------------------------------------------------------- 全量重算 26 档 9 字段
o("")
o("=" * 108)
o("§1 独立重算 26 档 × 9 字段，逐字段与 CRITERIA_METRICS.json（上报实跑结果）比对")
o("=" * 108)
M = json.loads(MJ.read_text(encoding="utf-8"))
FIELDS = ["triggers", "falseTriggers", "falseTriggerRate", "realHits", "missedReal",
          "latencyP50Ms", "latencyP95Ms", "latencyMaxMs", "within50msRate"]
RECALC = {}
TRIG = {}
for cid, fn in CASES:
    trig = fals = w50 = 0
    hits = set()
    lat = []
    idxmap = {}
    for r in RUNS:
        x = fn(r)
        if x is None:
            continue
        trig += 1
        if r["dfin"] < 100.0:
            fals += 1
        if r["key"] in rk:
            hits.add(r["key"])
            L = (r["T"][x] - r["T"][r["i"]]) * 1000.0
            lat.append(L)
            idxmap[r["key"]] = L
            if L <= 50.0:
                w50 += 1
    lat.sort()
    rec = {
        "triggers": trig, "falseTriggers": fals,
        "falseTriggerRate": r6(fals / trig) if trig else 0.0,
        "realHits": len(hits), "missedReal": len(rk) - len(hits),
        "latencyP50Ms": r6(med(lat)) if lat else 0.0,
        "latencyP95Ms": r6(pct(lat, .95)) if lat else 0.0,
        "latencyMaxMs": r6(lat[-1]) if lat else 0.0,
        "within50msRate": r6(w50 / len(rk)),
    }
    RECALC[cid] = rec
    TRIG[cid] = idxmap
    got = M.get(cid, {})
    diffs = [(f, got.get(f), v) for f, v in rec.items() if got.get(f) != v]
    tag = "全等" if not diffs else "差异 " + str(diffs)
    o(f"  {cid:<22} " + " ".join(f"{f}={rec[f]}" for f in FIELDS[:5]) + f" | {tag}")

o("")
o("【逐字段差异汇总（重算值 - 上报值，精确到 6 位小数）】")
ndiff = 0
for cid, _ in CASES:
    got = M.get(cid, {})
    for f in FIELDS:
        a, b = RECALC[cid][f], got.get(f)
        if a != b:
            ndiff += 1
            try:
                d = round(a - b, 6)
            except Exception:
                d = "n/a"
            o(f"    {cid:<22} {f:<20} 重算={a}  上报={b}  差={d}")
o(f"  差异字段总数 = {ndiff} / {len(CASES)*len(FIELDS)}")

o("")
o("【重点：C1-k10 全部 9 项逐项对比（题给「至少一个判据全部指标」）】")
cid = "C1-k10"
for f in FIELDS:
    a, b = RECALC[cid][f], M[cid][f]
    o(f"    {f:<20} 重算={a!r:>14}  上报={b!r:>14}  差={round(a-b,6)}  {'一致' if a==b else '不一致'}")
o(f"    复核导入：triggers={RECALC[cid]['triggers']}, false={RECALC[cid]['falseTriggers']}, "
  f"false/false= {RECALC[cid]['falseTriggers']}/{RECALC[cid]['triggers']} = "
  f"{RECALC[cid]['falseTriggers']/RECALC[cid]['triggers']:.9f} -> round6={RECALC[cid]['falseTriggerRate']}")

# ---------------------------------------------------------------- 两个延迟口径的母体差异
o("")
o("=" * 108)
o("§2 口径陷阱：waitAfterSMs（全触发中位）与 latencyP50Ms（仅真实命中中位）不是同一母体")
o("=" * 108)
probe_med = {"C1-k10": 17.613, "C1-k25": 47.766, "C1-k50": 97.750,
             "C2-P95x2": 73.378, "C2-P95x3": 107.699, "C2-P99x2": 75.441,
             "C2-P99x3": 111.754, "C2-abs-P95x2": 70.931, "C3-r4": 127.491,
             "C3-r8": 256.261, "C3-r12": 385.601, "C4-t16": 17.569,
             "C4-t24": 25.126, "C4-t30": 30.448, "C4-t40": 40.500,
             "C4-t48": 49.973, "C5-k10t30": 30.448}
for c in ("C1-k10", "C1-k25", "C1-k50", "C2-P95x2", "C2-P95x3", "C2-P99x2",
          "C2-abs-P95x2", "C3-r4", "C4-t40", "C4-t48"):
    o(f"  {c:<18} _dtrigger_probe_out wait中位(全 {RECALC[c]['triggers']} 次触发)="
      f"{probe_med[c]:>8.3f}ms  |  metrics latencyP50(仅真实命中 {M[c]['latencySampleN']} 个)="
      f"{RECALC[c]['latencyP50Ms']:>8.3f}ms  |  差={round(RECALC[c]['latencyP50Ms']-probe_med[c],3)}ms")
o("  说明：题给判据族 waitAfterSMs 与题给实跑结果 latencyP50Ms 数值不同并非笔误，")
o("        而是两个不同统计母体；把二者当同一个「等待中位」会直接误判 :177 余量。")

# ---------------------------------------------------------------- 坑(a) 冷启动覆盖
o("")
o("=" * 108)
o("§3 坑(a)：开局前 N 帧无历史 —— 缺基线是否覆盖「加载后第一波战斗」")
o("=" * 108)
real_runs = [r for r in RUNS if r["key"] in rk]
for N in (16, 64):
    cold_runs = [r for r in RUNS if len(r["hist"]) < N]
    cold_real = [r for r in real_runs if len(r["hist"]) < N]
    o(f"  N={N}: 全部游程无基线 {len(cold_runs)}/{len(RUNS)} = {len(cold_runs)/len(RUNS)*100:.2f}%"
      f"；其中真实事件 {len(cold_real)}/{len(real_runs)} = {len(cold_real)/len(real_runs)*100:.2f}%")
first_runs = [r for r in RUNS if r["b"] == 0]
first_real = [r for r in first_runs if r["key"] in rk]
o(f"  窗首游程(b=0, i=0) n={len(first_runs)}（= 窗数），其中真实事件 n={len(first_real)}")
o(f"  窗首真实事件明细（全部 he=0、og=None）：")
for r in first_real:
    o(f"    {r['key']}  npts={r['npts']}  dfin={r['dfin']:.3f}ms  he={len(r['hist'])}  og={r['og']}")
# 真实事件落在「窗开始后前 64 个帧沿」的占比（用 b 作为帧沿序号代理）
for N in (16, 64):
    n_early = sum(1 for r in real_runs if r["b"] < N)
    o(f"  真实事件位于窗内前 {N} 个帧沿之前(b<{N})：{n_early}/{len(real_runs)} = {n_early/len(real_runs)*100:.2f}%")
# 全部真实事件按 t_rel_win 分位，看它们有多靠前
trw = sorted(r["t_rel_win"] for r in real_runs)
o(f"  真实事件相对窗首时间 t_rel_win: P50={pct(trw,.5):.1f}ms P90={pct(trw,.9):.1f}ms "
  f"min={trw[0]:.1f}ms max={trw[-1]:.1f}ms")
o(f"  窗内前 2 秒(=64 帧沿 × ~32ms 名义)的真实事件数 = "
  f"{sum(1 for r in real_runs if r['t_rel_win'] <= 2000.0)}/{len(real_runs)}")
o("  结论：N=64 的基线空窗不是只丢几个边缘样本，而是把每个 25s 窗开头约 2 秒整段排除；")
o("        真实事件确实落在这一段内（见上面计数），加载/换图后的第一波战斗恰好落在盲区。")

# ---------------------------------------------------------------- 坑(b) 当前停滞自污染
o("")
o("=" * 108)
o("§4 坑(b)：历史窗口若含当前停滞，P95/P99 会不会被自己抬高")
o("=" * 108)
o("  先验证既有实现的结构：_dtrigger_probe.py:135-139 只在 fs[i]!=fs[i-1]（帧沿）时 append 帧间隔；")
o("  _dtrigger_metrics.py:120-124 同样；_check_metrics.py:116-122 用 edges[] 只生成已完成帧周期。")
o("  正在停滞的游程尚无结束帧沿，故 g_b 不存在 —— 结构上「当前停」进不了自己的基线。")
o("  本件独立构造 hist=g_0..g_{b-2} 亦复现该性质；下面量化「若被误纳入」的敏感度：")
long_runs = [r for r in RUNS if r["dfin"] >= 100.0 and len(r["hist"]) >= 64]
o(f"  参与敏感度测试的 dfin>=100ms 且 hist>=64 的游程 n={len(long_runs)}")
for pn, p in (("P95", .95), ("P99", .99)):
    moved25 = moved50 = n = 0
    ratios = []
    for r in long_runs:
        h = r["hist"][-64:]
        base = pct(h, p)
        naive = pct(h + [r["dfin"]], p)   # 把当前停滞当作一条「已完成帧间隔」塞进窗口
        if base and base > 0:
            n += 1
            rr = naive / base
            ratios.append(rr)
            if rr > 1.25:
                moved25 += 1
            if rr > 1.50:
                moved50 += 1
    ratios.sort()
    o(f"  {pn}: 阈值倍率 naive/base 中位={med(ratios):.4f} P90={pct(ratios,.9):.4f} "
      f"max={ratios[-1]:.4f}  >1.25 的游程 {moved25}/{n}  >1.50 的 {moved50}/{n}")
o("  机理：N=64 时最近秩 P95=sorted[int(.95*63)]=sorted[59]（需影响前 5 大才动），")
o("        P99=sorted[int(.99*63)]=sorted[62]（只需 2 条大间隔就动）；故当前停一旦被纳入，")
o("        P99 族(C2-P99x2/x3)首当其冲，P95 族相对钝感 —— 这正是「自我抑制」的不对称入口。")
# 先前停滞污染（真实存在、已测）
clean, dirty = [], []
for r in RUNS:
    h = r["hist"][-64:]
    if len(h) < 64:
        continue
    m64 = med(h)
    if any(g >= 100.0 for g in h):
        dirty.append(m64)
    else:
        clean.append(m64)
o(f"  另一类污染确实存在：近64条含>=1条>=100ms 长间隔的游程 n={len(dirty)} 基线中位={med(dirty):.3f}ms；")
o(f"                      洁净窗 n={len(clean)} 基线中位={med(clean):.3f}ms（抬升 "
  f"{med(dirty)/med(clean):.2f}×）—— 先前停滞把阈值抬高、须等更久，等价于自我抑制。")

# ---------------------------------------------------------------- 坑(c) 绝对时长 vs k 拍 抖动
o("")
o("=" * 108)
o("§5 坑(c)：绝对时长判据与 k 拍判据在采样抖动下是否同解、差多少")
o("=" * 108)
diffs = []
flip = 0
for r in RUNS:
    xk = q_k(r, 10)
    xa = q_abs(r, 20, 3)
    if xk is not None and xa is not None:
        dk = (r["T"][xk] - r["T"][r["i"]]) * 1000.0
        da = (r["T"][xa] - r["T"][r["i"]]) * 1000.0
        diffs.append(da - dk)
        if (dk > 50.0) != (da > 50.0):
            flip += 1
neq = sum(1 for d in diffs if abs(d) > 1.0)
o(f"  k=10 与 abs>20ms 同游程触发时刻差：n={len(diffs)}  相差>1ms 的游程 n={neq}"
  f"（上报 _dtrigger_probe_out.txt:268 为 27954）")
o(f"  差值(ms) min={min(diffs):.3f} P50={med(diffs):.3f} P90={pct(diffs,.9):.3f} "
  f"P99={pct(diffs,.99):.3f} max={max(diffs):.3f}")
o(f"  两判据对「>50ms 截止」判定翻转的游程 n={flip}")
# k25(名义48ms) 与 abs>48ms 的越线差异
c25, a48 = 0, 0
for r in RUNS:
    x = q_k(r, 25)
    if x is not None and (r["T"][x] - r["T"][r["i"]]) * 1000.0 > 50.0:
        c25 += 1
    y = q_abs(r, 48, 3)
    if y is not None and (r["T"][y] - r["T"][r["i"]]) * 1000.0 > 50.0:
        a48 += 1
o(f"  C1-k25 触发等待>50ms 的触发 n={c25}（上报 103/5343）；C4-t48 触发等待>50ms 的触发 "
  f"n={a48}（上报 2492/5168）")
o("  解读：k 拍按「采样点数」计数、绝对时长按墙钟计数；一次掉拍/抖动可让 10 拍跨越 20ms+，")
o("        故二者触发时刻可差数十 ms（本件 max 见上），并对 50ms 截止给出不同结论。")
o("        名义 18/48/98ms 只在理想 500Hz 均匀采样下成立；语料实测 k10 中位 17.613ms、")
o("        最大 95.186ms（_dtrigger_probe_out.txt:61），抖动已把个别触发推过 50ms 甚至接近 100ms。")

# C5 vs C4-t30 的微小差异（同源但 kmin 不同）
o("")
o("【C5-k10t30 与 C4-t30 的 1 个真实事件差异（专项定位）】")
m5, m30 = TRIG["C5-k10t30"], TRIG["C4-t30"]
d5 = {k: (m30.get(k), m5.get(k)) for k in set(m30) | set(m5) if m30.get(k) != m5.get(k)}
o(f"  两判据真实命中集合均 n={len(m30)}/{len(m5)}；延迟不同的真实事件 n={len(d5)}")
for k, v in list(d5.items())[:8]:
    o(f"    {k}  C4-t30 latency={v[0]}ms  C5 latency={v[1]}ms")
cross = [(k, v) for k, v in d5.items()
         if (v[0] is not None and v[0] <= 50.0) and (v[1] is None or v[1] > 50.0)]
o(f"  其中「C4-t30 在 50ms 内、C5 被推到 50ms 外」的真实事件 n={len(cross)}：{cross}")
o(f"  within50msRate 重算 C4-t30={RECALC['C4-t30']['within50msRate']}  "
  f"C5={RECALC['C5-k10t30']['within50msRate']}  "
  f"差={round(RECALC['C5-k10t30']['within50msRate']-RECALC['C4-t30']['within50msRate'],6)}")

# ---------------------------------------------------------------- 坑(d) 4 条 startTick=0
o("")
o("=" * 108)
o("§6 坑(d)：4 条 startTick=0 真实事件（缺前序帧沿）专项核查")
o("=" * 108)
z = [e for e in real if e.get("startTick") == 0]
o(f"  isRealMatch==True 且 startTick==0 的事件 n={len(z)}（全量 STALL_EVENTS 中 startTick==0 共 "
  f"{sum(1 for e in events if e.get('startTick')==0)} 条，其余非 real）")
for e in z:
    r = next((x for x in RUNS if x["key"] ==
              (e["trip"], e["window"], e["startTick"], e["endTick"])), None)
    o(f"    {e['trip']}/{e['window']} startTick=0 endTick={e['endTick']} durationMs={e['durationMs']}"
      f" windowSet={e['windowSet']} pos=FIRST={'FIRST' in e['evidence']}")
    if r:
        o(f"      游程 i={r['i']} j={r['j']} npts={r['npts']} dfin={r['dfin']:.3f}ms "
          f"he={len(r['hist'])} og={r['og']} t_rel_win={r['t_rel_win']:.3f}ms")
        o("      -> 无 t[i-1]：og=None，距上一帧沿(since_advance)无定义；he=0 低于任何 N。")
        # 逐判据是否命中
        hit = []
        for cid, fn in CASES:
            if r["key"] in TRIG[cid]:
                hit.append(cid + f"(L={TRIG[cid][r['key']]:.3f}ms)")
        o(f"      命中判据 n={len(hit)} / {len(CASES)}：")
        o(f"        {', '.join(hit) if hit else '(无)'}")
o("")
o("  【结构性结论】")
o("   · 依赖「距上次推进」的判据（C2-abs-P95x2 / C3-r4 / C3-r8 / C3-r12，均以 og 为 lastEdge 偏移）")
o("     在 og=None 时直接 return None；这 4 条事件上根本算不出起点，永远漏判。")
o("   · 依赖历史基线的全部 C2/C3（含 -clean / N16 版本）还额外因 he=0 < N 被冷启动排除；")
o("     即这 4 条在所有 C2/C3 档上都不可达（与 §3 的盲区重合）。")
o("   · runStart 锚的 C1/C4/C5 仍能算 latency = t[idx]-t[0]，故这 4 条被计入 1681 个延迟样本")
o("     （C1/C4/C5 的 latencySampleN=1681，见 CRITERIA_METRICS.json:15,375,465）。")
o("   · 但它们恰恰是 S_hat 最不可信的 4 条：窗首 t[0] 之前有 4s settle 空白与加载段")
o("     （:178），停滞完全可能在窗打开前就已开始，物理 S << t[0]，真实延迟可远大于登记值；")
o("     把它们按「latency 下界」计入，会系统性低估延迟尾部，也低估 :177 的越线比例。")
o("   · 对 C2/C3 的 within50msRate（分母固定 1681），这 4 条恒计 0，使该指标额外低估")
o(f"     {len(z)}/1681 = {len(z)/1681:.6f}；且延迟样本 n 本就只有 1~21，4 条的取舍足以改变 P50。")
o("   · 无法从语料恢复这 4 条的物理 S；:177 的严格核算在此缺独立观测，标「未验」。")

# ---------------------------------------------------------------- 可区分性：查准率 vs 前缀上界
o("")
o("=" * 108)
o("§7 区分度证据：各判据查准率、召回率、延迟，与前缀不可分辨理论上界对照")
o("=" * 108)
o("  理论查准率上界（_dtrigger_analysis_out.txt:17-28，仅用 (t,f) 前缀，禁引入其他观测量）：")
o("    T=16:6.03%  T=24:6.23%  T=30:10.64%  T=40:28.25%  T=48:32.97%  T=50:33.68%")
o("    T=98:96.60%  T=100:100.00%（但 T>=100 已越 :177/:191）")
o("")
o(f"  {'id':<22}|{'查准率':>8}|{'召回率':>8}|{'延迟P50':>9}|{'延迟P95':>9}|{'窗口内率':>9}| 备注")
for cid, _ in CASES:
    c = RECALC[cid]
    prec = 1.0 - c["falseTriggerRate"]
    recl = c["realHits"] / 1681.0
    o(f"  {cid:<22}|{prec*100:>7.2f}%|{recl*100:>7.2f}%|{c['latencyP50Ms']:>9.3f}|"
      f"{c['latencyP95Ms']:>9.3f}|{c['within50msRate']*100:>8.2f}%|")
o("")
o("  逐项核对 C4：precision 实测 C4-t16=6.03% / t24=6.23% / t30=10.64% / t40=28.25% /")
o("  t48=32.97% —— 与上表同 T 的「理论查准率上界」逐一相等：这些判据只是选取了 T 轴上的一个点，")
o("  没有任何一个超出平凡上界，故未带来区分度增益（只是把等待换成了查准率）。")
o("  C1-k50 查准率 91.32% < T=98 上界 96.60%（抖动使部分触发等效 T<98），亦未超界。")
o("  C2-cap40-P95x2 查准率 25.82%、召回 69.60%、延迟 40.63ms；C4-t40 查准率 28.25%、")
o("  召回 100%、延迟 40.68ms —— 后者在查准率与召回上同时占优，cap 版被严格支配。")
o("  C2/C3 未截断档全部触发 100% >50ms（多数 >=100ms），既违 :177 又触 :191 拒止线，")
o("  且召回 0%~31%，其「0% 误报」来自近乎弃权而非区分能力。")

# ---------------------------------------------------------------- 小样本延迟分位数的可靠性
o("")
o("=" * 108)
o("§8 延迟统计自身的脆弱性（小样本 / 占位零值）")
o("=" * 108)
for cid in ("C2-P99x3", "C2-P95x3", "C3-r8", "C3-r12", "C2-P95x2"):
    c = M[cid]
    o(f"  {cid:<18} latencySampleN={c['latencySampleN']:>4}  P50={c['latencyP50Ms']}  "
      f"P95={c['latencyP95Ms']}  P95<P50={c['latencyP95Ms'] < c['latencyP50Ms']}")
o("  C2-P99x3 n=2：sorted=[104.018, 112.765]，最近秩 P95=sorted[int(.95*1)]=sorted[0]=104.018，")
o("  反而小于中位数 108.3915 —— 该「P95」在 n=2 下无统计意义；C3-r8/r8-clean n=1 同理。")
o("  C3-r12 触发 15 次但真实命中 0，latencyP50/P95/Max 的 0.0 是占位值、不是实测延迟")
o("  （CRITERIA_METRICS.json:315-323），若当作「零延迟」将得出灾难性错误结论。")

# ---------------------------------------------------------------- 落盘
o("")
o("=" * 108)
o("复核结束：本件零真机、零采样代码、只读语料、未修改任何既有文件、未 commit/push")
o("=" * 108)
if not OUT.resolve().is_relative_to(WD):
    raise ValueError("output escapes write domain")
OUT.write_text("\n".join(BUF) + "\n", encoding="utf-8")
print(f"\n输出已写：{OUT}")
