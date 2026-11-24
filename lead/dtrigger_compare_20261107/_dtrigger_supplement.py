# -*- coding: utf-8 -*-
"""
_dtrigger_supplement.py - 补充核对：阈值等待是否越过 100ms、短历史基线、锚点+e 修正

运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_dtrigger_supplement.py
"""

import json
import re
import statistics
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
WRITEDIR = (ROOT / "lead/dtrigger_compare_20261107").resolve()
OUTPUT = WRITEDIR / "_dtrigger_supplement_out.txt"

def repo_rel(rel):
    p = (ROOT / rel).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError("escape")
    return p

lines = []
def out(s=""):
    lines.append(str(s))
    print(s)

def pctl(a, p):
    return a[int(p * (len(a) - 1))] if a else None

def fmt(v, n=3):
    return "N/A" if v is None else f"{v:.{n}f}"

cache = {}
for p in sorted(BASE.rglob("measure_w*.json")):
    pr = p.resolve()
    if not pr.is_relative_to(BASE):
        raise ValueError("escape")
    parts = pr.relative_to(BASE).parts
    cache[(parts[0] if len(parts) > 1 else "(root)", pr.stem[len("measure_"):])] = json.loads(pr.read_text(encoding="utf-8-sig"))

mani = repo_rel("lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").read_text(encoding="utf-8-sig")
keys = set()
for ln in mani.splitlines():
    m = re.match(r"^([a-zA-Z0-9_\(\)]+)\s+(w\d)\s+([0-9\.]+)", ln.strip())
    if m and (m[1], m[2]) in cache:
        s = cache[(m[1], m[2])]["samples"]
        if len(s["t"]) >= 2 and any(x != y for x, y in zip(s["f"], s["f"][1:])):
            keys.add((m[1], m[2]))
keys = sorted(keys)

events = json.loads(repo_rel("lead/stall_event_def_20261106/STALL_EVENTS.json").read_text(encoding="utf-8-sig"))
real_keys = {(e["trip"], e["window"], e["startTick"], e["endTick"]) for e in events if e.get("isRealMatch") is True}

WIN = {}
REC = []
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
        REC.append((trip, win, i, j, j - i + 1, (ts[j] - ts[i]) * 1000.0,
                    hlen[i - 1] if i > 0 else 0,
                    (ts[i] - ts[i - 1]) * 1000.0 if i > 0 else None))
        i = j + 1

out("=" * 100)
out("【补充核对 · 全量 64 推进窗 / 28381 游程】")
out("=" * 100)
e_med = statistics.median([r[7] for r in REC if r[7] is not None])
out(f"onset 观测滞后 e 中位 = {fmt(e_med)}ms（用于把 waitAfterS_hat 修正为相对物理 S 的下界估计）")

# ---- 判据（与主探针同定义，补算 >=100ms 与 +e 后 >50ms ----
def f_k(r, w, k):
    ts = w[0]
    return ((ts[r[2] + k - 1] - ts[r[2]]) * 1000.0) if r[4] >= k else None

def f_rel(r, w, q, mult, N, cap=None):
    ts, fs, hist, _ = w
    he = r[6]
    if he < N:
        return None
    th = pctl(sorted(hist[he - N:he]), q) * mult
    if cap is not None:
        th = min(th, cap)
    for idx in range(r[2], r[3] + 1):
        el = (ts[idx] - ts[r[2]]) * 1000.0
        if el > th:
            return el
    return None

def f_rate(r, w, mult, N):
    ts, fs, hist, _ = w
    he = r[6]
    if he < N:
        return None
    base = statistics.median(hist[he - N:he])
    if base <= 0:
        return None
    for idx in range(r[2], r[3] + 1):
        el = (ts[idx] - ts[r[2]]) * 1000.0
        if el / base > mult:
            return el
    return None

def f_abs(r, w, th, kmin=3):
    ts = w[0]
    if r[4] < kmin:
        return None
    for idx in range(r[2] + kmin - 1, r[3] + 1):
        el = (ts[idx] - ts[r[2]]) * 1000.0
        if el > th:
            return el
    return None

def f_hybrid(r, w, k, th):
    ts = w[0]
    if r[4] < k:
        return None
    for idx in range(r[2] + k - 1, r[3] + 1):
        el = (ts[idx] - ts[r[2]]) * 1000.0
        if el > th:
            return el
    return None

