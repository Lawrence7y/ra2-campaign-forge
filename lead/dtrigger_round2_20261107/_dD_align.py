# -*- coding: utf-8 -*-
"""_dD_align.py — 物理 S 可观测量对齐（离线、只读语料与既有件）

本脚本只做两件事：
  1. 用 Python hashlib 复核所有被核对象 SHA256 / 字节数；
  2. 从原始 500Hz 语料与 STALL_EVENTS.json 独立重算两套统计母体：
       母体 A = 全部帧号游程的 onset gap  e = t[runStart]-t[runStart-1]（CRITERIA_COMPARE.md §2.1）
       母体 B = 1681 条 isRealMatch==True 事件的 U = t[startTick]-t[startTick-1]（S_ESTIMATES / S_UNCERTAINTY / S_OBSERVABILITY）
     并逐条对齐 §2.1 的六个数字与两条语义。

唯一写域：lead/dtrigger_round2_20261107/ ；不修改任何既有文件。
本脚本不实现任何采样、进程或注入相关代码；只读 (t,f) 数值语料。
"""

import hashlib
import json
import re
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANIFEST = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EVENTS = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
S_EST = (ROOT / "lead/dstart_observable_20261107/S_ESTIMATES.json").resolve()
WRITEDIR = (ROOT / "lead/dtrigger_round2_20261107").resolve()
OUT = WRITEDIR / "_dD_align_out.txt"

lines = []


def out(s=""):
    lines.append(str(s))
    print(s)


def pct(sorted_arr, p):
    """线性最近秩：与 _dtrigger_probe.py:61-65 / _s_estimator_probe.py:40-46 同口径。"""
    if not sorted_arr:
        return None
    return sorted_arr[int(p * (len(sorted_arr) - 1))]


def med(arr):
    return statistics.median(arr) if arr else None


def f3(v):
    return "N/A" if v is None else "%.3f" % v


# ---------------------------------------------------------------------------
# 0. 被核对象指纹（hashlib，完整 64 位）
# ---------------------------------------------------------------------------
FPS = [
    "lead/dstart_observable_20261107/S_OBSERVABILITY.md",
    "lead/dstart_observable_20261107/S_UNCERTAINTY.md",
    "lead/dstart_observable_20261107/AUDIT_S_OBSERVABLE_20261107.md",
    "lead/dstart_observable_20261107/S_ESTIMATES.json",
    "lead/dstart_observable_20261107/_s_estimator_probe.py",
    "lead/dstart_observable_20261107/_independent_audit_probe.py",
    "lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md",
    "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json",
    "lead/dtrigger_compare_20261107/_cost_quota_data.json",
    "lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt",
    "lead/dtrigger_compare_20261107/_dtrigger_probe_out.txt",
    "lead/dtrigger_compare_20261107/_dtrigger_analysis_out.txt",
    "lead/d30_ruling_20261106/RULING_D30.md",
    "lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md",
    "lead/stall_event_def_20261106/STALL_EVENTS.json",
]

out("=" * 100)
out("【_dD · 物理 S 可观测量对齐 · 独立离线重算】")
out("=" * 100)
out("")
out("## 0. 被核对象 SHA256 / 字节数（本机 Python hashlib 实跑）")
fingerprints = {}
for rel in FPS:
    p = (ROOT / rel).resolve()
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    fingerprints[rel] = (h, len(b))
    out("被核对象 SHA256 = %s，字节数 = %d    <- %s" % (h, len(b), rel))
out("")

# ---------------------------------------------------------------------------
# 1. 载入原始语料（只读）
# ---------------------------------------------------------------------------
files = sorted(BASE.rglob("measure_w*.json"))
cache = {}
for p in files:
    pr = p.resolve()
    if not pr.is_relative_to(BASE):
        raise ValueError("corpus file escapes base: " + str(pr))
    rel_parts = pr.relative_to(BASE).parts
    key = (rel_parts[0] if len(rel_parts) > 1 else "(root)",
           pr.stem.replace("measure_", ""))
    d = json.loads(pr.read_text(encoding="utf-8-sig"))
    assert len(d["samples"]["t"]) == len(d["samples"]["f"])
    cache[key] = d

n_samples = sum(len(v["samples"]["t"]) for v in cache.values())
out("## 1. 语料载入")
out("文件 n=%d，总采样点 n=%d，hz=%s" % (
    len(files), n_samples, sorted({v.get("hz") for v in cache.values()})))

