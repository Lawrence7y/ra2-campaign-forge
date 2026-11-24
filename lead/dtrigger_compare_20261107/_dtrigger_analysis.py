# -*- coding: utf-8 -*-
"""
_dtrigger_analysis.py - 候选判据的扩展离线分析（只读语料）

补充 _dtrigger_probe.py 未覆盖的四项：
 A. 可区分性硬上界：仅凭 (t,f) 前缀，在时刻 T 时「正常慢帧」与「真实停滞」的
    观测前缀不可分辨，计算任意「持续到 T 仍同帧」型判据的理论查准率上界。
 B. 带 50ms 硬上限的相对阈值判据：证明「相对」信息一旦不越过 :177 就退化为绝对时长。
 C. 帧间隔变化率的干净语义（本次帧间隔 = 自上次推进起的观测时长），含 r2/r3/r4。
 D. 历史基线污染：滑窗内若含先前停滞，中位数/P95 被抬高，比率判据自我失效。

运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_dtrigger_analysis.py
"""

import json
import re
import statistics
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
WRITEDIR = (ROOT / "lead/dtrigger_compare_20261107").resolve()
OUTPUT = WRITEDIR / "_dtrigger_analysis_out.txt"

def repo_rel(rel):
    p = (ROOT / rel).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError("path escapes repo root")
    return p

lines = []
def out(s=""):
    lines.append(str(s))
    print(s)

def pctl(a, p):
    return a[int(p * (len(a) - 1))] if a else None

def fmt(v, n=3):
    return "N/A" if v is None else f"{v:.{n}f}"

# ---- 载入（独立实现：直接用 Path.rglob，键由 relative_to 生成） ----
cache = {}
for p in sorted(BASE.rglob("measure_w*.json")):
    pr = p.resolve()
    if not pr.is_relative_to(BASE):
        raise ValueError("escape")
    parts = pr.relative_to(BASE).parts
    key = (parts[0] if len(parts) > 1 else "(root)", pr.stem[len("measure_"):])
    cache[key] = json.loads(pr.read_text(encoding="utf-8-sig"))

mani = repo_rel("lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").read_text(encoding="utf-8-sig")
keys = set()
for ln in mani.splitlines():
    m = re.match(r"^([a-zA-Z0-9_\(\)]+)\s+(w\d)\s+([0-9\.]+)", ln.strip())
    if m and (m[1], m[2]) in cache:
        s = cache[(m[1], m[2])]["samples"]
        ts, fs = s["t"], s["f"]
        if len(ts) >= 2 and any(x != y for x, y in zip(fs, fs[1:])):
            keys.add((m[1], m[2]))
keys = sorted(keys)

events = json.loads(repo_rel("lead/stall_event_def_20261106/STALL_EVENTS.json").read_text(encoding="utf-8-sig"))
real_keys = {(e["trip"], e["window"], e["startTick"], e["endTick"])
             for e in events if e.get("isRealMatch") is True}

# 每窗：帧推进间隔序列 + 游程
REC = []   # (trip,win,runStart,runEnd,npts,d_final_ms,h_end,onset_gap_ms,hist_slice_start,ts,fs)
WIN = {}
for trip, win in keys:
    s = cache[(trip, win)]["samples"]
    ts, fs = s["t"], s["f"]
    n = len(fs)
    hist = []
    hlen = [0] * n
    le = 0
    for i in range(1, n):
        if fs[i] != fs[i - 1]:
            hist.append((ts[i] - ts[le]) * 1000.0)
            le = i
        hlen[i] = len(hist)
    WIN[(trip, win)] = (ts, fs, hist, hlen)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and fs[j + 1] == fs[i]:
            j += 1
        he = hlen[i - 1] if i > 0 else 0
        REC.append((trip, win, i, j, j - i + 1, (ts[j] - ts[i]) * 1000.0,
                    he, (ts[i] - ts[i - 1]) * 1000.0 if i > 0 else None))
        i = j + 1

out("=" * 100)
out("【候选判据扩展分析 · 全量 64 推进窗】")
out("=" * 100)
out(f"游程总数 n={len(REC)}，真实事件标签 n={len(real_keys)}（不与 1737 混口径）")
all_hist = sorted(h for (_, _, hist, _) in WIN.values() for h in hist)
out(f"全部已完成帧间隔 n={len(all_hist)}  P50={fmt(pctl(all_hist,.5))}ms  P95={fmt(pctl(all_hist,.95))}ms  P99={fmt(pctl(all_hist,.99))}ms")
out("交叉核对：:194 记载「游戏正常逻辑帧耗时 32.0ms(31.25fps)」，本探针实测帧间隔 P50=32.779ms，同量级，")
out("          说明 hist 构造取的是「帧沿到帧沿」的帧周期，而非采样点间隔 2ms。")

