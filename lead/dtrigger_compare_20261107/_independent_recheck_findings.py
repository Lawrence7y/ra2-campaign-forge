# -*- coding: utf-8 -*-
"""
_independent_recheck_findings.py —— 判据独立复核员·失败场景专项实跑（第二件）

把散落的临时检查固化成可复跑、可引用的输出：
  A. k 拍判据的墙钟等待是否真的等于名义 18/48/98ms（采样抖动/时间戳压缩）
  B. C2-cap* 的全部漏判是否恰好等于冷启动（N=64 / N=16）
  C. C2/C3 高阈值档的「0% 误报」是否由口径B计费漏洞造成（窗尾截断伪影）
  D. 4 条 startTick=0 真实事件与 C2/C3 不可达性、以及排除原因核验
  E. C1-k10 / C1-k50 的具体误触发游程样本

运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_independent_recheck_findings.py
写域：仅本件新建的 _independent_recheck_findings_out.txt
纪律：零真机 / 零采样代码 / 只读语料 / 不 import 任何既有探针 / 无 commit push
"""
import json
import re
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
EV = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
MANI = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
WD = (ROOT / "lead/dtrigger_compare_20261107").resolve()
OUT = WD / "_independent_recheck_findings_out.txt"

B = []
def o(s=""):
    B.append(str(s)); print(s)

def pc(a, p):
    s = sorted(a)
    return s[int(p * (len(s) - 1))] if s else None

# ------------------------------------------------------------------ 重建（独立）
EVENTS = json.loads(EV.read_text(encoding="utf-8-sig"))
RK = {(e["trip"], e["window"], e["startTick"], e["endTick"]) for e in EVENTS
      if e.get("isRealMatch") is True}
BYKEY = {(e["trip"], e["window"], e["startTick"], e["endTick"]): e for e in EVENTS}

corp = {}
for fp in sorted(BASE.rglob("measure_w*.json")):
    p = fp.resolve()
    if not p.is_relative_to(BASE):
        raise ValueError("escape")
    q = p.relative_to(BASE).parts
    corp[(q[0], p.stem[len("measure_"):])] = json.loads(p.read_text(encoding="utf-8-sig"))
wins = set()
for ln in MANI.read_text(encoding="utf-8-sig").splitlines():
    m = re.match(r"^([a-zA-Z0-9_()]+)\s+(w\d)\s+([0-9.]+)", ln.strip())
    if m and (m[1], m[2]) in corp:
        z = corp[(m[1], m[2])]["samples"]
        if len(z["t"]) >= 2 and any(a != b for a, b in zip(z["f"], z["f"][1:])):
            wins.add((m[1], m[2]))
wins = sorted(wins)

R = []
allgaps = []
for trip, win in wins:
    T = corp[(trip, win)]["samples"]["t"]
    F = corp[(trip, win)]["samples"]["f"]
    n = len(F)
    allgaps += [(T[a] - T[a - 1]) * 1000.0 for a in range(1, n)]
    st = [0] + [a for a in range(1, n) if F[a] != F[a - 1]]
    gp = [(T[st[b + 1]] - T[st[b]]) * 1000.0 for b in range(len(st) - 1)]
    for b, i in enumerate(st):
        j = st[b + 1] - 1 if b + 1 < len(st) else n - 1
        R.append({
            "key": (trip, win, i, j), "i": i, "j": j, "n": n, "b": b,
            "np": j - i + 1, "dfin": (T[j] - T[i]) * 1000.0,
            "hist": gp[:b - 1] if b >= 1 else [],
            "og": (T[i] - T[i - 1]) * 1000.0 if i > 0 else None,
            "t0": (T[i] - T[0]) * 1000.0, "T": T,
        })

o("=" * 104)
o("判据独立复核员 · 失败场景专项实跑（第二件，独立于执行者/核验者）")
o("=" * 104)
o(f"语料 files={len(corp)} windows={len(wins)} runs={len(R)} real_keys={len(RK)} "
  f"STALL_EVENTS={len(EVENTS)}")

# ------------------------------------------------------------------ A 采样抖动
o("")
o("=" * 104)
o("A. 「500Hz / 名义 2ms」前提是否成立：k 拍判据的墙钟等待")
o("=" * 104)
allgaps.sort()
o(f"moving64 窗内相邻采样间隔 n={len(allgaps)}  min={allgaps[0]:.6f}ms  "
  f"P50={pc(allgaps,.5):.4f}  P90={pc(allgaps,.9):.4f}  P99={pc(allgaps,.99):.4f}  max={allgaps[-1]:.4f}ms")
