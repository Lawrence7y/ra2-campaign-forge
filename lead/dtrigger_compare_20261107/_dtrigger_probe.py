# -*- coding: utf-8 -*-
"""
_dtrigger_probe.py - 候选触发判据离线比较探针（只读语料，零真机/零采样实现）

唯一写域：lead/dtrigger_compare_20261107/
运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_dtrigger_probe.py

设计原则
--------
1. 在线因果：判据只用「当前采样点 i 及其之前」的信息。绝不读取 fs[i+1..]、事件标签、
   durationMs、endTick 或「最终 d>=100ms」——那是事后分类，不是在线触发。
   「本次 d_final>=100ms」只在触发之后用于离线打分（计费），不参与是否触发。
2. k 点 = k-1 个间隔：所有名义等待 = (k-1)*2ms（标称500Hz），实测等待取 t[i]-t[start]。
3. waitAfterS 用「观测首拍 t[runStart]」为锚点（物理 S 无法从语料测得），
   并单列 onset 观测滞后上界 e = t[runStart]-t[runStart-1] 的实测分布。
4. 历史基线严格因果：滑窗只含 runStart-1 及更早的已完成帧间隔（每次帧号推进的
   t[edge]-t[prevEdge]），不含当前停滞游程本身；冷启动不足 N 条时不触发。
5. 对每档判据报告：总触发数、最终 d_final<100ms 的「事后误报」数/率、
   严格真实事件命中数、触发等待（min/中位/P90/max）、超过 50ms 截止的触发数。
"""

import hashlib
import json
import re
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
EVENTS = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
MANIFEST = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
WRITEDIR = (ROOT / "lead/dtrigger_compare_20261107").resolve()
OUTPUT = WRITEDIR / "_dtrigger_probe_out.txt"

def safe_open(rel):
    """读取仅在仓库根内的相对路径；解析后校验前缀，拒绝任何越界。"""
    p = (ROOT / rel).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError("path escapes repository root: " + str(p))
    return p

def read_text(rel):
    return safe_open(rel).read_text(encoding="utf-8-sig")

def fp_bytes(rel):
    p = safe_open(rel)
    if not p.is_relative_to(ROOT):
        raise ValueError("path escapes repository root: " + str(p))
    return p.read_bytes()

NOMINAL_MS = 2.0        # 500 Hz 标称周期
CUTOFF_MS = 50.0        # :177 S+50ms 截止（本探针以观测首拍为锚点近似）
DCLASS_MS = 100.0       # 口径B 事后分类门槛，只用于打分不用于触发

lines = []
def out(s=""):
    lines.append(str(s))
    print(s)

def pct(sorted_arr, p):
    """线性最近秩百分位：与既有 _feasibility_probe.py:54-63 同口径。"""
    if not sorted_arr:
        return None
    return sorted_arr[int(p * (len(sorted_arr) - 1))]

def med(arr):
    return statistics.median(arr) if arr else None

def fmt(v, n=3):
    return "N/A" if v is None else f"{v:.{n}f}"

# ----------------------------------------------------------------------------
# 1. 语料加载（只读）
# ----------------------------------------------------------------------------
out("=" * 100)
out("【候选触发判据离线比较探针 · 全量 104 窗】")
out("口径：在线因果判据；d_final>=100ms 仅用于事后计费，绝不参与触发。")
out("=" * 100)

files = sorted(BASE.rglob("measure_w*.json"))
cache = {}
for p in files:
    pr = p.resolve()
    if not pr.is_relative_to(BASE):
        raise ValueError("corpus file escapes base: " + str(pr))
    rel_parts = pr.relative_to(BASE).parts
    key = (rel_parts[0] if len(rel_parts) > 1 else "(root)", pr.stem.replace("measure_", ""))
    d = json.loads(pr.read_text(encoding="utf-8-sig"))
    assert len(d.get("samples", {}).get("t", [])) == len(d.get("samples", {}).get("f", []))
    cache[key] = d