# ---------------------------------------------------------------- A
out("\n" + "=" * 100)
out("A. 可区分性硬上界：前缀不可分辨")
out("=" * 100)
out("论证：语料只有 (t,f)。设某游程最终持续 d。在线判据在时刻 T 只看到「自上次推进起 d_obs>T 且 f 不变」。")
out("      对任意 d1,d2 均 >T 的两个游程，其 [起点, T] 内的 (t,f) 前缀在分布上无可用判别量")
out("      （除非引入历史/其他观测量）。故「持续到 T 仍同帧」型判据的查准率上限 = #{d>=100}/#{d>T}。")
out("      下式为语料实测，不依赖任何判据实现：")
durs = sorted(x[5] for x in REC)
n_stall = sum(1 for d in durs if d >= 100.0)
out(f"\n{'T(ms)':>6} | {'d>T游程':>9} | {'其中d<100(正常慢帧)':>20} | {'其中d>=100':>11} | {'理论查准率上界':>14} | {'理论误报率':>12}")
out("-" * 88)
for T in (16, 24, 30, 40, 48, 50, 60, 80, 98, 100):
    over = [d for d in durs if d > T]
    nfalse = sum(1 for d in over if d < 100.0)
    ngood = len(over) - nfalse
    if over:
        out(f"{T:>6} | {len(over):>9} | {nfalse:>20} | {ngood:>11} | {ngood/len(over)*100:>13.2f}% | {nfalse/len(over)*100:>11.2f}%")
out("\n结论：T<50ms 时正常慢帧仍大量存活；T=48ms 时仍有 3464 条 d<100ms 的正常慢帧与 1704 条 d>=100ms")
out("      候选共享相同前缀 —— 任何只看 (t,f) 前缀的判据都不可能把它们分开。")
out("      只有等到 T>=100ms（口径B分类门槛）才能完全分开，而那已越过 :177/:191。")

# ---------------------------------------------------------------- B
out("\n" + "=" * 100)
out("B. 带 50ms 硬上限的相对阈值判据（C2-cap）")
out("=" * 100)
out("定义：帧号不变 且 elapsed > min(P95(近64条帧间隔)*2, CAP)，CAP 取 40ms；冷启动<64 条不触发。")
out("      若 P95*2 >= CAP 则由 CAP 决定触发时刻 —— 此时「相对」信息不起作用。")
cap = 40.0
n_trig = n_by_cap = n_by_rel = n_cold = 0
waits = []
n_false = 0
hits = 0
for trip, win, i, j, npts, dfin, he, og in REC:
    ts, fs, hist, hlen = WIN[(trip, win)]
    if he < 64:
        n_cold += 1
        continue
    base = pctl(sorted(hist[he - 64:he]), 0.95)
    theta = min(base * 2.0, cap)
    governed_by_cap = (base * 2.0 >= cap)
    for idx in range(i, j + 1):
        el = (ts[idx] - ts[i]) * 1000.0
        if el > theta:
            n_trig += 1
            waits.append(el)
            if dfin < 100.0:
                n_false += 1
            if (trip, win, i, j) in real_keys:
                hits += 1
            if governed_by_cap:
                n_by_cap += 1
            else:
                n_by_rel += 1
            break
ws = sorted(waits)
out(f"  nTrig={n_trig}  nFalse(d<100)={n_false}  falseRate={n_false/n_trig*100:.2f}%  strictRealHits={hits}")
out(f"  waitAfterS_hat: min={fmt(ws[0])} med={fmt(statistics.median(ws))} P90={fmt(pctl(ws,.9))} max={fmt(ws[-1])} ms")
out(f"  越过50ms的触发数={sum(1 for x in ws if x>50)}/{n_trig}")
out(f"  由 CAP 决定触发时刻的触发数={n_by_cap}/{n_trig} ({n_by_cap/n_trig*100:.2f}%)，由相对阈值决定的仅 {n_by_rel} 次")
out(f"  冷启动(<64条历史)被排除的游程={n_cold}")
out("  结论：一旦用 CAP 把等待压到 50ms 内，相对分位阈值在绝大多数触发上不起作用，判据退化为绝对时长(C4-t40)。")