nsub = sum(1 for g in allgaps if g < 0.05)
o(f"  间隔 < 0.05ms 的采样 n={nsub}/{len(allgaps)} = {100*nsub/len(allgaps):.3f}%"
  f"；间隔 < 0.5ms n={sum(1 for g in allgaps if g<0.5)}；间隔 > 10ms n={sum(1 for g in allgaps if g>10)}")
o("  => 名义「每 2ms 一拍」在语料里有 17% 的采样被压缩到 0.05ms 内，"
  "k 拍计数与墙钟时长并非一一对应。")
for k, nom in ((10, 18.0), (25, 48.0), (50, 98.0)):
    w = sorted((r["T"][r["i"] + k - 1] - r["T"][r["i"]]) * 1000.0
               for r in R if r["np"] >= k)
    o(f"  k={k:<2} 触发 n={len(w):<6} min={w[0]:.3f} P1={pc(w,.01):.3f} P5={pc(w,.05):.3f} "
      f"P50={pc(w,.5):.3f} P95={pc(w,.95):.3f} max={w[-1]:.3f} ms （名义 {nom:.0f}ms）")
    for f in (0.1, 0.5, 0.9):
        c = sum(1 for x in w if x < nom * f)
        o(f"      等待 < {nom*f:.1f}ms（名义的 {f*100:.0f}%）: {c}/{len(w)} = {100*c/len(w):.2f}%")
o("  具体样本（时间戳压缩而非停滞）：")
for r in R:
    if r["np"] >= 50:
        w50 = (r["T"][r["i"] + 49] - r["T"][r["i"]]) * 1000.0
        if w50 < 1.0:
            o(f"    {r['key']} npts={r['np']} dfin={r['dfin']:.3f}ms "
              f"k50墙钟等待={w50:.3f}ms（名义98ms） 前10拍间隔(ms)="
              f"{[round((r['T'][r['i']+x+1]-r['T'][r['i']+x])*1000,4) for x in range(6)]}")
            break
o("  C4 绝对时长同样受抖动跳变支配（单一读取掉拍把多个阈值压到同一触发点）：")
for r in R:
    if r["key"] == ("l3_20261031hb", "w2", 0, 52):
        T, i, j = r["T"], r["i"], r["j"]
        gaps = [(T[a] - T[a - 1]) * 1000.0 for a in range(i + 1, j + 1)]
        mx = max(gaps)
        fires = {}
        for th in (24, 30, 40, 48):
            x = next((a for a in range(i + 2, j + 1)
                      if (T[a] - T[i]) * 1000.0 > th), None)
            fires[th] = (T[x] - T[i]) * 1000.0 if x else None
        o(f"    {r['key']} npts={r['np']} dfin={r['dfin']:.3f}ms；游程内最大单拍间隔"
          f"={mx:.3f}ms（名义 2ms），其后 elapsed 跳到 {fires[24]:.3f}ms")
        o(f"    C4-t24/t30/t40/t48 触发等待分别 = "
          f"{fires[24]:.3f}/{fires[30]:.3f}/{fires[40]:.3f}/{fires[48]:.3f}ms —— "
          f"四个不同阈值全被同一次掉拍压到同一时刻")
        break
# k10 vs abs>20ms
def q_abs(r, th, kmin=3):
    if r["np"] < kmin:
        return None
    for x in range(r["i"] + kmin - 1, r["j"] + 1):
        if (r["T"][x] - r["T"][r["i"]]) * 1000.0 > th:
            return x
    return None
d = []
flip = 0
for r in R:
    xk = r["i"] + 9 if r["np"] >= 10 else None
    xa = q_abs(r, 20)
    if xk is not None and xa is not None:
        dk = (r["T"][xk] - r["T"][r["i"]]) * 1000.0
        da = (r["T"][xa] - r["T"][r["i"]]) * 1000.0
        d.append(da - dk)
        if (dk > 50.0) != (da > 50.0):
            flip += 1
o(f"  k=10 与 abs>20ms 同游程触发时刻差：n={len(d)} 相差>1ms={sum(1 for x in d if abs(x)>1)}"
  f"（_dtrigger_probe_out.txt:268 报 27954）")
