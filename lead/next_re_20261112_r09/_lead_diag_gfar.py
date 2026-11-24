#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lead 诊断 U-3：W98 `g_far` 两趟差 4.9062 pp 的来源。

两个互斥假设：
  H-A 「干活变多」：同样时间里执行的指令/周期变多 -> cycles/cpu_s 大体不变，cpu 时间变多。
  H-B 「时钟/调度变了」：同一份工作被更慢的时钟执行，或线程被调度走
       -> cycles/cpu_s 显著变化（频率），或 cycles/wall_s 显著变化（占用率）。

判据（不做统计检验，只看逐值）：
  cycles_per_cpu_s = ΣΔwin_cycle / (ΣΔwin_cpu_ms / 1000)     # ~= 有效时钟频率
  cpu_share        = ΣΔwin_cpu_ms / wall_ms                    # 已定义为本项目 rate/100
  cycles_per_wall_s= ΣΔwin_cycle / wall_s

若 g_far_r1 与 r2 的 cycles_per_cpu_s 相差 > ~3 %，H-B（频率）优先；
若两台一致而 cpu_ms 不同，H-A 优先。
"""
from __future__ import annotations

import json
from pathlib import Path

W98 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r08\W98_clean\out")
TRIPS = ["g_idle_r1", "g_idle_r2", "g_near_r1", "g_near_r2", "g_far_r1", "g_far_r2"]


def load(trip):
    rows = []
    with (W98 / f"trip_{trip}" / "run.ndjson").open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("win_cpu_ms") is None or r.get("win_cycle") is None:
                continue
            rows.append(r)
    rows.sort(key=lambda r: int(r["t_perf_ns"]))
    return rows


def main():
    print(f"{'trip':<13}{'wall_s':>8}{'cpu_ms':>12}{'rate%':>9}{'cyc':>16}"
          f"{'MHz*':>9}{'cyc/wall_s':>13}{'fg%':>7}{'tid':>7}")
    agg = {}
    for t in TRIPS:
        rows = load(t)
        t0 = int(rows[0]["t_perf_ns"])
        t1 = int(rows[-1]["t_perf_ns"])
        wall = (t1 - t0) / 1e9
        dcpu = float(rows[-1]["win_cpu_ms"]) - float(rows[0]["win_cpu_ms"])
        dcyc = int(rows[-1]["win_cycle"]) - int(rows[0]["win_cycle"])
        rate = dcpu / (wall * 1000.0) * 100.0
        mhz = dcyc / (dcpu / 1000.0) / 1e6 if dcpu > 0 else float("nan")
        cyw = dcyc / wall if wall > 0 else float("nan")
        fg = sum(1 for r in rows if not r.get("win_foreground", True)) / len(rows) * 100.0
        tid = rows[0].get("win_tid")
        agg[t] = dict(wall=wall, dcpu=dcpu, dcyc=dcyc, rate=rate, mhz=mhz, cyw=cyw, fg=fg)
        print(f"{t:<13}{wall:>8.3f}{dcpu:>12.1f}{rate:>9.4f}{dcyc:>16}{mhz:>9.1f}{cyw:>13.3e}{fg:>7.1f}{str(tid):>7}")

    print("\n" + "=" * 90)
    print("同格两趟对比（找差因）")
    print("=" * 90)
    for cell in ("g_idle", "g_near", "g_far"):
        a, b = agg[f"{cell}_r1"], agg[f"{cell}_r2"]
        drate = b["rate"] - a["rate"]
        dmhz = (b["mhz"] - a["mhz"]) / a["mhz"] * 100.0
        dcyw = (b["cyw"] - a["cyw"]) / a["cyw"] * 100.0
        dcpu = (b["dcpu"] - a["dcpu"]) / a["dcpu"] * 100.0
        print(f"\n[{cell}]  r2 - r1 :  rate {drate:+.4f} pp    cpu_ms {dcpu:+.2f} %")
        print(f"   有效时钟 MHz*: r1={a['mhz']:.1f}  r2={b['mhz']:.1f}   差 {dmhz:+.2f} %")
        print(f"   cyc/wall_s   : r1={a['cyw']:.4e}  r2={b['cyw']:.4e}  差 {dcyw:+.2f} %")
        # 归因分解：rate ≈ (cyc/wall_s) / (MHz*)
        verdict = "H-A 干活变多" if abs(dmhz) < 1.5 else "H-B 时钟/频率差异主导"
        print(f"   => {verdict}（频率差 {dmhz:+.2f} %；占用差 {dcyw:+.2f} %）")


if __name__ == "__main__":
    main()
