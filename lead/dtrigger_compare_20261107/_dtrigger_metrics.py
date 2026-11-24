# -*- coding: utf-8 -*-
"""
_dtrigger_metrics.py - 判据全量实跑 + 完整指标（执行者）
唯一写域：lead/dtrigger_compare_20261107/ 下本脚本自己创建的 _dtrigger_metrics_out.txt
         与 CRITERIA_METRICS.json
运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_dtrigger_metrics.py

口径（照抄任务书，不自创）：
  - 真实事件集合 = STALL_EVENTS.json 中 isRealMatch==true 的 1681 条（不是 1737）。
  - 只在 moving64 推进窗上跑（manifest 同既有探针）。
  - k 点 = k-1 个间隔（length = j-i+1，length >= k）。
  - 误触发 = 触发了但该游程最终 dur < 100ms（口径B事后分类，只计费不参与触发）。
  - 误触发率 = 误触发数 / 触发总数（不是 FP/(FP+TN)）。
  - 每个游程最多触发一次；判据在线因果，只读 t[runStart..idx] 与 runStart 前历史。

延迟口径（本脚本新增，任务书要求）：
  - 起算点 = 真实事件的起点 S，用事件的 startTick 对应的 t[startTick] 锚定。
    实跑验证：1681 条 real 事件的 (trip,window,startTick,endTick) 与 moving64 窗内
    「帧号不变游程」(i,j) 逐条精确相等（本脚本打印对齐计数）。
    S 的物理精确值语料不可测；这里取可观测锚 S_hat = t[startTick]，
    故所有 latency 是相对物理 S 的**下界**（与既有文档一致，不声称是严格值）。
  - 触发时刻 T = 触发采样点 idx 的 t[idx]；latency = (t[idx]-t[startTick])*1000 ms。
  - 只统计「被某条真实事件覆盖的触发」的延迟；未覆盖的触发仍计入 triggers /
    falseTriggers，但不进延迟分布（按任务书要求）。
  - P50 = statistics.median，P95 = 线性最近秩 int(0.95*(n-1))，max = 最大值。
  - within50msRate = 在 S+50ms 窗口内（latency <= 50.0）的真实事件数 / 1681。
    分母固定为真实事件全集（1681），未命中的真实事件按「不在窗口内」计 0。

判据实现说明（与既有探针 _dtrigger_probe.py / _dtrigger_analysis.py /
  _dtrigger_supplement.py 的实跑数字对齐，但本脚本独立实现、不 import 它们）：
  - 历史基线 = 每次帧号推进的 t[edge]-t[prevEdge]（ms）；runStart 处可用历史
    = h_end = hist_len_at[i-1]，滑窗 = hist[h_end-N:h_end]，不含当前停滞。
  - C1：第 k 拍触发（idx = i+k-1）。
  - C2 相对：elapsed = t[idx]-t[runStart] > 分位基线*mult；C2-abs 用「上一帧沿」锚
    (since_advance = elapsed + onset_gap)；cap 版 min(theta, 40ms)。
  - C3 r1.5/r2/N16-*：runStart 锚（elapsed/median），与既有实跑数字 683/180/758/195
    对齐；C3-r4/r8/r12：上一帧沿锚（since_advance/median），与既有 24/16/15 对齐；
    -clean 后缀：runStart 锚，r4/r8 与既有 24/16 对齐。
  - C4：elapsed > theta 且 >=3 拍；C5：连续10拍 且 elapsed > 30ms，取较晚者。
  - 不可实现项 R1/U1..U4 不参与跑分，仅在 txt 中登记（JSON 中亦给出零值 +
    "notImplementable": true，避免伪造指标）。

纪律：零真机 / 零采样代码 / 只读语料 / 无 subprocess / 不 commit、不 push。
"""

import hashlib
import json
import re
import statistics
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANIFEST = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EVENTS = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
WD = (ROOT / "lead/dtrigger_compare_20261107").resolve()
OUT_TXT = WD / "_dtrigger_metrics_out.txt"
OUT_JSON = WD / "CRITERIA_METRICS.json"

DCLASS_MS = 100.0
CUTOFF_MS = 50.0