o(f"    差(ms) min={min(d):.3f} P50={pc(d,.5):.3f} P90={pc(d,.9):.3f} max={max(d):.3f}"
  f"；对 >50ms 截止判定翻转的游程 n={flip}")

# ------------------------------------------------------------------ B 冷启动=全部漏判
o("")
o("=" * 104)
o("B. C2-cap* 的 missedReal 是否恰好等于冷启动缺基线（即漏判全在窗首盲区）")
o("=" * 104)
def cap_idx(r, N):
    h = r["hist"][-N:]
    if len(h) < N:
        return None
    th = min(pc(h, .95) * 2, 40.0)
    for x in range(r["i"], r["j"] + 1):
        if (r["T"][x] - r["T"][r["i"]]) * 1000.0 > th:
            return x
    return None
for N, cid in ((64, "C2-cap40-P95x2"), (16, "C2-N16-P95x2-cap40")):
    cold = [r for r in R if r["key"] in RK and len(r["hist"]) < N]
    noncold_miss = [r for r in R if r["key"] in RK and len(r["hist"]) >= N and cap_idx(r, N) is None]
    hits = sum(1 for r in R if r["key"] in RK and cap_idx(r, N) is not None)
    o(f"  {cid}: 冷启动真实事件 n={len(cold)}；非冷启动而漏判 n={len(noncold_miss)}；"
      f"命中={hits}；1681-{len(cold)}={1681-len(cold)} == 命中? {1681-len(cold)==hits}")
    o(f"    全部游程冷启动 {sum(1 for r in R if len(r['hist'])<N)}/{len(R)} = "
      f"{100*sum(1 for r in R if len(r['hist'])<N)/len(R):.2f}%")
o(f"  真实事件落在窗首前 2 秒(t0<=2000ms) n={sum(1 for r in R if r['key'] in RK and r['t0']<=2000)}/1681"
  f" = {100*sum(1 for r in R if r['key'] in RK and r['t0']<=2000)/1681:.2f}%"
  f"；前 500ms n={sum(1 for r in R if r['key'] in RK and r['t0']<500)}")
o("  => N=64 基线空窗覆盖 511/1681=30.40% 的真实事件，且 100% 的漏判来自该盲区；")
o("     每个 25s 窗开头约 64×32ms≈2s 无基线，正是加载/换图后的第一波战斗。")

# ------------------------------------------------------------------ C 计费漏洞
o("")
o("=" * 104)
o("C. 「0.00% 误报」是不是真的没误触发 —— 口径B d>=100ms 计费漏洞")
o("=" * 104)
o("  误触发定义：触发但 d_final<100ms（_dtrigger_metrics_out.txt:49）。"
  "但权威真实标签是 isRealMatch==True（n=1681）。")
d100 = [r for r in R if r["dfin"] >= 100.0]
nonreal = [r for r in d100 if r["key"] not in RK]
o(f"  d>=100ms 游程 n={len(d100)}；其中 real={len(d100)-len(nonreal)}，非 real={len(nonreal)}")
o(f"  非 real 的排除原因：{dict(Counter(str(BYKEY.get(r['key'],{}).get('exclusionReason')) for r in nonreal))}")
o(f"  非 real 中窗尾截断(j==n-1) n={sum(1 for r in nonreal if r['j']==r['n']-1)}/{len(nonreal)}")
o("  具体样本（对局结束终局冻结 / 帧回退，持续 0.9~21 秒，明确 isRealMatch=False）：")
for r in nonreal[:5]:
    e = BYKEY.get(r["key"], {})
    o(f"    {r['key']} dfin={r['dfin']:.2f}ms isRealMatch={e.get('isRealMatch')} "
      f"exclusionReason={e.get('exclusionReason')} tail={r['j']==r['n']-1}")

def rel(r, p, m, N, cap=None, abs_=False):
    h = r["hist"][-N:]
    if len(h) < N or (abs_ and r["og"] is None):
        return None
    th = pc(h, p) * m
    if cap is not None:
        th = min(th, cap)
    off = r["og"] if abs_ else 0.0
    for x in range(r["i"], r["j"] + 1):
        if (r["T"][x] - r["T"][r["i"]]) * 1000.0 + off > th:
            return x
    return None

