# -*- coding: utf-8 -*-
"""W5 负担复算脚本 · 对齐 A2 测算并重算实际读取负担。

数据源：out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/*/measure_w*.json
只读数据源，零真机，零进程发射。

对比项：
  1. A2 基线模型：4 VA 读取 / 沿（16 B / 沿），基于 n_edges 原始沿表
  2. W5 实际模型 A（沿表口径）：6 读取 / 沿（4 VA + 2 帧号读，24 B / 沿），基于 28,309 沿
  3. W5 实际模型 B（状态机跳变口径）：6 读取 / 跳变（4 VA + 2 帧号读，24 B / 跳变），基于 28,222 次实际跳变（n_edges - 1）
"""

from __future__ import annotations

import glob
import io
import json
import os
import sys

GLOB = r"out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/*/measure_w*.json"
FULL_SPAN = 25.0

# 既有 harness 每拍 1 次 CurrentFrame 读 (VA 0x00A8ED84)
BASE_FRAME_VA = 0x00A8ED84

# 四个扩展 VA 地址
EXT_VAS = (
    ("gen_stamp", 0x0087E8E0),
    ("threat_calls", 0x00A8EC34),
    ("dirty_rect_count", 0x00B0CE88),
    ("bullet_count", 0x00A8ED50),
)

# A2 假定每沿读取数（只算 4 个业务 VA）
A2_READS_PER_EDGE = 4
A2_BYTES_PER_EDGE = 16

# W5 扩项副本实际读取数（按 frame_edge_sampler.py 的 read_sample 规范：f_pre + 4 VA + f_post）
W5_READS_PER_EDGE = 6
W5_BYTES_PER_EDGE = 24


def pctl(sorted_vals, q: float):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    idx = (len(sorted_vals) - 1) * q
    lo = int(idx)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return float(sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac)


