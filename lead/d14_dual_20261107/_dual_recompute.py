# -*- coding: utf-8 -*-
"""_dual_recompute.py — D-14 双口径离线复算（64 moving / 97 全量 并列，不裁决）

任务（2026-11-07）：
  1) 从原始语料 measure_w*.json 重算两个窗口集的四个 Spearman 系数，
     与既有公布值逐位比对（§522: -0.0403/+0.0395；§528 异族: +0.347432/+0.346119）。
  2) 按 PHASE_BY_BOOT BOOT 反推法（boot=round(t_abs0-t[0]) 先取整再聚类 ±2s 链式）
     复算 P2「可算 8 个 BOOT 内 4 负/2 正、中位 +0.4472」——含按原缺陷实现复现
     sorted()[len//2] 的结果与按 D-26 更正（滤 nan、偶数取中央均值）的结果。
  3) 语料漂移披露：2026-11-04 公布后语料新增 3 件（mtime 证据），现状全量重算并列。

方法依据（只读既有件，未 import 其代码）：
  - lead/goal3t_nightwatch_20261102/BATCH_XVERIFY_20261103.md ①（口径B定义表）
  - lead/goal3t_nightwatch_20261102/_phase_recompute.py（BOOT 反推与聚类规则，:105/:124-132）
  - lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md §1/§4 + ERRATUM 二/三

用法：python -I -X utf8 _dual_recompute.py > _dual_recompute_out.txt 2>&1
"""

import datetime
import hashlib
import json
import os

BASE = "D:/Project/ra2-campaign-forge"
OUTDIR = BASE + "/lead/d14_dual_20261107"          # 唯一写域（常量绝对路径）
ROOT = BASE + "/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
NW = BASE + "/lead/goal3t_nightwatch_20261102"
T = 0.100          # 口径B阈值，D-12② 已裁 B 为准（PHASE_BY_BOOT :5）
BOOT_TOL = 2       # ±2s 同一 BOOT（链式比较）

# 语料漂移：公布运行（_phase_recompute_out.txt mtime=2026-11-04 00:25:57）之后新增的 3 件
LATE_FILES = [
    "l3_1101v4f/measure_w0.json",
    "l3_1101v4g/measure_w0.json",
    "l3_1101v4h/measure_w0.json",
]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def P(s=""):
    print(s)


# ---------------------------------------------------------------- 口径B（BATCH_XVERIFY ① 定义表）
def b_pct(ts, fs):
    """平台=同 f 连续样本段（闭区间 [i,j]），时长 t[j]-t[i]，严格 >T 计入；
    B% = 100 * Σ计入 / (t[-1]-t[0])。span==0 时返回 0.0（与 _phase_recompute.py:39-40 一致）。"""
    n = len(ts)
    span = ts[-1] - ts[0]
    if not span:
        return 0.0
    segs = []
    i = 0
    while i < n:
        j = i
        while j + 1 < n and fs[j + 1] == fs[i]:
            j += 1
        d = ts[j] - ts[i]
        if d > T:
            segs.append(d)
        i = j + 1
    return 100.0 * sum(segs) / span


# ---------------------------------------------------------------- 手写 Pearson/Spearman（定义实现）
def rank(vs):
    order = sorted(range(len(vs)), key=lambda i: vs[i])
    r = [0.0] * len(vs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vs[order[j + 1]] == vs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0     # 并列取平均秩（1 基）
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else float("nan")


def spearman(xs, ys):
    return pearson(rank(xs), rank(ys))


# ---------------------------------------------------------------- 枚举（_phase_recompute.py:111-122 规则）
def enumerate_windows():
    """趟子目录（sorted listdir）+ 数据根散件 measure_w0/w1/w2。返回全部命中件。"""
    hits = []
    for trip in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, trip)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.startswith("measure_w") and f.endswith(".json"):
                hits.append((trip, f))
    for i in range(3):
        fn = "measure_w%d.json" % i
        if os.path.isfile(os.path.join(ROOT, fn)):
            hits.append(("(root)", fn))
    return hits


