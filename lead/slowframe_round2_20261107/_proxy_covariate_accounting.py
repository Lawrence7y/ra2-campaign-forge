# -*- coding: utf-8 -*-
"""_proxy_covariate_accounting.py — 可观测代理量核算（任务 2）。

问题：104 份语料里，哪些「窗口级 counters 标量」与「慢窗」共变？方向、强度、样本数？

访问模式与已过安全审查的 _proxy_scan_corpus.py 完全一致：
os.walk(常量语料根) + os.path.join + abspath + commonpath 越界拒收。

口径（全部沿用台账既有口径，不新造判据）：
  - 窗口资格 = verdict==ok 且 hz_effective>=100（§603 同口径）且 stats.frame_ms_p50 非空
    且 counters 中 units 有效读数 >=1。
  - 慢窗 = frame_ms_p50 > 60 ms（§603 的慢/快切法）；慢/快分组是**跨窗**分组，
    不构成同窗对照（§604 的同窗对照是另一件事，本轮不做也不冒充）。
  - 快照聚合 = 对 ~25 个 1 Hz 快照取中位/首/末（None 剔除）。
  - g_items/b_items 是 Items 指针（qc151_trip.harness8.py:3837-3840），
    不当物理量核算（指针值不进相关分析）。

统计：Spearman 秩相关（平均秩）+ 置换检验 + Pearson。
  - 置换检验伪随机流 = 自实现 xorshift64（固定种子 20261107，确定性可复现；
    非加密用途，蒙特卡洛置换足够）。
分层：A=全部合格窗（跨窗，受地图/趟别混淆）；B=§603 的 15 窗集；C=l1c/l1d/l1e/l3_20261021
同族 12 窗（同一批地图族内变体，跨图混淆最小）；分组对比=慢/快组中位。
"""
import json
import math
import os
import sys
from statistics import median

ROOT = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_proxy_covariate_accounting_out.txt")
SEED = 20261107
NPERM = 20000
SLOW_MS = 60.0


class XorShift64(object):
    """确定性 xorshift64（fixed seed；非加密，仅蒙特卡洛置换用）。"""

    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFFFFFFFFFF or 0x9E3779B97F4A7C15

    def next_u64(self):
        s = self.s
        s ^= (s << 13) & 0xFFFFFFFFFFFFFFFF
        s ^= s >> 7
        s ^= (s << 17) & 0xFFFFFFFFFFFFFFFF
        self.s = s
        return s

    def randint(self, n):
        return self.next_u64() % n


def _vals(cs, key):
    return [c[key] for c in cs if isinstance(c, dict)
            and isinstance(c.get(key), (int, float))]


def _end_start(cs, key):
    v = _vals(cs, key)
    return (v[-1] - v[0]) if len(v) >= 2 else None


def f_units0(g, cs):
    return g.get("units0")


def f_units_first(g, cs):
    v = _vals(cs, "units")
    return v[0] if v else None


def f_units_last(g, cs):
    v = _vals(cs, "units")
    return v[-1] if v else None


def f_d_units(g, cs):
    return _end_start(cs, "units")


def _med(key):
    def f(g, cs):
        v = _vals(cs, key)
        return median(v) if v else None
    return f


def _span(key):
    def f(g, cs):
        v = _vals(cs, key)
        return (max(v) - min(v)) if len(v) >= 2 else None
    return f


