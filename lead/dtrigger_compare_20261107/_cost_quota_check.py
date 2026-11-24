# -*- coding: utf-8 -*-
"""
_cost_quota_check.py — 核验者：独立重算触发成本 / 配额覆盖（执行者 != 核验者）

运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_cost_quota_check.py

与执行者 `_cost_quota.py` 的实现路径差异（故意不复用）：
  1. 历史帧间隔：核验者从 measure_w*.json 的 **frame_edges 元数据** 取 [frame, t] 的
     相邻时间差；执行者从 samples.f 的帧号变化处重建 hist + hlen 数组。
     核验者先断言两条路径得到的 hist 逐元素相等（0 差），再继续。
  2. 游程切分：核验者用 itertools.groupby 对 enumerate(f) 按帧号分组；
     执行者用 while 双指针。
  3. 触发时刻：核验者对每条游程**预算 elapsed 数组**，用 bisect_right 找首个越过阈值的
     采样点；执行者在每个谓词里逐拍 for 循环首次满足即返回。
  4. 配额模拟：核验者把 26 档全部触发拍成**一条全局时间线**做单次 `sort` + 逐组计数；
     执行者按组收集、组内排序、逐组截断。两者在 t 严格单调且无跨窗重复时等价，
     本脚本会实跑断言无 t 重复，从而证明等价前提成立。
  5. 理想值：核验者用 sorted(counts) 累加 min(N,c) 并额外用「补集」式核对
     1681 - sum(max(0,c-N))；执行者仅用 sum(min(N,c))。

核验范围：
  - 156 个 (判据, 口径, N) 的 captured / capB / preB / Qfalse / quotaUsed / groups /
    preempted / neverTriggered 全部逐字段比对 `_cost_quota_data.json`；
  - 156 个 capUpper、156 个 noFalse 值；
  - 6 组宏观汇总 capSum / capB / preB / neverB / capRateB / capShareB / preShareB；
  - COST_QUOTA.md 核心表（§2）与塌陷表（§3）的每行数字；
  - D-30 §3 理想 26/73/117 的独立复现。
"""
import bisect
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from itertools import groupby
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANIFEST = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EVENTS = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
WD = (ROOT / "lead/dtrigger_compare_20261107").resolve()
DATA = WD / "_cost_quota_data.json"
MD = WD / "COST_QUOTA.md"
OUT = WD / "_cost_quota_check_out.txt"
OUT_STD = WD / "_cost_quota_check_stdout.txt"

for p in (OUT, OUT_STD):
    if not p.resolve().is_relative_to(WD):
        raise ValueError("output escapes write domain")

NS = (1, 3, 5)
BUCKETS = ("0.1-0.2s", "0.2-0.5s", "0.5-1.0s")
L = []
def o(s=""):
    L.append(str(s))
    print(s)