def load_row(trip, fname):
    p = os.path.join(ROOT, "" if trip == "(root)" else trip, fname)
    try:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return None
    rel = (trip + "/" + fname) if trip != "(root)" else ("(root)/" + fname)
    s = d.get("samples") or {}
    ts, fs = s.get("t"), s.get("f")
    ta = d.get("t_abs0")
    # 有效性（phase_recompute 规则 :102）：ts/fs 非空、len>=2、t_abs0 存在
    if not ts or not fs or len(ts) < 2 or ta is None:
        return dict(rel=rel, valid=False, reason="empty/len<2/no t_abs0",
                    len_t=len(ts) if isinstance(ts, list) else -1,
                    len_f=len(fs) if isinstance(fs, list) else -1)
    # 有效性（xbatch 规则 :117-125）：len(t)>=2 且 len(f)>=2 且 len(t)==len(f)
    xbatch_valid = (len(fs) >= 2 and len(ts) == len(fs))
    return dict(rel=rel, trip=trip, wname="w" + fname[9:-5],
                valid=True, xbatch_valid=xbatch_valid,
                window=d.get("window"),
                t_abs0=float(ta),
                uptime=float(ts[0]),
                boot=float(round(float(ta) - float(ts[0]))),   # 先取整再聚类
                B=b_pct([float(x) for x in ts], [x for x in fs]),
                moving=any(fs[i] != fs[i - 1] for i in range(1, len(fs))),
                span=float(ts[-1]) - float(ts[0]),
                units0=(d.get("gate") or {}).get("units0"),
                mtime=datetime.datetime.fromtimestamp(os.stat(p).st_mtime).strftime("%Y-%m-%d %H:%M:%S"))


def cluster(rows):
    rows = sorted(rows, key=lambda r: r["boot"])
    groups = []
    for r in rows:
        if groups and r["boot"] - groups[-1]["last"] <= BOOT_TOL:
            groups[-1]["rows"].append(r)
            groups[-1]["last"] = r["boot"]
        else:
            groups.append({"rep": r["boot"], "last": r["boot"], "rows": [r]})
    return groups


def boot_label(rep):
    return datetime.datetime.fromtimestamp(rep).strftime("%m-%d %H:%M")