COVS = [
    ("units0_pre",   f_units0,      "gate.units0（窗前预置单位数）"),
    ("units_first",  f_units_first, "counters.units 窗内首读"),
    ("units_last",   f_units_last,  "counters.units 窗内末读"),
    ("units_med",    _med("units"), "counters.units 窗内快照中位"),
    ("d_units",      f_d_units,     "units末读−首读（窗内变化）"),
    ("units_range",  _span("units"), "units 窗内极差"),
    ("infantry_med", _med("infantry"), "counters.infantry 中位"),
    ("aircraft_med", _med("aircraft"), "counters.aircraft 中位"),
    ("techno_med",   _med("techno"),  "counters.techno 中位"),
    ("g_med",        _med("g"),       "counters.g（G DynArray 计数）中位"),
    ("b_med",        _med("b"),       "counters.b（B DynArray 计数）中位"),
    ("ws_kb_med",    _med("ws_kb"),   "counters.ws_kb（工作集 KB）中位"),
    ("pf_kb_med",    _med("pf_kb"),   "counters.pf_kb（PagefileUsage KB）中位"),
    ("d_ws_kb",      lambda g, cs: _end_start(cs, "ws_kb"), "ws_kb 末读−首读"),
    ("d_pf_kb",      lambda g, cs: _end_start(cs, "pf_kb"), "pf_kb 末读−首读"),
]


