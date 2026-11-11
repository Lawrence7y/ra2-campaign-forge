# -*- coding: utf-8 -*-
"""_cal_probe.py - 停滞 episode 口径三定义复算（离线、只读三件轨迹、零真机）。

背景：§507/§508 与 V4D_RECOMPUTE 把停滞时长口径钉为「卡住帧值首末拍跨度」，
但发布实现 _h8_waittrace_decomp.py L107-109 取 bts[e0]-bts[s0]，其中 s0/e0 是
*delta 数组* 的下标（delta[k] 描述「到达第 k 拍」的那条边），与平台真首末拍错位。
本探针枚举三定义并逐段给出恒等式，量化错位在三种拍节律下的后果。

  B（钉死定义，V4D_RECOMPUTE §四-2）= t(平台末拍) − t(平台首拍)
  C（已登记复算陷阱）             = B + gap_out（持续到下一推进拍）
  A（发布实现 L107-109）           = B + gap_out − d_in

其中 d_in = 平台首拍→第二拍间隔，gap_out = 平台末拍→下一推进拍间隔。
快拍时 d_in≈gap_out≈2.5ms ⇒ A≈B；v4-b 慢拍时二者可达数百 ms 且不等 ⇒ A≠B。

stdout 由 Bash 重定向落盘（tee 语义由重定向承担）。
用法：python -I -X utf8 _cal_probe.py > _cal_probe_out.txt
"""

import json
import statistics as st

BASE = ("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/"
        "lead/qc161_u0400_trip/%s/h8_wait_trace.json")
TRIPS = ("v4b", "v4c", "v4d")
T = 0.1


def P(s=""):
    print(s)


def load(tag):
    d = json.load(open(BASE % ("l3_1101" + tag), encoding="utf-8"))
    ts = [s[0] for s in d["samples"]]
    fs = [s[1] for s in d["samples"]]
    first = next(i for i in range(1, len(fs)) if fs[i] > fs[i - 1])
    return d, ts, fs, first


def plateaus(ts, fs, first):
    """战斗段内等帧平台（bfs 坐标），附三种定义的时长。"""
    bts, bfs = ts[first:], fs[first:]
    out = []
    i, n = 0, len(bfs)
    while i < n:
        j = i
        while j + 1 < n and bfs[j + 1] == bfs[i]:
            j += 1
        b = bts[j] - bts[i]
        d_in = bts[i + 1] - bts[i] if i + 1 < n else None
        gap_out = bts[j + 1] - bts[j] if j + 1 < n else None
        # A：实现取 bts[e0]-bts[s0]（s0/e0 为 delta 下标，两端各后移一拍）。
        # 段内平台 A = B + gap_out - d_in。末平台的 e0 越界 ⇒ 落 bts[-1] 兜底，
        # 终点不再后移而起点仍后移 ⇒ A = B - d_in（符号与内部段相反）。
        if d_in is None:
            a, kind = None, "head"
        elif gap_out is None:
            a, kind = b - d_in, "tail"
        else:
            a, kind = b + gap_out - d_in, "interior"
        out.append({"i": i, "j": j, "frame": bfs[i], "t0": bts[i], "t1": bts[j],
                    "B": b, "d_in": d_in, "gap_out": gap_out,
                    "A": a, "A_kind": kind,
                    "C": None if gap_out is None else b + gap_out})
        i = j + 1
    return bts, bfs, out


def impl_exact(ts, fs, first, thr=T):
    """逐字复刻 _h8_waittrace_decomp.py L87-109 的取值方式。"""
    deltas = [b - a for a, b in zip(fs, fs[1:])]
    bts, bfs = ts[first:], fs[first:]
    bdl = deltas[first - 1:]
    out = []
    i, n = 0, len(bdl)
    while i < n:
        if bdl[i] == 0:
            j = i
            while j < n and bdl[j] == 0:
                j += 1
            end_t = bts[j] if j < len(bts) else bts[-1]
            dur = end_t - bts[i]
            if dur >= thr:
                out.append({"s0": i, "e0": j, "t0": bts[i], "t1": end_t, "dur": dur})
            i = j
        else:
            i += 1
    return out