n_total_samples = sum(len(v.get("samples", {}).get("t", [])) for v in cache.values())
out(f"语料文件 n={len(files)}，总采样点 n={n_total_samples}，全部 hz={sorted({v.get('hz') for v in cache.values()})}")

for rel in ["lead/stall_event_def_20261106/STALL_EVENTS.json",
            "lead/early_trigger_feasibility_20261106/_feasibility_probe.py",
            "lead/d30_ruling_20261106/RULING_D30.md"]:
    out(f"sha256 {rel} = {hashlib.sha256(fp_bytes(rel)).hexdigest()}")

events_all = json.loads(read_text("lead/stall_event_def_20261106/STALL_EVENTS.json"))
real = [e for e in events_all if e.get("isRealMatch") is True]
real_keys = {(e["trip"], e["window"], e["startTick"], e["endTick"]) for e in real}
out(f"STALL_EVENTS 全量 n={len(events_all)}，isRealMatch==True n={len(real)}（不与 1737 混为同口径）")

# moving64 推进窗（与 lead/d30_ruling_20261106/_d30_facts.py:72-83 同口径）
manifest_keys = []
for line in read_text("lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").splitlines():
    m = re.match(r"^([a-zA-Z0-9_\(\)]+)\s+(w\d)\s+([0-9\.]+)", line.strip())
    if m:
        k = (m[1], m[2])
        if k in cache:
            s = cache[k].get("samples", {})
            ts, fs = s.get("t", []), s.get("f", [])
            if len(ts) >= 2 and any(a != b for a, b in zip(fs, fs[1:])):
                manifest_keys.append(k)
manifest_keys = sorted(set(manifest_keys))
out(f"moving64 推进窗 n={len(manifest_keys)}（D30 核证同口径）")

# ----------------------------------------------------------------------------
# 2. 逐窗构造：帧游程 + 因果历史帧间隔序列
# ----------------------------------------------------------------------------
# hist = 每次帧号推进的 t[edge]-t[prev_edge]（ms），按采样顺序
# hist_len_at[i] = 截至采样点 i（含）为止已完成的帧推进条数
# runStart=i 处的因果快照 = hist[:hist_len_at[i-1]]，只含 i-1 及更早，
# 保证「当前停滞游程本身不进基线」。
window_data = {}
for trip, win in manifest_keys:
    s = cache[(trip, win)]["samples"]
    ts, fs = s["t"], s["f"]
    n = len(fs)
    hist = []
    hist_len_at = [0] * n
    last_edge = 0
    for i in range(1, n):
        if fs[i] != fs[i - 1]:
            hist.append((ts[i] - ts[last_edge]) * 1000.0)
            last_edge = i
        hist_len_at[i] = len(hist)
    runs = []
    i = 0
    while i < n:
        j = i
        while j + 1 < n and fs[j + 1] == fs[i]:
            j += 1
        h_end = hist_len_at[i - 1] if i > 0 else 0
        runs.append({
            "trip": trip, "win": win, "i": i, "j": j,
            "npts": j - i + 1,
            "d_final_ms": (ts[j] - ts[i]) * 1000.0,
            "h_end": h_end,
            "onset_gap_ms": (ts[i] - ts[i - 1]) * 1000.0 if i > 0 else None,
        })
        i = j + 1
    window_data[(trip, win)] = {"ts": ts, "fs": fs, "hist": hist, "runs": runs}

all_runs = [r for w in window_data.values() for r in w["runs"]]
out(f"推进窗内全部帧号游程 n={len(all_runs)}（评分母体；每游程最多触发一次）")

all_hist = sorted(x for w in window_data.values() for x in w["hist"])
out("\n【历史帧间隔总体分布（moving64 窗内全部已完成帧推进，n=%d）】" % len(all_hist))
for p in (0.50, 0.75, 0.90, 0.95, 0.99, 1.00):
    out(f"  P{int(p*100):02d} = {fmt(pct(all_hist, p))} ms")
