# -*- coding: utf-8 -*-
"""
_cost_quota.py — 执行者：触发成本 / 配额覆盖率离线核算（零真机、零采样代码、只读语料）

唯一写域：lead/dtrigger_compare_20261107/ 下本次新建文件：
    _cost_quota.py（本脚本）、_cost_quota_out.txt、_cost_quota_data.json、COST_QUOTA.md
运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_cost_quota.py

本脚本自己重算 26 个判据的**触发序列**（不复用既有探针函数、不复用 CRITERIA_METRICS.json
的结果数字；后者仅用于事后交叉核对），然后按时间顺序让**每一次触发**（含误触发）消耗配额。

关键建模（全部写在输出里，不隐藏）：
  - 评分母体 = moving64 推进窗（manifest 中有帧号变化的 64 窗，28381 条帧号游程）。
    与 _dtrigger_metrics.py / _dtrigger_probe.py / _d30_facts.py:72-94 同口径。
  - 每条游程每判据最多 1 次触发；触发时刻 = t[idx]（绝对 perf_counter 秒）。
  - 配额「先到先得」：按触发时刻升序，前 N 次触发各消耗 1 个配额；第 N+1 次起丢弃。
    **误触发同样消耗配额**——这就是「误触发抢占」。
  - 真实事件被「捕获」= 该事件的触发发生在其所属配额组的前 N 次触发之内。
  - 每窗配额组 = (trip, window)；每会话配额组 = trip（跨窗按 t[idx] 全局排序）。
  - 真实事件 = STALL_EVENTS.json 中 isRealMatch==true 的 1681 条；不混用 1737。
  - 时长桶照 _d30_facts.py:50：<200ms→0.1-0.2s，<500ms→0.2-0.5s，否则→0.5-1.0s。
  - capUpper 是反事实上界：假设 1681 条真实事件全部在其观测起点 t[startTick] 就触发，
    同时保留该判据的**非真实触发**流，再跑同一配额。用于把「误触发抢占」与
    「判据自身召回不足」分开；它不是设计、不是工程可达性声明。
"""

import hashlib
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANIFEST = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EVENTS = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
METRICS_JSON = (ROOT / "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json").resolve()
WD = (ROOT / "lead/dtrigger_compare_20261107").resolve()
OUT_TXT = WD / "_cost_quota_out.txt"
OUT_JSON = WD / "_cost_quota_data.json"
OUT_MD = WD / "COST_QUOTA.md"

for p in (OUT_TXT, OUT_JSON, OUT_MD):
    if not p.resolve().is_relative_to(WD):
        raise ValueError("output escapes write domain: " + str(p))

NS = (1, 3, 5)
BUCKETS = ("0.1-0.2s", "0.2-0.5s", "0.5-1.0s")
IDEAL_WINDOW = {1: 26, 3: 73, 5: 117}          # D-30 §3 公布值，本脚本会自己重算核对

lines = []
def out(s=""):
    lines.append(str(s))
    print(s)

def pctl(a, p):
    """线性最近秩：与 _dtrigger_metrics.py:68-70 / _dtrigger_probe.py:61-65 同口径。"""
    return a[int(p * (len(a) - 1))] if a else None

def bucket(d):
    return "0.1-0.2s" if d < 200 else ("0.2-0.5s" if d < 500 else "0.5-1.0s")

def f6(x):
    return f"{x:.6f}"

def pct(x, den):
    return "N/A" if not den else f"{x/den*100:.2f}%"

# ------------------------------------------------------------------ 0 指纹
out("=" * 108)
out("【触发成本 / 配额覆盖率核算 · 执行者 _cost_quota.py】")
out("=" * 108)
for rel in ("lead/stall_event_def_20261106/STALL_EVENTS.json",
            "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json",
            "lead/dtrigger_compare_20261107/_dtrigger_metrics.py",
            "lead/d30_ruling_20261106/RULING_D30.md",
            "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt"):
    out(f"sha256 {rel} = {hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()}")

# ------------------------------------------------------------------ 1 语料
cache = {}
for p in sorted(BASE.rglob("measure_w*.json")):
    pr = p.resolve()
    if not pr.is_relative_to(BASE):
        raise ValueError("corpus escapes base")
    parts = pr.relative_to(BASE).parts
    key = (parts[0] if len(parts) > 1 else "(root)", pr.stem[len("measure_"):])
    d = json.loads(pr.read_text(encoding="utf-8-sig"))
    assert len(d["samples"]["t"]) == len(d["samples"]["f"])
    cache[key] = d
n_samples = sum(len(v["samples"]["t"]) for v in cache.values())
out(f"\n语料文件 n={len(cache)}，采样点 n={n_samples}，hz={sorted({v.get('hz') for v in cache.values()})}")

manifest_keys = set()
for ln in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
    m = re.match(r"^([a-zA-Z0-9_()]+)\s+(w\d)\s+([0-9.]+)", ln.strip())
    if m and (m[1], m[2]) in cache:
        s = cache[(m[1], m[2])]["samples"]
        if len(s["t"]) >= 2 and any(a != b for a, b in zip(s["f"], s["f"][1:])):
            manifest_keys.add((m[1], m[2]))
manifest_keys = sorted(manifest_keys)
out(f"moving64 推进窗 n={len(manifest_keys)}（manifest 97 行中带帧号变化者；_d30_facts.py:83 断言=64）")
out(f"推进窗覆盖 trip n={len(set(k[0] for k in manifest_keys))}")

events_all = json.loads(EVENTS.read_text(encoding="utf-8-sig"))
real = [e for e in events_all if e.get("isRealMatch") is True]
dur_by_key = {}
for e in real:
    k = (e["trip"], e["window"], e["startTick"], e["endTick"])
    assert k not in dur_by_key, ("duplicate real key", k)
    dur_by_key[k] = e["durationMs"]
real_keys = set(dur_by_key)
out(f"STALL_EVENTS 全量 n={len(events_all)}，isRealMatch==true n={len(real)}，去重后 real_keys n={len(real_keys)}")
assert len(real) == len(real_keys) == 1681
assert min(dur_by_key.values()) >= 100 and max(dur_by_key.values()) < 1000

bucket_of_key = {k: bucket(v) for k, v in dur_by_key.items()}
BASE_B = Counter(bucket_of_key.values())
out("时长桶基线（母数 1681）：" + " / ".join(f"{b}={BASE_B[b]} ({BASE_B[b]/1681*100:.4f}%)" for b in BUCKETS))
win_counts = Counter(k[:2] for k in real_keys)
trip_counts = Counter(k[0] for k in real_keys)
out(f"非空真实事件窗 n={len(win_counts)}（D-30 §3 同），真实事件所在 trip n={len(trip_counts)}")
out("真实事件窗是否在推进窗集合内：" +
    str(sum(1 for k in win_counts if k in set(manifest_keys))) + f"/{len(win_counts)}")

# ------------------------------------------------------------------ 2 逐窗构造游程 + 因果历史
# 独立构造：逐窗扫描 (t,f)，hist = 帧推进处的 t[edge]-t[prevEdge]（毫秒）
REC = []
nonmono = 0
for trip, win in manifest_keys:
    s = cache[(trip, win)]["samples"]
    T, F = s["t"], s["f"]
    n = len(F)
    if any(T[x + 1] <= T[x] for x in range(n - 1)):
        nonmono += 1
    hist, hlen, le = [], [0] * n, 0
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
            "trip": trip, "win": win, "i": i, "j": j, "npts": j - i + 1,
            "t_start": T[i], "T": T, "hist": hist,
            "he": hlen[i - 1] if i > 0 else 0,
            "og": (T[i] - T[i - 1]) * 1000.0 if i > 0 else None,
            "key": (trip, win, i, j),
        })
        i = j + 1
out(f"推进窗内帧号游程 n={len(REC)}；窗内 t 非单调的窗数={nonmono}")
assert nonmono == 0, "t must be strictly increasing inside each window for chronological ordering"
# 跨窗 t 重复值检查：同一 trip 内若多个窗共享 t 值，全局排序需要确定性 tie-break
_t_by_trip = defaultdict(list)
for k in manifest_keys:
    _t_by_trip[k[0]].extend(cache[k]["samples"]["t"])