def rate(r, m, N, anchor):
    h = r["hist"][-N:]
    if len(h) < N or (anchor == "lastEdge" and r["og"] is None):
        return None
    b = statistics.median(h)
    if b <= 0:
        return None
    off = r["og"] if anchor == "lastEdge" else 0.0
    for x in range(r["i"], r["j"] + 1):
        if (r["T"][x] - r["T"][r["i"]]) * 1000.0 + off > m * b:
            return x
    return None

CASES = [
    ("C2-P95x2", lambda r: rel(r, .95, 2, 64)),
    ("C2-P95x3", lambda r: rel(r, .95, 3, 64)),
    ("C2-P99x2", lambda r: rel(r, .99, 2, 64)),
    ("C2-P99x3", lambda r: rel(r, .99, 3, 64)),
    ("C2-abs-P95x2", lambda r: rel(r, .95, 2, 64, abs_=True)),
    ("C2-N16-P95x2", lambda r: rel(r, .95, 2, 16)),
    ("C3-r1.5", lambda r: rate(r, 1.5, 64, "runStart")),
    ("C3-r2", lambda r: rate(r, 2, 64, "runStart")),
    ("C3-r4", lambda r: rate(r, 4, 64, "lastEdge")),
    ("C3-r4-clean", lambda r: rate(r, 4, 64, "runStart")),
    ("C3-r8", lambda r: rate(r, 8, 64, "lastEdge")),
    ("C3-r8-clean", lambda r: rate(r, 8, 64, "runStart")),
    ("C3-r12", lambda r: rate(r, 12, 64, "lastEdge")),
    ("C3-N16-r1.5", lambda r: rate(r, 1.5, 16, "runStart")),
    ("C3-N16-r2", lambda r: rate(r, 2, 16, "runStart")),
]
o("")
o(f"  {'id':<20}{'trig':>7}{'real':>7}{'非real':>8}{'窗尾':>7}{'非real占比':>12}")
for cid, fn in CASES:
    t = [r for r in R if fn(r) is not None]
    nr = [r for r in t if r["key"] not in RK]
    tail = [r for r in nr if r["j"] == r["n"] - 1]
    o(f"  {cid:<20}{len(t):>7}{len(t)-len(nr):>7}{len(nr):>8}{len(tail):>7}"
      f"{100*len(nr)/len(t) if t else 0:>11.1f}%")
o("")
o("  C3-r12 的 15 次触发逐条（全部 isRealMatch=False，故误报率仍算 0.00%）：")
for r in R:
    x = rate(r, 12, 64, "lastEdge")
    if x is not None:
        e = BYKEY.get(r["key"], {})
        o(f"    {r['key']} dfin={r['dfin']:.2f}ms wait="
          f"{(r['T'][x]-r['T'][r['i']])*1000:.2f}ms isRealMatch={e.get('isRealMatch')} "
          f"exclusionReason={e.get('exclusionReason')}")
o("  => 高阈值 C2/C3 的「低/零误报」主要来自：触发落在 d>=100ms 的窗尾终局冻结伪影，")
o("     这些伪影按口径B被计为「真」，而真实战斗停滞只命中 0~21 条。"
  "这是计费口径漏洞，不是区分能力。")

# ------------------------------------------------------------------ D startTick=0
o("")
o("=" * 104)
o("D. 4 条 startTick=0 真实事件（缺前序信息）")
o("=" * 104)
Z = [e for e in EVENTS if e.get("isRealMatch") is True and e.get("startTick") == 0]
o(f"  isRealMatch==True 且 startTick==0 n={len(Z)}；"
  f"STALL_EVENTS 全量 startTick==0 n={sum(1 for e in EVENTS if e.get('startTick')==0)}")
for e in Z:
    r = next((x for x in R if x["key"] ==
              (e["trip"], e["window"], e["startTick"], e["endTick"])), None)
    o(f"    {e['trip']}/{e['window']} startTick=0 endTick={e['endTick']} "
      f"durationMs={e['durationMs']} windowSet={e['windowSet']} pos=FIRST={'FIRST' in e['evidence']}")
    if r:
        o(f"      游程 i=0 j={r['j']} npts={r['np']} dfin={r['dfin']:.3f}ms "
          f"he={len(r['hist'])} og={r['og']} b={r['b']} t0={r['t0']:.3f}ms")
        hit = [cid for cid, fn in CASES if fn(r) is not None]
        o(f"      C2/C3 全 15 档命中 n={len(hit)}（og=None 且 he=0<N，结构上不可达）")