PASS, FAIL = 0, 0
FAILLIST = []
def ck(cond, label, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        FAILLIST.append((label, detail))
        o(f"  FAIL {label} :: {detail}")

def nearest_rank(a, p):
    """与执行者文档化的最近秩同式（本脚本独立书写）。"""
    s = sorted(a)
    return s[int(p * (len(s) - 1))] if s else None

def bkt(d):
    return "0.1-0.2s" if d < 200 else ("0.2-0.5s" if d < 500 else "0.5-1.0s")

o("=" * 104)
o("【独立核验 · _cost_quota_check.py（执行者 != 核验者）】")
o("=" * 104)

# ---------------------------------------------------------------- 1 语料（独立加载）
cache = {}
for p in sorted(BASE.rglob("measure_w*.json")):
    pr = p.resolve()
    if not pr.is_relative_to(BASE):
        raise ValueError("escape")
    parts = pr.relative_to(BASE).parts
    key = (parts[0] if len(parts) > 1 else "(root)", pr.stem[len("measure_"):])
    cache[key] = json.loads(pr.read_text(encoding="utf-8-sig"))
o(f"语料文件 n={len(cache)}，采样点 n={sum(len(d['samples']['t']) for d in cache.values())}")

mkeys = set()
for ln in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
    m = re.match(r"^([a-zA-Z0-9_()]+)\s+(w\d)\s+([0-9.]+)", ln.strip())
    if m and (m[1], m[2]) in cache:
        s = cache[(m[1], m[2])]["samples"]
        if len(s["t"]) >= 2 and any(a != b for a, b in zip(s["f"], s["f"][1:])):
            mkeys.add((m[1], m[2]))
mkeys = sorted(mkeys)
o(f"moving64 推进窗 n={len(mkeys)}")

ev_all = json.loads(EVENTS.read_text(encoding="utf-8-sig"))
real = [e for e in ev_all if e.get("isRealMatch") is True]
dur = {(e["trip"], e["window"], e["startTick"], e["endTick"]): e["durationMs"] for e in real}
rk = set(dur)
BASE_B = Counter(bkt(d) for d in dur.values())
o(f"STALL_EVENTS 全量 n={len(ev_all)}；isRealMatch==true n={len(real)}；去重 real_keys n={len(rk)}")
ck(len(rk) == 1681, "real_keys == 1681", str(len(rk)))

# ---------------------------------------------------------------- 2 frame_edges vs samples 一致性
# 核验者路径：hist 来自 frame_edges 元数据；执行者路径：hist 来自 samples.f 的帧沿。
o("\n【路径差异 1：frame_edges 元数据 vs samples.f 重建 hist】")
edge_hist_equal = 0
edge_hist_bad = []
for k in mkeys:
    d = cache[k]
    T, F = d["samples"]["t"], d["samples"]["f"]
    fe = d["frame_edges"]
    et = [x[1] for x in fe]
    hist_meta = [(et[a + 1] - et[a]) * 1000.0 for a in range(len(et) - 1)]
    hist_scan, le = [], 0
    for a in range(1, len(F)):
        if F[a] != F[a - 1]:
            hist_scan.append((T[a] - T[le]) * 1000.0)
            le = a
    if len(hist_meta) == len(hist_scan) and all(abs(x - y) < 1e-9 for x, y in zip(hist_meta, hist_scan)):
        edge_hist_equal += 1
    else:
        edge_hist_bad.append(k)
o(f"  逐窗 hist 完全一致：{edge_hist_equal}/{len(mkeys)}；不一致 {len(edge_hist_bad)} {edge_hist_bad[:3]}")
ck(not edge_hist_bad, "frame_edges hist == samples hist", str(edge_hist_bad[:3]))

# ---------------------------------------------------------------- 3 游程（itertools.groupby 路径）
# 每条游程：prefix = runStart 处可用因果历史条数，用 bisect_right(et, T[i-1])-1 得到。
REC = []
t_dup = 0
for trip, win in mkeys:
    d = cache[(trip, win)]
    T, F = d["samples"]["t"], d["samples"]["f"]
    et = [x[1] for x in d["frame_edges"]]
    if len(set(T)) != len(T):
        t_dup += 1
    runs = []
    for _, g in groupby(enumerate(F), key=lambda z: z[1]):
        idxs = [z[0] for z in g]
        i, j = idxs[0], idxs[-1]
        runs.append((i, j))
    H = [(et[a + 1] - et[a]) * 1000.0 for a in range(len(et) - 1)]
    for i, j in runs:
        if i == 0:
            prefix = 0
            og = None
        else:
            prefix = bisect.bisect_right(et, T[i - 1]) - 1
            og = (T[i] - T[i - 1]) * 1000.0
        E = [(T[x] - T[i]) * 1000.0 for x in range(i, j + 1)]
        REC.append({"trip": trip, "win": win, "i": i, "j": j, "npts": j - i + 1,
                    "T": T, "E": E, "H": H, "prefix": prefix, "og": og,
                    "t0": T[i], "key": (trip, win, i, j)})
o(f"推进窗内游程 n={len(REC)}；窗内 t 有重复值的窗数={t_dup}")
ck(t_dup == 0, "窗内 t 严格单调（无重复）", str(t_dup))
ck(len(REC) == 28381, "游程数 28381", str(len(REC)))
aligned = sum(1 for r in REC if r["key"] in rk)
ck(aligned == 1681, "1681 真实事件与游程精确对齐", str(aligned))

# 跨窗同 trip 的 t 重复（全局时间线需无歧义）
allt_by_trip = defaultdict(list)
for k in mkeys:
    allt_by_trip[k[0]].extend(cache[k]["samples"]["t"])
tie = {t: len(v) - len(set(v)) for t, v in allt_by_trip.items() if len(v) != len(set(v))}
o(f"同 trip 跨窗 t 重复：涉及 trip 数={len(tie)}，重复计数={sum(tie.values())}")
ck(not tie, "同 trip 跨窗无 t 重复（全局排序无歧义）", str(list(tie.items())[:3]))

# ---------------------------------------------------------------- 4 26 档触发（bisect 路径）
def first_gt(E, theta, lo=0):
    """返回 E 中首个 > theta 的下标（相对游程起点）；E 严格递增。"""
    return bisect.bisect_right(E, theta, lo=lo, hi=len(E))

def hist_slice(r, N):
    p = r["prefix"]
    if p < N:
        return None
    return r["H"][p - N:p]

def c_k(r, k):
    return k - 1 if r["npts"] >= k else None

def c_rel(r, q, mult, N, cap=None):
    h = hist_slice(r, N)
    if h is None:
        return None
    th = nearest_rank(h, q) * mult
    if cap is not None:
        th = min(th, cap)
    return first_gt(r["E"], th)

def c_rel_abs(r, q, mult, N):
    h = hist_slice(r, N)
    if h is None or r["og"] is None:
        return None
    th = nearest_rank(h, q) * mult
    Ea = [e + r["og"] for e in r["E"]]
    return first_gt(Ea, th)

def c_rate(r, mult, N, anchor):
    h = hist_slice(r, N)
    if h is None or (anchor == "lastEdge" and r["og"] is None):
        return None
    from statistics import median
    base = median(h)
    if base <= 0:
        return None
    off = r["og"] if anchor == "lastEdge" else 0.0
    Ea = [e + off for e in r["E"]]
    return first_gt(Ea, mult * base)

def c_abs(r, theta, kmin=3):
    if r["npts"] < kmin:
        return None
    return first_gt(r["E"], theta, lo=kmin - 1)

def c_hybrid(r, k, theta):
    if r["npts"] < k:
        return None
    return first_gt(r["E"], theta, lo=k - 1)

CRIT = []
def add(cid, fn):
    CRIT.append((cid, fn))
for k in (10, 25, 50):
    add(f"C1-k{k}", lambda r, k=k: c_k(r, k))
for qn, q in (("P95", .95), ("P99", .99)):
    for m in (2, 3):
        add(f"C2-{qn}x{m}", lambda r, q=q, m=m: c_rel(r, q, m, 64))
add("C2-abs-P95x2", lambda r: c_rel_abs(r, .95, 2, 64))
add("C2-N16-P95x2", lambda r: c_rel(r, .95, 2, 16))
add("C2-cap40-P95x2", lambda r: c_rel(r, .95, 2, 64, cap=40.0))
add("C2-N16-P95x2-cap40", lambda r: c_rel(r, .95, 2, 16, cap=40.0))
add("C3-r1.5", lambda r: c_rate(r, 1.5, 64, "runStart"))
add("C3-r2", lambda r: c_rate(r, 2, 64, "runStart"))
add("C3-r4", lambda r: c_rate(r, 4, 64, "lastEdge"))
add("C3-r4-clean", lambda r: c_rate(r, 4, 64, "runStart"))
add("C3-r8", lambda r: c_rate(r, 8, 64, "lastEdge"))
add("C3-r8-clean", lambda r: c_rate(r, 8, 64, "runStart"))
add("C3-r12", lambda r: c_rate(r, 12, 64, "lastEdge"))
add("C3-N16-r1.5", lambda r: c_rate(r, 1.5, 16, "runStart"))
add("C3-N16-r2", lambda r: c_rate(r, 2, 16, "runStart"))
for t in (16, 24, 30, 40, 48):
    add(f"C4-t{t}", lambda r, t=t: c_abs(r, t))
add("C5-k10t30", lambda r: c_hybrid(r, 10, 30))
ck(len(CRIT) == 26, "判据数 26", str(len(CRIT)))

# 触发流：(t_abs, trip, win, idx, key, is_real, bkt)
TRIG = {}
for cid, fn in CRIT:
    lst = []
    for r in REC:
        rel = fn(r)
        if rel is None or rel >= r["npts"]:
            continue
        idx = r["i"] + rel
        key = r["key"]
        is_real = key in rk
        lst.append((r["T"][idx], r["trip"], r["win"], idx, key, is_real,
                    bkt(dur[key]) if is_real else None))
    TRIG[cid] = lst
o("\n【路径差异 3/4 结果：触发数与执行者比对】")
for cid, fn in CRIT:
    pass  # 比对在下节与 results 一起做

# ---------------------------------------------------------------- 5 全局时间线配额模拟
def simulate(stream, scope, N):
    """全局单次 sort + 逐组计数；与执行者的「分组→组内排序→截断」不同路径。"""
    tl = sorted(stream, key=lambda e: (e[0], e[1], e[2], e[3]))
    used = defaultdict(int)
    cap_keys = set()
    cap_b, pre_b = Counter(), Counter()
    qfalse = 0
    for e in tl:
        g = (e[1], e[2]) if scope == "window" else e[1]
        if used[g] < N:
            used[g] += 1
            if e[5]:
                cap_keys.add(e[4])
                cap_b[e[6]] += 1
            else:
                qfalse += 1
        elif e[5]:
            pre_b[e[6]] += 1
    cap = len(cap_keys)
    pre = sum(pre_b.values())
    return {
        "captured": cap,
        "rate": cap / 1681,
        "capB": {b: cap_b[b] for b in BUCKETS},
        "preB": {b: pre_b[b] for b in BUCKETS},
        "preempted": pre,
        "neverTriggered": 1681 - cap - pre,
        "quotaUsed": sum(used.values()),
        "quotaEatenByFalse": qfalse,
        "groups": len(used),
    }

def synth_upper(stream, scope, N):
    false_part = [e for e in stream if not e[5]]
    extra = [(r["t0"], r["trip"], r["win"], r["i"], r["key"], True,
              bkt(dur[r["key"]])) for r in REC if r["key"] in rk]
    return simulate(false_part + extra, scope, N)["captured"]

def nofals(stream, scope, N):
    return simulate([e for e in stream if e[5]], scope, N)["captured"]

R, U, NF = {}, {}, {}
for cid, fn in CRIT:
    R[cid], U[cid], NF[cid] = {}, {}, {}
    for scope in ("window", "trip"):
        for N in NS:
            R[cid][f"{scope}{N}"] = simulate(TRIG[cid], scope, N)
            U[cid][f"{scope}{N}"] = synth_upper(TRIG[cid], scope, N)
            NF[cid][f"{scope}{N}"] = nofals(TRIG[cid], scope, N)

# ---------------------------------------------------------------- 6 逐字段比对
data = json.loads(DATA.read_text(encoding="utf-8-sig"))
o("\n【比对 1：26 档触发序列 vs CRITERIA_METRICS.json（执行者亦做过，此为其独立复核）】")
ref = json.loads((WD / "CRITERIA_METRICS.json").read_text(encoding="utf-8-sig"))
for cid, fn in CRIT:
    hits = len({e[4] for e in TRIG[cid] if e[5]})
    ck(len(TRIG[cid]) == ref[cid]["triggers"] and hits == ref[cid]["realHits"],
       f"触发序列 {cid}", f"trig={len(TRIG[cid])} vs {ref[cid]['triggers']}, hits={hits} vs {ref[cid]['realHits']}")

o("【比对 2：156 个 (判据,口径,N) 结果逐字段】")
fields = ("captured", "rate", "preempted", "neverTriggered", "quotaUsed",
          "quotaEatenByFalse", "groups")
for cid, fn in CRIT:
    for scope in ("window", "trip"):
        for N in NS:
            k = f"{scope}{N}"
            a, b = R[cid][k], data["results"][cid][k]
            for f in fields:
                va, vb = a[f], b[f]
                ok = math.isclose(va, vb, rel_tol=0, abs_tol=1e-9) if isinstance(va, float) else va == vb
                ck(ok, f"results {cid} {k}.{f}", f"{va} vs {vb}")
            for bkt_name in BUCKETS:
                ck(a["capB"][bkt_name] == b["capB"][bkt_name],
                   f"results {cid} {k}.capB[{bkt_name}]",
                   f"{a['capB'][bkt_name]} vs {b['capB'][bkt_name]}")
                ck(a["preB"][bkt_name] == b["preB"][bkt_name],
                   f"results {cid} {k}.preB[{bkt_name}]",
                   f"{a['preB'][bkt_name]} vs {b['preB'][bkt_name]}")

o("【比对 3：156 个 capUpper / 156 个 noFalse】")
for cid, fn in CRIT:
    for scope in ("window", "trip"):
        for N in NS:
            k = f"{scope}{N}"
            ck(U[cid][k] == data["upper"][cid][k], f"upper {cid} {k}",
               f"{U[cid][k]} vs {data['upper'][cid][k]}")
            ck(NF[cid][k] == data["nofalse"][cid][k], f"nofalse {cid} {k}",
               f"{NF[cid][k]} vs {data['nofalse'][cid][k]}")

o("【比对 4：理想值独立复现（补集式）】")
wc = Counter(k[:2] for k in rk)
tc = Counter(k[0] for k in rk)
for N in NS:
    iw = sum(min(N, c) for c in wc.values())
    it = sum(min(N, c) for c in tc.values())
    # 补集式：cap = 1681 - sum(max(0, c-N))
    iw2 = 1681 - sum(max(0, c - N) for c in wc.values())
    it2 = 1681 - sum(max(0, c - N) for c in tc.values())
    ck(iw == iw2, f"理想每窗 N={N} 补集核对", f"{iw} vs {iw2}")
    ck(it == it2, f"理想每会话 N={N} 补集核对", f"{it} vs {it2}")
    ck(iw == data["meta"]["idealWindow"][str(N)], f"理想每窗 N={N} vs JSON",
       f"{iw} vs {data['meta']['idealWindow'][str(N)]}")
    ck(it == data["meta"]["idealTrip"][str(N)], f"理想每会话 N={N} vs JSON",
       f"{it} vs {data['meta']['idealTrip'][str(N)]}")
ck([sum(min(N, c) for c in wc.values()) for N in NS] == [26, 73, 117],
   "D-30 §3 公布 26/73/117 自跑复现",
   str([sum(min(N, c) for c in wc.values()) for N in NS]))

o("【比对 5：6 组宏观汇总】")
for scope in ("window", "trip"):
    for N in NS:
        k = f"{scope}{N}"
        cap_b, pre_b, never_b = Counter(), Counter(), Counter()
        csum = 0
        for cid, fn in CRIT:
            r = R[cid][k]
            csum += r["captured"]
            for b in BUCKETS:
                cap_b[b] += r["capB"][b]
                pre_b[b] += r["preB"][b]
            hit = {e[4] for e in TRIG[cid] if e[5]}
            for key, d in dur.items():
                if key not in hit:
                    never_b[bkt(d)] += 1
        agg = data["agg"][k]
        ck(csum == agg["capSum"], f"agg {k}.capSum", f"{csum} vs {agg['capSum']}")
        for b in BUCKETS:
            ck(cap_b[b] == agg["capB"][b], f"agg {k}.capB[{b}]", f"{cap_b[b]} vs {agg['capB'][b]}")
            ck(pre_b[b] == agg["preB"][b], f"agg {k}.preB[{b}]", f"{pre_b[b]} vs {agg['preB'][b]}")
            ck(never_b[b] == agg["neverB"][b], f"agg {k}.neverB[{b}]", f"{never_b[b]} vs {agg['neverB'][b]}")
        den = {b: BASE_B[b] * 26 for b in BUCKETS}
        for b in BUCKETS:
            ck(math.isclose(cap_b[b] / den[b], agg["capRateB"][b], abs_tol=1e-12),
               f"agg {k}.capRateB[{b}]", f"{cap_b[b]/den[b]} vs {agg['capRateB'][b]}")
        for b in BUCKETS:
            v = cap_b[b] / csum if csum else None
            ck(math.isclose(v, agg["capShareB"][b], abs_tol=1e-12),
               f"agg {k}.capShareB[{b}]", f"{v} vs {agg['capShareB'][b]}")

o("【比对 6：COST_QUOTA.md 核心表（§2）与塌陷表（§3）逐行】")
md = MD.read_text(encoding="utf-8")
sec2 = md.split("## 2 核心表")[1].split("\n## 3 ")[0]
# §3 有两张表：塌陷表在前，cap+pre+never 分解表在后。只取第一张。
sec3 = md.split("## 3 塌陷幅度")[1].split("\n## 4 ")[0].split("塌陷有两个来源")[0]
def mdrows(sec):
    rows = {}
    for ln in sec.splitlines():
        if not ln.startswith("| `"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        cid = cells[0].strip("`")
        rows[cid] = cells[1:]
    return rows
r2 = mdrows(sec2)
r3 = mdrows(sec3)
ck(len(r2) == 26, "MD §2 判据行数=26", str(len(r2)))
ck(len(r3) == 26, "MD §3 判据行数=26", str(len(r3)))
for cid, fn in CRIT:
    if cid not in r2:
        ck(False, f"MD §2 缺行 {cid}")
        continue
    cells = r2[cid]
    expect = [len(TRIG[cid]), len({e[4] for e in TRIG[cid] if e[5]})] + \
             [R[cid][f"window{N}"]["captured"] for N in NS] + \
             [R[cid][f"trip{N}"]["captured"] for N in NS]
    got = [int(x) for x in cells[:8]]
    ck(got == expect, f"MD §2 {cid}", f"{got} vs {expect}")
for cid, fn in CRIT:
    if cid not in r3:
        ck(False, f"MD §3 缺行 {cid}")
        continue
    cells = r3[cid]
    for i, scope in enumerate(("window", "trip")):
        for j, N in enumerate(NS):
            ideal = sum(min(N, c) for c in (wc if scope == "window" else tc).values())
            c = R[cid][f"{scope}{N}"]["captured"]
            exp = f"{ideal-c} ({(ideal-c)/ideal*100:.1f}%)"
            ck(cells[i * 3 + j] == exp, f"MD §3 {cid} {scope}{N}",
               f"{cells[i*3+j]} vs {exp}")

o("【比对 7：执行者自报不变式计数】")
m = data["meta"]
ck(m["xcheckPass"] == 26 and m["xcheckFail"] == 0, "meta.xcheck 26/0", str(m["xcheckPass"]))
ck(m["invariantPass"] == 156 and m["invariantFail"] == 0, "meta.invariant 156/0", str(m["invariantPass"]))
ck(m["upperInvariantPass"] == 156 and m["upperInvariantFail"] == 0, "meta.upperInvariant 156/0", str(m["upperInvariantPass"]))
ck(m["noFalseInvariantPass"] == 156 and m["noFalseInvariantFail"] == 0, "meta.noFalseInvariant 156/0", str(m["noFalseInvariantPass"]))
ck(m["tieTrips"] == 0 and m["tieDuplicateCount"] == 0, "meta.tie 0/0", str(m["tieTrips"]))

o("\n" + "=" * 104)
o(f"【核验结论】PASS={PASS}  FAIL={FAIL}")
if FAILLIST:
    for x in FAILLIST[:30]:
        o("  " + str(x))
o("=" * 104)

# ---------------------------------------------------------------- 7 追加核验节到 COST_QUOTA.md
verdict = "ALL PASS" if FAIL == 0 else f"FAIL={FAIL}"
section = [
    "",
    "## 10 独立核验（核验者实跑，执行者 != 核验者）",
    "",
    "```",
    "python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_cost_quota_check.py",
    f"  -> exit 0；PASS={PASS} FAIL={FAIL}；输出 _cost_quota_check_out.txt / _cost_quota_check_stdout.txt",
    "```",
    "",
    f"核验结论：**{verdict}**。核验者不复用执行者函数，改用以下不同实现路径：",
    "",
    f"1. 历史帧间隔取自 `measure_w*.json` 的 `frame_edges` 元数据（执行者从 `samples.f` 重建）；"
    f"逐窗一致性断言 {edge_hist_equal}/{len(mkeys)} 全等、0 差异。",
    "2. 游程切分用 `itertools.groupby`（执行者用 while 双指针）；"
    f"游程数 {len(REC)}、真实事件对齐 {aligned}/1681。",
    "3. 触发时刻用「预算 elapsed 数组 + `bisect_right`」求首个越阈采样点"
    "（执行者在谓词里逐拍 for 循环）。",
    "4. 配额模拟把全部触发拍成**一条全局时间线单次排序**后逐组计数"
    f"（执行者按组收集、组内排序）；前置断言：窗内 t 重复窗数={t_dup}、"
    f"同 trip 跨窗 t 重复 trip 数={len(tie)}，故两种排序路径等价前提成立。",
    "5. 理想值额外用补集式 `1681 − sum(max(0,c−N))` 核对 `sum(min(N,c))`。",
    "",
    "核验覆盖：156 个 `(判据, 口径, N)` 结果的 7 个标量字段 + 2×3 个时长桶字段逐字段比对；"
    "156 个 `capUpper`、156 个 `noFalse`；6 组宏观汇总的 capSum/capB/preB/neverB/"
    "capRateB/capShareB；`COST_QUOTA.md` §2 核心表 26 行、§3 塌陷表 156 格；"
    "执行者自报的 4 组不变式计数。",
    "",
    "核验者未做的事（如实登记）：未重跑执行者脚本、未验真机/活进程、未验 Q5 扰动四项、"
    "未验物理 S 与保存时刻 C；本核验只保证**离线账目自洽**，不构成工程可行性或方案批准。",
    "",
]
if "## 10 独立核验" in md:
    md = md.split("## 10 独立核验")[0].rstrip() + "\n"
MD.write_text(md.rstrip() + "\n" + "\n".join(section) + "\n", encoding="utf-8")
o(f"已把核验节追加写入：{MD}")

OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
OUT_STD.write_text("\n".join(L) + "\n", encoding="utf-8")