out("  注：这是全语料离线描述，不是在线可用基线；在线基线必须按下方滑窗因果取。")

cold = Counter()
for r in all_runs:
    for N in (16, 32, 64, 128):
        if r["h_end"] < N:
            cold[N] += 1
out("\n【冷启动不可触发的游程数（runStart 处历史不足 N 条）】")
for N in (16, 32, 64, 128):
    out(f"  N={N}: {cold[N]}/{len(all_runs)} 条游程无基线（占比 {cold[N]/len(all_runs)*100:.2f}%）")

# ----------------------------------------------------------------------------
# 3. 判据定义（全部为在线因果谓词；返回值 = 触发等待(ms) 或 None）
# ----------------------------------------------------------------------------
def C_k(run, w, k):
    """C1 连续 k 拍同帧：在第 k 拍（i+k-1）触发。k 点 = k-1 个间隔。"""
    ts = w["ts"]
    if run["npts"] < k:
        return None, 0.0
    return (ts[run["i"] + k - 1] - ts[run["i"]]) * 1000.0, 0.0

def C_rel(run, w, q, mult, N, floor_ms):
    """C2 相对帧间隔：帧号不变 且 自观测首拍起已持续 > q分位基线*mult。
       基线 = runStart-1 及之前最近 N 条已完成帧间隔；不含当前停；冷启动不触发。
    """
    if run["h_end"] < N:
        return None, None
    base = pct(sorted(w["hist"][run["h_end"] - N: run["h_end"]]), q)
    if base is None:
        return None, None
    theta = base * mult
    ts = w["ts"]
    for idx in range(run["i"], run["j"] + 1):
        elapsed = (ts[idx] - ts[run["i"]]) * 1000.0
        if elapsed > theta and elapsed >= floor_ms:
            return elapsed, elapsed
    return None, None

def C_rel_abs(run, w, q, mult, N, floor_ms):
    """C2' 距离锚 = 上一帧沿（多含 onset 观测滞后），其余同 C2。"""
    if run["h_end"] < N:
        return None, None
    base = pct(sorted(w["hist"][run["h_end"] - N: run["h_end"]]), q)
    if base is None:
        return None, None
    theta = base * mult
    ts = w["ts"]
    og = run["onset_gap_ms"]
    if og is None:
        return None, None
    t_last_edge = ts[run["i"]] - og / 1000.0
    for idx in range(run["i"], run["j"] + 1):
        since_advance = (ts[idx] - t_last_edge) * 1000.0
        elapsed = (ts[idx] - ts[run["i"]]) * 1000.0
        if since_advance > theta and elapsed >= floor_ms:
            return elapsed, elapsed
    return None, None

def C_rate(run, w, mult, N, floor_ms):
    """C3 帧间隔变化率：(t[idx]-t[上一帧沿]) / median(近N条帧间隔) > mult。"""
    if run["h_end"] < N:
        return None, None
    base = med(w["hist"][run["h_end"] - N: run["h_end"]])
    if base is None or base <= 0:
        return None, None
    ts = w["ts"]
    og = run["onset_gap_ms"]
    if og is None:
        return None, None
    t_last_edge = ts[run["i"]] - og / 1000.0
    for idx in range(run["i"], run["j"] + 1):
        elapsed = (ts[idx] - ts[run["i"]]) * 1000.0
        observed_gap = (ts[idx] - t_last_edge) * 1000.0
        if observed_gap / base > mult and elapsed >= floor_ms:
            return elapsed, elapsed
    return None, None

def C_abs(run, w, theta_ms, k_min):
    """C4 绝对时长：帧号不变持续 > theta_ms（且至少 k_min 拍）。"""
    ts = w["ts"]
    if run["npts"] < k_min:
        return None, 0.0
    for idx in range(run["i"] + k_min - 1, run["j"] + 1):
        elapsed = (ts[idx] - ts[run["i"]]) * 1000.0
        if elapsed > theta_ms:
            return elapsed, elapsed
    return None, 0.0