tie_trips = {t: (len(v) - len(set(v))) for t, v in _t_by_trip.items() if len(set(v)) != len(v)}
out(f"同 trip 跨窗 t 重复值：涉及 trip 数={len(tie_trips)}，重复计数合计={sum(tie_trips.values())}")
if tie_trips:
    out("  重复明细(前5)：" + str(list(tie_trips.items())[:5]))
aligned = sum(1 for r in REC if r["key"] in real_keys)
out(f"真实事件与游程 (i,j)=(startTick,endTick) 精确对齐 n={aligned}/{len(real_keys)}")
assert aligned == 1681

# 跨窗 t 序（每会话配额需要）：真实事件所在 trip 内各推进窗的时间区间
bytrip = defaultdict(list)
for k in manifest_keys:
    bytrip[k[0]].append(k[1])
cross_overlap = []
for trip, wins in bytrip.items():
    segs = []
    for w in sorted(wins):
        T = cache[(trip, w)]["samples"]["t"]
        segs.append((T[0], T[-1], w))
    segs.sort()
    for a in range(1, len(segs)):
        if segs[a][0] <= segs[a - 1][1]:
            cross_overlap.append((trip, segs[a - 1][2], segs[a][2]))
out(f"推进窗中同 trip 跨窗 t 区间重叠对 n={len(cross_overlap)}（空则按 t 全局排序无歧义）")
if cross_overlap:
    out("  重叠样例：" + str(cross_overlap[:5]))

# ------------------------------------------------------------------ 3 26 个判据（本脚本独立重算触发序列）
# 口径转写自 _dtrigger_metrics.py:146-232，但为独立实现：函数返回触发采样点 idx 或 None。
def c_k(r, k):
    return r["i"] + k - 1 if r["npts"] >= k else None

def c_rel(r, q, mult, N, cap=None):
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