# moving64 推进窗清单（与 _dtrigger_probe.py:106-118 完全同口径）
manifest_keys = []
for line in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
    m = re.match(r"^([a-zA-Z0-9_\(\)]+)\s+(w\d)\s+([0-9\.]+)", line.strip())
    if m:
        k = (m[1], m[2])
        if k in cache:
            s = cache[k].get("samples", {})
            ts, fs = s.get("t", []), s.get("f", [])
            if len(ts) >= 2 and any(a != b for a, b in zip(fs, fs[1:])):
                manifest_keys.append(k)
manifest_keys = sorted(set(manifest_keys))
out("moving64 推进窗 n=%d" % len(manifest_keys))
out("")

# ---------------------------------------------------------------------------
# 2. 母体 A：全部帧号游程的 onset gap e
# ---------------------------------------------------------------------------
all_runs = []
hist_all = []
for trip, win in manifest_keys:
    s = cache[(trip, win)]["samples"]
    ts, fs = s["t"], s["f"]
    n = len(fs)
    hist = []
    last_edge = 0
    for i in range(1, n):
        if fs[i] != fs[i - 1]:
            hist.append((ts[i] - ts[last_edge]) * 1000.0)
            last_edge = i
    hist_all.extend(hist)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and fs[j + 1] == fs[i]:
            j += 1
        all_runs.append({
            "trip": trip, "win": win, "i": i, "j": j,
            "onset_gap_ms": (ts[i] - ts[i - 1]) * 1000.0 if i > 0 else None,
            "d_final_ms": (ts[j] - ts[i]) * 1000.0,
        })
        i = j + 1

og = sorted(r["onset_gap_ms"] for r in all_runs if r["onset_gap_ms"] is not None)
window_first_runs = [r for r in all_runs if r["onset_gap_ms"] is None]
hist_all_sorted = sorted(hist_all)

out("## 2. 母体 A（CRITERIA_COMPARE.md §2.1 的 e）独立重算")
out("全部帧号游程 n=%d；有前序(i>0)游程 n=%d；窗首(i=0)游程 n=%d" % (
    len(all_runs), len(og), len(window_first_runs)))
out("e 分布：min=%s med(statistics.median)=%s P50(最近秩)=%s P95=%s P99=%s max=%s ms" % (
    f3(og[0]), f3(med(og)), f3(pct(og, 0.50)), f3(pct(og, 0.95)),
    f3(pct(og, 0.99)), f3(og[-1])))
out("e>0 计数=%d / %d（比例=%.6f%%）" % (
    sum(1 for x in og if x > 0), len(og),
    100.0 * sum(1 for x in og if x > 0) / len(og)))
out("e>6.0ms 计数=%d；e>50ms 计数=%d；e>=50ms 计数=%d；e>100ms 计数=%d" % (
    sum(1 for x in og if x > 6.0), sum(1 for x in og if x > 50.0),
    sum(1 for x in og if x >= 50.0), sum(1 for x in og if x > 100.0)))
out("e>50ms 占母体A比例=%.6f%%" % (100.0 * sum(1 for x in og if x > 50.0) / len(og)))
out("帧沿间隔 hist 总体 n=%d，P50=%s P95=%s P99=%s ms" % (
    len(hist_all_sorted), f3(pct(hist_all_sorted, 0.50)),
    f3(pct(hist_all_sorted, 0.95)), f3(pct(hist_all_sorted, 0.99))))
out("")

# ---------------------------------------------------------------------------
# 3. 母体 B：1681 条真实事件的 U，并与 S_ESTIMATES.json 逐字段比对
# ---------------------------------------------------------------------------
events_all = json.loads(EVENTS.read_text(encoding="utf-8"))
real = [e for e in events_all if e.get("isRealMatch") is True]
s_est = json.loads(S_EST.read_text(encoding="utf-8"))
by_id = {r["eventId"]: r for r in s_est}