def C_hybrid(run, w, k, theta_ms):
    """C5 复合：连续 k 拍同帧 AND 绝对时长 > theta_ms，取较晚者触发。"""
    ts = w["ts"]
    if run["npts"] < k:
        return None, 0.0
    t_k = (ts[run["i"] + k - 1] - ts[run["i"]]) * 1000.0
    for idx in range(run["i"] + k - 1, run["j"] + 1):
        elapsed = (ts[idx] - ts[run["i"]]) * 1000.0
        if elapsed > theta_ms:
            return elapsed, max(0.0, elapsed - t_k)
    return None, 0.0

CRITERIA = []
def add(cid, family, fn, params, desc, hist_desc, extra_note):
    CRITERIA.append({"id": cid, "family": family, "fn": fn, "params": params,
                     "desc": desc, "hist": hist_desc, "extra_note": extra_note})

for k in (10, 25, 50):
    add(f"C1-k{k}", "连续k拍同帧", C_k, {"k": k},
        f"游程内帧号不变连续 >= {k} 拍时在第 {k} 拍触发（k点=k-1间隔，名义 {(k-1)*2}ms）",
        "无", "无额外等待；阈值本身即等待 k-1 个间隔")

for qn, q in (("P95", 0.95), ("P99", 0.99)):
    for mult in (2, 3):
        add(f"C2-{qn}x{mult}", "相对帧间隔", C_rel,
            {"q": q, "mult": mult, "N": 64, "floor_ms": 0.0},
            f"帧号不变 且 自观测首拍起已持续 > {qn}(近64条帧间隔)×{mult}；逐拍首次满足即触发",
            "滑窗=runStart-1及之前最近64条已完成帧间隔；不含当前停；冷启动<64条不触发",
            "必须等到实测时长越过阈值本身（这就是阈值等待）")

add("C2-abs-P95x2", "相对帧间隔(距上次推进锚)", C_rel_abs,
    {"q": 0.95, "mult": 2, "N": 64, "floor_ms": 0.0},
    "帧号不变 且 t[idx]-t[上一帧沿] > P95(近64条)×2",
    "同 C2；距离锚改为上一帧沿而非观测首拍（多含 onset 观测滞后）",
    "同上，且锚点更早，阈值更早被突破")

for mult in (4, 8, 12):
    add(f"C3-r{mult}", "帧间隔变化率", C_rate,
        {"mult": mult, "N": 64, "floor_ms": 0.0},
        f"(t[idx]-t[上一帧沿]) / median(近64条帧间隔) > {mult}",
        "滑窗=runStart-1及之前最近64条帧间隔的中位数；不含当前停；冷启动<64不触发",
        "阈值随实测时长增长，须等比值突破（阈值等待）")

for theta in (16, 24, 30, 40, 48):
    add(f"C4-t{theta}", "绝对时长", C_abs, {"theta_ms": theta, "k_min": 3},
        f"帧号不变持续毫秒数 > {theta}ms（且至少3拍）",
        "无", "须等实测毫秒数越过阈值；与 k 拍不等价（采样抖动）")

add("C5-k10t30", "复合(k拍+绝对时长)", C_hybrid, {"k": 10, "theta_ms": 30},
    "连续10拍同帧 且 绝对时长 >30ms，取较晚者触发",
    "无", "若 30ms 阈值晚于第10拍则产生额外等待")

out(f"\n【判据清单】共 {len(CRITERIA)} 档")