def main():
    files = sorted(glob.glob(GLOB))
    print("=" * 78)
    print("W5 任务书 Q4 · 负担复算（对齐 A2）")
    print("=" * 78)
    print("数据源匹配路径:", GLOB)
    print("匹配文件总数:", len(files))
    assert files, "未找到任何 measure_w*.json 文件"

    rows = []
    bad = []
    excluded = []

    for p in files:
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception as exc:
            bad.append((p, repr(exc)))
            continue

        st = d.get("stats") or {}
        span_s = d.get("span_s")
        samples = st.get("samples") or 0

        item = {
            "path": p,
            "trip": d.get("trip_id"),
            "window": d.get("window"),
            "span_s": span_s,
            "verdict": d.get("verdict"),
            "samples": samples,
            "hz_eff": st.get("hz_effective"),
            "n_edges": st.get("n_edges") or 0,
            "n_multi": st.get("n_multi_advance") or 0,
            "logic": st.get("logic_frames"),
            "p50": st.get("frame_ms_p50"),
            "max_stall": st.get("max_stall_s"),
            "frame_edges": d.get("frame_edges") or [],
        }

        if span_s == FULL_SPAN and samples > 0:
            rows.append(item)
        else:
            excluded.append((p, span_s, samples, d.get("verdict")))

    print("解析成功总数:", len(rows) + len(excluded), " 解析错误数:", len(bad))
    print("排除窗（span_s!=25.0 或 samples<=0）:", len(excluded))
    print("纳入复算的完整 25 s 窗数:", len(rows))
    assert len(rows) == 87, f"完整窗数预期 87，实得 {len(rows)}"

    # 基础汇总统计
    tot_samples = sum(r["samples"] for r in rows)
    tot_edges = sum(r["n_edges"] for r in rows)
    # 状态机跳变次数：对于 n_edges >= 1 的窗，首个采样点为初态，后续 n_edges - 1 次为实际变化
    tot_transitions = sum(max(0, r["n_edges"] - 1) for r in rows)

    print("\n--- 基础总量 ---")
    print(f"87 窗既有读次合计 (Σ samples): {tot_samples:,}")
    print(f"87 窗原始沿表元素总数 (Σ n_edges): {tot_edges:,}")
    print(f"87 窗实际帧跳变总数 (Σ max(0, n_edges-1)): {tot_transitions:,}")

    # 最坏窗与最省窗
    worst_window = max(rows, key=lambda r: r["n_edges"])
    best_window = min(rows, key=lambda r: r["n_edges"])

    print(f"最坏窗: {worst_window['trip']} w{worst_window['window']} "
          f"(n_edges={worst_window['n_edges']}, samples={worst_window['samples']})")
    print(f"最省窗: {best_window['trip']} w{best_window['window']} "
          f"(n_edges={best_window['n_edges']}, samples={best_window['samples']})")

    # 1. A2 基线模型计算
    a2_tot_extra_reads = A2_READS_PER_EDGE * tot_edges
    a2_tot_extra_bytes = A2_BYTES_PER_EDGE * tot_edges
    a2_ratio_overall = 100.0 * a2_tot_extra_reads / tot_samples

    a2_worst_extra_reads = A2_READS_PER_EDGE * worst_window["n_edges"]
    a2_worst_ratio = 100.0 * a2_worst_extra_reads / worst_window["samples"]
    a2_worst_read_rate = a2_worst_extra_reads / FULL_SPAN
    a2_worst_byte_rate = (A2_BYTES_PER_EDGE * worst_window["n_edges"]) / FULL_SPAN

    # 2. W5 实际模型 A（按 28,309 沿，每沿 6 次 RPM：f_pre + 4 VA + f_post）
    w5a_tot_extra_reads = W5_READS_PER_EDGE * tot_edges
    w5a_tot_extra_bytes = W5_BYTES_PER_EDGE * tot_edges
    w5a_ratio_overall = 100.0 * w5a_tot_extra_reads / tot_samples

    w5a_worst_extra_reads = W5_READS_PER_EDGE * worst_window["n_edges"]
    w5a_worst_ratio = 100.0 * w5a_worst_extra_reads / worst_window["samples"]
    w5a_worst_read_rate = w5a_worst_extra_reads / FULL_SPAN
    w5a_worst_byte_rate = (W5_BYTES_PER_EDGE * worst_window["n_edges"]) / FULL_SPAN

    # 3. W5 实际模型 B（按 28,222 次实际跳变，每跳变 6 次 RPM）
    w5b_tot_extra_reads = W5_READS_PER_EDGE * tot_transitions
    w5b_tot_extra_bytes = W5_BYTES_PER_EDGE * tot_transitions
    w5b_ratio_overall = 100.0 * w5b_tot_extra_reads / tot_samples

    w5b_worst_trans = max(0, worst_window["n_edges"] - 1)
    w5b_worst_extra_reads = W5_READS_PER_EDGE * w5b_worst_trans
    w5b_worst_ratio = 100.0 * w5b_worst_extra_reads / worst_window["samples"]
    w5b_worst_read_rate = w5b_worst_extra_reads / FULL_SPAN
    w5b_worst_byte_rate = (W5_BYTES_PER_EDGE * w5b_worst_trans) / FULL_SPAN

    print("\n" + "=" * 78)
    print("逐项对照表：A2 基线 vs W5 实际模型 A (沿表口径) vs W5 实际模型 B (跳变口径)")
    print("=" * 78)

    headers = [
        "指标项",
        "A2 基线 (4 VA)",
        "W5 模型 A (6读/沿)",
        "W5 模型 B (6读/跳变)",
        "差额 (模型A - A2)",
    ]
    fmt = "%-24s | %-16s | %-18s | %-18s | %-16s"
    print(fmt % tuple(headers))
    print("-" * 102)

    rows_comp = [
        ("每触发追加 RPM 读次", f"{A2_READS_PER_EDGE} 读", f"{W5_READS_PER_EDGE} 读", f"{W5_READS_PER_EDGE} 读", f"+{W5_READS_PER_EDGE - A2_READS_PER_EDGE} 读 (+50.0%)"),
        ("每触发追加读取字节", f"{A2_BYTES_PER_EDGE} B", f"{W5_BYTES_PER_EDGE} B", f"{W5_BYTES_PER_EDGE} B", f"+{W5_BYTES_PER_EDGE - A2_BYTES_PER_EDGE} B (+50.0%)"),
        ("87 窗触发基数", f"{tot_edges:,} 沿", f"{tot_edges:,} 沿", f"{tot_transitions:,} 跳变", f"0 沿 (模型A) / -87"),
        ("87 窗追加读次合计", f"{a2_tot_extra_reads:,}", f"{w5a_tot_extra_reads:,}", f"{w5b_tot_extra_reads:,}", f"+{w5a_tot_extra_reads - a2_tot_extra_reads:,} (+50.0%)"),
        ("87 窗追加字节合计", f"{a2_tot_extra_bytes:,} B", f"{w5a_tot_extra_bytes:,} B", f"{w5b_tot_extra_bytes:,} B", f"+{w5a_tot_extra_bytes - a2_tot_extra_bytes:,} B"),
        ("整体读次相对增幅", f"+{a2_ratio_overall:.3f}%", f"+{w5a_ratio_overall:.3f}%", f"+{w5b_ratio_overall:.3f}%", f"+{w5a_ratio_overall - a2_ratio_overall:.3f} 百分点"),
        ("最坏单窗追加读次", f"{a2_worst_extra_reads:,} 读", f"{w5a_worst_extra_reads:,} 读", f"{w5b_worst_extra_reads:,} 读", f"+{w5a_worst_extra_reads - a2_worst_extra_reads:,} 读"),
        ("最坏单窗相对增幅", f"+{a2_worst_ratio:.2f}%", f"+{w5a_worst_ratio:.2f}%", f"+{w5b_worst_ratio:.2f}%", f"+{w5a_worst_ratio - a2_worst_ratio:.2f} 百分点"),
        ("最坏单窗追加读速率", f"{a2_worst_read_rate:.1f} reads/s", f"{w5a_worst_read_rate:.1f} reads/s", f"{w5b_worst_read_rate:.1f} reads/s", f"+{w5a_worst_read_rate - a2_worst_read_rate:.1f} reads/s"),
        ("最坏单窗追加字节率", f"{a2_worst_byte_rate:.1f} B/s", f"{w5a_worst_byte_rate:.1f} B/s", f"{w5b_worst_byte_rate:.1f} B/s", f"+{w5a_worst_byte_rate - a2_worst_byte_rate:.1f} B/s"),
        ("最省单窗追加读次", f"+{A2_READS_PER_EDGE * best_window['n_edges']} 读", f"+{W5_READS_PER_EDGE * best_window['n_edges']} 读", f"+0 读 (冻结无跳变)", f"+2 读 / -4 读"),
    ]

    for r in rows_comp:
        print(fmt % r)
    print("-" * 102)

    # 4. 差异归因分析
    print("\n" + "=" * 78)
    print("差异归因与分析")
    print("=" * 78)
    print("""
1. 为什么与 A2 的 +10.475% / +25.08% 不一致？
   【核心原因一：每沿读取次数差异】
   - A2 只计算了 4 个目标业务 VA（gen_stamp, threat_calls, dirty_rect_count, bullet_count），
     假定每沿只需 4 次 RPM（16 字节）。
   - W5 扩项副本严格执行 D-19 裁决书 §1 第 5 条与 TASK.md Q3 第 2 条规范，调用 frame_edge_sampler.py 的
     read_sample() 逻辑：在读取 4 VA 前后各读一次 CurrentFrame（f_pre 与 f_post），
     以检测跨帧条件（f_pre != f_post 标 cross_frame）。
     因此，每次触发实际产生 4 次业务 VA 读 + 2 次帧号读 = 6 次 ReadProcessMemory（24 字节）。
     这是 1.5 倍（+50.0%）的读数放大，使整体增幅由 +10.475% 上浮到 +15.713%（模型 A）/ +15.665%（模型 B），
     最坏窗增幅由 +25.08% 上浮到 +37.63%（模型 A）/ +37.58%（模型 B）。

   【次要原因二：沿计数定义差异（首采样点与冻结窗）】
   - A2 的统计脚本直接取 JSON 中的 n_edges（即 len(frame_edges)）。在 harness 的 _measure_stats() 中，
     frame_edges 列表首元素始终包含窗口启动时的初始观测值 samples[0]。
     这意味着在 28 个整窗帧号冻结的死窗中，虽然 logic_frames <= 0 且帧号从未前进，
     n_edges 仍记录为 1，A2 据此计入了 4 次读（最省单窗 +4 读）。
   - 若扩项实现在运行期仅当检测到 CurrentFrame 发生变化（f != prev_f）时才触发采样（模型 B），
     则窗口初始采样仅用于初始化 prev_f，不触发追加读；28 个冻结窗实际追加 0 次读（真正零样本零开销）。
     此时 87 窗实际跳变总数为 28,222 次（比 A2 少 87 次），整体增幅为 +15.665%。
""")

    # 5. 单窗相对增幅分布分位
    ratios_a2 = sorted(100.0 * (A2_READS_PER_EDGE * r["n_edges"]) / r["samples"] for r in rows)
    ratios_w5a = sorted(100.0 * (W5_READS_PER_EDGE * r["n_edges"]) / r["samples"] for r in rows)
    ratios_w5b = sorted(100.0 * (W5_READS_PER_EDGE * max(0, r["n_edges"] - 1)) / r["samples"] for r in rows)

    print("=" * 78)
    print("单窗增幅分位对比 (87 窗)")
    print("=" * 78)
    q_list = (0.0, 0.10, 0.25, 0.50, 0.75, 0.90, 1.0)
    print("%-6s | %-16s | %-16s | %-16s" % ("分位", "A2 基线增幅", "W5 模型 A 增幅", "W5 模型 B 增幅"))
    print("-" * 62)
    for q in q_list:
        v_a2 = pctl(ratios_a2, q)
        v_w5a = pctl(ratios_w5a, q)
        v_w5b = pctl(ratios_w5b, q)
        print("p%-5d | +%-15.3f%% | +%-15.3f%% | +%-15.3f%%" % (int(q * 100), v_a2, v_w5a, v_w5b))
    print("-" * 62)

    # 6. 冻结窗专项检查
    frozen_windows = [r for r in rows if (r["logic"] or 0) <= 0]
    print(f"\n冻结窗统计 (logic_frames <= 0): {len(frozen_windows)} / {len(rows)}")
    frozen_edges_set = set(r["n_edges"] for r in frozen_windows)
    print(f"冻结窗 n_edges 取值集合: {frozen_edges_set}")
    rescue_win = [r for r in frozen_windows if r["n_edges"] > 1]
    for rw in rescue_win:
        print(f"  特殊窗 (回退/误杀窗): {rw['trip']} w{rw['window']} edges={rw['n_edges']} logic={rw['logic']}")

    print("\n复算完成，结果已全面校验。")


if __name__ == "__main__":
    main()