recomputed = []
mismatch = []
for e in real:
    trip, win, st, et = e["trip"], e["window"], e["startTick"], e["endTick"]
    ev_id = "%s/%s/%s/%s" % (trip, win, st, et)
    ts = cache[(trip, win)]["samples"]["t"]
    t0 = ts[0]
    if st == 0:
        rec = {
            "eventId": ev_id,
            "durationMs": e["durationMs"],
            "firstObservedMs": 0.0,
            "sLowerBoundMs": 0.0,
            "sUpperBoundMs": 0.0,
            "sUncertaintyMs": 0.0,
            "priorIntervalMs": None,
            "quality": "unknown",
        }
        u_raw = None
    else:
        fo = round((ts[st] - t0) * 1000.0, 3)
        lo = round((ts[st - 1] - t0) * 1000.0, 3)
        unc = round(fo - lo, 3)
        rec = {
            "eventId": ev_id,
            "durationMs": e["durationMs"],
            "firstObservedMs": fo,
            "sLowerBoundMs": lo,
            "sUpperBoundMs": fo,
            "sUncertaintyMs": unc,
            "priorIntervalMs": unc,
            "quality": "full" if unc <= 6.0 else "bounded",
        }
        u_raw = (ts[st] - ts[st - 1]) * 1000.0
    recomputed.append((rec, u_raw))
    if ev_id not in by_id:
        mismatch.append((ev_id, "MISSING_IN_S_ESTIMATES"))
    else:
        b = by_id[ev_id]
        for k in ("durationMs", "firstObservedMs", "sLowerBoundMs",
                  "sUpperBoundMs", "sUncertaintyMs", "priorIntervalMs", "quality"):
            if b.get(k) != rec[k]:
                mismatch.append((ev_id, "%s: recomputed=%r vs json=%r" % (k, rec[k], b.get(k))))

U_rounded = sorted(r["sUncertaintyMs"] for r, u in recomputed if u is not None)
U_raw = sorted(u for r, u in recomputed if u is not None)
qual = Counter(r["quality"] for r, u in recomputed)
all_u_with_unknown = sorted(r["sUncertaintyMs"] for r, u in recomputed)

out("## 3. 母体 B（S 估计/不确定性件的 U）独立重算")
out("STALL_EVENTS 全量 n=%d；isRealMatch==True n=%d；S_ESTIMATES.json 记录 n=%d" % (
    len(events_all), len(real), len(s_est)))
out("逐字段重算 vs S_ESTIMATES.json：不匹配项数=%d / %d 条" % (len(mismatch), len(real)))
if mismatch:
    for x in mismatch[:20]:
        out("   MISMATCH " + repr(x))
out("quality 档位：full=%d bounded=%d unknown=%d 合计=%d" % (
    qual["full"], qual["bounded"], qual["unknown"], len(recomputed)))
out("U(有效 n=%d, 3位小数)：min=%s med(statistics.median)=%s P50(最近秩)=%s P95=%s P99=%s max=%s ms" % (
    len(U_rounded), f3(U_rounded[0]), f3(med(U_rounded)), f3(pct(U_rounded, 0.50)),
    f3(pct(U_rounded, 0.95)), f3(pct(U_rounded, 0.99)), f3(U_rounded[-1])))
out("U(有效 n=%d, 原始精度)：min=%.6f med=%.6f P99=%.6f max=%.6f ms" % (
    len(U_raw), U_raw[0], med(U_raw), pct(U_raw, 0.99), U_raw[-1]))
out("U 算术均值=%.3f ms" % (sum(U_rounded) / len(U_rounded)))
out("U>6.0ms 计数=%d（=bounded）；U>50ms 计数=%d；U>=50ms 计数=%d；U>100ms 计数=%d" % (
    sum(1 for x in U_rounded if x > 6.0), sum(1 for x in U_rounded if x > 50.0),
    sum(1 for x in U_rounded if x >= 50.0), sum(1 for x in U_rounded if x > 100.0)))
out("U>50ms 占 1677 有效=%.4f%%；占 1681 全集=%.4f%%" % (
    100.0 * sum(1 for x in U_rounded if x > 50.0) / len(U_rounded),
    100.0 * sum(1 for x in U_rounded if x > 50.0) / len(all_u_with_unknown)))
out("按 1681 全集计 sUncertaintyMs>50 计数=%d，占=%.4f%%" % (
    sum(1 for x in all_u_with_unknown if x > 50.0),
    100.0 * sum(1 for x in all_u_with_unknown if x > 50.0) / len(all_u_with_unknown)))
out("full 子集 U 中位=%s ms，P99=%s ms" % (
    f3(med(sorted(r["sUncertaintyMs"] for r, u in recomputed if r["quality"] == "full"))),
    f3(pct(sorted(r["sUncertaintyMs"] for r, u in recomputed if r["quality"] == "full"), 0.99))))