def spearman_ranks(xs):
    idx = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and xs[idx[j + 1]] == xs[idx[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[idx[k]] = avg
        i = j + 1
    return r


def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def spearman(xs, ys):
    """返回 (rho, p_perm, n)。并列用平均秩；置换检验用固定种子 xorshift64。"""
    n = len(xs)
    rx, ry = spearman_ranks(xs), spearman_ranks(ys)
    rho = pearson(rx, ry)
    if rho is None:
        return None, None, n
    rng = XorShift64(SEED)
    cnt = 0
    for _ in range(NPERM):
        ry2 = ry[:]
        for i in range(n - 1, 0, -1):  # Fisher–Yates（确定性 PRNG）
            j = rng.randint(i + 1)
            ry2[i], ry2[j] = ry2[j], ry2[i]
        rp = pearson(rx, ry2)
        if rp is not None and abs(rp) >= abs(rho) - 1e-12:
            cnt += 1
    return rho, (cnt + 1) / (NPERM + 1), n


def main():
    lines = []
    say = lines.append
    windows = []
    n_total = n_ok = n_p50 = n_used = 0
    files = []
    for root, dirs, fs in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in sorted(fs):
            if f.startswith("measure_w") and f.endswith(".json"):
                files.append(os.path.join(root, f))
    files.sort()
    for p in files:
        ap = os.path.abspath(p)
        if os.path.commonpath([os.path.abspath(ROOT), ap]) != os.path.abspath(ROOT):
            say("SKIP_OUTSIDE_ROOT %s" % p)
            continue
        n_total += 1
        with open(p, "rb") as fh:
            d = json.loads(fh.read().decode("utf-8"))
        st = d.get("stats") or {}
        gt = d.get("gate") or {}
        if d.get("verdict") != "ok":
            continue
        n_ok += 1
        p50 = st.get("frame_ms_p50")
        if not isinstance(p50, (int, float)):
            continue
        n_p50 += 1
        cs = d.get("counters") or []
        if not any(isinstance(c, dict) and isinstance(c.get("units"), (int, float))
                   for c in cs):
            continue
        n_used += 1
        rec = {"d": os.path.basename(os.path.dirname(ap)),
               "f": os.path.basename(ap), "p50": float(p50),
               "hz_eff": st.get("hz_effective"),
               "n_snap": sum(1 for c in cs if isinstance(c, dict)),
               "n_units_valid": len(_vals(cs, "units")),
               "n_shape_bad": sum(
                   1 for c in cs
                   if isinstance(c, dict) and isinstance(c.get("shape"), dict)
                   and (c["shape"].get("g_valid") is False
                        or c["shape"].get("b_valid") is False))}
        for name, fn, _desc in COVS:
            try:
                rec[name] = fn(gt, cs)
            except Exception:
                rec[name] = None
        windows.append(rec)

    say("inclusion: total=%d verdict_ok=%d p50_nonnull=%d used=%d" %
        (n_total, n_ok, n_p50, n_used))
    slow = [w for w in windows if w["p50"] > SLOW_MS]
    fast = [w for w in windows if w["p50"] <= SLOW_MS]
    say("slow(p50>%.0fms)=%d fast=%d  (慢/快切法=§603 口径，跨窗分组)" %
        (SLOW_MS, len(slow), len(fast)))

    def in_set(w, names):
        return w["d"] in names

    s15 = ("l1c_20261021", "l1d_20261021", "l1e_20261021",
           "l3_20261021", "t55k_20261020")
    fam = ("l1c_20261021", "l1d_20261021", "l1e_20261021", "l3_20261021")
    sets = [
        ("A_all_qualified", windows),
        ("B_set15_s603", [w for w in windows if in_set(w, s15)]),
        ("C_family12", [w for w in windows if in_set(w, fam)]),
    ]

    say("")
    say("== 逐窗明细（目录 | 文件 | p50ms | units0 | units_med | infantry_med | "
        "techno_med | g_med | b_med | ws_kb_med | pf_kb_med | d_units | "
        "n_snap/n_valid/shape_bad）==")
    for w in sorted(windows, key=lambda r: r["p50"]):
        say("  %-20s %-15s %7.1f %5s %7.1f %7.1f %7.1f %7.1f %5.1f %8.0f %8.0f %6.0f  %d/%d/%d" %
            (w["d"], w["f"], w["p50"], w["units0_pre"], w["units_med"],
             w["infantry_med"], w["techno_med"], w["g_med"], w["b_med"],
             w["ws_kb_med"], w["pf_kb_med"], w["d_units"],
             w["n_snap"], w["n_units_valid"], w["n_shape_bad"]))

    for sname, ws in sets:
        say("")
        say("== [%s] n=%d 慢=%d 快=%d — 按|rho|降序；rho=Spearman(frame_ms_p50, x)，"
            "p=置换p(20000次,种子20261107) ==" %
            (sname, len(ws), sum(1 for w in ws if w["p50"] > SLOW_MS),
             sum(1 for w in ws if w["p50"] <= SLOW_MS)))
        rows = []
        for name, _fn, desc in COVS:
            pairs = [(w[name], w["p50"]) for w in ws
                     if isinstance(w.get(name), (int, float))]
            if len(pairs) < 3:
                rows.append((name, desc, None, None, len(pairs), None, None, None,
                             "n<3"))
                continue
            xs = [a for a, _ in pairs]
            yy = [b for _, b in pairs]
            rho, p, n = spearman(xs, yy)
            pr = pearson(xs, yy)
            # 慢/快组内取的是**协变量 x 的中位**（不是 y 的组中位——那是恒等式）
            sl = median([a for a, b in pairs if b > SLOW_MS]) \
                if any(b > SLOW_MS for a, b in pairs) else None
            fa = median([a for a, b in pairs if b <= SLOW_MS]) \
                if any(b <= SLOW_MS for a, b in pairs) else None
            note = ("x恒定rho不可定义" if rho is None
                    else ("x↑y↑" if rho > 0 else "x↑y↓"))
            rows.append((name, desc, rho, p, n, pr, sl, fa, note))
        rows.sort(key=lambda r: -abs(r[2]) if r[2] is not None else -9)
        for name, desc, rho, p, n, pr, sl, fa, note in rows:
            rs = ("%+.3f" % rho) if rho is not None else "  n/a"
            if p is None:
                ps = "  n/a"
            elif p <= 1.0 / (NPERM + 1):
                ps = "<%.6g" % (1.0 / (NPERM + 1))
            else:
                ps = "%.4f" % p
            prs = ("%+.3f" % pr) if pr is not None else "  n/a"
            sls = ("%.1f" % sl) if sl is not None else "n/a"
            fas = ("%.1f" % fa) if fa is not None else "n/a"
            say("  %-13s rho=%s p=%s n=%2d pearson=%s 慢中位=%s 快中位=%s %s | %s" %
                (name, rs, ps, n, prs, sls, fas, note, desc))

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("WROTE", OUT, "lines:", len(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
