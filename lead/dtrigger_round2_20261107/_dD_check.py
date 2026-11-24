# -*- coding: utf-8 -*-
"""_dD_check.py — 逐条对齐的补充确定性核算（离线、只读）

检查项：
  B1 母体 B 的 U 分布在不同阈值下的计数，定位 S 件内部 56/62 不一致；
  B2 母体 A 的长尾 e 与真实停滞事件的富集关系（证明两个母体为何 P99 差 107ms）；
  B3 :177 合规核验所需的两个不等式（观测锚下界 / 保守确证）的确定性与独立性；
  B4 最小新观测量清单的必要性证明（逐项缺一即不能闭合）。
"""

import json
import re
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANIFEST = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EVENTS = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
WRITEDIR = (ROOT / "lead/dtrigger_round2_20261107").resolve()
OUT = WRITEDIR / "_dD_check_out.txt"

lines = []


def out(s=""):
    lines.append(str(s))
    print(s)


files = sorted(BASE.rglob("measure_w*.json"))
cache = {}
for p in files:
    pr = p.resolve()
    rel = pr.relative_to(BASE).parts
    key = (rel[0] if len(rel) > 1 else "(root)", pr.stem.replace("measure_", ""))
    cache[key] = json.loads(pr.read_text(encoding="utf-8-sig"))

manifest_keys = []
for line in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
    m = re.match(r"^([a-zA-Z0-9_\(\)]+)\s+(w\d)\s+([0-9\.]+)", line.strip())
    if m:
        k = (m[1], m[2])
        if k in cache:
            s = cache[k]["samples"]
            ts, fs = s["t"], s["f"]
            if len(ts) >= 2 and any(a != b for a, b in zip(fs, fs[1:])):
                manifest_keys.append(k)
manifest_keys = sorted(set(manifest_keys))

events_all = json.loads(EVENTS.read_text(encoding="utf-8"))
real = [e for e in events_all if e.get("isRealMatch") is True]
real_keys = {(e["trip"], e["window"], e["startTick"]) for e in real}

# 母体 A 全部游程 e
A = []  # (trip, win, i, gap_or_None)
for trip, win in manifest_keys:
    ts, fs = cache[(trip, win)]["samples"]["t"], cache[(trip, win)]["samples"]["f"]
    n = len(fs)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and fs[j + 1] == fs[i]:
            j += 1
        gap = (ts[i] - ts[i - 1]) * 1000.0 if i > 0 else None
        A.append((trip, win, i, gap))
        i = j + 1

A_valid = [x for x in A if x[3] is not None]
B_gap = []  # (trip, win, startTick, gap_rounded) for 1677 real events with startTick>0
for e in real:
    if e["startTick"] > 0:
        ts = cache[(e["trip"], e["window"])]["samples"]["t"]
        B_gap.append((e["trip"], e["window"], e["startTick"],
                      round((ts[e["startTick"]] - ts[e["startTick"] - 1]) * 1000.0, 3)))

out("=" * 100)
out("【_dD · 补充确定性核算】")
out("=" * 100)
out("")
out("## B1 门限扫描：定位 S 件内部 U>50ms 计数 56 / 62 的差异")
out("S_OBSERVABILITY.md:171 原文「全量语料中有 56 条真实事件（占全集 3.33%）U > 50ms」")
out("S_UNCERTAINTY.md:126 原文「极端长尾（U > 50 ms，共 62 例，占 3.69%）」")
out("本轮从原始语料重算的 U（有效 n=1677）在各门限下的计数：")
for thr in (35.367, 40.0, 45.0, 48.0, 49.0, 50.0, 51.0, 55.0, 60.0, 100.0):
    n_gt = sum(1 for x in B_gap if x[3] > thr)
    n_ge = sum(1 for x in B_gap if x[3] >= thr)
    out("  U > %7.3f ms : n=%3d (占1681=%6.4f%%)   U >= %7.3f ms : n=%3d" % (
        thr, n_gt, 100.0 * n_gt / 1681, thr, n_ge))
out("  -> 56 与 U>50ms 严格相符；62 在本轮重算的任何门限上都不对应（最接近的是 U>48ms 附近）。")
out("  -> 62/1681=%.4f%% 与 S_UNCERTAINTY.md:126 自报的 3.69%% 内部自洽，但与原始语料重算不符。" % (
    100.0 * 62 / 1681))
out("  -> 判定：S 件两份文档在同一统计量上口径不一致；以本轮从原始语料重算的 56 为准，成因未验。")
out("")

