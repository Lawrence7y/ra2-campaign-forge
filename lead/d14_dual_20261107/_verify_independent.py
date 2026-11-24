# -*- coding: utf-8 -*-
"""_verify_independent.py — 双口径复核员·hy4 独立复算（默认怀疑复算回件）

零真机 / 零采样代码 / 只读语料。不 import 任何复算员/上游 .py 实现；
B% 用独立写的逐样本扫描（记录每段的 (i,j,d)），Pearson/Spearman 另写一条
（用 sorted+二分计数处理并列秩），窗口集构造按 os.walk 全递归（异族 _xbatch_verify.py:94-101 规则），
与复算员的「趟子目录+根散件」清单做集合比对。

用法：python -I -X utf8 _verify_independent.py > _verify_independent_out.txt 2>&1
"""
import bisect
import datetime
import json
import math
import os

BASE = "D:/Project/ra2-campaign-forge"
ROOT = BASE + "/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
NW = BASE + "/lead/goal3t_nightwatch_20261102"
T = 0.100
BOOT_TOL = 2
PUB_MTIME = datetime.datetime(2026, 11, 4, 0, 25, 57).timestamp()


def P(s=""):
    print(s)


# ---- B% 独立实现：逐样本扫描段，显式记录 (i,j,时长)；与 groupby/双指针写法不同 ----
def b_pct(ts, fs):
    span = ts[-1] - ts[0]
    if span == 0.0:
        return 0.0, 0
    total = 0.0
    nseg = 0
    start = 0
    for k in range(1, len(fs) + 1):
        if k == len(fs) or fs[k] != fs[start]:
            dur = ts[k - 1] - ts[start]
            if dur > T:                 # 严格大于 T（等于不计入）
                total += dur
                nseg += 1
            start = k
    return 100.0 * total / span, nseg


# ---- 平均秩：对每个值用二分求 [<v] 与 [<=v] 的个数，不复用 rank(vs) ----
def mean_ranks(v):
    s = sorted(v)
    return [((bisect.bisect_left(s, x) + bisect.bisect_right(s, x)) / 2.0 + 0.5)
            for x in v]


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


def spearman(xs, ys):
    return pearson(mean_ranks(xs), mean_ranks(ys))


def collect_walk():
    """os.walk 全递归（异族规则 _xbatch_verify.py:94-101）"""
    out = []
    for dp, dn, fns in os.walk(ROOT):
        for fn in sorted(fns):
            if fn.startswith("measure_w") and fn.endswith(".json"):
                p = os.path.join(dp, fn)
                rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
                out.append((rel, p))
    return sorted(out)


def collect_phase():
    """趟子目录 sorted listdir + 数据根散件（_phase_recompute.py:111-122 规则）"""
    out = []
    for trip in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, trip)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.startswith("measure_w") and fn.endswith(".json"):
                out.append((trip + "/" + fn, os.path.join(d, fn)))
    for i in range(3):
        fn = "measure_w%d.json" % i
        p = os.path.join(ROOT, fn)
        if os.path.isfile(p):
            out.append(("(root)/" + fn, p))
    return sorted(out)


def load(rel, p):
    with open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    s = d.get("samples") or {}
    t, f = s.get("t"), s.get("f")
    ta = d.get("t_abs0")
    if not t or not f or len(t) < 2 or ta is None:
        return None, "empty/len<2/no t_abs0"
    if len(t) != len(f):
        return None, "len mismatch"
    t = [float(x) for x in t]
    f = [int(x) for x in f]
    B, nseg = b_pct(t, f)
    return dict(rel=rel, window=d.get("window"), uptime=t[0], t_abs0=float(ta),
                B=B, nseg=nseg, span=t[-1] - t[0],
                boot=float(round(float(ta) - t[0])),
                moving=any(f[k] != f[k - 1] for k in range(1, len(f))),
                mtime=os.stat(p).st_mtime), None