# ----------------------------------------------------------------------------
# 4. 逐判据全量跑分
# ----------------------------------------------------------------------------
RESULTS = []
for c in CRITERIA:
    triggers = []
    for w in window_data.values():
        for r in w["runs"]:
            wait, extra = c["fn"](r, w, **c["params"])
            if wait is not None:
                triggers.append((r, wait, extra))
    waits = sorted(x[1] for x in triggers)
    extras = [x[2] for x in triggers if x[2] is not None]
    n_trig = len(triggers)
    n_d100 = sum(1 for r, _, _ in triggers if r["d_final_ms"] >= DCLASS_MS)
    n_false = n_trig - n_d100
    hits = sum(1 for r, _, _ in triggers
               if (r["trip"], r["win"], r["i"], r["j"]) in real_keys)
    n_late = sum(1 for x in waits if x > CUTOFF_MS)
    n_late50 = sum(1 for x in waits if x >= CUTOFF_MS)
    res = {
        "id": c["id"], "family": c["family"], "desc": c["desc"], "hist": c["hist"],
        "extra_note": c["extra_note"],
        "nTrig": n_trig, "nFalse": n_false,
        "falseRate": n_false / n_trig if n_trig else None,
        "precision": n_d100 / n_trig if n_trig else None,
        "strictRealHits": hits, "missedReal": len(real_keys) - hits,
        "waitMin": waits[0] if waits else None,
        "waitMed": med(waits),
        "waitP90": pct(waits, 0.90),
        "waitP99": pct(waits, 0.99),
        "waitMax": waits[-1] if waits else None,
        "nLateGt50": n_late, "nLateGe50": n_late50,
        "lateRate": n_late / n_trig if n_trig else None,
        "extraMax": max(extras) if extras else None,
        "extraMed": med(extras),
        "nNoTrigger": len(all_runs) - n_trig,
    }
    RESULTS.append(res)

out("\n" + "=" * 100)
out("【主表：每档判据的触发数 / 事后误报率 / 真实命中 / 触发等待(ms) / 越过50ms截止数】")
out("=" * 100)
hdr = f"{'id':<18}|{'触发n':>7}|{'误报n':>7}|{'误报率':>8}|{'真实命中':>8}|{'漏':>5}|{'wait中位':>9}|{'waitP90':>9}|{'waitMax':>9}|{'>50ms数':>9}|{'>50占比':>8}"
out(hdr)
out("-" * len(hdr))
for r in RESULTS:
    fr = "N/A" if r["falseRate"] is None else f"{r['falseRate']*100:.2f}%"
    lr = "N/A" if r["lateRate"] is None else f"{r['lateRate']*100:.2f}%"
    out(f"{r['id']:<18}|{r['nTrig']:>7}|{r['nFalse']:>7}|{fr:>8}|{r['strictRealHits']:>8}|{r['missedReal']:>5}|"
        f"{fmt(r['waitMed']):>9}|{fmt(r['waitP90']):>9}|{fmt(r['waitMax']):>9}|{r['nLateGt50']:>9}|{lr:>8}")

out("\n【逐档明细（含 waitMin / P99 / 额外等待 / 未触发游程数）】")
for r in RESULTS:
    out(f"\n  {r['id']}  [{r['family']}]")
    out(f"    rule       : {r['desc']}")
    out(f"    needsHistory: {r['hist']}")
    out(f"    extraWaitNote: {r['extra_note']}")
    out(f"    nTrig={r['nTrig']}  nFalse(d<100ms)={r['nFalse']}  falseRate={fmt(r['falseRate'],4) if r['falseRate'] is not None else 'N/A'}"
        f"  precision={fmt(r['precision'],4) if r['precision'] is not None else 'N/A'}")
    out(f"    strictRealHits={r['strictRealHits']}/1681  missedReal={r['missedReal']}")
    out(f"    waitAfterS_hat(ms): min={fmt(r['waitMin'])} med={fmt(r['waitMed'])} P90={fmt(r['waitP90'])} P99={fmt(r['waitP99'])} max={fmt(r['waitMax'])}")
    out(f"    nTriggersBeyond50ms={r['nLateGt50']}/{r['nTrig']} ({fmt(r['lateRate']*100,2) if r['lateRate'] is not None else 'N/A'}%)  >=50ms含边界={r['nLateGe50']}")
    out(f"    extraWait(ms): med={fmt(r['extraMed'])} max={fmt(r['extraMax'])}")
    out(f"    未触发游程数(含冷启动缺基线)={r['nNoTrigger']}")

