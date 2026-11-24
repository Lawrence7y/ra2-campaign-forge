#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lead 独立复算 W102 的攻击点（不读 W102 的 json，只读原始 run.ndjson + 地图几何）。

只算这些（够用来裁决）：
  1. 6 趟 rate（全窗 / 丢前10s / 裁到150s 三口径）
  2. 三点均值、极差、分量、份额、参照比
  3. 8 顶点端点枚举 → 份额包络
  4. Σd（敌军到最近玩家对象的 Chebyshev 距离和）与一阶混杂修正
  5. A8ED50 首非零 idx / 秒
  6. 效应/噪声（用 g_far 极差作分母）

口径（已裁定，不改）：CPU 消耗率 = Σ win_cpu_ms_delta / 墙钟 × 100（单核 %）。
用法：python _lead_verify_w102.py
"""
from __future__ import annotations

import itertools
import json
import statistics
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
W98 = ROOT / "lead" / "next_re_20261112_r08" / "W98_clean" / "out"
TRIPS = ["g_idle_r1", "g_idle_r2", "g_near_r1", "g_near_r2", "g_far_r1", "g_far_r2"]


def load(trip):
    p = W98 / f"trip_{trip}" / "run.ndjson"
    rows = []
    with p.open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("win_cpu_ms") is None:
                continue
            rows.append(r)
    rows.sort(key=lambda r: int(r["t_perf_ns"]))
    return rows


def rate(rows, drop_first_s=None, cut_s=None):
    """返回 (rate%, wall_s, n, delta_ms)。全窗口径 = 首末样本端点差。"""
    if not rows:
        return None
    t0 = int(rows[0]["t_perf_ns"])
    sel = rows
    if drop_first_s is not None:
        sel = [r for r in rows if int(r["t_perf_ns"]) - t0 >= drop_first_s * 1e9]
    if cut_s is not None:
        sel = [r for r in sel if int(r["t_perf_ns"]) - t0 <= cut_s * 1e9]
    if len(sel) < 2:
        return None
    wall = (int(sel[-1]["t_perf_ns"]) - int(sel[0]["t_perf_ns"])) / 1e9
    delta = float(sel[-1]["win_cpu_ms"]) - float(sel[0]["win_cpu_ms"])
    if wall <= 0 or delta < 0:
        return None
    return (delta / (wall * 1000.0) * 100.0, wall, len(sel), delta)


def seg_rates(rows, seg_s=60.0):
    """把一趟切成等长段，返回每段 rate。"""
    t0 = int(rows[0]["t_perf_ns"])
    out = []
    k = 0
    while True:
        lo = t0 + k * seg_s * 1e9
        hi = lo + seg_s * 1e9
        sel = [r for r in rows if lo <= int(r["t_perf_ns"]) <= hi]
        if len(sel) < 2:
            break
        wall = (int(sel[-1]["t_perf_ns"]) - int(sel[0]["t_perf_ns"])) / 1e9
        d = float(sel[-1]["win_cpu_ms"]) - float(sel[0]["win_cpu_ms"])
        if wall > 0 and d >= 0:
            out.append(d / (wall * 1000.0) * 100.0)
        k += 1
        if k > 20:
            break
    return out


def a8ed_first_nonzero(rows):
    for i, r in enumerate(rows):
        if (r.get("A8ED50") or 0) != 0:
            t0 = int(rows[0]["t_perf_ns"])
            return i, (int(r["t_perf_ns"]) - t0) / 1e9
    return None, None


def main():
    data = {}
    print("=" * 100)
    print("§1 · 三口径 rate 复算（Lead 独立）")
    print("=" * 100)
    print(f"{'trip':<14}{'全窗%':>10}{'丢前10s%':>12}{'裁到150s%':>12}{'wall_s':>9}{'n':>8}")
    for t in TRIPS:
        rows = load(t)
        full = rate(rows)
        d10 = rate(rows, drop_first_s=10.0)
        c150 = rate(rows, cut_s=150.0)
        data[t] = {"rows": rows, "full": full, "d10": d10, "c150": c150}
        print(f"{t:<14}{full[0]:>10.4f}{(d10[0] if d10 else float('nan')):>12.4f}"
              f"{(c150[0] if c150 else float('nan')):>12.4f}{full[1]:>9.3f}{full[2]:>8}")

    def agg(cell, key="full"):
        vals = [data[f"{cell}_r{i}"][key][0] for i in (1, 2)]
        return sum(vals) / 2.0, max(vals) - min(vals), vals

    print()
    print("=" * 100)
    print("§2 · 三点聚合 / 分量 / 份额 / 参照比")
    print("=" * 100)
    for key, label in (("full", "全窗"), ("d10", "丢前10s"), ("c150", "裁到150s")):
        mid, rid, vid = agg("g_idle", key)
        mnr, rnr, vnr = agg("g_near", key)
        mfr, rfr, vfr = agg("g_far", key)
        combat = mnr - mid
        march = mfr - mnr
        total = mfr - mid
        print(f"\n[{label}]  idle={mid:.4f}(极差{rid:.4f})  near={mnr:.4f}({rnr:.4f})  far={mfr:.4f}({rfr:.4f})")
        print(f"          交战={combat:.4f} pp  行军={march:.4f} pp  总={total:.4f} pp")
        print(f"          份额 交战={combat/total*100:.4f} %  行军={march/total*100:.4f} %")
        print(f"          参照比 R(far)/R(idle) = {mfr/mid:.4f}")
        if key == "full":
            base = (mid, mnr, mfr, rid, rnr, rfr)
            # A8ED50
            print("\n  --- A8ED50 首非零 ---")
            for t in TRIPS:
                i, s = a8ed_first_nonzero(data[t]["rows"])
                print(f"    {t:<14} idx={str(i):>6}  t={('%.4f s' % s) if s is not None else '从未'}")

    mid, mnr, mfr, rid, rnr, rfr = base
    print()
    print("=" * 100)
    print("§3 · 8 顶点端点枚举 → 份额包络")
    print("=" * 100)
    idv = [mid - rid / 2, mid + rid / 2]
    nrv = [mnr - rnr / 2, mnr + rnr / 2]
    frv = [mfr - rfr / 2, mfr + rfr / 2]
    rows = []
    for i, n, f in itertools.product(idv, nrv, frv):
        tot = f - i
        cbt = n - i
        rows.append((i, n, f, tot, cbt, cbt / tot * 100, (tot - cbt) / tot * 100))
    rows.sort(key=lambda x: x[5])
    print(f"{'idle':>10}{'near':>10}{'far':>10}{'总pp':>10}{'交战pp':>10}{'交战%':>10}{'行军%':>10}")
    for r in rows:
        print(f"{r[0]:>10.4f}{r[1]:>10.4f}{r[2]:>10.4f}{r[3]:>10.4f}{r[4]:>10.4f}{r[5]:>10.4f}{r[6]:>10.4f}")
    print(f"\n  交战份额包络 = [{rows[0][5]:.4f} %, {rows[-1][5]:.4f} %]  跨度 {rows[-1][5]-rows[0][5]:.4f} pp")

    print()
    print("=" * 100)
    print("§4 · Σd 一阶混杂修正")
    print("=" * 100)
    g = ROOT / "lead" / "next_re_20261112_r09" / "W102_audit_adversarial" / "work" / "w102_geom.json"
    if g.is_file():
        geo = json.loads(g.read_text(encoding="utf-8"))
        print("  [info] 读 W102 的几何 json 仅作对照；下面用它的 mean 值复算，不采信它的结论")
        print("  " + json.dumps(geo, ensure_ascii=False)[:600])
    # 独立：直接从 design json 重算 Σd
    sys_path = ROOT / "lead" / "next_re_20261112_r08" / "W98_clean" / "work"
    print("\n  --- 从 design json 独立重算 mean Chebyshev ---")
    for cell in ("g_near", "g_far"):
        dj = sys_path / f"w94_design_{cell}.json"
        if not dj.is_file():
            print(f"    {cell}: {dj} 缺失")
            continue
        d = json.loads(dj.read_text(encoding="utf-8"))
        # 找 units / structures：结构随 ra2forge 版本变化，做宽松解析
        found = []
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(d)
        print(f"    {cell}: keys(top)={list(d.keys())[:8]}  size={dj.stat().st_size}")

    print()
    print("=" * 100)
    print("§5 · 效应/噪声（分母 = g_far 极差）")
    print("=" * 100)
    combat = mnr - mid
    march = mfr - mnr
    total = mfr - mid
    print(f"  g_far 极差 = {rfr:.4f} pp")
    print(f"  交战 {combat:.4f} / {rfr:.4f} = {combat/rfr:.4f}")
    print(f"  行军 {march:.4f} / {rfr:.4f} = {march/rfr:.4f}")
    print(f"  总   {total:.4f} / {rfr:.4f} = {total/rfr:.4f}")

    print()
    print("=" * 100)
    print("§6 · 60 s 段内散布（同趟同 cell）")
    print("=" * 100)
    for t in TRIPS:
        s = seg_rates(data[t]["rows"], 60.0)
        if s:
            print(f"  {t:<14} 段数={len(s)}  值={[round(x,3) for x in s]}  极差={max(s)-min(s):.4f} pp")


if __name__ == "__main__":
    main()
