#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
W102 独立复算：从 run.ndjson 重算 R(cell)，不复用 SUMMARY.csv / SPLIT.md 的任何数字。

口径（已裁定，不改）：
  CPU 消耗率(%) = sum(win_cpu_ms_delta over consecutive ok-sample pairs) / wall_ms * 100
  wall = (last.t_perf_ns - first.t_perf_ns) / 1e6 ms；FILETIME 主通道。
  （与 batch_analyze.py:71-88 逐字同式，但我这里独立实现并用第二个通道校验。）

额外做的四件攻击性分析（§634 用）：
  A. 用 raw (win_kernel_ms + win_user_ms) 端点差的第二通道算 rate，两条通道逐位比。
  B. per-sample instantaneous rate，看 per-trip 内时间结构（相位），
     并与 §627 的相位表（A 56.86 / B早期 64.23 / B后期 27.08 / 末段 22.27）对照。
  C. g_far 两趟的逐秒 rate 曲线差，定位 4.91 pp 极差落在哪一段。
  D. 敏感度：对整个采样窗做 k-秒滑窗，看 cell 均值对窗长的弹性（短窗不可用性）。
"""
import json, os, sys, statistics as st

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r08\W98_clean\out"
TRIPS = [
    ("g_idle", "trip_g_idle_r1"), ("g_idle", "trip_g_idle_r2"),
    ("g_near", "trip_g_near_r1"), ("g_near", "trip_g_near_r2"),
    ("g_far",  "trip_g_far_r1"),  ("g_far",  "trip_g_far_r2"),
]
NS_MS = 1_000_000.0


def load(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def samples_of(rows):
    return [r for r in rows if r.get("kind") == "sample"
            and r.get("elapsed_ingame_s") is not None]


def rate_delta_channel(win):
    """主通道：Σ win_cpu_ms_delta / wall —— 与 batch_analyze 同式，独立实现。"""
    t0, t1 = win[0]["t_perf_ns"], win[-1]["t_perf_ns"]
    wall_ms = (t1 - t0) / NS_MS
    sum_ms = 0.0
    n_used = 0
    n_null = 0
    for i in range(1, len(win)):
        a, b = win[i - 1], win[i]
        if b.get("read_status") != "ok" or a.get("read_status") != "ok":
            continue
        d = b.get("win_cpu_ms_delta")
        if d is None:
            n_null += 1
            continue
        sum_ms += d
        n_used += 1
    return dict(rate=sum_ms / wall_ms * 100.0, sum_ms=sum_ms, wall_ms=wall_ms,
                n_used=n_used, n_null_delta=n_null)


def rate_endpoint_channel(win):
    """第二通道：raw (kernel+user) 端点差 / wall。独立于 delta 字段。"""
    t0, t1 = win[0]["t_perf_ns"], win[-1]["t_perf_ns"]
    wall_ms = (t1 - t0) / NS_MS
    c0 = win[0]["win_kernel_ms"] + win[0]["win_user_ms"]
    c1 = win[-1]["win_kernel_ms"] + win[-1]["win_user_ms"]
    return dict(rate=(c1 - c0) / wall_ms * 100.0, sum_ms=c1 - c0, wall_ms=wall_ms)


def phase_rates(win, t_start=None, t_end=None):
    """按局内秒切片，返回 {秒: rate}"""
    if t_start is not None:
        win = [r for r in win if t_start <= r["elapsed_ingame_s"] < t_end]
    if len(win) < 5:
        return None
    return rate_delta_channel(win)["rate"]


def main():
    res = {}
    for cell, trip in TRIPS:
        p = os.path.join(OUT, trip, "run.ndjson")
        rows = load(p)
        s = samples_of(rows)
        d = rate_delta_channel(s)
        e = rate_endpoint_channel(s)
        fg_loss = sum(1 for r in s if not r.get("win_foreground"))
        tids = sorted({r.get("win_tid") for r in s})
        read_fail = sum(1 for r in s if r.get("read_status") != "ok")
        # 前后各 2 s 丢掉，看边缘效应
        inner = [r for r in s if 2.0 <= r["elapsed_ingame_s"] <= s[-1]["elapsed_ingame_s"] - 2.0]
        di = rate_delta_channel(inner)
        # 前 10 s（很多分析会丢预热）
        after10 = [r for r in s if r["elapsed_ingame_s"] >= 10.0]
        d10 = rate_delta_channel(after10)
        # 只到 150 s 之前（ingame_s 上限裁到 150，与 §630-1 的"统一裁到 150 s"一致）
        cut150 = [r for r in s if r["elapsed_ingame_s"] <= 150.0]
        d150 = rate_delta_channel(cut150)
        res[trip] = dict(
            cell=cell, trip=trip, n_samples=len(s),
            t_first=s[0]["elapsed_ingame_s"], t_last=s[-1]["elapsed_ingame_s"],
            wall_s=d["wall_ms"] / 1000.0, sum_cpu_ms=d["sum_ms"],
            rate_delta=d["rate"], rate_endpoint=e["rate"],
            rate_delta_minus_endpoint=d["rate"] - e["rate"],
            n_used=d["n_used"], n_null_delta=d["n_null_delta"],
            fg_loss=fg_loss, fg_loss_pct=fg_loss / max(1, len(s)) * 100.0,
            n_tid=len(tids), tids=tids, read_fail=read_fail,
            rate_trim2s=di["rate"], rate_after10s=d10["rate"],
            rate_cut150=d150["rate"],
            max_gap_ms=max(
                ((s[i]["t_perf_ns"] - s[i - 1]["t_perf_ns"]) / NS_MS)
                for i in range(1, len(s))),
        )

    print("=" * 116)
    print("W102 §A-1 · 逐趟独立复算（口径：Σ win_cpu_ms_delta / wall，FILETIME）")
    print("=" * 116)
    hdr = ("trip", "n", "wall_s", "sum_cpu_ms", "rate_delta%", "rate_endpt%", "Δ(pp)",
           "tid", "fg_loss%", "readfail")
    print("{:<18}{:>7}{:>10}{:>12}{:>12}{:>12}{:>9}{:>7}{:>9}{:>9}".format(*hdr))
    for cell, trip in TRIPS:
        r = res[trip]
        print("{:<18}{:>7}{:>10.3f}{:>12.2f}{:>12.4f}{:>12.4f}{:>+9.4f}{:>7}{:>9.1f}{:>9}".format(
            trip, r["n_samples"], r["wall_s"], r["sum_cpu_ms"], r["rate_delta"],
            r["rate_endpoint"], r["rate_delta_minus_endpoint"], r["n_tid"],
            r["fg_loss_pct"], r["read_fail"]))

    print()
    print("=" * 116)
    print("W102 §A-2 · 稳健性：同一趟在不同预处理下的 rate（看定义弹性）")
    print("=" * 116)
    print("{:<18}{:>12}{:>12}{:>12}{:>12}{:>12}{:>12}".format(
        "trip", "全窗", "裁掉首尾2s", "丢前10s", "裁到150s", "极差(4口径)", "max_gap_ms"))
    for cell, trip in TRIPS:
        r = res[trip]
        vals = [r["rate_delta"], r["rate_trim2s"], r["rate_after10s"], r["rate_cut150"]]
        print("{:<18}{:>12.4f}{:>12.4f}{:>12.4f}{:>12.4f}{:>12.4f}{:>12.2f}".format(
            trip, *vals, max(vals) - min(vals), r["max_gap_ms"]))

    # ---------- 三点聚合 ----------
    def agg(cell, key="rate_delta"):
        v = [res[t][key] for c, t in TRIPS if c == cell]
        return dict(vals=v, mean=sum(v) / len(v), lo=min(v), hi=max(v), rng=max(v) - min(v))

    print()
    print("=" * 116)
    print("W102 §A-3 · 三点聚合（我自算，主通道）")
    print("=" * 116)
    A = {}
    for cell in ("g_idle", "g_near", "g_far"):
        a = agg(cell)
        A[cell] = a
        print("{:<8} 逐值 = {}".format(cell, " / ".join("{:.4f}".format(x) for x in a["vals"])))
        print("{:<8} 均值 = {:.4f}   极差 = {:.4f}   [{:.4f} .. {:.4f}]".format(
            "", a["mean"], a["rng"], a["lo"], a["hi"]))

    Ri, Rn, Rf = A["g_idle"]["mean"], A["g_near"]["mean"], A["g_far"]["mean"]
    comb = Rn - Ri
    march = Rf - Rn
    tot = Rf - Ri
    print()
    print("R(idle) = {:.4f}".format(Ri))
    print("R(near) = {:.4f}".format(Rn))
    print("R(far)  = {:.4f}".format(Rf))
    print("交战分量 R(near)-R(idle) = {:.4f} pp".format(comb))
    print("行军分量 R(far)-R(near)  = {:.4f} pp".format(march))
    print("总分 R(far)-R(idle)      = {:.4f} pp".format(tot))
    print("恒等式残差 = {:.12f} pp   <-- 这一项按定义必为 0".format((comb + march) - tot))
    print("份额 交战 = {:.4f} %   行军 = {:.4f} %".format(comb / tot * 100.0, march / tot * 100.0))
    print("参照带 R(far)/R(idle) = {:.4f}".format(Rf / Ri))
    print("相对增量 (R(far)/R(idle)-1)*100 = {:.4f} %".format((Rf / Ri - 1.0) * 100.0))

    # ---------- 端点组合枚举 ----------
    print()
    print("=" * 116)
    print("W102 §A-4 · 端点组合枚举（4 个顶点，其余 4 个是内点）")
    print("=" * 116)
    iv, nv, fv = A["g_idle"]["vals"], A["g_near"]["vals"], A["g_far"]["vals"]
    corners = []
    for i in iv:
        for n in nv:
            for f in fv:
                t_ = f - i
                c_ = n - i
                m_ = f - n
                corners.append(dict(i=i, n=n, f=f, tot=t_, comb=c_, march=m_,
                                    comb_pct=c_ / t_ * 100.0 if t_ else float("nan"),
                                    march_pct=m_ / t_ * 100.0 if t_ else float("nan")))
    corners.sort(key=lambda x: x["comb_pct"])
    print("{:>10}{:>10}{:>10}{:>10}{:>10}{:>10}{:>10}".format(
        "idle", "near", "far", "总pp", "交战pp", "交战%", "行军%"))
    for c in corners:
        print("{:>10.4f}{:>10.4f}{:>10.4f}{:>10.4f}{:>10.4f}{:>10.2f}{:>10.2f}".format(
            c["i"], c["n"], c["f"], c["tot"], c["comb"], c["comb_pct"], c["march_pct"]))
    pcts = [c["comb_pct"] for c in corners]
    print()
    print("交战份额 端点包络 = [{:.2f} %, {:.2f} %]，跨度 {:.2f} pp".format(
        min(pcts), max(pcts), max(pcts) - min(pcts)))

    # ---------- 效应/噪声 ----------
    print()
    print("=" * 116)
    print("W102 §A-5 · 效应/噪声（只用极差，不用 sd/CI/p）")
    print("=" * 116)
    print("g_far 极差 = {:.4f} pp".format(A["g_far"]["rng"]))
    print("行军分量 = {:.4f} pp  => 效应/该极差 = {:.3f}".format(march, march / A["g_far"]["rng"]))
    print("总效应   = {:.4f} pp  => 效应/该极差 = {:.3f}".format(tot, tot / A["g_far"]["rng"]))
    print("交战分量 = {:.4f} pp  => 效应/该极差 = {:.3f}".format(comb, comb / A["g_far"]["rng"]))
    # 单趟 at g_far 取 max、near 取 min 之类：份额极端
    print()
    print("若 g_far 真实水平在其观测端点之间任意位置 p（第二趟占权 p），")
    print("且 g_near 固定中心值，则份额随 p 的弹性：")
    for p in (0.0, 0.25, 0.5, 0.75, 1.0):
        f_ = (1 - p) * fv[0] + p * fv[1]
        t_ = f_ - Ri
        m_ = f_ - Rn
        print("  p={:.2f}  R(far)={:.4f}  总={:.4f}  行军={:.4f} pp  行军份额={:.2f} %".format(
            p, f_, t_, m_, m_ / t_ * 100.0))
    print()
    print("若把 g_idle 与 g_near 也各允许取端点（最坏的份额口径）：")
    worst = []
    for c in corners:
        worst.append((c["comb_pct"], c["i"], c["n"], c["f"]))
    print("  最小交战份额 = {:.2f} %  (idle={:.4f}, near={:.4f}, far={:.4f})".format(*worst[0]))
    print("  最大交战份额 = {:.2f} %  (idle={:.4f}, near={:.4f}, far={:.4f})".format(*worst[-1]))

    # ---------- 相位结构 ----------
    print()
    print("=" * 116)
    print("W102 §A-6 · 逐 10 s 相位表（暴露 cell 内时间结构，ABBA 与 §634 都要用）")
    print("=" * 116)
    phase = {}
    for cell, trip in TRIPS:
        s = samples_of(load(os.path.join(OUT, trip, "run.ndjson")))
        row = []
        for lo in range(0, 150, 10):
            r = phase_rates(s, lo, lo + 10)
            row.append(r)
        phase[trip] = row
        print("{:<18}".format(trip) + " ".join(
            ("{:>7.2f}".format(x) if x is not None else "{:>7}".format("-")) for x in row))
    print("{:<18}".format("(窗口 s)") + " ".join(
        "{:>7}".format("{}-{}".format(lo, lo + 10)) for lo in range(0, 150, 10)))

    print()
    print("逐 10 s 的 cell 内极差（同一 cell 两趟之间，按 10 s 时间对齐）：")
    for cell in ("g_idle", "g_near", "g_far"):
        t1 = [t for c, t in TRIPS if c == cell][0]
        t2 = [t for c, t in TRIPS if c == cell][1]
        diffs = []
        for k in range(len(phase[t1])):
            a, b = phase[t1][k], phase[t2][k]
            if a is not None and b is not None:
                diffs.append((k * 10, b - a))
        mx = max(diffs, key=lambda x: abs(x[1]))
        print("  {:<8} 最大段间差 {:+.3f} pp @ {}-{} s   （全段均值差 {:+.3f} pp）".format(
            cell, mx[1], mx[0], mx[0] + 10,
            A[cell]["vals"][1] - A[cell]["vals"][0]))

    json.dump(dict(trips=res, cells={k: v for k, v in A.items()},
                   corners=corners, phase=phase),
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "w102_recompute.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