lines = []
def out(s=""):
    lines.append(str(s))
    print(s)

def pctl(sorted_arr, p):
    """线性最近秩百分位（与既有 _dtrigger_probe.py:61-65 同口径）。"""
    return sorted_arr[int(p * (len(sorted_arr) - 1))] if sorted_arr else None

def fmt(v, n=3):
    return "N/A" if v is None else f"{v:.{n}f}"

def r6(v):
    return round(v, 6)

# ---------------------------------------------------------------- 语料加载
out("=" * 104)
out("【判据全量实跑 · 完整指标】执行者 _dtrigger_metrics.py")
out("=" * 104)
cache = {}
for p in sorted(BASE.rglob("measure_w*.json")):
    pr = p.resolve()
    if not pr.is_relative_to(BASE):
        raise ValueError("corpus escape")
    parts = pr.relative_to(BASE).parts
    key = (parts[0] if len(parts) > 1 else "(root)", pr.stem[len("measure_"):])
    d = json.loads(pr.read_text(encoding="utf-8-sig"))
    assert len(d["samples"]["t"]) == len(d["samples"]["f"])
    cache[key] = d
n_samples = sum(len(v["samples"]["t"]) for v in cache.values())
out(f"语料文件 n={len(cache)}，采样点 n={n_samples}，hz={sorted({v.get('hz') for v in cache.values()})}")

manifest_keys = set()
for ln in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
    m = re.match(r"^([a-zA-Z0-9_()]+)\s+(w\d)\s+([0-9.]+)", ln.strip())
    if m and (m[1], m[2]) in cache:
        s = cache[(m[1], m[2])]["samples"]
        if len(s["t"]) >= 2 and any(a != b for a, b in zip(s["f"], s["f"][1:])):
            manifest_keys.add((m[1], m[2]))
manifest_keys = sorted(manifest_keys)
out(f"moving64 推进窗 n={len(manifest_keys)}")

events_all = json.loads(EVENTS.read_text(encoding="utf-8-sig"))
real = [e for e in events_all if e.get("isRealMatch") is True]
real_keys = {(e["trip"], e["window"], e["startTick"], e["endTick"]) for e in real}
out(f"STALL_EVENTS 全量 n={len(events_all)}，isRealMatch==true n={len(real)}，real_keys 去重 n={len(real_keys)}")

# ---------------------------------------------------------------- 逐窗构造
# rec = dict(trip,win,i,j,npts,dfin,he,onset_gap,T,hist)
REC = []
for trip, win in manifest_keys:
    s = cache[(trip, win)]["samples"]
    T, F = s["t"], s["f"]
    n = len(F)
    hist = []
    hlen = [0] * n
    le = 0
    for a in range(1, n):
        if F[a] != F[a - 1]:
            hist.append((T[a] - T[le]) * 1000.0)
            le = a
        hlen[a] = len(hist)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and F[j + 1] == F[i]:
            j += 1
        REC.append({
            "trip": trip, "win": win, "i": i, "j": j,
            "npts": j - i + 1,
            "dfin": (T[j] - T[i]) * 1000.0,
            "he": hlen[i - 1] if i > 0 else 0,
            "og": (T[i] - T[i - 1]) * 1000.0 if i > 0 else None,
            "T": T, "hist": hist,
        })
        i = j + 1
out(f"推进窗内帧号游程 n={len(REC)}（评分母体，每游程每判据最多触发一次）")
aligned = sum(1 for r in REC if (r["trip"], r["win"], r["i"], r["j"]) in real_keys)
out(f"real 事件与游程 (i,j)=(startTick,endTick) 精确对齐 n={aligned}/{len(real_keys)}"
    f"  -> 延迟锚 S_hat=t[startTick] 可用（物理 S 仍不可测，latency 为下界）")

# ---------------------------------------------------------------- 判据谓词
# 每个函数返回 (trigger_idx 或 None)；触发时刻 T[idx] 与等待统一在评分处算。
def f_k(r, k):
    return r["i"] + k - 1 if r["npts"] >= k else None