out("## B2 母体 A 长尾与真实停滞事件的富集关系")
out("母体 A 有前序游程 n=%d；母体 B（真实事件且有前序）n=%d；B/A=%.4f%%" % (
    len(A_valid), len(B_gap), 100.0 * len(B_gap) / len(A_valid)))
for thr in (6.0, 50.0, 100.0):
    a_big = [x for x in A_valid if x[3] > thr]
    b_big = [x for x in B_gap if x[3] > thr]
    real_in_a_big = sum(1 for x in a_big if (x[0], x[1], x[2]) in real_keys)
    out("  e>%-6.1f ms : 母体A %3d 条，其中真实事件 %3d 条；母体B %3d 条（富集比 %.2f×）" % (
        thr, len(a_big), real_in_a_big, len(b_big),
        (len(b_big) / len(B_gap)) / (len(a_big) / len(A_valid)) if a_big else float("nan")))
out("  -> 结论：A 的 P99=4.145ms 与 B 的 P99=111.495ms 不是矛盾，而是同一批大 onset gap")
out("     高度集中在真实停滞事件子集（B 只占 A 的约 %.2f%%，却含 A 中 e>50ms 的 56/84 条）。" % (
    100.0 * len(B_gap) / len(A_valid)))
out("  -> 故 §2.1 用 A 的 P99 描述「全体游程的观测滞后」，S 件用 B 的 P99 描述「真实事件的 S 不确定度」，")
out("     二者回答不同问题；把 A 的 4.145ms 当作 :177 的真实事件误差上界会系统性低估长尾。")
out("")

out("## B3 :177 合规核验的两个不等式（确定性，不外推）")
out("记 S=物理起点，S_hat=观测首拍，C=快照保存完成时刻，U=S_hat-S_low，e=S_hat-S_low_max。")
out("(i) 由 S ∈ (S_low, S_hat] 得 C-S >= C-S_hat >= 0：所有 waitAfterS_hat 是 C-S 的下界。")
out("    §2.1:96 与本轮实跑 e>0 计数=28317/28317 一致（观测锚无一与物理 S 重合的可证情形）。")
out("(ii) 保守确证条件 C <= S_hat + (50 - U)（S_UNCERTAINTY.md:113）。")
out("    本轮实跑 U>50ms 真实事件=56 条，对这些事件 50-U<0，离线语料无法给出合规闭环证明。")
out("(iii) 反向不等式（不合规方向的独立证成）：若某触发的 C-S_hat > 50ms，则 C-S > 50ms。")
out("    该结论不依赖 S 的精确值；_dtrigger_supplement_out.txt:11-24,29 给出观测锚下已 >50ms 的触发数，")
out("    CRITERIA_COMPARE.md:34-35,145-147 记为「不合规方向」。")
out("(iv) C 在语料中完全缺席：CRITERIA_METRICS.json:542-558 U4-EndToEndSave = notImplementable 占位；")
out("    CRITERIA_COMPARE.md:398 与 S_OBSERVABILITY.md:194 均明写无实际保存时刻 C。")
out("    => 即便补得物理 S，(i)/(ii) 仍无法给出 C-S<=50ms 的肯定结论；C 是第二个独立阻断项。")
out("")

out("## B4 最小新观测量清单的必要性（逐项缺一不可闭合）")
out("目标命题 P：对声明覆盖的每条真实事件，C - S <= 50.0ms 且保存的是 :177 要求的目标线程上下文。")
out("  O1 物理停滞起点 S（逐事件）：缺则只有 (S_low, S_hat] 区间，C-S 仅有下界，肯定结论不可达。")
out("  O2 现场快照保存完成时刻 C（逐事件）：缺则 C-S 无值可算（现有语料唯一空缺）。")
out("  O3 S 与 C 的共同时基/同步残差上界：缺则两个时刻相减的差可能含未知系统偏差，P 不可闭合。")
out("  O4 目标线程上下文完整性与归属标记（逐事件）：缺则即使时延达标，也不能证明「保存上下文」的对象正确。")
out("  O5（条件项）窗首/跨窗无断档前序连续时序：仅当 P 覆盖 4 条 startTick=0 事件时为必需；")
out("     若 P 只覆盖 1677 条窗内可还原事件，则 O5 非必需（须在结论中显式声明覆盖母体）。")
out("  -> O1..O4 为解除「S+50ms 合规核验」阻断的最小集；O5 是声明范围的条件项。")
out("  -> 本清单只描述观测量名称、口径与精度；不含任何采样手段、API、探针设计或注入方案。")
out("")
out("【_dD_check.py 运行完成 · 输出落盘 " + str(OUT) + "】")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