CRIT = [
    ("C1-k10", lambda r, w: f_k(r, w, 10), "无"),
    ("C1-k25", lambda r, w: f_k(r, w, 25), "无"),
    ("C1-k50", lambda r, w: f_k(r, w, 50), "无"),
    ("C2-P95x2", lambda r, w: f_rel(r, w, .95, 2, 64), "近64条"),
    ("C2-P95x3", lambda r, w: f_rel(r, w, .95, 3, 64), "近64条"),
    ("C2-P99x2", lambda r, w: f_rel(r, w, .99, 2, 64), "近64条"),
    ("C2-P99x3", lambda r, w: f_rel(r, w, .99, 3, 64), "近64条"),
    # 说明：本补充探针未实现「上一帧沿距离锚」，故此处为 C2-P95x2 的独立复算，
    # 不是主探针 _dtrigger_probe.py 的 C2-abs-P95x2（后者 nTrig=29 / med=70.931ms）。
    ("C2-P95x2-复算", lambda r, w: f_rel(r, w, .95, 2, 64), "近64条(独立复算，非上一帧沿锚)"),
    ("C2-cap40-P95x2", lambda r, w: f_rel(r, w, .95, 2, 64, cap=40.0), "近64条+40ms硬上限"),
    ("C2-N16-P95x2", lambda r, w: f_rel(r, w, .95, 2, 16), "近16条"),
    ("C2-N16-P95x2-cap40", lambda r, w: f_rel(r, w, .95, 2, 16, cap=40.0), "近16条+40ms硬上限"),
    ("C3-r1.5", lambda r, w: f_rate(r, w, 1.5, 64), "近64条中位数"),
    ("C3-r2", lambda r, w: f_rate(r, w, 2, 64), "近64条中位数"),
    ("C3-r4", lambda r, w: f_rate(r, w, 4, 64), "近64条中位数"),
    ("C3-r8", lambda r, w: f_rate(r, w, 8, 64), "近64条中位数"),
    ("C3-N16-r1.5", lambda r, w: f_rate(r, w, 1.5, 16), "近16条中位数"),
    ("C3-N16-r2", lambda r, w: f_rate(r, w, 2, 16), "近16条中位数"),
    ("C4-t16", lambda r, w: f_abs(r, w, 16), "无"),
    ("C4-t24", lambda r, w: f_abs(r, w, 24), "无"),
    ("C4-t30", lambda r, w: f_abs(r, w, 30), "无"),
    ("C4-t40", lambda r, w: f_abs(r, w, 40), "无"),
    ("C4-t48", lambda r, w: f_abs(r, w, 48), "无"),
    ("C5-k10t30", lambda r, w: f_hybrid(r, w, 10, 30), "无"),
]

hdr = f"{'id':<20}|{'nTrig':>7}|{'误报率':>9}|{'wait中位':>9}|{'waitP90':>9}|{'waitMax':>9}|{'>50':>7}|{'>50+e':>8}|{'>=100':>8}|{'>=100占比':>10}|{'+e后>50占比':>13}|{'命中':>7}"
out("\n" + hdr)
out("-" * len(hdr))
SUMMARY = {}
for cid, fn, hist in CRIT:
    waits = []
    nfalse = 0
    hits = 0
    for r in REC:
        w = WIN[(r[0], r[1])]
        v = fn(r, w)
        if v is None:
            continue
        waits.append(v)
        if r[5] < 100.0:
            nfalse += 1
        if (r[0], r[1], r[2], r[3]) in real_keys:
            hits += 1
    if not waits:
        out(f"{cid:<20}| 无触发")
        continue
    ws = sorted(waits)
    n = len(ws)
    n50 = sum(1 for x in ws if x > 50)
    n50e = sum(1 for x in ws if x + e_med > 50)
    n100 = sum(1 for x in ws if x >= 100)
    SUMMARY[cid] = {
        "nTrig": n, "falseRate": nfalse / n, "waitMed": statistics.median(ws),
        "waitP90": pctl(ws, .9), "waitMax": ws[-1], "nGt50": n50, "nGt50PlusE": n50e,
        "nGe100": n100, "fracGe100": n100 / n, "fracGt50PlusE": n50e / n, "hits": hits,
        "hist": hist,
    }
    s = SUMMARY[cid]
    out(f"{cid:<20}|{n:>7}|{s['falseRate']*100:>8.2f}%|{fmt(s['waitMed']):>9}|{fmt(s['waitP90']):>9}|{fmt(s['waitMax']):>9}|"
        f"{n50:>7}|{n50e:>8}|{n100:>8}|{s['fracGe100']*100:>9.2f}%|{s['fracGt50PlusE']*100:>12.2f}%|{hits:>7}")

out("\n说明：")
out("  >50       = waitAfterS_hat 超过 50ms 的触发数（:177 的观测锚口径）")
out(f"  >50+e     = 加上 onset 观测滞后中位 e={fmt(e_med)}ms 后超过 50ms 的触发数")
out("  >=100     = 触发等待已达/越过口径B 100ms 事后分类门槛的触发数；该列 >0 即判据不再是「提前」候选")
out("  误报率    = 触发中最终 d_final<100ms 的占比（事后计费，不参与触发）")

out("\n【短历史基线 N=16 的冷启动改善与代价】")
for N in (16, 32, 64):
    cold = sum(1 for r in REC if r[6] < N)
    out(f"  N={N}: 无基线游程 {cold}/{len(REC)} = {cold/len(REC)*100:.2f}%")

out("\n【不可实现项登记】")
out("  1. 相对「物理起点 S」的精确 waitAfterS：语料只有 (t,f)，物理 S 落在 (t[runStart-1], t[runStart]] 内，")
out("     无法从语料测得；本报告全部 waitAfterSMs 只能给观测锚 S_hat 下的实测值，作为下界。缺：物理停滞起点的独立观测。")
out("  2. 跨窗连续历史基线：语料被切成 25s 孤立窗、窗间 4s 空白（:178），窗首游程无前窗帧间隔，")
out("     任何要求「跨窗长程历史」的判据在窗首不可实现。缺：未切片连续时序。")
out("  3. 依赖内部状态旗标(IN_TACTICAL/SCORE_SCREEN/PAUSED/LOADING)区分慢帧与停滞：")
out("     :176 明确语料只有外部 CurrentFrame，无内部枚举；此类判据在本语料不可实现。缺：内部状态字段。")
out("     本项不声称旗标足以区分二者，仅登记为数据缺口。")

if not OUTPUT.resolve().is_relative_to(WRITEDIR):
    raise ValueError("escape")
OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
out(f"\n输出已写：{OUTPUT}")