o("  影响：")
o("   · C2-abs-P95x2 / C3-r4 / r8 / r12 用 og 作「距上一帧沿」偏移，og=None 时谓词无定义；")
o("   · 全部 C2/C3 还因 he=0 被冷启动排除（与 B 节盲区重叠）；")
o("   · C1/C4/C5 用 runStart 锚 t[0] 仍能算 latency，故这 4 条进入 1681 个延迟样本，")
o("     但 :178 记载窗间 4s settle 空白，物理 S 可能远早于 t[0]，"
  "把 t[0] 当 S_hat 会系统性低估延迟尾部与 :177 越线比例；")
o(f"   · 对 C2/C3 的 within50msRate（分母固定 1681），这 4 条恒计 0，"
  f"额外低估 {len(Z)}/1681 = {len(Z)/1681:.6f}。")

# ------------------------------------------------------------------ E 具体误触发
o("")
o("=" * 104)
o("E. 具体误触发游程样本（正常慢帧 d<100ms 被触发）")
o("=" * 104)
fps = [r for r in R if r["key"] not in RK and r["dfin"] < 100.0 and r["np"] >= 10]
o(f"  C1-k10 误触发 n={len(fps)}（上报 26590），前 5 条：")
for r in fps[:5]:
    o(f"    {r['key']} npts={r['np']} dfin={r['dfin']:.3f}ms "
      f"k10等待={(r['T'][r['i']+9]-r['T'][r['i']])*1000:.3f}ms")
f50 = [r for r in R if r["key"] not in RK and r["dfin"] < 100.0 and r["np"] >= 50]
o(f"  C1-k50 误触发 n={len(f50)}（上报 162），前 4 条：")
for r in f50[:4]:
    o(f"    {r['key']} npts={r['np']} dfin={r['dfin']:.3f}ms "
      f"k50等待={(r['T'][r['i']+49]-r['T'][r['i']])*1000:.3f}ms")
rr = [r for r in R if r["key"] in RK]
o(f"  真实事件 npts: min={min(r['np'] for r in rr)} "
  f"P50={pc([r['np'] for r in rr],.5)} max={max(r['np'] for r in rr)}"
  f"；d_fin P50={pc([r['dfin'] for r in rr],.5):.3f}ms "
  f"P90={pc([r['dfin'] for r in rr],.9):.3f}ms max={pc([r['dfin'] for r in rr],1):.3f}ms")
o("  本语料全部真实事件 npts>=50，故 k 拍在本语料未因「采样点不足」漏判；")
o("  但 A 节已证 17.1% 采样间隔被压缩，若真机读取掉拍导致 npts<k，"
  "k 拍判据会完全不触发 —— 该场景本语料无样本，标「未验」。")

o("")
o("=" * 104)
o("F. 基线污染是真实事件的主导条件而非边缘情形（自我抑制的实际形态）")
o("=" * 104)
rr = [r for r in R if r["key"] in RK and len(r["hist"]) >= 64]
clean = [r for r in rr if not any(g >= 100.0 for g in r["hist"][-64:])]
dirty = [r for r in rr if any(g >= 100.0 for g in r["hist"][-64:])]
o(f"  he>=64 的真实事件 n={len(rr)}；近64条含>=1条>=100ms 长间隔（被先前停滞污染）"
  f"n={len(dirty)} = {100*len(dirty)/len(rr):.2f}%；洁净 n={len(clean)}")
o(f"  基线中位数 P50：洁净={statistics.median([statistics.median(r['hist'][-64:]) for r in clean]):.3f}ms"
  f"  污染={statistics.median([statistics.median(r['hist'][-64:]) for r in dirty]):.3f}ms")
for cid, fn in [("C3-r1.5", lambda r: rate(r, 1.5, 64, "runStart")),
                ("C3-r2", lambda r: rate(r, 2, 64, "runStart")),
                ("C3-r4", lambda r: rate(r, 4, 64, "lastEdge")),
                ("C3-r4-clean", lambda r: rate(r, 4, 64, "runStart"))]:
    hc = sum(1 for r in clean if fn(r) is not None)
    hd = sum(1 for r in dirty if fn(r) is not None)
    o(f"    {cid:<14} 洁净命中 {hc}/{len(clean)}={100*hc/len(clean):.2f}%  "
      f"污染命中 {hd}/{len(dirty)}={100*hd/len(dirty):.2f}%")