def main():
    P("独立复核 _verify_independent.py  运行时刻 %s"
      % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    P("零真机/零采样代码/只读语料；不 import 复算员或上游 .py。")
    walk = collect_walk()
    phase = collect_phase()
    # 归一化根散件命名后比对集合
    pn = set(("(root)/" + r if "/" not in r else r) for r, _ in phase)
    wn = set(("(root)/" + r if "/" not in r else r) for r, _ in walk)
    P("")
    P("## 窗口集构造规则核对")
    P("   os.walk 全递归命中 = %d；phase 规则命中 = %d" % (len(wn), len(pn)))
    P("   两规则归一化后集合差异：walk-only=%s phase-only=%s" % (sorted(wn - pn), sorted(pn - wn)))
    late = [r for r, p in walk if os.stat(p).st_mtime > PUB_MTIME]
    P("   mtime 晚于公布输出(2026-11-04 00:25:57)的件 = %d -> %s" % (len(late), late))
    frozen = [(r, p) for r, p in walk if r not in set(late)]

    rows, drops = [], []
    for r, p in frozen:
        row, why = load(r, p)
        if row is None:
            drops.append((r, why))
        else:
            rows.append(row)
    P("   冻结语料命中=%d 有效窗=%d 剔除=%d -> %s" % (len(frozen), len(rows), len(drops), [d[0] for d in drops]))
    P("   span==0 的有效窗 = %d" % sum(1 for r in rows if r["span"] == 0.0))
    mv = [r for r in rows if r["moving"]]
    P("   有推进 moving = %d / %d" % (len(mv), len(rows)))

    P("")
    P("## 四系数独立复算（冻结语料）")
    w_mv = [float(r["window"]) for r in mv]
    u_mv = [r["uptime"] for r in mv]
    b_mv = [r["B"] for r in mv]
    w_all = [float(r["window"]) for r in rows]
    u_all = [r["uptime"] for r in rows]
    b_all = [r["B"] for r in rows]
    vals = [
        ("64 moving rho(window,B%)", spearman(w_mv, b_mv), -0.04026776101462127),
        ("64 moving rho(uptime,B%)", spearman(u_mv, b_mv), 0.03945103538787863),
        ("97 全量   rho(window,B%)", spearman(w_all, b_all), 0.347432459482872),
        ("97 全量   rho(uptime,B%)", spearman(u_all, b_all), 0.3461192878606675),
    ]
    for name, mine, pub in vals:
        P("   %-26s 本算=%+.17g  复算员repr=%+.17g  |dev|=%.3e"
          % (name, mine, pub, abs(mine - pub)))
    P("   逐位比对：%s" % ", ".join("%s" % ("MATCH" if abs(a - b) < 1e-12 else "DIFF")
                                  for _, a, b in vals))

    # B% 逐窗核对（15 个公布值）
    pub_b = {
        "archive_T32/measure_w0.json": 38.30000, "archive_T33/measure_w0.json": 43.25877,
        "archive_T34/measure_w0.json": 98.93967, "archive_T36/measure_w0.json": 77.33598,
        "archive_T38/measure_w1.json": 96.31241, "archive_T39/measure_w1.json": 95.92992,
        "archive_T43/measure_w0.json": 76.75764, "archive_T47/measure_w0.json": 26.47454,
        "archive_T49_u0800/measure_w0.json": 59.28170, "l1_20261023e1/measure_w0.json": 94.49626,
        "l1_20261023hb/measure_w0.json": 63.91013, "l1_20261023hc/measure_w0.json": 82.17387,
        "l1_20261023k/measure_w0.json": 88.57199, "l3_20261023q/measure_w2.json": 84.62417,
        "l3_20261023r/measure_w1.json": 37.74596,
    }
    byrel = {r["rel"]: r for r in rows}
    devs = [(rel, abs(byrel[rel]["B"] - v), byrel[rel]["B"], v) for rel, v in pub_b.items()]
    P("")
    P("## B%% 逐窗核对（15 个公布值，_xbatch_verify_out.txt:35-49）")
    for rel, dv, mine, pv in sorted(devs):
        P("   %-38s 公布=%9.5f  本算=%12.6f  |dev|=%.2e" % (rel, pv, mine, dv))
    P("   最大偏差 = %.3e" % max(d[1] for d in devs))

    # C1 自检（units0 需另读，此处复用 load 但补读 gate）
    P("")
    P("## C1 旁证（Pearson/Spearman 独立实现）")
    xs, ys = [], []
    for r in rows:
        if not r["moving"]:
            continue
        p = os.path.join(ROOT, r["rel"].replace("/", os.sep))
        with open(p, encoding="utf-8") as fh:
            u = (json.load(fh).get("gate") or {}).get("units0")
        if u is not None:
            xs.append(float(u))
            ys.append(r["B"])
    P("   n=%d  Pearson r=%+.6f (公布 -0.200527)  Spearman rho=%+.6f (公布 -0.170611)"
      % (len(xs), pearson(xs, ys), spearman(xs, ys)))

    # BOOT 聚类（先取整、±2s 链式）
    sr = sorted(rows, key=lambda r: r["boot"])
    groups = []
    for r in sr:
        if groups and r["boot"] - groups[-1]["last"] <= BOOT_TOL:
            groups[-1]["rows"].append(r)
            groups[-1]["last"] = r["boot"]
        else:
            groups.append({"rep": r["boot"], "last": r["boot"], "rows": [r]})
    P("")
    P("## BOOT / P2 / P3")
    P("   BOOT 数 = %d" % len(groups))
    within = []
    for g in groups:
        sel = [r for r in g["rows"] if r["moving"]]
        if len(sel) < 3:
            continue
        a = spearman([r["uptime"] for r in sel], [r["B"] for r in sel])
        b = spearman([float(r["window"]) for r in sel], [r["B"] for r in sel])
        within.append(a)
        lbl = datetime.datetime.fromtimestamp(g["rep"]).strftime("%m-%d %H:%M")
        P("   %-14s n=%2d rho(uptime,B)=%+.4f  rho(window,B)=%+.4f" % (lbl, len(sel), a, b))
    fin = sorted(x for x in within if x == x)
    med = (fin[len(fin) // 2] if len(fin) % 2 else
           (fin[len(fin) // 2 - 1] + fin[len(fin) // 2]) / 2.0)
    buggy = sorted(within)[len(within) // 2]
    P("   uptime 列：正 %d / 负 %d / nan %d" % (sum(1 for x in fin if x > 0),
                                                sum(1 for x in fin if x < 0),
                                                len(within) - len(fin)))
    P("   D-26 更正中位（滤 nan、偶数取中央均值）= %+.17g" % med)
    P("   原缺陷 sorted(within)[len//2]（含 nan，%d 个）= %+.17g" % (len(within), buggy))
    bx = [sum(r["uptime"] for r in g["rows"]) / len(g["rows"]) for g in groups]
    by = [sum(r["B"] for r in g["rows"]) / len(g["rows"]) for g in groups]
    P("   P3 BOOT 间 rho = %+.17g (n=%d)" % (spearman(bx, by), len(bx)))

    # 语料漂移（现状全量）
    rows_now = [x for r, p in walk for x in [load(r, p)[0]] if x is not None]
    mv_now = [r for r in rows_now if r["moving"]]
    P("")
    P("## 语料漂移（现状全量，仅披露）")
    P("   现状命中=%d 有效=%d moving=%d" % (len(walk), len(rows_now), len(mv_now)))
    P("   全量 n=%d: rho(window)=%+.6f rho(uptime)=%+.6f"
      % (len(rows_now), spearman([float(r["window"]) for r in rows_now], [r["B"] for r in rows_now]),
         spearman([r["uptime"] for r in rows_now], [r["B"] for r in rows_now])))
    P("   moving n=%d: rho(window)=%+.6f rho(uptime)=%+.6f"
      % (len(mv_now), spearman([float(r["window"]) for r in mv_now], [r["B"] for r in mv_now]),
         spearman([r["uptime"] for r in mv_now], [r["B"] for r in mv_now])))
    P("完。")


if __name__ == "__main__":
    main()