def run_pipeline(rows_all_valid, title):
    """rows_all_valid: 全部有效窗行（不做 moving 预过滤）。返回汇总 dict。"""
    mv = [r for r in rows_all_valid if r["moving"]]
    out = {"n_valid": len(rows_all_valid), "n_moving": len(mv)}
    P("")
    P("=" * 104)
    P(title)
    P("=" * 104)
    # ---- P1 双口径
    w_mv = [float(r["window"]) for r in mv if r["window"] is not None]
    u_mv = [r["uptime"] for r in mv if r["window"] is not None]
    b_mv = [r["B"] for r in mv if r["window"] is not None]
    r_w_mv = spearman(w_mv, b_mv)
    r_u_mv = spearman(u_mv, b_mv)
    P("[moving 口径] n=%d" % len(w_mv))
    P("   rho(window, B%%) = %+.6f   (repr %r)" % (r_w_mv, r_w_mv))
    P("   rho(uptime, B%%) = %+.6f   (repr %r)" % (r_u_mv, r_u_mv))
    w_all = [float(r["window"]) for r in rows_all_valid if r["window"] is not None]
    u_all = [r["uptime"] for r in rows_all_valid if r["window"] is not None]
    b_all = [r["B"] for r in rows_all_valid if r["window"] is not None]
    r_w_all = spearman(w_all, b_all)
    r_u_all = spearman(u_all, b_all)
    P("[全量口径] n=%d" % len(w_all))
    P("   rho(window, B%%) = %+.6f   (repr %r)" % (r_w_all, r_w_all))
    P("   rho(uptime, B%%) = %+.6f   (repr %r)" % (r_u_all, r_u_all))
    out.update(n_moving_nw=len(w_mv), n_full_nw=len(w_all),
               rho_w_moving=r_w_mv, rho_u_moving=r_u_mv,
               rho_w_full=r_w_all, rho_u_full=r_u_all)
    # ---- BOOT 聚类表
    groups = cluster(list(rows_all_valid))
    P("")
    P("BOOT 聚类（boot=round(t_abs0-t[0])，±%ds 链式）: BOOT 数 = %d" % (BOOT_TOL, len(groups)))
    P("   %-14s %5s %5s %7s %14s" % ("BOOT", "趟", "窗", "有推进", "uptime范围(h)"))
    P("   " + "-" * 62)
    for g in groups:
        ups = [r["uptime"] for r in g["rows"]]
        P("   %-14s %5d %5d %7d %6.2f..%5.2f"
          % (boot_label(g["rep"]), len({r["trip"] for r in g["rows"]}), len(g["rows"]),
             sum(1 for r in g["rows"] if r["moving"]),
             min(ups) / 3600.0, max(ups) / 3600.0))
    # ---- P2 BOOT 内（n>=3 moving；与 _phase_recompute.py:183-189 同规则）
    P("")
    P("P2 BOOT 内（moving 且 n>=3）:")
    P("   %-14s %4s %14s %14s" % ("BOOT", "n", "rho(uptime,B)", "rho(window,B)"))
    P("   " + "-" * 62)
    within = []            # 与原脚本同序（boot 升序、组内枚举序）
    for g in groups:
        sel = [r for r in g["rows"] if r["moving"] and r["window"] is not None]
        if len(sel) < 3:
            continue
        r1 = spearman([r["uptime"] for r in sel], [r["B"] for r in sel])
        r2 = spearman([float(r["window"]) for r in sel], [r["B"] for r in sel])
        within.append(r1)
        P("   %-14s %4d %+14.4f %+14.4f"
          % (boot_label(g["rep"]), len(sel), r1, r2))
    fin = [x for x in within if x == x]      # 滤 nan
    pos = sum(1 for x in fin if x > 0)
    neg = sum(1 for x in fin if x < 0)
    fin_sorted = sorted(fin)
    m = len(fin_sorted)
    correct_median = (fin_sorted[m // 2] if m % 2 else
                      (fin_sorted[m // 2 - 1] + fin_sorted[m // 2]) / 2.0)
    P("")
    P("   [D-26 更正口径] 有限值 = %d 个（nan %d 个已排除）；正 %d / 负 %d"
      % (m, len(within) - m, pos, neg))
    P("   [D-26 更正口径] 有限值排序 = %s" % ["%+.4f" % x for x in fin_sorted])
    P("   [D-26 更正口径] 正确中位（偶数取中央两项均值）= %+.6f (repr %r)"
      % (correct_median, correct_median))
    # 复现原缺陷（_phase_recompute.py:197: sorted(within)[len//2]，nan 未滤）
    if within:
        buggy = sorted(within)[len(within) // 2]
        P("   [原缺陷复现] sorted(within)[len//2]（含 nan，%d 个）= %r" % (len(within), buggy))
        out["buggy_median"] = buggy
    out.update(p2_finite=m, p2_pos=pos, p2_neg=neg, p2_median_correct=correct_median,
               p2_values=fin_sorted)
    # ---- P3 BOOT 间
    boot_x, boot_y = [], []
    P("")
    P("P3 BOOT 间（全部窗均值）:")
    P("   %-14s %4s %10s %10s" % ("BOOT", "n", "uptime(h)", "B%均值"))
    P("   " + "-" * 54)
    for g in groups:
        up = sum(r["uptime"] for r in g["rows"]) / len(g["rows"])
        bb = sum(r["B"] for r in g["rows"]) / len(g["rows"])
        boot_x.append(up)
        boot_y.append(bb)
        P("   %-14s %4d %10.2f %10.2f" % (boot_label(g["rep"]), len(g["rows"]), up / 3600.0, bb))
    r_p3 = spearman(boot_x, boot_y)
    P("   rho(BOOT均值 uptime, BOOT均值 B%%) = %+.6f (repr %r)  n=%d"
      % (r_p3, r_p3, len(boot_x)))
    out["rho_p3"] = r_p3
    return out


def compare(mine, pub, nd):
    if mine != mine and pub != pub:
        return True, float("nan")
    d = abs(mine - pub)
    fmt = "%." + str(nd) + "f"
    return (fmt % d) == ("0." + "0" * nd), d


def main():
    P("双口径复算 _dual_recompute.py  运行时刻 %s"
      % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    P("语料根: " + ROOT)
    P("零真机 / 零采样代码 / 只读语料；本脚本输出全部经 stdout 重定向落入写域 out.txt。")

    # 〇、被核对象指纹
    P("")
    P("=" * 104)
    P("## 〇、被核对象 SHA256（本机实跑 hashlib）")
    P("=" * 104)
    for rel in ["lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md",
                "lead/goal3t_nightwatch_20261102/BATCH_XVERIFY_20261103.md",
                "lead/goal3t_nightwatch_20261102/_phase_recompute.py",
                "lead/goal3t_nightwatch_20261102/_phase_recompute_out.txt",
                "lead/goal3t_nightwatch_20261102/_xbatch_verify_out.txt",
                "lead/PENDING_DECISIONS.md"]:
        p = os.path.join(BASE, rel.replace("/", os.sep))
        P("被核对象 SHA256 = %s，字节数 = %d  <- %s" % (sha256_file(p), os.path.getsize(p), rel))

    # 一、语料清点与冻结
    hits = enumerate_windows()
    late_set = set(LATE_FILES)
    frozen_hits = [h for h in hits if ("%s/%s" % h) not in late_set]
    P("")
    P("=" * 104)
    P("## 一、语料清点（枚举=趟子目录+数据根散件，_phase_recompute.py:111-122 规则）")
    P("=" * 104)
    P("现状命中 measure_w*.json = %d 件；冻结语料（剔除 %d 件后到件）= %d 件"
      % (len(hits), len(LATE_FILES), len(frozen_hits)))
    P("后到件 mtime 证据（公布输出 _phase_recompute_out.txt mtime = %s）："
      % datetime.datetime.fromtimestamp(
          os.stat(os.path.join(NW, "_phase_recompute_out.txt")).st_mtime).strftime("%Y-%m-%d %H:%M:%S"))
    for rel in LATE_FILES:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        P("   %s  mtime=%s  sha256=%s"
          % (rel, datetime.datetime.fromtimestamp(os.stat(p).st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
             sha256_file(p)))

    rows_frozen, drop_frozen = [], []
    for trip, fname in frozen_hits:
        r = load_row(trip, fname)
        if r is None:
            drop_frozen.append((("%s/%s" % (trip, fname)), "parse error"))
        elif not r["valid"]:
            drop_frozen.append((r["rel"], r["reason"]))
        else:
            rows_frozen.append(r)
    P("")
    P("冻结语料：phase 规则有效窗 = %d，剔除 = %d" % (len(rows_frozen), len(drop_frozen)))
    for rel, why in drop_frozen:
        P("   - %s  (%s)" % (rel, why))
    P("   （公布剔除件对照 _xbatch_verify_out.txt:8-11：l1_20261023c / l3_1101v3c / l3_1101v4b / l3_20261023 的 w0）")
    xb = [r for r in rows_frozen if not r["xbatch_valid"]]
    P("phase 规则与 xbatch 规则（len(t)==len(f)）有效性差异件数 = %d" % len(xb))
    P("span==0 的有效窗 = %d" % sum(1 for r in rows_frozen if r["span"] == 0.0))
    P("有推进 moving = %d / %d" % (sum(1 for r in rows_frozen if r["moving"]), len(rows_frozen)))

    # B% 逐窗交叉核对（_xbatch_verify_out.txt:35-49 公布的 15 个单段主导窗 B%，5 位小数）
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
    byrel = {r["rel"]: r for r in rows_frozen}
    devs = []
    P("")
    P("B%% 逐窗核对（15 个公布值，_xbatch_verify_out.txt:35-49）：")
    for rel, bv in sorted(pub_b.items()):
        mine = byrel[rel]["B"]
        dev = abs(mine - bv)
        devs.append(dev)
        P("   %-38s 公布=%9.5f  本算=%12.6f  |dev|=%.2e" % (rel, bv, mine, dev))
    P("   最大偏差 = %.3e （<=5e-6 即 5 位小数逐位吻合）" % max(devs) if devs else "   （无）")

    # C1 旁证（实现自检，公布值 _xbatch_verify_out.txt:18）
    mv64 = [r for r in rows_frozen if r["moving"]]
    xs = [float(r["units0"]) for r in mv64 if r["units0"] is not None]
    ys = [r["B"] for r in mv64 if r["units0"] is not None]
    P("")
    P("C1 旁证（实现自检）：n=%d  Pearson r = %+.6f（公布 -0.200527）  Spearman rho = %+.6f（公布 -0.170611）"
      % (len(xs), pearson(xs, ys), spearman(xs, ys)))

    # 二、冻结语料主复算（双口径 + BOOT）
    res_f = run_pipeline(rows_frozen, "## 二、P1/P2/P3 —— 冻结语料（=公布时 97 窗语料）【主回件】")

    # 与公布值逐位比对
    P("")
    P("=" * 104)
    P("## 三、与既有公布值逐位比对（冻结语料）")
    P("=" * 104)
    checks = [
        ("64 moving rho(window,B%%)", res_f["rho_w_moving"], -0.0403, 4, "GOAL:2465 / PHASE:25"),
        ("64 moving rho(window,B%%)", res_f["rho_w_moving"], -0.040268, 6, "XVERIFY:26"),
        ("64 moving rho(uptime,B%%)", res_f["rho_u_moving"], +0.0395, 4, "GOAL:2466 / PHASE:26"),
        ("64 moving rho(uptime,B%%)", res_f["rho_u_moving"], +0.039451, 6, "XVERIFY:26"),
        ("97 全量   rho(window,B%%)", res_f["rho_w_full"], +0.3474, 4, "PHASE:30"),
        ("97 全量   rho(window,B%%)", res_f["rho_w_full"], +0.347432, 6, "XVERIFY:27 / GOAL:2936"),
        ("97 全量   rho(uptime,B%%)", res_f["rho_u_full"], +0.3461, 4, "PHASE:31"),
        ("97 全量   rho(uptime,B%%)", res_f["rho_u_full"], +0.346119, 6, "XVERIFY:27 / GOAL:2936"),
        ("P3 BOOT 间 rho", res_f["rho_p3"], -0.2369, 4, "PHASE:59"),
    ]
    for name, mine, pub, nd, src in checks:
        ok, d = compare(mine, pub, nd)
        P("   %-26s 本算 %+.6f  公布 %+.4f  |dev|=%-.3e  %-28s %s"
          % (name, mine, pub, d, src, "MATCH" if ok else "DIFF"))

    # P2 表值比对（PHASE_BY_BOOT :62-69 / _phase_recompute_out.txt:41-48）
    pub_p2 = [
        ("10-16 12:10", 16, -0.2176, +0.4920), ("10-19 14:31", 6, +0.6547, +0.5477),
        ("10-21 09:45", 12, -0.4685, -0.3844), ("10-26 15:14", 3, -0.5000, 0.0000),
        ("10-30 13:10", 5, +0.4472, +0.8250), ("10-31 08:26", 13, -0.8061, +0.0058),
        ("11-01 15:51", 3, float("nan"), float("nan")), ("11-03 08:54", 3, float("nan"), float("nan")),
    ]
    P("")
    P("P2 逐 BOOT 表值比对（公布 _phase_recompute_out.txt:41-48，4dp）：")
    groups = cluster(list(rows_frozen))
    gi = 0
    all_ok = True
    for g in groups:
        sel = [r for r in g["rows"] if r["moving"] and r["window"] is not None]
        if len(sel) < 3:
            continue
        lbl, pn, pu, pw = pub_p2[gi]
        r1 = spearman([r["uptime"] for r in sel], [r["B"] for r in sel])
        r2 = spearman([float(r["window"]) for r in sel], [r["B"] for r in sel])
        ok1, d1 = compare(r1, pu, 4)
        ok2, d2 = compare(r2, pw, 4)
        okn = (len(sel) == pn)
        all_ok = all_ok and ok1 and ok2 and okn
        P("   %-14s n=%d/%d %s  uptime列 %+.4f vs %+.4f %s   window列 %+.4f vs %+.4f %s"
          % (boot_label(g["rep"]), len(sel), pn, "nMATCH" if okn else "nDIFF",
             r1, pu, "MATCH" if ok1 else "DIFF", r2, pw, "MATCH" if ok2 else "DIFF"))
        gi += 1
    P("   P2 表值全比对（n、两列、nan 位置）= %s" % ("MATCH" if all_ok else "DIFF"))

    # 汇总句复算
    P("")
    P("## 四、汇总句复算：「可算 8 个 BOOT / 4 负 2 正 / 中位 +0.4472」")
    P("-" * 104)
    P("   原句（PHASE_BY_BOOT:71 / GOAL:3505 / PENDING:55）：可算 8 个 BOOT，负 4 / 正 2，中位 +0.4472")
    P("   本算（D-26 更正口径）：有限值 = %d 个（另有 %d 个 nan）" % (res_f["p2_finite"], 8 - res_f["p2_finite"]))
    P("                       uptime 列 正 %d / 负 %d" % (res_f["p2_pos"], res_f["p2_neg"]))
    P("                       正确中位 = %+.6f" % res_f["p2_median_correct"])
    if "buggy_median" in res_f:
        P("   原缺陷实现复现 sorted(within)[len//2]（含 nan）= %r  （公布句 +0.4472）" % res_f["buggy_median"])
    P("   依据 D-26（PENDING:144-147）：4 负/2 正 只描述 uptime 列；中位 +0.4472 已被撤销。")

    # 五、语料漂移敏感性（现状全量）
    rows_now = []
    for trip, fname in hits:
        r = load_row(trip, fname)
        if r is not None and r["valid"]:
            rows_now.append(r)
    res_n = run_pipeline(rows_now, "## 五、语料漂移敏感性 —— 现状语料（%d 件命中，%d 有效窗）【仅披露，非第三口径】"
                         % (len(hits), len(rows_now)))
    P("")
    P("   注：现状语料较公布时新增 l3_1101v4f/w0、l3_1101v4g/w0（有效、no_advance）、l3_1101v4h/w0（空样本）。")
    P("       64 moving 口径不受影响（新增两窗无推进）；97 全量口径变为 n=%d 全量。" % res_n["n_full_nw"])
    P("       本节仅为语料漂移披露，D-14 双口径仍按公布语料（97/64）并列呈现，不构成第三口径。")

    # 六、逐窗清单打进 stdout（随重定向落 out.txt；脚本不另写文件）
    P("")
    P("=" * 104)
    P("## 六、冻结语料逐窗清单（%d 行，排序=boot,rel）" % len(rows_frozen))
    P("=" * 104)
    P("%-38s %3s %12s %14s %10s %5s %s" % ("rel", "win", "boot", "uptime", "B%", "mov", "trip"))
    for r in sorted(rows_frozen, key=lambda r: (r["boot"], r["rel"])):
        P("%-38s %3s %12.1f %14.6f %10.4f %5s %s"
          % (r["rel"], r["window"], r["boot"], r["uptime"], r["B"], r["moving"], r["trip"]))
    P("完。")


if __name__ == "__main__":
    main()