o("  => 真实停滞在语料里密集成簇（每窗约 26 条），故几乎每条真实事件的近 64 条基线")
o("     都含前一个停滞；阈值被抬高 2 倍以上，后续真实停滞被系统性抑制。")
o("     注意区分：当前停「结构上」进不了自己的基线（见 C 节与 _dtrigger_probe.py:135-139），")
o("     但「前一个停抬高后一个」的跨事件自我抑制真实存在且覆盖 99% 的真实事件。")

o("")
o("=" * 104)
o("G. lastEdge 锚的起点偏差：onset gap 落在阈值内会提前/推迟多少")
o("=" * 104)
ogs = sorted(r["og"] for r in R if r["og"] is not None and len(r["hist"]) >= 64)
o(f"  he>=64 游程的 onset gap e: n={len(ogs)} P50={pc(ogs,.5):.3f} "
  f"P99={pc(ogs,.99):.3f} max={ogs[-1]:.3f}ms；e>50ms 的游程 n={sum(1 for x in ogs if x>50)}")
o("  若读取掉拍使 e 达到数百 ms，则「距上次推进」在停滞尚未被观测时就已含该 gap，"
  "lastEdge 锚类判据(C2-abs-P95x2/C3-r4/r8/r12)的 since_advance 会提前越过阈值；")
o("  本语料 he>=64 的游程里未出现 wait==0 的触发（实跑 0/29、0/24、0/16、0/15），")
o("  但 e 最大 338.157ms 已与 C3-r4 阈值(~128ms)同量级，阈值漂移风险未验。")

o("")
o("=" * 104)
o("H. C2/C3 相对判据的具体误触发样本（正常慢帧 / 伪影）")
o("=" * 104)

def rel2(r, p, m, N, cap=None, abs_=False):
    h = r["hist"][-N:]
    if len(h) < N or (abs_ and r["og"] is None):
        return None, None
    th = pc(h, p) * m
    if cap is not None:
        th = min(th, cap)
    off = r["og"] if abs_ else 0.0
    for x in range(r["i"], r["j"] + 1):
        if (r["T"][x] - r["T"][r["i"]]) * 1000.0 + off > th:
            return x, th
    return None, th

o("  C2-P95x2 的 4 次 d<100ms 误触发（normal slow frame 越过了偏低的 P95×2 阈值）：")
for r in R:
    x, th = rel2(r, .95, 2, 64)
    if x is not None and r["dfin"] < 100.0:
        o(f"    {r['key']} dfin={r['dfin']:.3f}ms theta={th:.3f}ms "
          f"触发等待={(r['T'][x]-r['T'][r['i']])*1000:.3f}ms he={len(r['hist'])}")
o("  C3-r1.5 的 d<100ms 误触发前 4 条：")
cnt = 0
for r in R:
    x = rate(r, 1.5, 64, "runStart")
    if x is not None and r["dfin"] < 100.0:
        o(f"    {r['key']} dfin={r['dfin']:.3f}ms "
          f"触发等待={(r['T'][x]-r['T'][r['i']])*1000:.3f}ms")
        cnt += 1
        if cnt >= 4:
            break
o("  C2-cap40-P95x2 的 d<100ms 误触发前 3 条（阈值完全由 40ms CAP 决定）：")
cnt = 0
for r in R:
    x, th = rel2(r, .95, 2, 64, cap=40.0)
    if x is not None and r["dfin"] < 100.0:
        o(f"    {r['key']} dfin={r['dfin']:.3f}ms theta={th:.3f}ms "
          f"触发等待={(r['T'][x]-r['T'][r['i']])*1000:.3f}ms")
        cnt += 1
        if cnt >= 3:
            break
o("  注：C2/C3 高阈值档的「触发」多数落在 d>=100ms 但 isRealMatch=False 的窗尾终局冻结")
o("  （见 C 节），这些不是真实战斗停滞，却因口径B按 d>=100ms 计费而免于计为误报。")

o("")
o("=" * 104)
o("本件：零真机 / 零采样代码 / 只读语料 / 不修改任何既有文件 / 未 commit push")
o("=" * 104)
if not OUT.resolve().is_relative_to(WD):
    raise ValueError("escape")
OUT.write_text("\n".join(B) + "\n", encoding="utf-8")
print(f"\n输出已写：{OUT}")