for tag in TRIPS:
    d, ts, fs, first = load(tag)
    bts, bfs, rows = plateaus(ts, fs, first)
    span = bts[-1] - bts[0]
    rate = len(ts) / d["wait_s"]
    impl = impl_exact(ts, fs, first)
    P("=" * 78)
    P("## %s  n=%s verdict=%s wait_s=%s beats=%d cadence=%.1fHz span=%.4fs"
      % (tag, d["n"], d["verdict"], d["wait_s"], len(ts), rate, span))
    P("   plateaus=%d  100ms=%.1f beats" % (len(rows), rate / 10.0))

    # 恒等式核验：内部段 A == B + gap_out - d_in（逐段残差，浮点应为 0）
    introws = [r for r in rows if r["A_kind"] == "interior"]
    resid = [abs(r["A"] - (r["B"] + r["gap_out"] - r["d_in"])) for r in introws]
    P("   identity A==B+gap_out-d_in(内部段): n=%d 残差 max=%.9fms" % (len(resid), max(resid) * 1000))
    tail = [r for r in rows if r["A_kind"] == "tail"]
    if tail:
        P("   末平台(越界兜底): B=%.1fms d_in=%.1fms → A=B-d_in=%.1fms（与内部段符号相反）"
          % (tail[0]["B"] * 1000, tail[0]["d_in"] * 1000, tail[0]["A"] * 1000))

    for label, key in (("A(发布实现)", "A"), ("B(钉死定义)", "B"), ("C(到下一推进拍)", "C")):
        sel = [r for r in rows if r[key] is not None and r[key] >= T]
        tot = sum(r[key] for r in sel)
        P("   %-18s %3d 段  %9.4fs  %6.2f%%" % (label, len(sel), tot, 100 * tot / span))

    totA = sum(r["dur"] for r in impl)
    P("   逐字复刻实现      %3d 段  %9.4fs  %6.2f%%  （对上表 A 应一致）"
      % (len(impl), totA, 100 * totA / span))

    A = [r for r in rows if r["A"] is not None and r["A"] >= T]
    B = [r for r in rows if r["B"] >= T]
    cross_up = [r for r in rows if r["A"] is not None and r["B"] < T <= r["A"]]
    cross_dn = [r for r in rows if r["A"] is not None and r["A"] < T <= r["B"]]
    P("   跨越段: B不计→A计 %d 段 ；A不计→B计 %d 段" % (len(cross_up), len(cross_dn)))
    P("   A−B = %d 段 / %+.4fs（%+.2f pp）"
      % (len(A) - len(B), sum(r["A"] for r in A) - sum(r["B"] for r in B),
         100 * (sum(r["A"] for r in A) - sum(r["B"] for r in B)) / span))

    if cross_up:
        P("   跨越段样例（B<100ms<=A）：")
        for r in sorted(cross_up, key=lambda x: -x["A"])[:5]:
            P("      t=%.3fs frame=%d  B=%.1fms → A=%.1fms  (d_in=%.1fms gap_out=%.1fms)"
              % (r["t0"], r["frame"], r["B"] * 1000, r["A"] * 1000,
                 r["d_in"] * 1000, r["gap_out"] * 1000))

    di = [r["d_in"] for r in rows if r["d_in"] is not None]
    go = [r["gap_out"] for r in rows if r["gap_out"] is not None]
    P("   d_in    中位=%.2fms p90=%.2fms max=%.2fms"
      % (1000 * st.median(di), 1000 * sorted(di)[int(.9 * (len(di) - 1))], 1000 * max(di)))
    P("   gap_out 中位=%.2fms p90=%.2fms max=%.2fms"
      % (1000 * st.median(go), 1000 * sorted(go)[int(.9 * (len(go) - 1))], 1000 * max(go)))

P()
P("=" * 78)
P("## 阈值敏感性（各定义，段数随阈变化）")
for tag in TRIPS:
    d, ts, fs, first = load(tag)
    bts, bfs, rows = plateaus(ts, fs, first)
    for key in ("B", "A", "C"):
        cells = []
        for thr in (0.095, 0.099, 0.100, 0.101, 0.105, 0.110):
            n = sum(1 for r in rows if r[key] is not None and r[key] >= thr)
            cells.append("%.3f→%d" % (thr, n))
        P("   %s %s: %s" % (tag, key, "  ".join(cells)))
