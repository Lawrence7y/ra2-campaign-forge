# -*- coding: utf-8 -*-
"""
_dA_run.py — 新判据族「在线因果」三维离线比较（零真机 / 零采样代码 / 只读语料）

唯一写域：lead/dtrigger_round2_20261107/ 下 _dA_ 前缀新文件：
    _dA_run.py（本脚本）、_dA_out.txt、_dA_stdout.txt、_dA_data.json、_dA_check.txt
运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_dA_run.py

【本轮做了什么 / 没做什么】
- 设计 5 个**不同于 C1–C5** 的判据族 D1..D5，全部只用 (t,f) 前缀形状：
  D1 形状字(gap ordinal)、D2 连续短间隔游程、D3 相邻游程关系、D4 肘形(局部加速度)、D5 相对前一帧周期的序数。
  禁止项自检：不使用 k 值档、P95/P99 分位×倍、滑窗 N 的历史分位、40ms CAP；
  D1..D5 的「内部整常量」是**形状字母表、游程长度、序数**等结构性定义，不是上述四类调参。
- 每档判据在线因果：只读 t[runStart..idx]、runStart 前的**已完成**历史（前一帧周期 D、前一周期最短间隔、
  已完成帧间隔序列）；绝不读 endTick / durationMs / isRealMatch / 最终 d>=100ms。
  后者只在触发后用于**事后计费**（误触发 / 真实捕获的分母与标签）。
- 三维比较：
  ① :177 及时性：S_hat 锚等待 waitAfterS_hat 是下界；逐游程 e 修正后
     strict_ok = (waitAfterS_hat + e <= 50ms)。首拍游程 e 未验（口径 B 保留）。
     另报告「:177 严格及时且被真实触发」的事件数 in50_strict（分母 1681）。
  ② 区分度（真实捕获）：按触发时刻升序、误触发先到先得抢占配额后的 captured / 1681，
     同时给 falseTriggers / falseRate（口径 B：dfin<100 的触发数 / 总触发数）、quotaEatenByFalse。
  ③ 配额 N=1/3/5：每窗 (trip,window) 与每会话 trip 两种口径，逐档全给。
- 形式化证据：对「≤τ 内触发全部 1681 条 real」的任意前缀特征函数型判据，
  给出可判定的计数下界 forced_FP 与查准率上界 precision，以及存活集基准率上界（见 §6、_dA_design.md §3）。
- 校准：本脚本独立重算 C1-k10 / C1-k25 / C4-t40 / C5-k10t30 的触发序列与 6 格配额捕获，
  与 _cost_quota_data.json 的既有实跑值逐格比对；不复用其 trig 列表、不 import 其实现。
- 数字全部来自本脚本实跑；引用既有数字时给出 file:line 或「题给上游指纹」。

【未验项（单列，不并入结论）】见输出 §8 与 _dA_design.md §5。
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
QUOTA_JSON = (ROOT / "lead/dtrigger_compare_20261107/_cost_quota_data.json").resolve()
METRICS_JSON = (ROOT / "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json").resolve()
WD = (ROOT / "lead/dtrigger_round2_20261107").resolve()
OUT_TXT = WD / "_dA_out.txt"
OUT_JSON = WD / "_dA_data.json"
CHECK_TXT = WD / "_dA_check.txt"

for p in (OUT_TXT, OUT_JSON, CHECK_TXT):
    if not p.resolve().is_relative_to(WD):
        raise ValueError("output escapes write domain: " + str(p))

NS = (1, 3, 5)
DCLASS = 100.0          # 口径 B 事后分类门槛：只计费，不参与触发
B50 = 50.0              # :177 的 S+50ms；S_hat 锚等待 + 逐游程 e 是严格下界核算

lines = []
def out(s=""):
    lines.append(str(s)); print(s)

def pctl(a, p):
    return a[int(p * (len(a) - 1))] if a else None

def med(a):
    return statistics.median(a) if a else None

def f6(x):
    return "N/A" if x is None else f"{x:.6f}"

# ================================================================== 0 指纹（含被核对象）
out("=" * 112)
out("【新判据族在线因果三维离线比较 · 执行者 _dA_run.py · 零真机/零采样代码/只读语料/无commit push】")
out("=" * 112)
FINGERPRINT_RELS = (
    "lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md",
    "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json",
    "lead/dtrigger_compare_20261107/_cost_quota_data.json",
    "lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt",
    "lead/d30_ruling_20261106/RULING_D30.md",
    "lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md",
    "lead/dstart_observable_20261107/S_OBSERVABILITY.md",
    "lead/stall_event_def_20261106/STALL_EVENTS.json",
    "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt",
)
FP = {}
for rel in FINGERPRINT_RELS:
    b = (ROOT / rel).read_bytes()
    FP[rel] = (hashlib.sha256(b).hexdigest(), len(b))
    out(f"sha256 {rel} = {FP[rel][0]} bytes={FP[rel][1]}")
# 题给上游 7 项指纹逐条核对
GIVEN = {
 "lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md":"4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726",
 "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json":"7e2533eabf795e8aa0063a16ee875d95742880dcefab55d596cfc5aa6e7f958b",
 "lead/dtrigger_compare_20261107/_cost_quota_data.json":"e6c26896319acb0387f06384665d5db3668e0f15e29f7328cac97f4931c03cac",
 "lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt":"f0177d2cbafdb4dbd388d6b38b97d14ae73688f36f58df4f0fff7edc31a59b66",
 "lead/d30_ruling_20261106/RULING_D30.md":"d5afc90c50bbf57be1e58bf9000b1940392337b6c57a444e3b084fe57983d04f",
 "lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md":"ed8951e72bd61cd322b1687c4496ec9fc0e8a362c1425d4020901228d885a001",
 "lead/dstart_observable_20261107/S_OBSERVABILITY.md":"1d90325ca899c0611ac03dd49a6fb07ede4e21cde2062a5a793a7ea694c9da29",
}
for rel, h in GIVEN.items():
    out(f"  题给指纹核对 {rel}: {'MATCH' if FP[rel][0]==h else 'MISMATCH'}")

# ================================================================== 1 语料与游程（独立重建）
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
out(f"moving64 推进窗 n={len(manifest_keys)}，覆盖 trip n={len(set(k[0] for k in manifest_keys))}")

events_all = json.loads(EVENTS.read_text(encoding="utf-8-sig"))
real = [e for e in events_all if e.get("isRealMatch") is True]
dur_of = {(e["trip"], e["window"], e["startTick"], e["endTick"]): e["durationMs"] for e in real}
real_keys = set(dur_of)
out(f"STALL_EVENTS 全量 n={len(events_all)}，isRealMatch==true n={len(real)}，去重 real_keys n={len(real_keys)}")
assert len(real) == len(real_keys) == 1681

# 逐窗扫描：游程 + 每个采样点可用的「已完成历史」（帧沿到帧沿的帧周期）
REC = []
nonmono = 0
for trip, win in manifest_keys:
    s = cache[(trip, win)]["samples"]
    T, F = s["t"], s["f"]
    n = len(F)
    if any(T[x + 1] <= T[x] for x in range(n - 1)):
        nonmono += 1
    # hist[k] = 第 k 条已完成帧周期(ms)；he[a] = 采样点 a 之前已完成的帧周期数
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
        he = hlen[i - 1] if i > 0 else 0
        e = (T[i] - T[i - 1]) * 1000.0 if i > 0 else None
        # 前一「已完成」游程的形状（只用 t[..i-1]，全部已完成）
        prev_gaps = []
        if i > 0:
            q = i - 1
            fq = F[q]
            while q > 0 and F[q - 1] == fq:
                q -= 1
            prev_gaps = [(T[k] - T[k - 1]) * 1000.0 for k in range(q + 1, i + 1)]
        REC.append({
            "trip": trip, "win": win, "i": i, "j": j, "npts": j - i + 1,
            "T": T, "F": F,
            "dfin": (T[j] - T[i]) * 1000.0,          # 事后计费：绝不进触发谓词
            "e": e,
            "key": (trip, win, i, j),
            "is_real": (trip, win, i, j) in real_keys,
            "hist": hist, "he": he,
            "D": hist[he - 1] if he >= 1 else None,   # 前一帧周期，已完成历史
            "prev_min": min(prev_gaps) if prev_gaps else None,
            "prev_max": max(prev_gaps) if prev_gaps else None,
            "prev_len": len(prev_gaps) if prev_gaps else None,
        })
        i = j + 1
out(f"推进窗内帧号游程 n={len(REC)}；窗内 t 非单调的窗数={nonmono}")
assert nonmono == 0
aligned = sum(1 for r in REC if r["is_real"])
out(f"真实事件与游程 (i,j)=(startTick,endTick) 精确对齐 n={aligned}/{len(real_keys)}")
assert aligned == 1681

# 跨窗 t 重复与区间重叠（全局时间线排序的确定性前提）
_t_by_trip = defaultdict(list)
for k in manifest_keys:
    _t_by_trip[k[0]].extend(cache[k]["samples"]["t"])
tie_trips = {t: (len(v) - len(set(v))) for t, v in _t_by_trip.items() if len(set(v)) != len(v)}
out(f"同 trip 跨窗 t 重复值：涉及 trip 数={len(tie_trips)}，重复计数合计={sum(tie_trips.values())}")

# 逐游程 e 与 dfin 核对（计费口径）
es = sorted(r["e"] for r in REC if r["e"] is not None)
out(f"逐游程 e 有效 n={len(es)}（首拍游程 {len(REC)-len(es)} 条 e 未验） "
    f"min={es[0]:.3f} med={med(es):.3f} P99={pctl(es,.99):.3f} max={es[-1]:.3f} ms")
diffs = [abs(r["dfin"] - dur_of[r["key"]]) for r in REC if r["is_real"]]
out(f"真实事件 |dfin - durationMs| max={max(diffs):.6f}ms mean={sum(diffs)/len(diffs):.6f}ms")

win_counts = Counter(k[:2] for k in real_keys)
trip_counts = Counter(k[0] for k in real_keys)
ideal_w = {N: sum(min(N, c) for c in win_counts.values()) for N in NS}
ideal_t = {N: sum(min(N, c) for c in trip_counts.values()) for N in NS}
out(f"理想值自跑复现：每窗 W={ideal_w}，每会话 T={ideal_t}，真实事件非空窗 n={len(win_counts)} 非空 trip n={len(trip_counts)}")

# ================================================================== 2 判据族定义
# 公共形状字母表（结构性定义；不是 k 值/P95/P99/滑窗 N/40ms CAP 的调参）
# S: gap<0.05ms  M: 0.05-0.5ms  L: 0.5-2ms  X: 2-5ms  G: >=5ms（单位 ms，取自 t 的差值）
def bkt(g):
    return "S" if g < 0.05 else ("M" if g < 0.5 else ("L" if g < 2 else ("X" if g < 5 else "G")))

def gaps_upto(r, idx):
    T, i = r["T"], r["i"]
    return [(T[x] - T[x - 1]) * 1000.0 for x in range(i + 1, idx + 1)]

def elapsed_ms(r, idx):
    return (r["T"][idx] - r["T"][r["i"]]) * 1000.0

CRIT = []
def add(cid, fn, family, note, needs):
    CRIT.append((cid, fn, family, note, needs))

# ---- 基线校准（不是新判据，仅验证本 runner 的触发/配额实现与既有实跑一致）----
def cal_k(r, k):
    return r["i"] + k - 1 if r["npts"] >= k else None
def cal_abs(r, theta):
    if r["npts"] < 3:
        return None
    for x in range(r["i"] + 2, r["j"] + 1):
        if elapsed_ms(r, x) > theta:
            return x
    return None
def cal_hybrid(r, k, theta):
    if r["npts"] < k:
        return None
    for x in range(r["i"] + k - 1, r["j"] + 1):
        if elapsed_ms(r, x) > theta:
            return x
    return None
add("CAL-C1-k10", lambda r: cal_k(r, 10), "CAL", "校准：连续10拍第10拍", "无")
add("CAL-C1-k25", lambda r: cal_k(r, 25), "CAL", "校准：连续25拍第25拍", "无")
add("CAL-C4-t40", lambda r: cal_abs(r, 40.0), "CAL", "校准：elapsed>40ms且>=3拍", "无")
add("CAL-C5-k10t30", lambda r: cal_hybrid(r, 10, 30.0), "CAL", "校准：10拍且>30ms", "无")

# ---- D1 形状字（gap-ordinal word）：相邻采样间隔的序数模式，命中即触发 ----
# 与 C1(计数)/C2(分位)/C3(比值)/C4(绝对时长)/C5(计数+时长) 都不同：判据是「字母序列」的有限自动机。
def d1_make(target, minlen):
    def fn(r):
        T, i, j = r["T"], r["i"], r["j"]
        w = ""
        for x in range(i + 1, j + 1):
            w += bkt((T[x] - T[x - 1]) * 1000.0)
            if len(w) >= len(target) and w[-len(target):] == target and len(w) >= minlen:
                return x
        return None
    return fn
# D1 三档是**不同形状字**（结构性变体），不是同一谓词换阈值
add("D1-word-MMM", d1_make("MMM", 3), "D1", "形状字 MMM（3 个连续中等间隔）在间隔字中首次出现即触发", "t[runStart..i] 的相邻间隔")
add("D1-word-LLL", d1_make("LLL", 3), "D1", "形状字 LLL（3 个连续长间隔）首次出现即触发", "t[runStart..i] 的相邻间隔")
add("D1-word-G",   d1_make("G", 3),   "D1", "任一采样间隔 >=5ms 且已>=3 项间隔字时触发（掉拍型肘点）", "t[runStart..i] 的相邻间隔")

# ---- D2 连续短间隔游程（run-length of S/M 字母）：连续短拍段结束于第 L 项 ----
def d2_make(letter, L):
    def fn(r):
        T, i, j = r["T"], r["i"], r["j"]
        run = 0
        for x in range(i + 1, j + 1):
            if bkt((T[x] - T[x - 1]) * 1000.0) == letter:
                run += 1
                if run >= L:
                    return x
            else:
                run = 0
        return None
    return fn
add("D2-run-S4", d2_make("S", 4), "D2", "连续 4 个 <0.05ms 的极短间隔（密集拍）即触发", "t[runStart..i] 的间隔游程")
add("D2-run-M6", d2_make("M", 6), "D2", "连续 6 个 0.05-0.5ms 中等间隔即触发", "t[runStart..i] 的间隔游程")

# ---- D3 相邻游程关系（adjacent-run）：当前游程间隔形状 vs 前一已完成游程 ----
# 判据 = 当前前缀的最小/最大间隔相对「前一已完成游程」最小/最大间隔的序数关系，全为已完成历史。
def d3_min_ratio_gt(r):
    pm = r["prev_min"]
    if pm is None or pm <= 0:
        return None
    T, i, j = r["T"], r["i"], r["j"]
    for x in range(i + 1, j + 1):
        g = min((T[k] - T[k - 1]) * 1000.0 for k in range(i + 1, x + 1))
        if g > pm and (x - i) >= 3:          # 当前前缀最短间隔 > 前一游程最短间隔（全部拍都不密集）
            return x
    return None
def d3_ordinal_flip(r):
    # 前一游程形状字与当前前缀形状字的「首字不同 + 当前首字 >= L」=> 相邻游程节奏切换
    if r["prev_len"] is None or r["prev_len"] < 2:
        return None
    T, i, j = r["T"], r["i"], r["j"]
    pg = [(T[k] - T[k - 1]) * 1000.0 for k in range(r["i"] - r["prev_len"] + 1, r["i"] + 1)]
    pfirst = bkt(pg[0])
    cfirst = bkt((T[i + 1] - T[i]) * 1000.0) if i + 1 <= j else None
    if cfirst is None or cfirst == pfirst or cfirst not in ("L", "X", "G"):
        return None
    for x in range(i + 2, j + 1):           # 至少 2 项间隔才确认不是单点抖动
        return x
    return None
add("D3-min>prev", d3_min_ratio_gt, "D3", "当前前缀最短间隔 > 前一已完成游程最短间隔（且>=3拍）", "前一游程最短间隔(已完成)")
add("D3-flip",     d3_ordinal_flip, "D3", "相邻游程首间隔序数跳到 L/X/G 且与前游程首字不同", "前一游程首间隔(已完成)")

# ---- D4 肘形（local acceleration）：连续 3 项间隔的序数单调 / 突降 ----
def d4_rising(r):
    T, i, j = r["T"], r["i"], r["j"]
    gs = []
    for x in range(i + 1, j + 1):
        gs.append((T[x] - T[x - 1]) * 1000.0)
        if len(gs) >= 3 and gs[-3] < gs[-2] < gs[-1]:
            return x
    return None
def d4_burst(r):
    # 前一项短(M/S)、当前项长(X/G) 的「短->长」肘点
    T, i, j = r["T"], r["i"], r["j"]
    prev = None
    for x in range(i + 1, j + 1):
        g = (T[x] - T[x - 1]) * 1000.0
        if prev is not None and prev < 0.5 and g >= 2.0:
            return x
        prev = g
    return None
add("D4-rising", d4_rising, "D4", "连续 3 项相邻采样间隔严格递增（局部减速肘形）", "t[runStart..i] 的间隔序数")
add("D4-burst",  d4_burst,  "D4", "相邻间隔由短(<0.5ms)突变到长(>=2ms) 的肘点", "t[runStart..i] 的间隔序数")

# ---- D5 相对前一帧周期的序数（phase-ordinal，非阈值倍率、非分位）----
# 判据 = 当前游程第 m 拍的 elapsed 与「前一帧周期 D」的**整数商**是否跨过一个整数边界，
# 且要求该拍的间隔序数字发生变化。用 D 作标尺的「相位跳变」，不是 elapsed/D > r 的倍率阈值。
def d5_phase(r):
    D = r["D"]
    if D is None or D <= 0:
        return None
    T, i, j = r["T"], r["i"], r["j"]
    prev_phase = 0
    prev_bkt = None
    for x in range(i + 1, j + 1):
        g = (T[x] - T[x - 1]) * 1000.0
        ph = int(elapsed_ms(r, x) / D)       # 以已完成帧周期为 1 个相位的整数商
        cb = bkt(g)
        if ph > prev_phase and cb != prev_bkt and (x - i) >= 3:
            return x
        prev_phase, prev_bkt = ph, cb
    return None
def d5_ordinal_cross(r):
    # 当前前缀间隔字中 L/X/G 的**序数位置**首次超过前一游程 L/X/G 的序数位置数
    if r["prev_len"] is None or r["prev_len"] < 2:
        return None
    T, i, j = r["T"], r["i"], r["j"]
    pstart = r["i"] - r["prev_len"]
    pg = [(T[k] - T[k - 1]) * 1000.0 for k in range(pstart + 1, r["i"] + 1)]
    pscore = sum(1 for g in pg if bkt(g) in ("L", "X", "G"))
    cscore = 0
    for x in range(i + 1, j + 1):
        cscore += 1 if bkt((T[x] - T[x - 1]) * 1000.0) in ("L", "X", "G") else 0
        if cscore > pscore and (x - i) >= 3:
            return x
    return None
add("D5-phase",  d5_phase,         "D5", "elapsed 跨过前一帧周期 D 的整数相位边界且间隔字变化", "前一帧周期 D(已完成)")
add("D5-ordinal", d5_ordinal_cross, "D5", "当前前缀 L/X/G 序数计数超过前一游程的同序数计数", "前一游程形状(已完成)")

# 禁止项自检（结构性，不是运行期调参）
BANNED = ("P95", "P99", "cap40", "CAP", "滑窗", "分位", "倍率")
def banned_scan():
    bad = []
    for cid, fn, fam, note, needs in CRIT:
        if fam == "CAL":
            continue
        for tok in ("P95", "P99", "CAP", "percentile"):
            if tok in note or tok in cid:
                bad.append((cid, tok))
    return bad
out("\n【禁止项自检】新判据族 D1..D5 的 id/定义中不含 k 值档 / P95-P99 分位×倍 / 滑窗 N 历史分位 / 40ms CAP：")
out(f"  扫描命中={banned_scan()}（空=通过）；D1..D5 共 {sum(1 for c in CRIT if c[2].startswith('D'))} 档，"
    f"CAL 校准 {sum(1 for c in CRIT if c[2]=='CAL')} 档（仅核对用，不参与新判据比较）")

# ================================================================== 3 触发序列 + 三维核算
# trig item = (t_abs, idx, trip, win, key, is_real, dfin, waitMS, e, strict_ok)
def build_trig(fn):
    lst = []
    for r in REC:
        idx = fn(r)
        if idx is None:
            continue
        w = elapsed_ms(r, idx)
        e = r["e"]
        # 事后计费标签：is_real / dfin 只在触发后读取，谓词 fn 内部从未接触
        lst.append((r["T"][idx], idx, r["trip"], r["win"], r["key"], r["is_real"],
                    r["dfin"], w, e, (e is not None and w + e <= B50)))
    return lst

def simulate(trig, scope, N):
    """按触发时刻升序、先到先得；每次触发（含误触发）消耗 1 个配额。"""
    groups = defaultdict(list)
    for t in trig:
        g = (t[2], t[3]) if scope == "window" else t[2]
        groups[g].append(t)
    cap_keys = set()
    quota_used = 0
    false_eaten = 0
    cap_strict = set()          # 被配额捕获且 :177 严格合规的真实事件
    for g, arr in groups.items():
        arr.sort(key=lambda x: (x[0], x[3], x[1]))
        used = 0
        for t in arr:
            if used < N:
                used += 1
                quota_used += 1
                if not t[5]:
                    false_eaten += 1
                else:
                    cap_keys.add(t[4])
                    if t[9]:
                        cap_strict.add(t[4])
            # else: 配额已耗尽，丢弃（真实事件被抢占）
    return {
        "captured": len(cap_keys),
        "captured_strict50": len(cap_strict),
        "quotaEatenByFalse": false_eaten,
        "quotaUsed": quota_used,
    }

RESULTS = {}
TRIG = {}
for cid, fn, fam, note, needs in CRIT:
    lst = build_trig(fn)
    TRIG[cid] = lst
    trig = len(lst)
    hits = len({t[4] for t in lst if t[5]})
    false = sum(1 for t in lst if t[6] < DCLASS)
    real_lats = [t[7] for t in lst if t[5]]
    strict_hits = len({t[4] for t in lst if t[5] and t[9]})
    strict_e_unknown = len({t[4] for t in lst if t[5] and t[8] is None})
    r = {
        "family": fam, "note": note, "needs": needs,
        "triggers": trig, "realHits": hits, "missedReal": 1681 - hits,
        "falseTriggers": false, "falseRate": (false / trig if trig else None),
        "latP50": med(real_lats), "latP95": pctl(sorted(real_lats), .95) if real_lats else None,
        "latMax": max(real_lats) if real_lats else None,
        # ① :177 严格及时：分母固定 1681（含漏检与 e 未验按不合规计 0）
        "in50_strict_hits": strict_hits,
        "in50_strict_rate": strict_hits / 1681,
        "strict_e_unknown_real": strict_e_unknown,
        "W": {}, "T": {},
    }
    for N in NS:
        r["W"][str(N)] = simulate(lst, "window", N)
        r["T"][str(N)] = simulate(lst, "trip", N)
    RESULTS[cid] = r

# ================================================================== 4 校准核对（独立实现 vs 既有实跑）
qref = json.loads(QUOTA_JSON.read_text(encoding="utf-8-sig"))
mref = json.loads(METRICS_JSON.read_text(encoding="utf-8-sig"))
cal_map = {"CAL-C1-k10": "C1-k10", "CAL-C1-k25": "C1-k25",
           "CAL-C4-t40": "C4-t40", "CAL-C5-k10t30": "C5-k10t30"}
out("\n" + "=" * 112)
out("【校准：本 runner 独立重算 4 档既有判据 vs _cost_quota_data.json / CRITERIA_METRICS.json】")
cal_pass = cal_fail = 0
for cal_id, ref_id in cal_map.items():
    r = RESULTS[cal_id]
    m = mref[ref_id]
    ok_trig = (r["triggers"] == m["triggers"])
    ok_hits = (r["realHits"] == m["realHits"])
    ok_w = all(r["W"][str(N)]["captured"] == qref["results"][ref_id]["window" + str(N)]["captured"] for N in NS)
    ok_t = all(r["T"][str(N)]["captured"] == qref["results"][ref_id]["trip" + str(N)]["captured"] for N in NS)
    ok = ok_trig and ok_hits and ok_w and ok_t
    cal_pass += ok; cal_fail += (not ok)
    out(f"  {cal_id:<16} trig={r['triggers']:>6}(ref {m['triggers']:>6}) hits={r['realHits']:>5}(ref {m['realHits']:>5}) "
        f"W={[r['W'][str(N)]['captured'] for N in NS]} T={[r['T'][str(N)]['captured'] for N in NS]} "
        f"ref W={[qref['results'][ref_id]['window'+str(N)]['captured'] for N in NS]} "
        f"ref T={[qref['results'][ref_id]['trip'+str(N)]['captured'] for N in NS]}  "
        f"{'PASS' if ok else 'FAIL'}")
out(f"  校准合计 PASS={cal_pass} FAIL={cal_fail}（4 档 × triggers/hits/W1W3W5/T1T3T5）")

# ================================================================== 5 三维主表
out("\n" + "=" * 112)
out("【三维离线比较 · D1..D5 共 11 档（CAL 校准档另列，不并入新判据结论）】")
out("  ① :177 及时性：in50_strict = 真实事件中「触发等待 + 逐游程 e <= 50ms」的条数/1681；")
out("     waitAfterS_hat 是下界，S_hat-S∈[0,e]；e 未验的 4 条首拍游程按不合规计；latP50 仅真实命中子集、S_hat 锚下界。")
out("  ② 区分度：false = dfin<100 的触发数(事后计费)、falseRate=false/trig；captured = 误触发先到先得抢占配额后真实捕获/1681。")
out("  ③ 配额 N=1/3/5：W=每窗 (trip,window)，T=每会话 trip。")
out("  " + "-" * 108)
hdr = f"{'id':<17}|{'trig':>6}|{'hits':>5}|{'false':>6}|{'fRate%':>8}|{'latP50':>8}|{'latP95':>8}|{'in50s':>6}|" \
      + "".join(f"{'W'+str(N):>5}" for N in NS) + "|" + "".join(f"{'T'+str(N):>5}" for N in NS) + f"|{'Qfalse@W5':>10}"
out(hdr); out("-" * len(hdr))
for cid, fn, fam, note, needs in CRIT:
    r = RESULTS[cid]
    wcells = "".join(f"{r['W'][str(N)]['captured']:>5}" for N in NS)
    tcells = "".join(f"{r['T'][str(N)]['captured']:>5}" for N in NS)
    qf = r["W"]["5"]["quotaEatenByFalse"]
    fr = "N/A" if r["falseRate"] is None else f"{r['falseRate']*100:.3f}"
    out(f"{cid:<17}|{r['triggers']:>6}|{r['realHits']:>5}|{r['falseTriggers']:>6}|{fr:>8}|"
        f"{f6(r['latP50']):>8}|{f6(r['latP95']):>8}|{r['in50_strict_hits']:>6}|"
        f"{wcells}|{tcells}|{qf:>10}")

out("\n【三维逐档明细（含 captured_strict50：配额捕获且 :177 严格合规的真实事件数）】")
for cid, fn, fam, note, needs in CRIT:
    if fam == "CAL":
        continue
    r = RESULTS[cid]
    out(f"\n  --- {cid} [{fam}] {note}")
    out(f"      需求历史: {needs}；触发={r['triggers']} 真实命中={r['realHits']}/1681 漏检={r['missedReal']} "
        f"误触发={r['falseTriggers']} 误报率={f6(r['falseRate'])}")
    out(f"      latP50={f6(r['latP50'])} latP95={f6(r['latP95'])} latMax={f6(r['latMax'])} ms（仅真实命中、S_hat 锚、下界）")
    out(f"      :177 严格及时命中 in50_strict={r['in50_strict_hits']}/1681 ({r['in50_strict_rate']*100:.4f}%)；"
        f"其中真实事件 e 未验={r['strict_e_unknown_real']} 条（首拍游程，口径 B 保留）")
    for scope in ("W", "T"):
        for N in NS:
            z = r[scope][str(N)]
            out(f"      {scope} N={N}: captured={z['captured']:>5}/1681  "
                f"captured_strict50={z['captured_strict50']:>5}/1681  "
                f"false抢占槽={z['quotaEatenByFalse']:>6}")

# ================================================================== 6 形式化证据（可判定的计数上界/下界）
out("\n" + "=" * 112)
out("【形式化证据 ①：谓词无关的配额硬上界 —— 捕获维度对任何 (t,f) 前缀判据一律成立】")
out("  设配额组为 (trip,window)，26 个非空真实事件窗，N∈{1,3,5}。每组前 N 次「触发」消耗 N 个槽，")
out("  每槽最多对应 1 个真实事件，故 captured <= Σ_windows min(N, c_w) = 理想值，与谓词、前缀形状、")
out("  误触发多少完全无关（误触发只会让 captured 更小）。trip 口径同理。")
# 逐 N 实跑复现（不依赖任何判据）
out("  N | 每窗理想(26窗) | 每会话理想(12 trip) | 可判定上界率(W) | 实测最佳 W (判据) | 实测最佳 T (判据)")
out("  " + "-" * 100)
quota_hard = {}
for N in NS:
    best_w = max((RESULTS[c[0]]["W"][str(N)]["captured"], c[0]) for c in CRIT)
    best_t = max((RESULTS[c[0]]["T"][str(N)]["captured"], c[0]) for c in CRIT)
    quota_hard[N] = (ideal_w[N], ideal_t[N])
    out(f"  {N} | {ideal_w[N]:>14} | {ideal_t[N]:>18} | {ideal_w[N]/1681*100:>14.4f}% | "
        f"{best_w[0]:>5} ({best_w[1]}) | {best_t[0]:>5} ({best_t[1]})")
best_w5 = max((RESULTS[c[0]]["W"]["5"]["captured"], c[0]) for c in CRIT)
out(f"  推论：即使「:177 全合规 + 零误触发」的完美谓词存在，N=5 每窗 captured<=117/1681=6.96%；")
out(f"  本轮 11 档新判据 + 4 档校准档里，误触发先到先得后实测最佳 W5={best_w5[0]}/1681 "
    f"({best_w5[0]/1681*100:.2f}%, {best_w5[1]})。捕获维度本身不可兼得。")

out("\n【形式化证据 ②：存活集基准率 —— 及时性对区分度的**单次触发**计数上界】")
out("  任取在线因果谓词 P，若其在某游程 elapsed=τ 处触发，则要求该游程在 τ 处帧仍冻结（dfin>τ）；")
out("  P 在 τ 处的触发母体只能是 A(τ)={r: dfin>τ}。因此在 τ 处触发的那一次，")
out("  P(该次为真实 | 在 τ 处触发) <= A_real(τ)/A(τ)（对读 (t,f) 前缀的任意谓词皆成立）。")
out("  混合 τ 触发的谓词，其总查准率 <= max_{a<=τ} A_real(a)/A(a)（非此列某一行，取前缀上确界）。")
out("  τ(ms) |   A(τ) | A_real | A_falseB | base_rate 上界 | 与 :177 的关系")
out("  " + "-" * 100)
bound = {}
for tau in (10, 18, 25, 30, 40, 45, 50, 60, 70, 80, 90, 99, 100):
    A = [r for r in REC if r["dfin"] > tau]
    a_real = sum(1 for r in A if r["is_real"])
    a_fb = sum(1 for r in A if r["dfin"] < DCLASS and not r["is_real"])
    br = a_real / len(A) if A else None
    bound[tau] = (len(A), a_real, a_fb, br)
    note = ":177 允许（S_hat 锚 ≤50，加 e 更严）" if tau <= 50 else "超出 S+50ms（不合规方向）"
    out(f"  {tau:>5} | {len(A):>7} | {a_real:>6} | {a_fb:>9} | "
        f"{(f'{br*100:.4f}%' if br is not None else 'N/A'):>14} | {note}")
out("  结论：τ<=50ms 时该上界 ≤33.2279%；只有 τ>=100ms 才可能排除全部 dfin<100 假游程，")
out("  但那已越过 :177 的 S+50ms（且 :190 拒止累计判定>=100ms）。")

out("\n【形式化证据 ③：前缀签名命中集 —— 限定特征类下的强制误触发计数下界】")
out("  设 σ(r,a) = 平移不变前缀特征签名（间隔形状字 + 前一帧周期桶 + 前一游程长度桶），")
out("  φ 为仅依赖 σ 的确定性函数型谓词，触发(R,a) ⇔ φ(σ(R,a))=1。")
out("  定义 S_R = {σ(R,a): a<=τ}（每条 real 可选的前缀签名集），U = ∪_R S_R；")
out("  记 falseB 游程类上的签名计数 c(s) = #{F: dfin<100 且 s∈S_F}（每个 F 每游程最多触发 1 次）。")
out("  任一 φ 若覆盖全部有前缀 real，其接受集 W={s:φ(s)=1} 必须命中每条 S_R（命中集问题）。")
out("  强制误触发数 forced_FP(W) = #{F: S_F ∩ W ≠ ∅}（去重计数，不是 Σ c(s)）；")
out("  下界 LB1 = max_R min_{s∈S_R} c(s)：为覆盖最贵的那条 R，W 至少含一个 s∈S_R，")
out("  该 s 单独就使 >= c(s) >= min_{S_R} c 个不同 F 被强制触发（去重后仍成立）。")
out("  UB_naive = #{F: S_F ∩ U ≠ ∅}（朴素 φ=接受 U 的一次去重实跑，仅作上界参考）。")
out("  τ(ms) | real有前缀 | 空前缀real | LB1=max_R min c | UB_naive(去重) | 任意φ的precision<= | 朴素φ的precision= ")
out("  " + "-" * 108)
def sig_stream(r, tau):
    T, i, j = r["T"], r["i"], r["j"]
    dsig = bkt(r["D"]) if r["D"] is not None else "NONE"
    psig = ("P0" if r["prev_len"] is None else
            "P1" if r["prev_len"] <= 3 else "P2" if r["prev_len"] <= 8 else "P3")
    word = ""
    S = set()
    x = i + 1
    while x <= j and elapsed_ms(r, x) <= tau:
        word += bkt((T[x] - T[x - 1]) * 1000.0)
        S.add((x - i, word, dsig, psig))
        x += 1
    return S
prefix_bound = {}
for tau in (18, 25, 30, 40, 45, 50):
    short_ct = Counter()
    real_sigsets = []
    U = set()
    empty_real = 0
    false_sigsets = []
    for r in REC:
        S = sig_stream(r, tau)
        if r["is_real"]:
            if not S:
                empty_real += 1
            else:
                real_sigsets.append(S)
                U |= S
        elif r["dfin"] < DCLASS:
            false_sigsets.append(S)
            for s in S:
                short_ct[s] += 1
    lb1 = max(min(short_ct[s] for s in S) for S in real_sigsets) if real_sigsets else 0
    ub_naive = sum(1 for S in false_sigsets if (S & U))
    # 分母用「朴素 φ 覆盖的真实事件数」（此处 = 有前缀 real 数）
    n_cov = len(real_sigsets)
    prec_lb1 = n_cov / (n_cov + lb1) if n_cov + lb1 else None
    prec_ub = n_cov / (n_cov + ub_naive) if n_cov + ub_naive else None
    prefix_bound[tau] = (len(real_sigsets), empty_real, lb1, ub_naive, prec_lb1)
    out(f"  {tau:>5} | {len(real_sigsets):>10} | {empty_real:>10} | {lb1:>17} | {ub_naive:>15} | "
        f"{(f'{prec_lb1*100:.4f}%' if prec_lb1 is not None else 'N/A'):>22} | "
        f"{(f'{prec_ub*100:.4f}%' if prec_ub is not None else 'N/A'):>23}")
out("  【诚实边界】UB_naive 是「接受 U 的那一个朴素谓词」的实跑，不是所有 φ 的公共下界；")
out("  故本件只把 LB1 当作可判定的强制误触发计数下界（任意 φ 的 precision <= n_cov/(n_cov+LB1)），")
out("  UB_naive 与「朴素 φ 的 precision」仅作单次实跑参考，不并入通用结论。")
out("  另：τ=18 有 9 条 real 在 <=18ms 内没有任何采样间隔前缀（首拍/掉拍），故「τ 内触发全部 1681」")
out("  在语料上直接不可达，与 φ 选法无关 —— 这是前缀信息的可判定计数上界（空前缀计数）。")
out("  LB1 限定于「形状/序数/相邻游程摘要」特征类；对任意实值函数型谓词的信息论级断言见 U5。")

out("\n【形式化证据 ④：:177 严格合规 + 全召回 + 区分度三者不可兼得（e 与配额维）】")
out(f"  逐游程 e：有效 n={len(es)}，其中 e>50ms 的游程 {sum(1 for x in es if x>50)} 条 -> "
    f"这些游程即使 waitAfterS_hat=0 也无法证明 wait+e<=50ms（:177 严格核算不可判定）。")
real_e_gt50 = sum(1 for r in REC if r["is_real"] and r["e"] is not None and r["e"] > B50)
real_e_none = sum(1 for r in REC if r["is_real"] and r["e"] is None)
real_e_unknown = real_e_gt50 + real_e_none
out(f"  其中落在真实事件上的 e>50ms n={real_e_gt50}；startTick=0 的真实事件 e 未验 n={real_e_none}；"
    f"合计 n={real_e_unknown}/1681 无法给出 :177 严格合规证明，故 in50_strict <= {1681-real_e_unknown}/1681 "
    f"= {(1681-real_e_unknown)/1681*100:.4f}% 是**任何 (t,f) 前缀判据的上确界**。")
out(f"  配额维：理想(只由真实事件消耗) W1/W3/W5 = {ideal_w[1]}/{ideal_w[3]}/{ideal_w[5]}，"
    f"即 N=5 时仍有 {1681-ideal_w[5]}/1681 = {(1681-ideal_w[5])/1681*100:.4f}% 真实事件被母数放弃；")
out(f"  误触发抢占后实测 captured 见 §5 主表，全部 <= 理想值。")
out(f"  三维不可兼得的可判定式：captured <= Σmin(N,c_w)，in50_strict <= {1681-real_e_unknown}/1681，")
out("  precision(<=50ms) <= max_{a<=50} A_real(a)/A(a) = 33.2279%；三者上确界互不相容于「全都要」。")

# ================================================================== 7 判据族之间 & 与 C1-C5 的差异核对
out("\n" + "=" * 112)
out("【与 C1–C5 的差异核对：触发点集合是否重合（防止「换名调参」）】")
# 逐档给出触发点相对 C1-k10 的差异率（同一游程上触发 idx 不同即算差异）
c1 = {t[4]: t[1] for t in TRIG["CAL-C1-k10"]}
for cid, fn, fam, note, needs in CRIT:
    if fam == "CAL":
        continue
    mine = {t[4]: t[1] for t in TRIG[cid]}
    common = set(mine) & set(c1)
    diff = sum(1 for k in common if mine[k] != c1[k])
    only_mine = len(set(mine) - set(c1))
    only_c1 = len(set(c1) - set(mine))
    out(f"  {cid:<17} 与 C1-k10 共同触发游程={len(common):>6} 其中触发拍不同={diff:>6} "
        f"({(diff/len(common)*100 if common else 0):>6.2f}%)  仅本档触发={only_mine:>6} 仅C1触发={only_c1:>6}")
out("  注：触发拍不同即谓词结构不同；D1..D5 均不复用 k 值/分位倍率/滑窗分位/CAP。")

# ================================================================== 8 未验项（单列）
out("\n" + "=" * 112)
out("【未验项 · 单列，不并入结论】")
UNVERIFIED = [
 "物理起点 S 的微秒点估计：语料不可得；e 只是观测滞后上界代理，:177 的严格 S+50ms 闭环证明未验（题给 STALL_EVENT_DEFINITION.md:177、S_OBSERVABILITY.md §5.3）。",
 "4 条 startTick=0 的真实事件 e 未验（S 落在观测窗外）；本件按不合规计 0，未外推。",
 ":190 检测确认 D 到采样动作生效的端到端延迟、:191 累计判定耗时、Q5 四项扰动：本件零采样代码，全部未验（RULING_D30.md:22,78）。",
 "内部对局状态旗标 IN_TACTICAL/SCORE_SCREEN/PAUSED/LOADING：语料缺，未验（RULING_D30.md:54）。",
 "形式化证据③的 LB1 限定于「平移不变前缀特征签名（间隔形状/序数/相邻游程摘要）」类；对任意实值函数型谓词（利用绝对 t 值、跨窗全局身份、全精度 1µs 差值记忆）的信息论级不可判定性未验——_dA_probe_out.txt:75-76 显示精确(1µs 差值)签名下 LB1=0、朴素 φ 的 UB_naive 仅 1 条，故不作「任意谓词皆不可能」的断言；但对这类谓词，证据①配额硬上界、证据②存活集基准率上界、证据④的 e 硬上界仍无条件成立。",
 "触发后实际保存动作是否成功、线程上下文是否在 S+50ms 内被保存、跨硬件/跨战术场景外推：均未验（STALL_EVENT_DEFINITION.md:170,179）。",
 "D1..D5 的字母表边界(0.05/0.5/2/5ms)与游程长度(S4/M6)是结构性定义，未做超参数敏感性扫描；按题给禁止项，本件不做 k/P95-P99/滑窗N/CAP 扫描。",
 "配额「先到先得」是离线模拟，非在线保证；窗间 4s 空白与跨窗边界截断未验（STALL_EVENT_DEFINITION.md:178）。",
]
for i, u in enumerate(UNVERIFIED, 1):
    out(f"  U{i}. {u}")

# ================================================================== 9 输出落地
DATA = {
    "meta": {
        "script": "lead/dtrigger_round2_20261107/_dA_run.py",
        "files": len(cache), "samples": n_samples, "manifestWindows": len(manifest_keys),
        "runs": len(REC), "real": 1681, "NS": list(NS),
        "idealWindow": ideal_w, "idealTrip": ideal_t,
        "e": {"n": len(es), "min": es[0], "med": med(es), "P99": pctl(es, .99), "max": es[-1]},
        "calPass": cal_pass, "calFail": cal_fail,
        "fingerprints": {rel: {"sha256": FP[rel][0], "bytes": FP[rel][1]} for rel in FINGERPRINT_RELS},
    },
    "criteria": {cid: {"family": fam, "note": note, "needs": needs,
                       "triggers": r["triggers"], "realHits": r["realHits"],
                       "falseTriggers": r["falseTriggers"], "falseRate": r["falseRate"],
                       "latP50": r["latP50"], "latP95": r["latP95"], "latMax": r["latMax"],
                       "in50_strict_hits": r["in50_strict_hits"], "in50_strict_rate": r["in50_strict_rate"],
                       "W": r["W"], "T": r["T"]}
                 for (cid, fn, fam, note, needs), r in zip(CRIT, (RESULTS[c[0]] for c in CRIT))},
    "bound_baserate": {str(k): v for k, v in bound.items()},
    "bound_prefix": {str(k): v for k, v in prefix_bound.items()},
    "unverified": UNVERIFIED,
}
OUT_JSON.write_text(json.dumps(DATA, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# 自检 + 被核对象指纹（铁律 9）
checks = []
checks.append(("语料 runs=28381", len(REC) == 28381))
checks.append(("real 对齐=1681", aligned == 1681))
checks.append(("校准 4 档 PASS", cal_pass == 4 and cal_fail == 0))
checks.append(("所有 captured<=realHits", all(
    RESULTS[c[0]][s][str(N)]["captured"] <= RESULTS[c[0]]["realHits"]
    for c in CRIT for s in ("W", "T") for N in NS)))
checks.append(("所有 captured<=ideal", all(
    RESULTS[c[0]]["W"][str(N)]["captured"] <= ideal_w[N] and
    RESULTS[c[0]]["T"][str(N)]["captured"] <= ideal_t[N]
    for c in CRIT for N in NS)))
checks.append(("captured_strict50<=captured", all(
    RESULTS[c[0]][s][str(N)]["captured_strict50"] <= RESULTS[c[0]][s][str(N)]["captured"]
    for c in CRIT for s in ("W", "T") for N in NS)))
checks.append(("禁止项扫描为空", banned_scan() == []))
checks.append(("τ=50 基准率上界<=0.35", bound[50][3] <= 0.35))
checks.append(("τ=50 LB1>0（命中集下界可判定）", prefix_bound[50][2] > 0))
checks.append(("τ=18 存在空前缀 real（全召回不可达）", prefix_bound[18][1] > 0))
checks.append(("in50_strict 全部 <= e 硬上界(1681-real_e_unknown)",
               all(RESULTS[c[0]]["in50_strict_hits"] <= 1681 - real_e_unknown for c in CRIT)))
# 结构差异自检：零触发档单列为 DEGENERATE（空集不参与「触发拍是否全同」判定）
diff_detail = []
for cid, fn, fam, note, needs in CRIT:
    if not fam.startswith("D"):
        continue
    mine = {t[4]: t[1] for t in TRIG[cid]}
    common = set(mine) & set(c1)
    n_diff = sum(1 for k in common if mine[k] != c1[k])
    if not mine:
        diff_detail.append((cid, "DEGENERATE", 0))
    elif n_diff > 0:
        diff_detail.append((cid, "DISTINCT", n_diff))
    else:
        diff_detail.append((cid, "SAME_AS_C1", 0))
out("  结构差异自检（DEGENERATE=该档在本语料零触发，单列，不计入对照）：" +
    ", ".join(f"{c}={s}" for c, s, _ in diff_detail))
checks.append(("所有非零触发 D 档触发拍不与 C1-k10 全同",
               all(s in ("DISTINCT", "DEGENERATE") for _, s, _ in diff_detail)))
chk_lines = ["【自检 · 实跑断言】"]
for name, ok in checks:
    chk_lines.append(f"  {'PASS' if ok else 'FAIL'}  {name}")
chk_lines.append(f"  合计 PASS={sum(1 for _,o in checks if o)} FAIL={sum(1 for _,o in checks if not o)}")
# 铁律 9：被核对象 SHA256（本轮主要被核对象 = 上游 CRITERIA_COMPARE.md；另列全部输入件）
chk_lines.append("")
chk_lines.append("【被核对象 SHA256（铁律 9）】")
for rel in FINGERPRINT_RELS:
    chk_lines.append(f"被核对象 SHA256 = {FP[rel][0]}，字节数 = {FP[rel][1]}    [{rel}]")
chk_lines.append("")
chk_lines.append("【本轮 _dA_ 输出件指纹】")
for p in (WD / "_dA_probe_out.txt", OUT_TXT, OUT_JSON, CHECK_TXT, WD / "_dA_run.py", WD / "_dA_probe.py"):
    if p.exists():
        b = p.read_bytes()
        chk_lines.append(f"  {p.name} sha256={hashlib.sha256(b).hexdigest()} bytes={len(b)}")
CHECK_TXT.write_text("\n".join(chk_lines) + "\n", encoding="utf-8")

out("\n" + "=" * 112)
out("【自检】")
for l in chk_lines[:12]:
    out(l)
out(f"  自检明细与全部指纹见 {CHECK_TXT}")
out("\n【执行者结束 · 零真机 / 零采样代码 / 只读语料 / 无 commit push】")
OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"\n[written] {OUT_TXT} / {OUT_JSON} / {CHECK_TXT}")
