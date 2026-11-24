# -*- coding: utf-8 -*-
"""_dual_xcheck_scipy.py — 用 scipy/numpy 独立实现交叉复核 _dual_recompute.py 的四系数与 P2/P3

独立性：B% 用 itertools.groupby 另写一条实现路径；Spearman 用 scipy.stats.spearmanr；
       不 import _dual_recompute / _phase_recompute / _xbatch_verify 的任何代码。
语料：与主件相同的冻结口径（剔除 3 件后到件；mtime 证据见 _dual_recompute_out.txt §一）。
用法：python -I -X utf8 _dual_xcheck_scipy.py > _dual_xcheck_scipy_out.txt 2>&1
"""
import itertools
import json
import os
import statistics

import numpy as np
from scipy import stats

BASE = "D:/Project/ra2-campaign-forge"
ROOT = BASE + "/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
T = 0.100
BOOT_TOL = 2
LATE = {"l3_1101v4f/measure_w0.json", "l3_1101v4g/measure_w0.json", "l3_1101v4h/measure_w0.json"}


def P(s=""):
    print(s)


def b_pct_groupby(t, f):
    """B% 另一条实现：groupby 等值游程。定义同 BATCH_XVERIFY ① 表。"""
    span = t[-1] - t[0]
    if not span:
        return 0.0
    total = 0.0
    for _, grp in itertools.groupby(range(len(f)), key=lambda i: f[i]):
        idx = list(grp)
        d = t[idx[-1]] - t[idx[0]]
        if d > T:
            total += d
    return 100.0 * total / span


def collect():
    rows = []
    for trip in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, trip)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.startswith("measure_w") and fn.endswith(".json"):
                rel = trip + "/" + fn
                if rel in LATE:
                    continue
                rows.append((rel, trip, os.path.join(d, fn)))
    for i in range(3):
        fn = "measure_w%d.json" % i
        p = os.path.join(ROOT, fn)
        if os.path.isfile(p):
            rows.append(("(root)/" + fn, "(root)", p))
    out = []
    for rel, trip, p in rows:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        s = d.get("samples") or {}
        t, f = s.get("t"), s.get("f")
        ta = d.get("t_abs0")
        if not t or not f or len(t) < 2 or ta is None:
            continue
        out.append(dict(rel=rel, trip=trip, window=d.get("window"),
                        t=[float(x) for x in t], f=[int(x) for x in f],
                        t_abs0=float(ta)))
    return out


def main():
    wins = collect()
    mv = []
    for w in wins:
        w["B"] = b_pct_groupby(w["t"], w["f"])
        w["uptime"] = w["t"][0]
        w["boot"] = float(round(w["t_abs0"] - w["t"][0]))
        w["moving"] = any(w["f"][i] != w["f"][i - 1] for i in range(1, len(w["f"])))
        if w["moving"]:
            mv.append(w)
    P("xcheck: 有效窗=%d moving=%d（主件 97/64）" % (len(wins), len(mv)))

    P("")
    P("[64 moving 口径]")
    r1 = stats.spearmanr([float(w["window"]) for w in mv], [w["B"] for w in mv])
    r2 = stats.spearmanr([w["uptime"] for w in mv], [w["B"] for w in mv])
    P("   scipy spearmanr rho(window,B%%) = %.9f   (主件 -0.04026776101462127, dev=%.3e)"
      % (r1.statistic, abs(r1.statistic - (-0.04026776101462127))))
    P("   scipy spearmanr rho(uptime,B%%) = %.9f   (主件 +0.03945103538787863, dev=%.3e)"
      % (r2.statistic, abs(r2.statistic - 0.03945103538787863)))

    P("")
    P("[97 全量口径]")
    r3 = stats.spearmanr([float(w["window"]) for w in wins], [w["B"] for w in wins])
    r4 = stats.spearmanr([w["uptime"] for w in wins], [w["B"] for w in wins])
    P("   scipy spearmanr rho(window,B%%) = %.9f   (主件 +0.347432459482872, dev=%.3e)"
      % (r3.statistic, abs(r3.statistic - 0.347432459482872)))
    P("   scipy spearmanr rho(uptime,B%%) = %.9f   (主件 +0.3461192878606675, dev=%.3e)"
      % (r4.statistic, abs(r4.statistic - 0.3461192878606675)))

    # BOOT 聚类（同规则：先取整、±2s 链式）
    wins_sorted = sorted(wins, key=lambda w: w["boot"])
    groups = []
    for w in wins_sorted:
        if groups and w["boot"] - groups[-1]["last"] <= BOOT_TOL:
            groups[-1]["rows"].append(w)
            groups[-1]["last"] = w["boot"]
        else:
            groups.append({"rep": w["boot"], "last": w["boot"], "rows": [w]})
    P("")
    P("BOOT 数 = %d（主件 11）" % len(groups))
    P("")
    P("[P2 BOOT 内]（moving 且 n>=3）")
    within = []
    for g in groups:
        sel = [w for w in g["rows"] if w["moving"]]
        if len(sel) < 3:
            continue
        a = stats.spearmanr([w["uptime"] for w in sel], [w["B"] for w in sel]).statistic
        within.append(a)
        P("   rep=%s n=%2d rho(uptime,B) = %+.6f" % (g["rep"], len(sel), a))
    fin = [x for x in within if x == x]
    fin_sorted = sorted(fin)
    med = statistics.median(fin)
    P("   有限值=%d  正=%d 负=%d  scipy+statistics.median 中位 = %+.9f (主件 -0.343089263677499)"
      % (len(fin), sum(1 for x in fin if x > 0), sum(1 for x in fin if x < 0), med))

    P("")
    P("[P3 BOOT 间]")
    bx = [sum(w["uptime"] for w in g["rows"]) / len(g["rows"]) for g in groups]
    by = [sum(w["B"] for w in g["rows"]) / len(g["rows"]) for g in groups]
    r5 = stats.spearmanr(bx, by)
    P("   scipy spearmanr = %.9f  n=%d  (主件 -0.2369026647406667)"
      % (r5.statistic, len(bx)))

    P("")
    P("完。")


if __name__ == "__main__":
    main()