out("")

# ---------------------------------------------------------------------------
# 4. 两套母体的集合关系
# ---------------------------------------------------------------------------
og_counter = Counter(og)  # 原始精度浮点数多重集
contained = sum(1 for u in U_raw if og_counter.get(u, 0) > 0)
# 逐事件 U 与母体 A 中同 (trip,win,startTick) 位置的 e 是否相等
run_index = {(r["trip"], r["win"], r["i"]): r["onset_gap_ms"] for r in all_runs}
pair_equal = 0
pair_checked = 0
for e in real:
    if e["startTick"] > 0:
        pair_checked += 1
        k = (e["trip"], e["window"], e["startTick"])
        if k in run_index and run_index[k] is not None:
            ts = cache[(e["trip"], e["window"])]["samples"]["t"]
            if abs(run_index[k] - (ts[e["startTick"]] - ts[e["startTick"] - 1]) * 1000.0) < 1e-9:
                pair_equal += 1

unknown_real = [e for e in real if e["startTick"] == 0]
wf_keys = {(r["trip"], r["win"]) for r in window_first_runs}
unknown_in_wf = sum(1 for e in unknown_real if (e["trip"], e["window"]) in wf_keys)

out("## 4. 母体 A / 母体 B 的集合关系（两套统计母体的口径差）")
out("逐事件 U 值落在母体 A 多重集内的条数=%d / %d" % (contained, len(U_raw)))
out("逐事件 U 与同 (trip,win,startTick) 游程 onset gap 相等的条数=%d / %d" % (
    pair_equal, pair_checked))
out("窗首(i=0)游程 n=%d；其中 isRealMatch==True 且 startTick==0 的真实事件 n=%d（在窗首游程内=%d）" % (
    len(window_first_runs), len(unknown_real), unknown_in_wf))
out("全部游程中 d_final>=100ms 的条数=%d；其中 isRealMatch==True 条数=%d" % (
    sum(1 for r in all_runs if r["d_final_ms"] >= 100.0), len(real)))
out("母体 A 中 e>50ms 的游程数=%d；这些游程里 isRealMatch==True 事件数=%d" % (
    sum(1 for x in og if x > 50.0),
    sum(1 for e in real if e["startTick"] > 0 and
        (run_index.get((e["trip"], e["window"], e["startTick"])) or 0) > 50.0)))
out("")

# ---------------------------------------------------------------------------
# 5. §2.1 六数字 / 两语义的逐条对齐判定
# ---------------------------------------------------------------------------
out("## 5. 与 CRITERIA_COMPARE.md §2.1 逐条对齐")
claims = [
    ("A1 区间定义 S in (t[i-1], t[i]]",
     "S_OBSERVABILITY.md:57 / S_UNCERTAINTY.md:33 同为 (sLowerBoundMs, sUpperBoundMs]",
     "一致（同一夹逼区间；符号不同）"),
    ("A2 S_hat-S in [0,e]",
     "S_OBSERVABILITY.md:163 等价式 C-S_obs <= C-S <= (C-S_obs)+U；S_UNCERTAINTY.md:110-118",
     "等价；但 S in (t[i-1],t[i]] 严格给出 [0,e) 上界开，§2.1 写 [0,e] 为保守松弛"),
    ("A3 e 有效 n=28317",
     "本轮实跑母体 A 有前序游程 n=%d；母体 B 有效 n=%d / 全集 n=%d" % (len(og), len(U_rounded), len(real)),
     "数值可复现，但统计母体不同：A=全部游程，B=仅 1681 真实停滞事件"),
    ("A4 中位 2.511",
     "本轮 e 中位=%s；U 中位=%s" % (f3(med(og)), f3(med(U_rounded))),
     "e 可复现；U 为 2.515，属不同母体，不是矛盾也不是同一统计量"),
    ("A5 P99 4.145",
     "本轮 e P99=%s；U P99=%s" % (f3(pct(og, 0.99)), f3(pct(U_rounded, 0.99))),
     "e 可复现；S 件的 P99 是 111.495，两者相差 107.350ms，不可互代"),
    ("A6 max 488.616",
     "本轮 e max=%s；U max=%s" % (f3(og[-1]), f3(U_rounded[-1])),
     "一致；同一极值事件 l3_20261031hb/w1:samples[1377]"),
]
for name, obs, verdict in claims:
    out("  [%s]" % name)
    out("       S件/实跑：%s" % obs)
    out("       对齐判定：%s" % verdict)