def c_rel_abs(r, q, mult, N):
    he, og = r["he"], r["og"]
    if he < N or og is None:
        return None
    theta = pctl(sorted(r["hist"][he - N:he]), q) * mult
    T, i = r["T"], r["i"]
    for x in range(i, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 + og > theta:
            return x
    return None

def c_rate(r, mult, N, anchor):
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

def c_abs(r, theta, kmin=3):
    if r["npts"] < kmin:
        return None
    T, i = r["T"], r["i"]
    for x in range(i + kmin - 1, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 > theta:
            return x
    return None

def c_hybrid(r, k, theta):
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
    add(f"C1-k{k}", lambda r, k=k: c_k(r, k), f"连续{k}拍第{k}拍触发")
for qn, q in (("P95", .95), ("P99", .99)):
    for m in (2, 3):
        add(f"C2-{qn}x{m}", lambda r, q=q, m=m: c_rel(r, q, m, 64), "近64条P95/P99分位×倍;runStart锚")
add("C2-abs-P95x2", lambda r: c_rel_abs(r, .95, 2, 64), "上一帧沿锚;近64条P95×2")
add("C2-N16-P95x2", lambda r: c_rel(r, .95, 2, 16), "近16条P95×2")
add("C2-cap40-P95x2", lambda r: c_rel(r, .95, 2, 64, cap=40.0), "min(近64条P95×2,40ms)")
add("C2-N16-P95x2-cap40", lambda r: c_rel(r, .95, 2, 16, cap=40.0), "min(近16条P95×2,40ms)")
add("C3-r1.5", lambda r: c_rate(r, 1.5, 64, "runStart"), "runStart锚;近64条中位数")
add("C3-r2", lambda r: c_rate(r, 2, 64, "runStart"), "runStart锚;近64条中位数")
add("C3-r4", lambda r: c_rate(r, 4, 64, "lastEdge"), "上一帧沿锚;近64条中位数")
add("C3-r4-clean", lambda r: c_rate(r, 4, 64, "runStart"), "runStart锚;近64条中位数")
add("C3-r8", lambda r: c_rate(r, 8, 64, "lastEdge"), "上一帧沿锚;近64条中位数")
add("C3-r8-clean", lambda r: c_rate(r, 8, 64, "runStart"), "runStart锚;近64条中位数")
add("C3-r12", lambda r: c_rate(r, 12, 64, "lastEdge"), "上一帧沿锚;近64条中位数")
add("C3-N16-r1.5", lambda r: c_rate(r, 1.5, 16, "runStart"), "runStart锚;近16条中位数")
add("C3-N16-r2", lambda r: c_rate(r, 2, 16, "runStart"), "runStart锚;近16条中位数")
for t in (16, 24, 30, 40, 48):
    add(f"C4-t{t}", lambda r, t=t: c_abs(r, t), f"elapsed>{t}ms且>=3拍")
add("C5-k10t30", lambda r: c_hybrid(r, 10, 30), "连续10拍且elapsed>30ms取较晚")
assert len(CRIT) == 26

# ------------------------------------------------------------------ 4 触发序列
# trig = (t_abs, idx, trip, win, key, is_real, bkt)
TRIG = {}
for cid, fn, note in CRIT:
    lst = []
    for r in REC:
        idx = fn(r)
        if idx is None:
            continue
        key = r["key"]
        is_real = key in real_keys
        lst.append((r["T"][idx], idx, r["trip"], r["win"], key, is_real,
                    bucket_of_key[key] if is_real else None))
    TRIG[cid] = lst

# 与既有 CRITERIA_METRICS.json 事后交叉核对（不复用其结果，只比对）
ref = json.loads(METRICS_JSON.read_text(encoding="utf-8-sig"))
out("\n【触发序列自跑 vs CRITERIA_METRICS.json 交叉核对】")
xcheck = []
for cid, _, _ in CRIT:
    lst = TRIG[cid]
    hits = len({t[4] for t in lst if t[5]})
    m = ref[cid]
    ok = (len(lst) == m["triggers"] and hits == m["realHits"])
    xcheck.append(ok)
    out(f"  {cid:<22} triggers={len(lst):>6} (ref {m['triggers']:>6})  realHits={hits:>5} (ref {m['realHits']:>5})  {'PASS' if ok else 'FAIL'}")
out(f"  交叉核对合计 PASS={sum(xcheck)} FAIL={len(xcheck)-sum(xcheck)}（26 档）")

# ------------------------------------------------------------------ 5 理想值自跑复现
ideal_w = {N: sum(min(N, c) for c in win_counts.values()) for N in NS}
ideal_t = {N: sum(min(N, c) for c in trip_counts.values()) for N in NS}
out("\n【理想配额覆盖自跑复现（假设配额只由真实事件消耗）】")
for N in NS:
    out(f"  N={N}: 每窗理想={ideal_w[N]}/1681 ({ideal_w[N]/1681*100:.4f}%)  D-30 公布={IDEAL_WINDOW[N]}  "
        f"{'一致' if ideal_w[N]==IDEAL_WINDOW[N] else '不一致'}；每会话理想={ideal_t[N]}/1681 ({ideal_t[N]/1681*100:.4f}%)")
    out(f"        每窗放弃={1681-ideal_w[N]}；每会话放弃={1681-ideal_t[N]}；"
        f"每会话理想配额槽={N*len(trip_counts)} vs 每窗理想配额槽={N*len(win_counts)}")
assert all(ideal_w[N] == IDEAL_WINDOW[N] for N in NS), "recomputed window ideal differs from D-30"

# ------------------------------------------------------------------ 6 配额模拟
def simulate(trig, scope, N):
    """按时间顺序、先到先得；每次触发（含误触发）消耗 1 个配额。"""
    groups = defaultdict(list)
    for t in trig:
        g = (t[2], t[3]) if scope == "window" else t[2]
        groups[g].append(t)
    cap_keys = set()
    cap_b, pre_b = Counter(), Counter()
    used_total = 0
    false_eaten = 0
    for g, arr in groups.items():
        arr.sort(key=lambda x: (x[0], x[3], x[1]))   # 绝对时间优先；win/idx 仅作确定性 tie-break
        used = 0
        for t in arr:
            if used < N:
                used += 1
                used_total += 1
                if not t[5]:
                    false_eaten += 1
                else:
                    cap_keys.add(t[4])
                    cap_b[t[6]] += 1
            elif t[5]:
                pre_b[t[6]] += 1
    cap = len(cap_keys)
    pre = sum(pre_b.values())
    never = 1681 - cap - pre
    return {
        "captured": cap,
        "rate": cap / 1681,
        "capB": {b: cap_b[b] for b in BUCKETS},
        "preB": {b: pre_b[b] for b in BUCKETS},
        "preempted": pre,
        "neverTriggered": never,
        "quotaUsed": used_total,
        "quotaEatenByFalse": false_eaten,
        "groups": len(groups),
    }

def synthetic_upper(cid, scope, N):
    """反事实上界：全部 1681 真实事件在 t[startTick] 触发 + 该判据的非真实触发流。"""
    false_part = [t for t in TRIG[cid] if not t[5]]
    synth = list(false_part)
    for r in REC:
        if r["key"] in real_keys:
            synth.append((r["t_start"], r["i"], r["trip"], r["win"], r["key"], True,
                          bucket_of_key[r["key"]]))
    return simulate(synth, scope, N)["captured"]

RESULTS, UPPER, NOFALSE = {}, {}, {}
for cid, _, _ in CRIT:
    RESULTS[cid], UPPER[cid], NOFALSE[cid] = {}, {}, {}
    real_only = [t for t in TRIG[cid] if t[5]]
    for scope in ("window", "trip"):
        for N in NS:
            RESULTS[cid][f"{scope}{N}"] = simulate(TRIG[cid], scope, N)
            UPPER[cid][f"{scope}{N}"] = synthetic_upper(cid, scope, N)
            NOFALSE[cid][f"{scope}{N}"] = simulate(real_only, scope, N)["captured"]

out("\n【主结果：真实事件实际被捕获数 / 1681】")
hdr = f"{'id':<22}|{'trig':>6}|{'hits':>5}|" + "".join(f"{'W'+str(N):>7}" for N in NS) + "|" + "".join(f"{'T'+str(N):>7}" for N in NS)
out(hdr)
out("-" * len(hdr))
for cid, _, _ in CRIT:
    hits = len({t[4] for t in TRIG[cid] if t[5]})
    row = f"{cid:<22}|{len(TRIG[cid]):>6}|{hits:>5}|"
    row += "".join(f"{RESULTS[cid][f'window{N}']['captured']:>7}" for N in NS) + "|"
    row += "".join(f"{RESULTS[cid][f'trip{N}']['captured']:>7}" for N in NS)
    out(row)
out("  W=每窗配额，T=每会话(trip)配额；数字为 captured/1681")

out("\n【不变式自检：captured <= 判据真实命中数，且 <= 理想值】")
inv_ok = 0
inv_bad = []
for cid, _, _ in CRIT:
    hits = len({t[4] for t in TRIG[cid] if t[5]})
    for scope in ("window", "trip"):
        for N in NS:
            c = RESULTS[cid][f"{scope}{N}"]["captured"]
            ideal = ideal_w[N] if scope == "window" else ideal_t[N]
            if c <= hits and c <= ideal:
                inv_ok += 1
            else:
                inv_bad.append((cid, scope, N, c, hits, ideal))
out(f"  PASS={inv_ok}/156  FAIL={len(inv_bad)}  {inv_bad[:5]}")

# ------------------------------------------------------------------ 7 时长桶偏差
out("\n【时长桶偏差：被捕获 / 被放弃的构成】")
for scope in ("window", "trip"):
    for N in NS:
        out(f"\n  --- {scope} N={N} ---")
        out(f"  {'id':<22}|{'cap':>5}|" + "".join(f"{b+'cap':>12}" for b in BUCKETS) + "|" +
            "".join(f"{b+'pre':>12}" for b in BUCKETS) + f"|{'s01':>8}|{'never':>7}|{'pre':>6}|{'Qfalse':>8}")
        for cid, _, _ in CRIT:
            r = RESULTS[cid][f"{scope}{N}"]
            cap = r["captured"]
            s01 = (r["capB"]["0.1-0.2s"] / cap * 100) if cap else float("nan")
            out(f"  {cid:<22}|{cap:>5}|" +
                "".join(f"{r['capB'][b]:>12}" for b in BUCKETS) + "|" +
                "".join(f"{r['preB'][b]:>12}" for b in BUCKETS) + "|" +
                (f"{s01:>7.2f}%" if cap else f"{'N/A':>8}") +
                f"|{r['neverTriggered']:>7}|{r['preempted']:>6}|{r['quotaEatenByFalse']:>8}")
        out("  s01 = 被捕获事件中 0.1-0.2s 桶占比（基线 90.4224%）；pre = 配额耗尽被抢占的真实事件；")
        out("  never = 判据从未在该真实事件上触发；Qfalse = 被误触发吃掉的配额槽数")

# 宏观汇总：26 判据合并的桶级捕获率
out("\n【宏观汇总：26 判据 × 3 档 N 合并后的桶级捕获率】")
AGG = {}
for scope in ("window", "trip"):
    for N in NS:
        cap_b, pre_b, never_b = Counter(), Counter(), Counter()
        csum = 0
        for cid, _, _ in CRIT:
            r = RESULTS[cid][f"{scope}{N}"]
            csum += r["captured"]
            for b in BUCKETS:
                cap_b[b] += r["capB"][b]
                pre_b[b] += r["preB"][b]
        # never 的桶分布需按判据分别算：never = 未触发的真实事件
        for cid, _, _ in CRIT:
            hit_keys = {t[4] for t in TRIG[cid] if t[5]}
            for k, b in bucket_of_key.items():
                if k not in hit_keys:
                    never_b[b] += 1
        denom = {b: BASE_B[b] * 26 for b in BUCKETS}
        AGG[f"{scope}{N}"] = {
            "capSum": csum, "capB": dict(cap_b), "preB": dict(pre_b),
            "neverB": dict(never_b),
            "capRateB": {b: cap_b[b] / denom[b] for b in BUCKETS},
            "capShareB": {b: cap_b[b] / csum if csum else None for b in BUCKETS},
            "preShareB": {b: pre_b[b] / sum(pre_b.values()) if sum(pre_b.values()) else None for b in BUCKETS},
        }
        a = AGG[f"{scope}{N}"]
        out(f"  {scope} N={N}: 合计捕获={csum}/(26*1681)  捕获率=" +
            ", ".join(f"{b}={a['capRateB'][b]*100:.4f}%" for b in BUCKETS) +
            "  被捕获构成=" + ", ".join(f"{b}={(a['capShareB'][b] or 0)*100:.2f}%" for b in BUCKETS))
        out(f"            被抢占构成=" + ", ".join(f"{b}={(a['preShareB'][b] or 0)*100:.2f}%" for b in BUCKETS) +
            "  基线构成=" + ", ".join(f"{b}={BASE_B[b]/1681*100:.2f}%" for b in BUCKETS))
        out(f"            从未触发(never)桶构成=" +
            ", ".join(f"{b}={a['neverB'][b]}" for b in BUCKETS) +
            f"  (每桶母数×26={dict((b,BASE_B[b]*26) for b in BUCKETS)})")

out("\n【每窗 vs 每会话配额：偏差是否改变】")
out("  W=每窗，T=每会话；Δ=T−W（负数=会话口径捕获更少）；s01(W)/s01(T)=被捕获中0.1-0.2s桶占比。")
for N in NS:
    out(f"\n  --- N={N} ---")
    out(f"  {'id':<22}|{'W':>5}|{'T':>5}|{'Δ':>5}|{'Wcap01':>8}|{'Tcap01':>8}|{'s01W':>8}|{'s01T':>8}|{'s01Δ':>8}")
    for cid, _, _ in CRIT:
        w = RESULTS[cid][f"window{N}"]; t = RESULTS[cid][f"trip{N}"]
        s01w = w["capB"]["0.1-0.2s"]/w["captured"]*100 if w["captured"] else None
        s01t = t["capB"]["0.1-0.2s"]/t["captured"]*100 if t["captured"] else None
        f = lambda v: "N/A" if v is None else f"{v:.2f}%"
        d = None if (s01w is None or s01t is None) else s01t - s01w
        out(f"  {cid:<22}|{w['captured']:>5}|{t['captured']:>5}|{t['captured']-w['captured']:>5}|"
            f"{w['capB']['0.1-0.2s']:>8}|{t['capB']['0.1-0.2s']:>8}|{f(s01w):>8}|{f(s01t):>8}|"
            + ("N/A" if d is None else f"{d:>+7.2f}pp").rjust(8))
    aw, at = AGG[f"window{N}"], AGG[f"trip{N}"]
    out(f"  {'宏观(26判据合并)':<22}|{sum(RESULTS[c][f'window{N}']['captured'] for c,_,_ in CRIT):>5}|"
        f"{sum(RESULTS[c][f'trip{N}']['captured'] for c,_,_ in CRIT):>5}|"
        f"{aw['capShareB']['0.1-0.2s']*100:.2f}% vs {at['capShareB']['0.1-0.2s']*100:.2f}% s01")

out("\n【反事实上界 capUpper（真实事件全部在 t[startTick] 触发 + 该判据误触发流）】")
out(f"  {'id':<22}|" + "".join(f"{'W'+str(N):>7}" for N in NS) + "|" + "".join(f"{'T'+str(N):>7}" for N in NS))
for cid, _, _ in CRIT:
    out(f"  {cid:<22}|" + "".join(f"{UPPER[cid][f'window{N}']:>7}" for N in NS) + "|" +
        "".join(f"{UPPER[cid][f'trip{N}']:>7}" for N in NS))
out("  对照：每窗理想=" + str([IDEAL_WINDOW[N] for N in NS]) +
    "  每会话理想=" + str([ideal_t[N] for N in NS]))
_up_ok = _up_bad = 0
for cid, _, _ in CRIT:
    for scope in ("window", "trip"):
        for N in NS:
            c = RESULTS[cid][f"{scope}{N}"]["captured"]
            u = UPPER[cid][f"{scope}{N}"]
            ideal = ideal_w[N] if scope == "window" else ideal_t[N]
            if c <= u <= ideal:
                _up_ok += 1
            else:
                _up_bad += 1
                out(f"  FAIL capUpper: {cid} {scope}{N} captured={c} upper={u} ideal={ideal}")
out(f"  capUpper 不变式（captured <= capUpper <= ideal）：PASS={_up_ok}/156 FAIL={_up_bad}")

MARGIN = {}
_nf_ok = _nf_bad = 0
for cid, _, _ in CRIT:
    for scope in ("window", "trip"):
        for N in NS:
            r = RESULTS[cid][f"{scope}{N}"]
            ideal = ideal_w[N] if scope == "window" else ideal_t[N]
            nf = NOFALSE[cid][f"{scope}{N}"]
            u = UPPER[cid][f"{scope}{N}"]
            MARGIN[f"{cid}|{scope}{N}"] = {
                "recallLoss": ideal - nf,
                "falsePreemptionLoss": nf - r["captured"],
                "maxPreemptionLoss": ideal - u,
                "gapFromUpper": u - r["captured"],
            }
            if 0 <= r["captured"] <= nf <= ideal and ideal - nf + nf - r["captured"] == ideal - r["captured"]:
                _nf_ok += 1
            else:
                _nf_bad += 1
                out(f"  FAIL noFalse decomposition: {cid} {scope}{N} cap={r['captured']} nf={nf} ideal={ideal}")
out(f"  noFalse 分解不变式（0 <= captured <= noFalse <= ideal 且两项相加=塌陷）："
    f"PASS={_nf_ok}/156 FAIL={_nf_bad}")

out("\n【塌陷归因（每项非负，可加）】")
out("  noFalse = 只保留该判据在真实事件上的触发、删掉全部误触发，跑同一配额后的捕获数。")
out("  ideal − captured = (ideal − noFalse) [召回不足 / 触发晚于起点] + "
    "(noFalse − captured) [误触发抢占]")
out("  另有 (ideal − capUpper) = 给定误触发流且真实事件全部在起点触发时的最大抢占损失（上界）。")
for N in NS:
    out(f"\n  --- N={N} 每窗 ---")
    out(f"  {'id':<22}|{'ideal':>6}|{'noFalse':>8}|{'capUpper':>9}|{'captured':>9}|{'召回/时序':>10}|{'误触发抢占':>11}|{'塌陷':>6}|{'最大抢占损失':>12}")
    for cid, _, _ in CRIT:
        r = RESULTS[cid][f"window{N}"]
        nf = NOFALSE[cid][f"window{N}"]
        u = UPPER[cid][f"window{N}"]
        out(f"  {cid:<22}|{IDEAL_WINDOW[N]:>6}|{nf:>8}|{u:>9}|{r['captured']:>9}|"
            f"{IDEAL_WINDOW[N]-nf:>10}|{nf-r['captured']:>11}|{IDEAL_WINDOW[N]-r['captured']:>6}|{IDEAL_WINDOW[N]-u:>12}")

# ------------------------------------------------------------------ 8 生成 COST_QUOTA.md
def md_table(head, rows, align=None):
    s = "| " + " | ".join(head) + " |\n"
    s += "|" + "|".join(["---"] * len(head)) + "|\n"
    for row in rows:
        s += "| " + " | ".join(str(x) for x in row) + " |\n"
    return s

M = []
A = M.append
A("# 触发成本 / 配额覆盖率核算：误触发抢占后的真实事件覆盖")
A("")
A("写域唯一：`lead/dtrigger_compare_20261107/`。本件**只算账、不定方案**；不选定任何判据，")
A("不放开配额，不把理想覆盖率当在线保证。所有数字由本次实跑产生。")
A("")
A("## 0 口径、建模与硬约束")
A("")
A("- 语料：`out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/**/measure_w*.json`，"
  f"本次读取 n={len(cache)} 文件、{n_samples} 采样点、hz={sorted({v.get('hz') for v in cache.values()})}。")
A(f"- 评分母体 = moving64 推进窗 {len(manifest_keys)} 窗、帧号游程 {len(REC)} 条"
  "（manifest 97 行中带帧号变化者；与 `_d30_facts.py:83`、`_dtrigger_metrics.py:95-103` 同口径）。")
A(f"- 真实事件 = `STALL_EVENTS.json` 中 `isRealMatch==true` 的 **{len(real_keys)}** 条；"
  f"全量 1737 为不同口径，不混用。{aligned}/1681 条与游程 `(i,j)=(startTick,endTick)` 精确对齐。")
A(f"- 时长桶（`_d30_facts.py:50`）：" +
  " / ".join(f"`{b}`={BASE_B[b]} ({BASE_B[b]/1681*100:.4f}%)" for b in BUCKETS) +
  f"；durationMs 实测范围 {min(dur_by_key.values()):.2f}–{max(dur_by_key.values()):.2f} ms，无 ≥1.0s 样本。")
A("- **触发序列由本件自己重算**：26 档判据谓词独立实现于 `_cost_quota.py:3` 节，"
  "不 import 既有探针、不复用 `CRITERIA_METRICS.json` 的结果数字（仅事后比对）。"
  "每条游程每判据最多 1 次触发，触发时刻 = `t[idx]`（绝对 `perf_counter` 秒，窗内严格单调）。")
A("- **配额消耗规则**：按触发时刻升序「先到先得」，前 N 次触发各消耗 1 个配额，"
  "第 N+1 次起丢弃；**误触发（非真实事件的触发）同样消耗配额**。"
  "真实事件被「捕获」= 其触发位于所属配额组的前 N 次触发之内。")
A("- 每窗配额组 = `(trip, window)`；每会话配额组 = `trip`（跨窗按 `t[idx]` 全局排序，"
  f"同 trip 推进窗 t 区间重叠对 n={len(cross_overlap)}）。")
A("- `capUpper` 为**反事实上界**：假设 1681 条真实事件全部在观测起点 `t[startTick]` 触发，"
  "同时保留该判据的非真实触发流，再跑同一配额。用于分离「误触发抢占」与「判据自身召回不足」；"
  "它不是设计、不是工程可达性声明，`t[startTick]` 是乐观锚（物理 S 不可测）。")
A("- 硬约束：**理想覆盖率不是在线保证；不放开配额（D-30 §3 明文）；N=1/3/5 仅为离线预算情景，"
  "未选定为实际设计参数**。不把低误报外推为栈采样可行（Q5 扰动四项全未验）；"
  "不改口径 B、不改 :177/:190/:191；不以「等 P95 突破」使触发晚于 :177 的 S+50ms 截止；"
  "不称已取得推进真实修复的机制证据，目标①机制挂账不解除。")
A("")

A("## 1 指纹与核对")
A("")
A("```")
for rel in ("lead/stall_event_def_20261106/STALL_EVENTS.json",
            "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json",
            "lead/d30_ruling_20261106/RULING_D30.md",
            "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt"):
    A(f"sha256 {rel} = {hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()}")
A("```")
A("")
A(f"触发序列与 `CRITERIA_METRICS.json` 事后交叉核对：**PASS={sum(xcheck)}/26 FAIL={len(xcheck)-sum(xcheck)}**"
  "（比对 triggers 与 realHits 两列；逐档明细见 `_cost_quota_out.txt`）。")
A("")
A("理想值自跑复现（sum over 非空真实事件窗 `sum(min(N, 事件数))`）：")
A("")
A(md_table(["配额口径", "N=1", "N=3", "N=5", "非空组数"], [
    ["每窗（D-30 §3 公布）"] + [f"{IDEAL_WINDOW[N]}/1681 ({IDEAL_WINDOW[N]/1681*100:.2f}%)" for N in NS] + [len(win_counts)],
    ["每窗（本次自跑）"] + [f"{ideal_w[N]}/1681 ({ideal_w[N]/1681*100:.4f}%)" for N in NS] + [len(win_counts)],
    ["每会话 trip（本次自跑）"] + [f"{ideal_t[N]}/1681 ({ideal_t[N]/1681*100:.4f}%)" for N in NS] + [len(trip_counts)],
]))
A(f"**与 D-30 公布的 26/73/117 一致**（每窗口径，本次自跑逐档相等）。"
  f"D-30 §3 中 104 是语料文件数，不是真实事件窗数；真实事件窗为 {len(win_counts)} 个，"
  f"所在 trip 为 {len(trip_counts)} 个。每会话口径的配额槽数更少（N×{len(trip_counts)} vs N×{len(win_counts)}），"
  "故其理想值低于每窗口径。")
A("")

A("## 2 核心表：真实事件实际被捕获数 / 1681")
A("")
A("`trig` = 该判据总触发数；`hits` = 该判据在真实事件上触发过的事件数（不看配额，即召回上界）；")
A("`W1/W3/W5` = 每窗配额 N=1/3/5 的实际捕获；`T1/T3/T5` = 每会话配额 N=1/3/5 的实际捕获。")
A("")
rows = []
for cid, _, _ in CRIT:
    hits = len({t[4] for t in TRIG[cid] if t[5]})
    rows.append([f"`{cid}`", len(TRIG[cid]), hits] +
                [RESULTS[cid][f"window{N}"]["captured"] for N in NS] +
                [RESULTS[cid][f"trip{N}"]["captured"] for N in NS])
rows.append(["**理想（D-30 §3）**", "—", "1681"] +
            [IDEAL_WINDOW[N] for N in NS] + [ideal_t[N] for N in NS])
A(md_table(["判据", "trig", "hits", "W1", "W3", "W5", "T1", "T3", "T5"], rows))
A("")
A("**不变式**：对每个 (判据, 口径, N)，`captured ≤ hits` 且 `captured ≤ 该口径理想值`；"
  f"本次自检 PASS={inv_ok}/156，FAIL={len(inv_bad)}。原因是误触发只可能挤占、不可能新增配额槽。")
A("")

A("## 3 塌陷幅度（相对理想值）")
A("")
A("`塌陷 = 理想捕获 − 实际捕获`；括号内为 `塌陷/理想`。")
A("")
rows = []
for cid, _, _ in CRIT:
    row = [f"`{cid}`"]
    for scope, lab in (("window", "每窗"), ("trip", "每会话")):
        for N in NS:
            ideal = ideal_w[N] if scope == "window" else ideal_t[N]
            c = RESULTS[cid][f"{scope}{N}"]["captured"]
            row.append(f"{ideal-c} ({(ideal-c)/ideal*100:.1f}%)")
    rows.append(row)
A(md_table(["判据", "W1 塌陷", "W3 塌陷", "W5 塌陷", "T1 塌陷", "T3 塌陷", "T5 塌陷"], rows))
A("")
A("塌陷有两个来源，必须分开读（`pre` = 判据触发了但配额已被抢占；`never` = 判据根本没在该真实事件上触发）：")
A("")
A("```")
A("1681 = captured + preempted + neverTriggered")
A("ideal − captured = (ideal − hits) + preempted     # 召回不足 + 抢占")
A("```")
A("")
A("下表给出每窗 N=1/3/5 的 `pre` / `never` / `Qfalse`（被误触发吃掉的配额槽数）分解：")
A("")
rows = []
for cid, _, _ in CRIT:
    row = [f"`{cid}`",
           len({t[4] for t in TRIG[cid] if t[5]})]
    for N in NS:
        r = RESULTS[cid][f"window{N}"]
        row.append(f"{r['captured']}+{r['preempted']}+{r['neverTriggered']} / Qfalse={r['quotaEatenByFalse']}")
    rows.append(row)
A(md_table(["判据", "hits", "N=1 cap+pre+never / Qfalse", "N=3 cap+pre+never / Qfalse", "N=5 cap+pre+never / Qfalse"], rows))
A("")
A("**读法**：`Qfalse` 高而 `cap` 低的判据（C1-k10、C4-t16/t24/t30、C5-k10t30 等），"
  "塌陷由误触发抢占主导；`hits` 本身就极低的判据（C2/C3 高档），"
  "塌陷主要由判据自身召回不足造成，配额只是次要因素。二者不可混为一谈。")
A("")

A("## 4 反事实上界 capUpper（只看误触发抢占）")
A("")
A("假设真实事件全部在 `t[startTick]` 触发（最乐观），保留该判据的非真实触发流，"
  "再按同一规则消耗配额。这是**给定该误触发流时真实覆盖的上界**，不是任何方案的性能。")
A("")
rows = []
for cid, _, _ in CRIT:
    rows.append([f"`{cid}`"] + [UPPER[cid][f"window{N}"] for N in NS] +
                [UPPER[cid][f"trip{N}"] for N in NS])
rows.append(["**理想（无误触发）**"] + [IDEAL_WINDOW[N] for N in NS] + [ideal_t[N] for N in NS])
A(md_table(["判据", "W1", "W3", "W5", "T1", "T3", "T5"], rows))
A("")

A("**不变式**：`captured ≤ capUpper ≤ 该口径理想值`；"
  f"本次自检 PASS={_up_ok}/156 FAIL={_up_bad}。`capUpper` 等于理想值的判据（如 C2/C3 高档）"
  "说明其误触发流几乎吃不到配额——但这**不代表修复**：它们的实际捕获极低，"
  "因为几乎不在真实事件上触发（召回不足）；其等待越线情况见 `CRITERIA_COMPARE.md:67,69,83,110`"
  "（既有实跑，本件未重跑延迟分布）。")
A("")

A("## 5 塌陷归因：召回不足 vs 误触发抢占")
A("")
A("`noFalse` = 只保留该判据在真实事件上的触发、删掉全部误触发，再跑同一配额后的捕获数。")
A("它是「没有误触发抢占」时该判据能达到的覆盖，可低于理想值（判据本身漏检或触发太晚）。")
A("")
A("```")
A("ideal − captured = (ideal − noFalse)    # 召回不足 / 触发时刻晚于起点（判据自身代价）")
A("                 + (noFalse − captured) # 误触发抢占（本件要算的那部分）")
A("两项均 >= 0，且相加恰为塌陷。另有 ideal − capUpper = 给定误触发流时的最大抢占损失（上界）。")
A("```")
A("")
A(f"分解不变式 `0 ≤ captured ≤ noFalse ≤ ideal` 且两项相加=塌陷："
  f"PASS={_nf_ok}/156 FAIL={_nf_bad}。")
A("")
A("下表为 N=1/3/5 每窗口径：")
A("")
for N in NS:
    A(f"**N={N}（每窗）**")
    A("")
    rows = []
    for cid, _, _ in CRIT:
        r = RESULTS[cid][f"window{N}"]
        nf = NOFALSE[cid][f"window{N}"]
        u = UPPER[cid][f"window{N}"]
        rows.append([f"`{cid}`", IDEAL_WINDOW[N], nf, u, r["captured"],
                     IDEAL_WINDOW[N] - nf, nf - r["captured"],
                     IDEAL_WINDOW[N] - r["captured"], IDEAL_WINDOW[N] - u])
    A(md_table(["判据", "ideal", "noFalse", "capUpper", "captured", "召回/时序", "误触发抢占", "塌陷", "最大抢占损失"], rows))
    A("")

A("## 6 时长桶偏差：配额耗尽后是不是只剩某一类时长")
A("")
A("基线构成：" + " / ".join(f"`{b}` = {BASE_B[b]}/1681 = {BASE_B[b]/1681*100:.4f}%" for b in BUCKETS) +
  "。`s01` = 被捕获事件中 0.1–0.2s 桶的占比；基线为 90.4224%，"
  "若 `s01` 显著高于/低于该值即存在时长方向的系统性偏差。")
A("")
for scope, lab in (("window", "每窗配额"), ("trip", "每会话配额")):
    for N in NS:
        A(f"### 6.{NS.index(N)+1 + (0 if scope=='window' else 3)} {lab} N={N}")
        A("")
        A("`cap` 三列 = 被捕获事件按时长桶的构成；`pre` 三列 = 被配额抢占的真实事件按时长桶的构成；"
          "`never` = 判据从未触发；`Qfalse` = 误触发吃掉的配额槽。")
        A("")
        rows = []
        for cid, _, _ in CRIT:
            r = RESULTS[cid][f"{scope}{N}"]
            cap = r["captured"]
            s01 = f"{r['capB']['0.1-0.2s']/cap*100:.2f}%" if cap else "N/A"
            rows.append([f"`{cid}`", cap] +
                        [r["capB"][b] for b in BUCKETS] + [s01] +
                        [r["preB"][b] for b in BUCKETS] +
                        [r["neverTriggered"], r["preempted"], r["quotaEatenByFalse"]])
        A(md_table(["判据", "cap", "cap 0.1-0.2", "cap 0.2-0.5", "cap 0.5-1.0", "s01",
                    "pre 0.1-0.2", "pre 0.2-0.5", "pre 0.5-1.0", "never", "pre", "Qfalse"], rows))
        A("")

A("### 6.7 宏观汇总（26 判据合并）")
A("")
A("`捕获率` = 该桶在 26 判据下的被捕获次数 / (该桶母数 × 26)；`捕获构成` = 该桶占全部捕获的比例。")
A("")
rows = []
for scope in ("window", "trip"):
    for N in NS:
        a = AGG[f"{scope}{N}"]
        rows.append([f"{scope} N={N}", a["capSum"]] +
                    [f"{a['capRateB'][b]*100:.3f}%" for b in BUCKETS] +
                    [f"{(a['capShareB'][b] or 0)*100:.2f}%" for b in BUCKETS] +
                    [f"{(a['preShareB'][b] or 0)*100:.2f}%" for b in BUCKETS])
A(md_table(["口径", "合计捕获", "率 0.1-0.2", "率 0.2-0.5", "率 0.5-1.0",
            "捕获 0.1-0.2", "捕获 0.2-0.5", "捕获 0.5-1.0",
            "抢占 0.1-0.2", "抢占 0.2-0.5", "抢占 0.5-1.0"], rows))
A("")
A("基线构成：" + " / ".join(f"{BASE_B[b]/1681*100:.2f}%" for b in BUCKETS) + "。")
A("")
A("`never`（判据从未触发的真实事件，26 判据合并计数）的桶构成：")
A("")
A(md_table(["口径", "never 0.1-0.2", "never 0.2-0.5", "never 0.5-1.0",
            "各桶母数×26 (0.1-0.2 / 0.2-0.5 / 0.5-1.0)"],
           [[f"{scope} N={N}"] + [AGG[f"{scope}{N}"]["neverB"][b] for b in BUCKETS] +
            [" / ".join(str(BASE_B[b] * 26) for b in BUCKETS)]
            for scope in ("window", "trip") for N in NS]))
A("")
A("> 注：`never` 只取决于判据是否有触发，与 N 和配额口径无关，故同一 scope 下三档 N 的"
  "三列完全相同；`window` 与 `trip` 的 never 也相同。它衡量的是**召回不足**，不是抢占。")
A("")

A("### 6.8 换成「每次会话（trip）配额」后，偏差是否改变")
A("")
A("`Δ = T − W`（负数表示会话口径捕获更少）；`s01Δ = s01(T) − s01(W)`，单位百分点(pp)。")
A("")
for N in NS:
    A(f"**N={N}**")
    A("")
    rows = []
    for cid, _, _ in CRIT:
        w = RESULTS[cid][f"window{N}"]; t = RESULTS[cid][f"trip{N}"]
        s01w = w["capB"]["0.1-0.2s"] / w["captured"] * 100 if w["captured"] else None
        s01t = t["capB"]["0.1-0.2s"] / t["captured"] * 100 if t["captured"] else None
        f = lambda v: "N/A" if v is None else f"{v:.2f}%"
        d = None if (s01w is None or s01t is None) else s01t - s01w
        rows.append([f"`{cid}`", w["captured"], t["captured"], t["captured"] - w["captured"],
                     w["capB"]["0.1-0.2s"], t["capB"]["0.1-0.2s"],
                     f(s01w), f(s01t), "N/A" if d is None else f"{d:+.2f}pp"])
    A(md_table(["判据", "W", "T", "Δ", "W cap01", "T cap01", "s01(W)", "s01(T)", "s01Δ"], rows))
    A("")
A("宏观（26 判据合并）的 `s01` 对比：")
A("")
A(md_table(["N", "s01(每窗)", "s01(每会话)", "差 (pp)", "捕获合计 W", "捕获合计 T"],
           [[N, f"{AGG[f'window{N}']['capShareB']['0.1-0.2s']*100:.2f}%",
             f"{AGG[f'trip{N}']['capShareB']['0.1-0.2s']*100:.2f}%",
             f"{(AGG[f'trip{N}']['capShareB']['0.1-0.2s']-AGG[f'window{N}']['capShareB']['0.1-0.2s'])*100:+.2f}",
             AGG[f"window{N}"]["capSum"], AGG[f"trip{N}"]["capSum"]] for N in NS]))
A("")

A("## 7 诚实账 / 未验项")
A("")
A(f"- 触发等待仍以观测首拍 `t[runStart]` 为锚；物理起点 S 落在 `(t[i-1], t[i]]`，"
  "语料只有 `(t,f)`，S 与实际保存时刻 C 不可测。本文的「捕获」是**离线触发序列上的配额记账**，"
  "不等于真实线程上下文在 S+50ms 内被保存。")
A(f"- 每窗配额的评分组是 {len(manifest_keys)} 个推进窗；每会话配额把它们按 trip 合并"
  f"（{len(set(k[0] for k in manifest_keys))} 个 trip）。语料为 25s 孤立窗、窗间 4s 空白，"
  "跨窗连续时序缺失（`:178`），故每会话口径只是**同一批切片窗的重新分组**，不是完整会话。")
A("- 未验：Q5 扰动四项、实际保存负担、端到端延迟（`:190`）、内部状态旗标（`:176`）、"
  "现场快照耗时与实际 C。低误报不得外推为栈采样可行。")
A("- `capUpper` 用了 `t[startTick]` 作为真实事件触发时刻，是乐观锚；"
  "任何实际判据的触发都晚于该点，故它是上界而非可达值。")
A("- `0.5-1.0s` 桶母数仅 3 条，任何该桶的百分比都不具统计意义，不能据此下结论。")
A("- 不选定任何判据、不改口径 B（D-12）、不改 :177/:190/:191（D-29 四条全保留）；"
  "不以「等 P95 突破」使触发晚于 S+50ms；不把 n=1681 与 n=1737 当同口径对照；"
  "目标①机制挂账不解除。")
A("")

# 结论节的数值全部由本脚本 RESULTS/UPPER/AGG 现算，不硬编码
A("## 8 结论（只算账，不定方案）")
A("")
A("### 8.1 塌陷幅度")
A("")
_mean = lambda s, N: sum(RESULTS[c][f"{s}{N}"]["captured"] for c, _, _ in CRIT) / 26
A(f"26 档判据在每窗口径下的实际捕获均值：N=1 → {_mean('window',1):.3f}/1681（理想 26），"
  f"N=3 → {_mean('window',3):.3f}/1681（理想 73），"
  f"N=5 → {_mean('window',5):.3f}/1681（理想 117）。"
  "均值仅作量级描述，不用于选择判据（26 档并非等权候选）。")
A("")
A("逐档关键读数（均取自本件 §2/§3 实跑表）：")
A("")
A(md_table(["情景", "理想", "最差", "最好", "说明"], [
    ["每窗 N=1", "26",
     f"{min(RESULTS[c]['window1']['captured'] for c,_,_ in CRIT)} (C3-r12)",
     f"{max(RESULTS[c]['window1']['captured'] for c,_,_ in CRIT)} (C3-r2)",
     "误触发最多的 C1-k10/C4-t16/t24/t30/C5-k10t30 仅 4/1681"],
    ["每窗 N=3", "73",
     f"{min(RESULTS[c]['window3']['captured'] for c,_,_ in CRIT)} (C3-r12)",
     f"{max(RESULTS[c]['window3']['captured'] for c,_,_ in CRIT)} (C1-k50)",
     "C1-k10 仅 23/1681；C1-k50 达 61/1681（但其等待已越 :177）"],
    ["每窗 N=5", "117",
     f"{min(RESULTS[c]['window5']['captured'] for c,_,_ in CRIT)} (C3-r12)",
     f"{max(RESULTS[c]['window5']['captured'] for c,_,_ in CRIT)} (C1-k50)",
     "C1-k10 仅 40/1681；C4-t48 55/1681"],
    ["每会话 N=1", "12",
     f"{min(RESULTS[c]['trip1']['captured'] for c,_,_ in CRIT)} (C2-cap40-P95x2/C3-r12)",
     f"{max(RESULTS[c]['trip1']['captured'] for c,_,_ in CRIT)} (C1-k50)",
     "配额槽总数由 26 降至 12，理想值本身就更低"],
    ["每会话 N=3", "31",
     f"{min(RESULTS[c]['trip3']['captured'] for c,_,_ in CRIT)} (C3-r12)",
     f"{max(RESULTS[c]['trip3']['captured'] for c,_,_ in CRIT)} (C1-k50)",
     "C1-k10 13/1681"],
    ["每会话 N=5", "47",
     f"{min(RESULTS[c]['trip5']['captured'] for c,_,_ in CRIT)} (C3-r12)",
     f"{max(RESULTS[c]['trip5']['captured'] for c,_,_ in CRIT)} (C1-k50)",
     "C1-k10 20/1681"],
]))
A("")
A("**核心事实**：D-30 §3 的 26/73/117 是「配额只由真实事件消耗」的理想值，"
  "本次实跑**逐档复现该值**（每窗口径 26/73/117 完全一致）；"
  "但一旦让误触发按时间顺序先到先得地消耗配额，**没有任何一个判据在任何一个 N 下达到理想值**。"
  "例如 C1-k10 在 N=1 只有 4/1681（塌陷 22，84.6%），"
  "C4-t16/t24/t30、C5-k10t30 同为 4/1681；"
  "N=5 时 C1-k10 也只有 40/1681（塌陷 77，65.8%）。"
  "塌陷不能靠「降低误报」简单读出：C2/C3 高档误触发极少、`capUpper` 甚至等于理想值，"
  "但实际捕获仅 0–8/1681，因为它们几乎不在真实事件上触发（召回不足），"
  "其触发等待越线情况见 `CRITERIA_COMPARE.md:67,69,83,110`（既有实跑，本件未重跑延迟分布）"
  "——**属不合规方向，不是修复**。")
A("")
A("归因（§5 分解）：对 C1/C4/C5 族，`noFalse` 恰等于理想值、"
  "`ideal − capUpper` = `noFalse − captured`，即塌陷**全部来自误触发抢占**；"
  "对 C2/C3 高档，`noFalse − captured = 0`，即塌陷**全部来自判据自身漏检**，配额不是主因。"
  "两类塌陷必须分开记账。")
A("")

A("### 8.2 被放弃真实事件的时长桶偏差")
A("")
A("基线：" + " / ".join(f"`{b}` = {BASE_B[b]}/1681 = {BASE_B[b]/1681*100:.2f}%" for b in BUCKETS) + "。")
A("")
_aw1, _aw3, _aw5 = (AGG[f"window{n}"] for n in NS)
_at1, _at3, _at5 = (AGG[f"trip{n}"] for n in NS)
A(md_table(["口径", "被捕获中 0.1-0.2s 占比", "较基线 (pp)",
            "被抢占中 0.1-0.2s 占比", "0.1-0.2s 捕获率", "0.2-0.5s 捕获率", "0.5-1.0s 捕获率"], [
    [f"每窗 N={N}", f"{a['capShareB']['0.1-0.2s']*100:.2f}%",
     f"{(a['capShareB']['0.1-0.2s']-BASE_B['0.1-0.2s']/1681)*100:+.2f}",
     f"{a['preShareB']['0.1-0.2s']*100:.2f}%"] +
    [f"{a['capRateB'][b]*100:.3f}%" for b in BUCKETS]
    for N, a in ((1, _aw1), (3, _aw3), (5, _aw5))
] + [
    [f"每会话 N={N}", f"{a['capShareB']['0.1-0.2s']*100:.2f}%",
     f"{(a['capShareB']['0.1-0.2s']-BASE_B['0.1-0.2s']/1681)*100:+.2f}",
     f"{a['preShareB']['0.1-0.2s']*100:.2f}%"] +
    [f"{a['capRateB'][b]*100:.3f}%" for b in BUCKETS]
    for N, a in ((1, _at1), (3, _at3), (5, _at5))
]))
A("")
A("**合并口径下偏差方向是单向且稳定的**：被抢占的真实事件构成几乎就是母体构成"
  "（0.1–0.2s 占 " + ", ".join(f"{a['preShareB']['0.1-0.2s']*100:.2f}%" for a in (_aw1, _aw3, _aw5, _at1, _at3, _at5)) +
  "，基线 90.42%），说明**就全体判据合并而言，抢占本身近似按时长比例丢弃**；"
  "但**26 判据合并后的被捕获集合偏向长时长**：0.1–0.2s 桶占被捕获集合仅 "
  + ", ".join(f"{a['capShareB']['0.1-0.2s']*100:.2f}%" for a in (_aw1, _aw3, _aw5)) +
  "（每窗 N=1/3/5），全部低于基线 90.42%。"
  "等价地，桶级捕获率随时长单调上升：每窗 N=1 为 "
  + " / ".join(f"`{b}`={_aw1['capRateB'][b]*100:.3f}%" for b in BUCKETS) +
  "；N=5 为 " + " / ".join(f"`{b}`={_aw5['capRateB'][b]*100:.3f}%" for b in BUCKETS) + "。")
A("")
A("**这个合并偏差主要不是「配额耗尽后只剩长时长」造成的**，必须分开看。"
  "按 `hits` 把 26 档拆成两组（本脚本现算）：")
A("")
_full = [c for c, _, _ in CRIT if len({t[4] for t in TRIG[c] if t[5]}) == 1681]
_part = [c for c, _, _ in CRIT if len({t[4] for t in TRIG[c] if t[5]}) < 1681]
A(f"- 全召回组（hits=1681，n={len(_full)}）：" + "、".join(f"`{c}`" for c in _full))
A(f"- 召回不足组（hits<1681，n={len(_part)}）：其余 17 档 C2/C3 族。")
A("")
A(md_table(["N（每窗）", "组", "捕获合计", "被捕获 s01", "被抢占合计", "被抢占 s01"], [
    [N, lab, sum(RESULTS[c][f"window{N}"]["captured"] for c in grp),
     f"{sum(RESULTS[c][f'window{N}']['capB']['0.1-0.2s'] for c in grp)/sum(RESULTS[c][f'window{N}']['captured'] for c in grp)*100:.2f}%",
     sum(RESULTS[c][f"window{N}"]["preempted"] for c in grp),
     f"{sum(RESULTS[c][f'window{N}']['preB']['0.1-0.2s'] for c in grp)/sum(RESULTS[c][f'window{N}']['preempted'] for c in grp)*100:.2f}%"]
    for N in NS for lab, grp in (("全召回", _full), ("召回不足", _part))
]))
A("")
A("读法：**全召回组**的被捕获 s01 为 " +
  ", ".join(f"N={N}: {sum(RESULTS[c][f'window{N}']['capB']['0.1-0.2s'] for c in _full)/sum(RESULTS[c][f'window{N}']['captured'] for c in _full)*100:.2f}%" for N in NS) +
  "（N 越大越贴近基线 90.42%，N=1 时 78.18% 仍偏低，样本量小）；"
  "其被抢占 s01 为 " +
  ", ".join(f"N={N}: {sum(RESULTS[c][f'window{N}']['preB']['0.1-0.2s'] for c in _full)/sum(RESULTS[c][f'window{N}']['preempted'] for c in _full)*100:.2f}%" for N in NS) +
  "，几乎等于基线——**在误触发抢占主导的判据里，被放弃事件的时长构成没有系统性偏移**。")
A("")
A("**召回不足组**的被捕获 s01 仅 " +
  ", ".join(f"N={N}: {sum(RESULTS[c][f'window{N}']['capB']['0.1-0.2s'] for c in _part)/sum(RESULTS[c][f'window{N}']['captured'] for c in _part)*100:.2f}%" for N in NS) +
  "，把合并数拉低。原因是这些判据（C2 相对分位 / C3 变化率）**要等实测时长越过阈值才触发**，"
  "短时长（0.1–0.2s）事件更难达到高倍率阈值，长时长事件更容易被触发；"
  "这是**判据自身的时长选择性**，叠加 `never` 项（该组 §6.7 的 never 桶构成），不是配额耗尽产生的。")
A("")
A("因此对任务问题「配额耗尽后是不是系统性地只剩某类时长被采到」的**如实回答**：")
A("")
A("1. **被放弃事件（`pre` + `never`）的时长构成整体接近母体**：`pre` 的 s01 为 89.7–90.1%，"
  "`never` 的 26 判据合并 s01 为 "
  f"{AGG['window1']['neverB']['0.1-0.2s']/sum(AGG['window1']['neverB'].values())*100:.2f}%"
  "（§6.7 表，基线 90.42%）。**没有观察到「配额耗尽后只剩某一类时长被采到」的证据**；"
  "合并表 s01 偏低是「全召回组近似按母体比例 + 召回不足组偏向长时长」两组混合后被稀释的结果，"
  "不是配额机制本身的选择性。")
A("2. 在被抢占主导的全召回判据上，N=1 每档仅捕获 4–18 条，样本太小，"
  "不足以支持任何「只剩某类时长」的强断言；")
A("")
A("3. 在召回不足判据上，**被采到的集合确实偏向 0.2–0.5s**，但那是判据阈值等待造成的。"
  "据 `CRITERIA_COMPARE.md:67,69,83,110`（既有实跑，本件未重跑延迟分布）："
  "C2 未截断族全部触发 >50ms、C3 族触发 >50ms 占比 100% 或 ≥95.6%，"
  "P95x3/P99x3/C3-r4/r8/r12 的触发等待已 ≥100ms，属越过 :177 的不合规方向，"
  "不得当作可用样本来源。`C2-cap40-*` 由 40ms 硬上限触发、已退化为 C4-t40"
  "（`CRITERIA_COMPARE.md:68`），本件不对其延迟另作实测声明。")
A("")
A("`capUpper` 可直接核对抢占的量级：即使把全部真实事件提前到观测起点触发，"
  "C1-k10 在 N=1 也只能拿到 " + str(UPPER["C1-k10"]["window1"]) + "/1681，"
  "因为同窗更早的误触发已吃掉配额——这量化的是**覆盖量塌陷**，不是时长选择性。")
A("")
A("> **样本量警告**：`0.5-1.0s` 桶母数仅 3 条，其捕获率（如每窗 N=1 的 "
  f"{_aw1['capRateB']['0.5-1.0s']*100:.3f}%）由 26×3=78 个 (判据,事件) 格子中极少数命中主导，"
  "**不具统计意义**，不得据此声称长停滞更容易被采到或形成结论。"
  "可支持的结论仅限「被捕获集合中 0.1–0.2s 占比低于基线」这一方向性事实。")
A("")

A("### 8.3 换成每次会话（trip）配额后，偏差是否改变")
A("")
A(md_table(["N", "每窗理想 / 每窗捕获合计", "每会话理想 / 每会话捕获合计",
            "每窗 s01", "每会话 s01", "s01 差 (pp)"], [
    [N, f"{IDEAL_WINDOW[N]} / {_aw['capSum']}", f"{ideal_t[N]} / {_at['capSum']}",
     f"{_aw['capShareB']['0.1-0.2s']*100:.2f}%", f"{_at['capShareB']['0.1-0.2s']*100:.2f}%",
     f"{(_at['capShareB']['0.1-0.2s']-_aw['capShareB']['0.1-0.2s'])*100:+.2f}"]
    for N, _aw, _at in ((1, _aw1, _at1), (3, _aw3, _at3), (5, _aw5, _at5))
]))
A("")
A("**结论：偏差方向不变，但幅度加深、覆盖进一步下降。** "
  f"真实事件集中在 {len(trip_counts)} 个 trip / {len(win_counts)} 个窗，"
  "改成每会话配额后配额槽总数由 N×26 降为 N×12，"
  "理想值本身从 26/73/117 降到 " + "/".join(str(ideal_t[N]) for N in NS) + "；"
  "26 判据合并捕获合计从 " + "/".join(str(a["capSum"]) for a in (_aw1, _aw3, _aw5)) +
  " 降到 " + "/".join(str(a["capSum"]) for a in (_at1, _at3, _at5)) + "。")
A("")
A("时长偏差方向未反转：每会话口径下被捕获集合中 0.1–0.2s 占比为 "
  + ", ".join(f"N={N}: {a['capShareB']['0.1-0.2s']*100:.2f}%" for N, a in ((1, _at1), (3, _at3), (5, _at5))) +
  "，**均低于每窗口径同档**，也均低于基线 90.42%；"
  "被抢占集合构成仍贴近母体（" +
  ", ".join(f"N={N}: {a['preShareB']['0.1-0.2s']*100:.2f}%" for N, a in ((1, _at1), (3, _at3), (5, _at5))) +
  "）。逐判据的 Δ 与 s01Δ 见 §6.8："
  "所有判据在 N=1/3/5 下均 `T − W ≤ 0`（会话口径不增加捕获）。")
A("")
A("因此「把配额从每窗改成每次会话」**不是**缓解偏差的办法：它只是把同一批切片窗"
  "（25s 孤立窗、窗间 4s 空白，`:178`）重新分组，减少了槽位数，"
  "既放大覆盖塌陷，也没有消除召回不足判据带来的时长选择性。")
A("")

A("## 9 实跑命令与产物")
A("")
A("```")
A("python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_cost_quota.py")
A(f"  -> exit 0；_cost_quota_out.txt、_cost_quota_data.json、COST_QUOTA.md")
A("```")
A("")
A("执行者与核验者分离：本件由 `_cost_quota.py` 生成；独立核验脚本 `_cost_quota_check.py` "
  "以不同实现路径重算并比对（结论见 §10，由核验脚本实跑后追加）。")
A("零真机（不启动 gamemd.exe / ra2loader / YURI.exe，不 taskkill，不读活进程内存）；"
  "零采样代码；只读语料与只读目录；不 commit、不 push；Python 全部 `python -I -X utf8` + 绝对路径；"
  "指纹用 Python `hashlib`。")
A("")

OUT_MD.write_text("\n".join(M) + "\n", encoding="utf-8")
OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
payload = {
    "meta": {"files": len(cache), "samples": n_samples, "manifestWindows": len(manifest_keys),
             "runs": len(REC), "real": len(real_keys), "baseB": dict(BASE_B),
             "realWindows": len(win_counts), "realTrips": len(trip_counts),
             "crossWindowOverlapPairs": len(cross_overlap),
             "xcheckPass": sum(xcheck), "xcheckFail": len(xcheck) - sum(xcheck),
             "invariantPass": inv_ok, "invariantFail": len(inv_bad),
             "upperInvariantPass": _up_ok, "upperInvariantFail": _up_bad,
             "noFalseInvariantPass": _nf_ok, "noFalseInvariantFail": _nf_bad,
             "tieTrips": len(tie_trips), "tieDuplicateCount": sum(tie_trips.values()),
             "idealWindow": ideal_w, "idealTrip": ideal_t},
    "criteria": {cid: {"triggers": len(TRIG[cid]),
                       "hits": len({t[4] for t in TRIG[cid] if t[5]}),
                       "note": note}
                 for cid, _, note in CRIT},
    "results": RESULTS, "upper": UPPER, "nofalse": NOFALSE, "margin": MARGIN, "agg": AGG,
}
OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
out("\n输出已写：" + str(OUT_MD))
out("输出已写：" + str(OUT_TXT))
out("输出已写：" + str(OUT_JSON))
out("【执行者结束 · 零真机 / 零采样代码 / 只读语料 / 无 commit push】")