# ----------------------------------------------------------------------------
# 5. 起点观测滞后 e 与物理 S 的诚实核算
# ----------------------------------------------------------------------------
out("\n" + "=" * 100)
out("【物理起点 S 的可观测性 · 诚实账】")
out("=" * 100)
og = sorted(r["onset_gap_ms"] for r in all_runs if r["onset_gap_ms"] is not None)
out(f"游程首拍前一采样间隔 e=t[runStart]-t[runStart-1] 有效样本 n={len(og)}（首拍游程 {len(all_runs)-len(og)} 条无前序）")
out(f"  min={fmt(og[0])} med={fmt(med(og))} P95={fmt(pct(og,0.95))} P99={fmt(pct(og,0.99))} max={fmt(og[-1])} ms")
out("  说明：e 是「观测起点滞后上界」的代理量，不是实测物理 S 误差；物理 S 落在 (t[runStart-1], t[runStart]] 内。")
out("  所有 waitAfterS 均以观测首拍 S_hat=t[runStart] 为锚；真实 S 更早，故相对 S 的等待 = waitAfterS_hat + (S_hat-S)，")
out(f"  其中 (S_hat-S) ∈ [0, e]，e 实测中位 {fmt(med(og))}ms、最大 {fmt(og[-1])}ms（最大值为采样掉拍，不证明线程被卡）。")
out("  因此本表 waitAfterS_hat 是「相对物理 S 等待」的下界估计；:177 的 S+50ms 严格核算需物理 S，本次语料不可得。")

out("\n【k 点 = k-1 个间隔 · 名义等待核对】")
for k in (10, 25, 50):
    out(f"  k={k}: 名义 (k-1)*2ms = {(k-1)*2}ms；与题给 D30 的 18/48/98ms 同值")
for r in RESULTS:
    if r["id"] in ("C1-k10", "C1-k25", "C1-k50"):
        out(f"  {r['id']} 语料实测触发等待中位 {fmt(r['waitMed'])}ms / 最大 {fmt(r['waitMax'])}ms（抖动使实测≠名义）")

# ----------------------------------------------------------------------------
# 6. D30 基线复现核对（自跑，不抄文档）
# ----------------------------------------------------------------------------
out("\n" + "=" * 100)
out("【D30 基线自跑复现核对（本探针独立统计，非抄文档）】")
out("=" * 100)
for k in (10, 25, 50):
    tr = [r for r in all_runs if r["npts"] >= k]
    bad = [r for r in tr if r["d_final_ms"] < DCLASS_MS]
    good = [r for r in tr if r["d_final_ms"] >= DCLASS_MS]
    out(f"  k={k}: total={len(tr)} false={len(bad)} d>=100={len(good)} falseRate={len(bad)/len(tr)*100:.2f}%")

out("\n【C4 绝对时长 与 C1 k拍 不等价实证（同一游程两判据触发时刻差）】")
neq = 0
examples = []
for w in window_data.values():
    for r in w["runs"]:
        if r["npts"] >= 10:
            wk, _ = C_k(r, w, 10)
            wa, _ = C_abs(r, w, 20, 3)
            if wa is not None and abs(wk - wa) > 1.0:
                neq += 1
                if len(examples) < 5:
                    examples.append((r["trip"], r["win"], r["i"], round(wk, 3), round(wa, 3)))
out(f"  k=10 与 abs>20ms 在同一游程触发时刻相差>1ms 的游程数 = {neq}")
for e in examples:
    out(f"    {e[0]} {e[1]} runStart={e[2]}: k10_wait={e[3]}ms  abs20_wait={e[4]}ms")

# ----------------------------------------------------------------------------
# 7. 写输出（仅在写域内）
# ----------------------------------------------------------------------------
if not OUTPUT.resolve().is_relative_to(WRITEDIR):
    raise ValueError("output escapes write domain: " + str(OUTPUT))
OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
out(f"\n输出已写：{OUTPUT}")
out("【探针结束 · 零真机 / 零采样代码 / 只读语料】")