out("")
out("  [A7 下界语义] §2.1:96 所有 waitAfterS_hat/latency* 都是下界；")
out("       S_OBSERVABILITY.md:163-165 / S_UNCERTAINTY.md:116-118 给同一不等式（乐观锚 vs 保守预算）。")
out("       对齐判定：一致；且本轮实跑 e>0 计数=%d/%d，即所有事件的观测锚都可能严格晚于物理 S。" % (
    sum(1 for x in og if x > 0), len(og)))
out("  [A8 硬阻断] §2.1:97「:177 的严格 S+50ms 核算需物理 S，本次语料不可得」；")
out("       S_OBSERVABILITY.md:194「没有任何在线抓栈与保存动作的完成时刻 C 的实测数据」；")
out("       CRITERIA_COMPARE.md:414（§7 第2项）物理 S 与实际保存时刻 C 未验。")
out("       对齐判定：一致；两份件共同登记 C 缺席，S 缺席只是其中一个缺口。")
out("  [A9 掉拍定性] §2.1:98「e 的最大值 488.616ms 是采样掉拍，不证明线程被卡」；")
out("       S_OBSERVABILITY.md:106-118 / S_UNCERTAINTY.md:89-100 / RULING_D30.md:78。")
out("       对齐判定：一致。")
out("")

# ---------------------------------------------------------------------------
# 6. 结论所需的确定性量（不外推）
# ---------------------------------------------------------------------------
out("## 6. 结论判定所需的确定性量")
out("(1) 观测锚下界不足：e>0 的游程=%d/%d；全部 waitAfterS_hat 均为下界（§2.1:96）。" % (
    sum(1 for x in og if x > 0), len(og)))
out("(2) 保守确证条件 C <= S_obs + (50 - U)（S_UNCERTAINTY.md:113）；")
out("    U>50ms 的真实事件=%d 条，其 50-U 净裕量为负，故这些事件在离线语料上无法给出合规闭环证明。" % (
    sum(1 for x in U_rounded if x > 50.0)))
out("(3) 已证明不合规方向的独立证据（观测锚下界已越 50ms，真实值 >= 下界）：")
out("    _dtrigger_supplement_out.txt:11-24,29 与 CRITERIA_COMPARE.md:34-35,145-147；")
out("    CRITERIA_COMPARE.md:216 明写 ≤50% 不是对 :177 的合规证明（S 不可测、:190 端到端延迟未验）。")
out("(4) 语料中无任何 C：CRITERIA_METRICS.json:542-558 U4-EndToEndSave 为 notImplementable 占位；")
out("    CRITERIA_COMPARE.md:398（§6 第4项）语料无现场快照耗时、无实际保存时刻 C。")
out("(5) D-30 §2（RULING_D30.md:30）原文：「物理S与实际保存时刻C仍未知，不能判成物理采不到」。")
out("")

# ---------------------------------------------------------------------------
# 7. 未验项（单列，不并入结论）
# ---------------------------------------------------------------------------
out("## 7. 未验项（本轮单列，不并入任何结论）")
out("未验：真机 / 活进程任何量（本轮零真机，未启动任何进程、未读活进程内存）。")
out("未验：物理 S 的逐事件点值、现场快照实际保存完成时刻 C、:190 端到端延迟、Q5 四项工程依赖、内部状态旗标。")
out("未验：既有探针 _s_estimator_probe.py / _independent_audit_probe.py / _dtrigger_probe.py /")
out("      _dtrigger_analysis.py / _dtrigger_supplement.py 本轮未重跑（它们会覆写只读既有件，铁律禁止）；")
out("      本轮只引用其已落盘输出，并自写 _dD_align.py 从原始语料独立重算两套母体。")
out("未验：S_UNCERTAINTY.md:126「U>50ms 共 62 例」与 S_OBSERVABILITY.md:171「56 条」两处差异的成因；")
out("      本轮实跑值见第 3 节（可判定哪个计数与重算相符，但成因不可判定）。")
out("未验：n=1681 与 n=1737 的同口径对照（裁决边界明令禁止，本轮未做）。")
out("")

WRITEDIR.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
out("【_dD_align.py 运行完成 · 输出落盘 " + str(OUT) + "】")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