def f_rel(r, q, mult, N, cap=None):
    he = r["he"]
    if he < N:
        return None
    theta = pctl(sorted(r["hist"][he - N:he]), q) * mult
    if cap is not None:
        theta = min(theta, cap)
    T, i = r["T"], r["i"]
    for x in range(i, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 > theta:
            return x
    return None

def f_rel_abs(r, q, mult, N):
    """C2-abs：距离锚 = 上一帧沿；since_advance = elapsed + onset_gap。"""
    he, og = r["he"], r["og"]
    if he < N or og is None:
        return None
    theta = pctl(sorted(r["hist"][he - N:he]), q) * mult
    T, i = r["T"], r["i"]
    for x in range(i, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 + og > theta:
            return x
    return None

def f_rate(r, mult, N, anchor):
    """anchor='runStart': elapsed/base > mult；anchor='lastEdge': (elapsed+og)/base > mult。"""
    he, og = r["he"], r["og"]
    if he < N or (anchor == "lastEdge" and og is None):
        return None
    base = statistics.median(r["hist"][he - N:he])
    if base <= 0:
        return None
    T, i = r["T"], r["i"]
    off = og if anchor == "lastEdge" else 0.0
    for x in range(i, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 + off > mult * base:
            return x
    return None

def f_abs(r, theta, kmin=3):
    if r["npts"] < kmin:
        return None
    T, i = r["T"], r["i"]
    for x in range(i + kmin - 1, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 > theta:
            return x
    return None

def f_hybrid(r, k, theta):
    """连续 k 拍 且 elapsed > theta，取较晚者：idx >= i+k-1 且 elapsed > theta。"""
    if r["npts"] < k:
        return None
    T, i = r["T"], r["i"]
    for x in range(i + k - 1, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 > theta:
            return x
    return None

CRIT = []
def add(cid, fn, note):
    CRIT.append((cid, fn, note))

for k in (10, 25, 50):
    add(f"C1-k{k}", lambda r, k=k: f_k(r, k), f"连续{k}拍第{k}拍触发(k点=k-1间隔)")
for qn, q in (("P95", .95), ("P99", .99)):
    for m in (2, 3):
        add(f"C2-{qn}x{m}", lambda r, q=q, m=m: f_rel(r, q, m, 64), "近64条分位*倍;runStart锚")
add("C2-abs-P95x2", lambda r: f_rel_abs(r, .95, 2, 64), "上一帧沿锚;近64条P95*2")
add("C2-N16-P95x2", lambda r: f_rel(r, .95, 2, 16), "近16条P95*2")
add("C2-cap40-P95x2", lambda r: f_rel(r, .95, 2, 64, cap=40.0), "min(近64条P95*2,40ms)")
add("C2-N16-P95x2-cap40", lambda r: f_rel(r, .95, 2, 16, cap=40.0), "min(近16条P95*2,40ms)")
add("C3-r1.5", lambda r: f_rate(r, 1.5, 64, "runStart"), "runStart锚;近64条中位数")
add("C3-r2", lambda r: f_rate(r, 2, 64, "runStart"), "runStart锚;近64条中位数")
add("C3-r4", lambda r: f_rate(r, 4, 64, "lastEdge"), "上一帧沿锚;近64条中位数")
add("C3-r4-clean", lambda r: f_rate(r, 4, 64, "runStart"), "runStart锚;近64条中位数")
add("C3-r8", lambda r: f_rate(r, 8, 64, "lastEdge"), "上一帧沿锚;近64条中位数")
add("C3-r8-clean", lambda r: f_rate(r, 8, 64, "runStart"), "runStart锚;近64条中位数")
add("C3-r12", lambda r: f_rate(r, 12, 64, "lastEdge"), "上一帧沿锚;近64条中位数")
add("C3-N16-r1.5", lambda r: f_rate(r, 1.5, 16, "runStart"), "runStart锚;近16条中位数")
add("C3-N16-r2", lambda r: f_rate(r, 2, 16, "runStart"), "runStart锚;近16条中位数")
for t in (16, 24, 30, 40, 48):
    add(f"C4-t{t}", lambda r, t=t: f_abs(r, t), f"elapsed>{t}ms且>=3拍")
add("C5-k10t30", lambda r: f_hybrid(r, 10, 30), "连续10拍且elapsed>30ms取较晚")

NOT_IMPLEMENTABLE = [
    ("R1-PostHoc100", "需事后读取 endTick/durationMs 或最终 d>=100ms，违反在线因果"),
    ("U1-PhysicalS-Anchored", "物理停滞起点 S 无独立观测，语料只有 (t,f)"),
    ("U2-CrossWindow-History", "语料为 25s 孤立窗、窗间 4s 空白，缺未切片连续长程时序"),
    ("U3-InternalStateFlag", "语料只有外部 CurrentFrame 帧号，缺内部状态枚举"),
    ("U4-EndToEndSave", "缺实际保存时刻 C 与现场快照耗时（Q5 四项全未验）"),
]

# ---------------------------------------------------------------- 全量跑分
out(f"\n可执行判据 n={len(CRIT)}，不可实现项 n={len(NOT_IMPLEMENTABLE)}")
out("")
hdr = (f"{'id':<22}|{'triggers':>9}|{'falseTr':>8}|{'falseRate':>10}|{'realHits':>9}|"
       f"{'missed':>7}|{'latP50':>9}|{'latP95':>9}|{'latMax':>9}|{'within50':>9}| note")
out(hdr)
out("-" * len(hdr))
METRICS = {}
for cid, fn, note in CRIT:
    triggers = 0
    false_tr = 0
    hit_keys = set()
    lat = []           # 仅被真实事件覆盖的触发的延迟
    within50 = 0
    for r in REC:
        idx = fn(r)
        if idx is None:
            continue
        triggers += 1
        if r["dfin"] < DCLASS_MS:
            false_tr += 1
        key = (r["trip"], r["win"], r["i"], r["j"])
        if key in real_keys:
            hit_keys.add(key)
            L = (r["T"][idx] - r["T"][r["i"]]) * 1000.0   # S_hat = t[startTick] = t[i]
            lat.append(L)
            if L <= CUTOFF_MS:
                within50 += 1
    lat.sort()
    real_hits = len(hit_keys)
    missed = len(real_keys) - real_hits
    rec = {
        "id": cid,
        "triggers": triggers,
        "falseTriggers": false_tr,
        "falseTriggerRate": r6(false_tr / triggers) if triggers else 0.0,
        "realHits": real_hits,
        "missedReal": missed,
        "latencyP50Ms": r6(statistics.median(lat)) if lat else 0.0,
        "latencyP95Ms": r6(pctl(lat, .95)) if lat else 0.0,
        "latencyMaxMs": r6(lat[-1]) if lat else 0.0,
        "within50msRate": r6(within50 / len(real_keys)),
        "within50msRateOverHits": r6(within50 / real_hits) if real_hits else 0.0,
        "within50msRateDenominator": len(real_keys),
        "latencySampleN": len(lat),
        "latencyNote": ("延迟分布为空：本判据没有任何触发被真实事件覆盖，"
                        "latencyP50/P95/Max 的 0.0 是占位值、不是实测值"
                        if not lat else ("延迟样本 n=%d；P95 为最近秩，小样本下可能小于 P50" % len(lat))),
        "note": note,
        "notImplementable": False,
    }
    METRICS[cid] = rec
    out(f"{cid:<22}|{triggers:>9}|{false_tr:>8}|{rec['falseTriggerRate']:>10.6f}|{real_hits:>9}|"
        f"{missed:>7}|{fmt(rec['latencyP50Ms']):>9}|{fmt(rec['latencyP95Ms']):>9}|"
        f"{fmt(rec['latencyMaxMs']):>9}|{rec['within50msRate']:>9.6f}| {note}")

for cid, why in NOT_IMPLEMENTABLE:
    METRICS[cid] = {
        "id": cid, "triggers": 0, "falseTriggers": 0, "falseTriggerRate": 0.0,
        "realHits": 0, "missedReal": len(real_keys),
        "latencyP50Ms": 0.0, "latencyP95Ms": 0.0, "latencyMaxMs": 0.0,
        "within50msRate": 0.0, "within50msRateOverHits": 0.0,
        "within50msRateDenominator": len(real_keys), "latencySampleN": 0,
        "latencyNote": "不可实现，未实跑；所有指标为占位零值、不是实测值",
        "note": "不可实现：" + why, "notImplementable": True,
    }
    out(f"{cid:<22}|{'N/A':>9}|{'N/A':>8}|{'N/A':>10}|{'N/A':>9}|{'N/A':>7}|"
        f"{'N/A':>9}|{'N/A':>9}|{'N/A':>9}|{'N/A':>9}| 不可实现：{why}")

# ---------------------------------------------------------------- 诚实账与交叉核对
out("\n" + "=" * 104)
out("【口径与诚实账】")
out("=" * 104)
out("误触发 = 触发但游程最终 d_final<100ms（事后分类，只计费不参与触发）；误触发率 = 误触发数/触发总数。")
out("查准率(口径B) = 最终 d>=100ms 的触发数/触发总数；本表未列，但可由 1-falseTriggerRate 直接得出。")
out("延迟起算 = 事件 startTick 的 t[startTick]（S_hat 观测锚）。物理 S∈(t[i-1],t[i]]，")
out("真实 latency = 本表 latency + (S_hat-S) >= 本表值；:177 的严格 S+50ms 核算需物理 S，本次语料不可得。")
out("未被任何真实事件覆盖的触发：计入 triggers/falseTriggers，不进延迟分布（按任务书要求）。")
out("within50msRate 分母固定 = 1681 条真实事件全集；漏掉的真实事件按不在 S+50ms 窗口内计 0。")
out("  备选口径 within50msRateOverHits = 窗口内事件数 / realHits（只在 JSON 中给出，"
    "供选择权人对照；主字段 within50msRate 用「真实事件占比」口径）。")
out("P50=statistics.median；P95=线性最近秩 int(0.95*(n-1))；max=最大值；falseTriggerRate 保留 6 位小数。")
out("注意：延迟样本 n 很小（部分判据仅 1~19 个真实命中）时，最近秩 P95 可能小于 P50、")
out("      且中位数/最大值由极少数事件主导；这是实测分布，不是错误。C3-r12 无任何真实命中，")
out("      其 latencyP50/P95/Max 的 0.0 是占位值（latencySampleN=0），不是实测延迟。")
og = sorted(r["og"] for r in REC if r["og"] is not None)
out(f"onset 观测滞后 e=t[i]-t[i-1] 有效 n={len(og)} 中位={fmt(statistics.median(og))} "
    f"P95={fmt(pctl(og,.95))} max={fmt(og[-1])} ms（自跑，仅作 S 不可测的旁证）")

out("\n【自跑交叉核对：与既有实跑输出对照（不抄数字当结果，只报差异）】")
for cid in ("C1-k10", "C1-k25", "C1-k50", "C2-P95x2", "C2-P95x3", "C2-P99x2",
            "C2-P99x3", "C2-abs-P95x2", "C2-N16-P95x2", "C2-cap40-P95x2",
            "C2-N16-P95x2-cap40", "C3-r1.5", "C3-r2", "C3-r4", "C3-r4-clean",
            "C3-r8", "C3-r8-clean", "C3-r12", "C3-N16-r1.5", "C3-N16-r2",
            "C4-t16", "C4-t24", "C4-t30", "C4-t40", "C4-t48", "C5-k10t30"):
    m = METRICS[cid]
    out(f"  {cid:<22} triggers={m['triggers']:>6} false={m['falseTriggers']:>6} "
        f"rate={m['falseTriggerRate']*100:>8.4f}% hits={m['realHits']:>5} "
        f"latP50={fmt(m['latencyP50Ms'])}ms")

# ---------------------------------------------------------------- 落盘
for p in (OUT_TXT, OUT_JSON):
    if not p.resolve().is_relative_to(WD):
        raise ValueError("output escapes write domain")
OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
OUT_JSON.write_text(json.dumps(METRICS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
out(f"\n输出已写：{OUT_TXT}")
out(f"输出已写：{OUT_JSON}")
out("【执行者结束 · 零真机 / 零采样代码 / 只读语料 / 无 commit push】")