# ---------------------------------------------------------------- C
out("\n" + "=" * 100)
out("C. 帧间隔变化率（干净语义：本次帧间隔 = 自上次推进起的观测时长）")
out("=" * 100)
out("定义：ratio(T) = (t[idx]-t[上次推进]) / median(近64条已完成帧间隔)；逐拍首次 ratio>mult 即触发。")
out("      上次推进 = 本游程首拍 i（帧号在此刻变为当前值）；基线不含当前停滞；冷启动<64 不触发。")
for mult in (1.5, 2, 3, 4, 8):
    waits = []
    nfalse = 0
    hits = 0
    ntrig = 0
    for trip, win, i, j, npts, dfin, he, og in REC:
        ts, fs, hist, hlen = WIN[(trip, win)]
        if he < 64:
            continue
        base = statistics.median(hist[he - 64:he])
        if base <= 0:
            continue
        for idx in range(i, j + 1):
            el = (ts[idx] - ts[i]) * 1000.0
            if el / base > mult:
                ntrig += 1
                waits.append(el)
                if dfin < 100.0:
                    nfalse += 1
                if (trip, win, i, j) in real_keys:
                    hits += 1
                break
    ws = sorted(waits)
    if not ws:
        out(f"  r{mult}: 无触发")
        continue
    out(f"  r{mult}: nTrig={ntrig} nFalse={nfalse} falseRate={nfalse/ntrig*100:.2f}% hits={hits}/1681 "
        f"wait med={fmt(statistics.median(ws))} P90={fmt(pctl(ws,.9))} max={fmt(ws[-1])}ms "
        f">50ms触发={sum(1 for x in ws if x>50)}/{ntrig}")
out("  注：median(近64条) ≈ 32ms，故 mult=1.5 阈值已约 48ms；mult>=2 阈值>64ms，必然越过 :177。")

# ---------------------------------------------------------------- D
out("\n" + "=" * 100)
out("D. 历史基线污染（滑窗含先前停滞 → 比率判据自我失效）")
out("=" * 100)
clean_med = []
dirty_med = []
for trip, win, i, j, npts, dfin, he, og in REC:
    if he < 64:
        continue
    _, _, hist, _ = WIN[(trip, win)]
    win64 = hist[he - 64:he]
    m = statistics.median(win64)
    n_long = sum(1 for x in win64 if x >= 100.0)
    (dirty_med if n_long > 0 else clean_med).append(m)
out(f"  近64条历史中不含任何 >=100ms 长间隔的游程 n={len(clean_med)}，其基线中位数 P50={fmt(statistics.median(clean_med))}ms")
if dirty_med:
    out(f"  近64条历史中含 >=1 条 >=100ms 长间隔的游程 n={len(dirty_med)}，其基线中位数 P50={fmt(statistics.median(dirty_med))}ms "
        f"P95={fmt(pctl(sorted(dirty_med),.95))}ms")
out("  含义：停滞密集窗里，近期帧间隔中位数被先前的停滞抬高，同一比率阈值要等更久才能突破；")
out("        这正是 C3-r4 实测中位等待 127.491ms、P90 346.357ms 的成因（见 _dtrigger_probe_out.txt:149）。")

# ---------------------------------------------------------------- E
out("\n" + "=" * 100)
out("E. :177 严格核算的诚实账（物理 S 不可测）")
out("=" * 100)
ogs = sorted(x[7] for x in REC if x[7] is not None)
out(f"  e = t[runStart]-t[runStart-1] 有效 n={len(ogs)}  min={fmt(ogs[0])} med={fmt(statistics.median(ogs))} "
    f"P95={fmt(pctl(ogs,.95))} P99={fmt(pctl(ogs,.99))} max={fmt(ogs[-1])} ms")
out("  物理 S ∈ (t[runStart-1], t[runStart]]；观测锚 S_hat=t[runStart]；S_hat-S ∈ [0,e]。")
out("  故 waitAfterS(真实) = waitAfterS_hat + (S_hat-S) >= waitAfterS_hat，本报告 waitAfterSMs 均为下界。")
out("  例：C1-k25 实测中位 47.766ms + e 中位 2.511ms = 50.277ms > 50ms（以中位 e 计已越 :177）。")
out("  C1-k10 实测中位 17.613ms + e 中位 2.511ms = 20.124ms < 50ms，但 P99 e=4.145ms、最大 e=488.616ms")
out("  仍可能透支；且 :190 端到端还须含保存时延（Q5 四项未验）。")

if not OUTPUT.resolve().is_relative_to(WRITEDIR):
    raise ValueError("escape")
OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
out(f"\n输出已写：{OUTPUT}")
