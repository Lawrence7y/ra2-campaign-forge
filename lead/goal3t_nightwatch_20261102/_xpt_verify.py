# -*- coding: utf-8 -*-
"""
_xpt_verify.py —— 独立核验员（异族）实现（纯只读，只打印 stdout）。

只依据任务书给出的定义，独立实现「口径B 平台停滞」分析，用于证伪：
  判定一：所有「B%>=25 且 有推进 且 单段主导(最长段占>0.80)」的窗满足
          B% ≈ 100*(span-freezeStart)/span，误差<0.01个百分点。
  判定二：多次型(最长段占<0.40)窗的 B 段帧号严格递增且互不相同。

定义（照抄任务书）：
  T = 0.1 秒
  平台 = f 相同的连续样本；平台停滞时长 = 该平台最后样本t − 第一样本t；只计 > T 的平台。
  B% = 100 × Σ(计入平台时长) / (t[-1] − t[0])
  有推进 = 窗内 f 至少变化过一次
  最长段占 = 最长计入平台时长 / Σ(计入平台时长)；>0.80 单段主导；<0.40 多次型
  freezeStart = 帧号最后一次变化的时刻（相对窗首 = t[lastEdge] − t[0]）
  恒等式：|B% − 100*(span−freezeStart)/span| < 0.01

枚举：out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/ 下所有
measure_w*.json（递归），必须含数据根直属 3 个散件。
有效窗 = samples 存在且 len(t)>=2。
"""
import json
import os
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
DATA = os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003",
                    "lead", "qc161_u0400_trip")
T = 0.1
IDENT_EPS = 0.01  # 百分点


def find_files():
    hits = []
    for dirpath, dirnames, filenames in os.walk(DATA):
        dirnames.sort()
        for fn in sorted(filenames):
            if fn.startswith("measure_w") and fn.endswith(".json"):
                hits.append(os.path.join(dirpath, fn))
    hits.sort(key=lambda p: os.path.relpath(p, DATA).replace("\\", "/"))
    return hits


def analyze(fp):
    """返回 (row, err_msg)。row 为 None 表示窗无效。"""
    rel = os.path.relpath(fp, DATA).replace("\\", "/")
    parts = rel.split("/")
    trip = parts[0] if len(parts) > 1 else "ROOT"
    wname = parts[-1][len("measure_"):-len(".json")]
    label = "trip %s %s" % (trip, wname)

    try:
        with open(fp, "r", encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception as e:  # noqa
        return None, "%s: JSON读取失败 %r" % (label, e)

    if not isinstance(d, dict) or not isinstance(d.get("samples"), dict):
        return None, "%s: samples 缺失或非dict" % label
    s = d["samples"]
    if "t" not in s or "f" not in s:
        return None, "%s: samples 缺 t/f" % label
    t, f = s["t"], s["f"]
    if not isinstance(t, list) or not isinstance(f, list):
        return None, "%s: t/f 非列表" % label
    if len(t) < 2:
        return None, "%s: len(t)=%d <2" % (label, len(t))
    if len(f) != len(t):
        return None, "%s: len(f)=%d != len(t)=%d" % (label, len(f), len(t))

    n = len(t)
    t0, tN = t[0], t[-1]
    span = tN - t0

    # 单调性检查
    mono_bad = sum(1 for i in range(1, n) if t[i] < t[i - 1])

    # 平台：连续相同 f 的极大游程
    plats = []  # (fval, i_first, i_last)
    start = 0
    for i in range(1, n):
        if f[i] != f[i - 1]:
            plats.append((f[i - 1], start, i - 1))
            start = i
    plats.append((f[n - 1], start, n - 1))

    durs = [t[e] - t[b] for (_, b, e) in plats]
    counted = [(fv, b, e, du) for (fv, b, e), du in zip(plats, durs) if du > T]
    b_sum = sum(c[3] for c in counted)
    b_pct = 100.0 * b_sum / span if span > 0 else 0.0

    # 有推进
    edges = [i for i in range(1, n) if f[i] != f[i - 1]]
    has_prog = bool(edges)
    freeze_start_rel = (t[edges[-1]] - t0) if edges else None

    n_segs = len(counted)
    longest_share = None
    if n_segs > 0 and b_sum > 0:
        longest_share = max(c[3] for c in counted) / b_sum

    # 恒等式（仅当有推进时 freezeStart 相对量有定义）
    ident = None
    ident_err = None
    pred = None
    if has_prog and span > 0:
        pred = 100.0 * (span - freeze_start_rel) / span
        ident_err = abs(b_pct - pred)
        ident = ident_err < IDENT_EPS

    # 分段帧号序列（按时间序）
    seg_fvals = [c[0] for c in counted]
    seg_strict_inc = all(seg_fvals[i] < seg_fvals[i + 1]
                         for i in range(len(seg_fvals) - 1))
    seg_distinct = len(set(seg_fvals)) == n_segs
    seg_no_desc_pair = all(seg_fvals[i] <= seg_fvals[j]
                           for i in range(len(seg_fvals))
                           for j in range(i + 1, len(seg_fvals)))

    # 主导段是否为最末平台（「大停滞后又动过」检查）
    dom_is_final = None
    if n_segs > 0:
        dom_idx = max(range(n_segs), key=lambda k: counted[k][3])
        dom_is_final = (counted[dom_idx][2] == n - 1)

    # 阈值边界敏感段：时长落在 0.1±0.002 的平台
    borderline = [round(du, 6) for du in durs if abs(du - T) <= 0.002]

    row = dict(
        label=label, n=n, span=span, mono_bad=mono_bad,
        n_plats=len(plats), n_segs=n_segs, b_sum=b_sum, b_pct=b_pct,
        has_prog=has_prog, freeze_start_rel=freeze_start_rel,
        pred=pred, ident_err=ident_err, ident=ident,
        longest_share=longest_share,
        seg_fvals=seg_fvals, seg_strict_inc=seg_strict_inc,
        seg_distinct=seg_distinct, seg_no_desc_pair=seg_no_desc_pair,
        dom_is_final=dom_is_final, borderline=borderline,
    )
    return row, None


def main():
    files = find_files()
    root_loose = [fp for fp in files
                  if os.path.dirname(fp) == DATA]
    rows = []
    errs = []
    for fp in files:
        row, err = analyze(fp)
        if err:
            errs.append(err)
        if row:
            rows.append(row)

    def cls(r):
        ls = r["longest_share"]
        if ls is None:
            return "noseg"
        if ls > 0.80:
            return "single"
        if ls < 0.40:
            return "multi"
        return "mid"

    for r in rows:
        r["cls"] = cls(r)

    hsm = [r for r in rows if r["b_pct"] >= 25.0 and r["has_prog"]]
    singles = [r for r in hsm if r["cls"] == "single"]
    multis = [r for r in hsm if r["cls"] == "multi"]
    mids = [r for r in hsm if r["cls"] == "mid"]

    ident_ok = [r for r in singles if r["ident"]]
    ident_bad = [r for r in singles if not r["ident"]]

    # 反例类
    ce1 = ident_bad                                   # 单段主导但恒等式不成立
    ce1b = [r for r in singles if r["dom_is_final"] is False]  # 大停滞后又动过
    ce1c = [r for r in singles if r["n_segs"] > 1]    # 多段却单段主导
    ce2 = [r for r in multis if not (r["seg_strict_inc"] and r["seg_distinct"]
                                     and r["seg_no_desc_pair"])]

    out = []
    w = out.append
    w("=" * 78)
    w("独立核验 _xpt_verify.py 输出")
    w("枚举根: %s" % DATA)
    w("枚举文件总数: %d；其中数据根直属散件: %s"
      % (len(files), [os.path.basename(p) for p in root_loose]))
    w("有效窗(len(t)>=2): %d；无效: %d" % (len(rows), len(errs)))
    for e in errs:
        w("  无效明细: %s" % e)
    mono_bad_rows = [r for r in rows if r["mono_bad"]]
    w("t 出现非单调的窗: %d %s" % (len(mono_bad_rows),
                                   [r["label"] for r in mono_bad_rows]))

    w("")
    w("—— 分类（全部有效窗）——")
    for k in ("single", "multi", "mid", "noseg"):
        w("  %-6s: %d" % (k, sum(1 for r in rows if r["cls"] == k)))

    w("")
    w("—— 高停滞且有推进（B%%>=25 且 有推进）：共 %d 窗 ——" % len(hsm))
    w("%-28s %7s %9s %9s %6s %10s %10s %10s %9s %6s %5s %5s %s"
      % ("window", "B%", "span", "frzStart", "nSegs", "Bsum",
         "pred", "identErr", "longest%", "domFin", "inc", "dst", "segFvals"))
    for r in sorted(hsm, key=lambda r: r["label"]):
        w("%-28s %7.4f %9.4f %9.4f %6d %10.4f %10.4f %10.2e %9.4f %6s %5s %5s %s"
          % (r["label"], r["b_pct"], r["span"],
             (r["freeze_start_rel"] if r["freeze_start_rel"] is not None else -1.0),
             r["n_segs"], r["b_sum"], (r["pred"] if r["pred"] is not None else -1.0),
             (r["ident_err"] if r["ident_err"] is not None else -1.0),
             (r["longest_share"] if r["longest_share"] is not None else -1.0),
             str(r["dom_is_final"]), str(r["seg_strict_inc"]), str(r["seg_distinct"]),
             r["seg_fvals"] if r["n_segs"] <= 8 else str(r["seg_fvals"][:8]) + "..."))

    w("")
    w("—— 判定一核对 ——")
    w("单段主导(最长段占>0.80)窗数（高停滞有推进集合内）: %d" % len(singles))
    w("恒等式成立: %d；不成立: %d" % (len(ident_ok), len(ident_bad)))
    w("单段主导窗中 nSegs>1 的窗数: %d  labels=%s"
      % (len(ce1c), [r["label"] for r in ce1c]))
    w("单段主导窗中主导段非最末平台（大停滞后又动过）: %d  labels=%s"
      % (len(ce1b), [r["label"] for r in ce1b]))
    w("")
    for r in singles:
        w("  [S] %-28s B%%=%.4f pred=%.4f err=%.3e nSegs=%d longest=%.4f "
          "domFin=%s freeze=%.4f span=%.4f segFvals=%s"
          % (r["label"], r["b_pct"], r["pred"], r["ident_err"], r["n_segs"],
             r["longest_share"], r["dom_is_final"], r["freeze_start_rel"],
             r["span"], r["seg_fvals"]))
    for r in ident_bad:
        w("  [!!CE1] %-28s B%%=%.4f pred=%.4f err=%.4f" %
          (r["label"], r["b_pct"], r["pred"], r["ident_err"]))

    w("")
    w("—— 判定二核对 ——")
    w("多次型(最长段占<0.40)窗数（高停滞有推进集合内）: %d" % len(multis))
    all_multi_ok = all(r["seg_strict_inc"] and r["seg_distinct"]
                       and r["seg_no_desc_pair"] for r in multis)
    w("全部多次型窗 B 段帧号严格递增且互不相同: %s" % all_multi_ok)
    for r in multis:
        ok = (r["seg_strict_inc"] and r["seg_distinct"]
              and r["seg_no_desc_pair"])
        w("  [M] %-28s nSegs=%d longest=%.4f strictInc=%s distinct=%s "
          "noDescPair=%s fvals=%s %s"
          % (r["label"], r["n_segs"], r["longest_share"], r["seg_strict_inc"],
             r["seg_distinct"], r["seg_no_desc_pair"], r["seg_fvals"],
             "" if ok else "  <<CE2"))
    for r in ce2:
        w("  [!!CE2] %s fvals=%s" % (r["label"], r["seg_fvals"]))

    w("")
    w("—— 中间带（0.40<=最长段占<=0.80，两类都不算）——")
    w("窗数: %d" % len(mids))
    for r in mids:
        w("  [?] %-28s B%%=%.4f nSegs=%d longest=%.4f identErr=%.3e segFvals=%s"
          % (r["label"], r["b_pct"], r["n_segs"], r["longest_share"],
             (r["ident_err"] if r["ident_err"] is not None else -1.0),
             r["seg_fvals"]))

    w("")
    w("—— 阈值边界敏感（平台时长在 0.1±0.002 内）——")
    nb = 0
    for r in rows:
        if r["borderline"]:
            nb += 1
            w("  [~] %-28s nSegs=%d B%%=%.4f cls=%s borderline=%s"
              % (r["label"], r["n_segs"], r["b_pct"], r["cls"], r["borderline"]))
    w("含边界敏感平台的窗数: %d" % nb)

    w("")
    w("—— 汇总行 ——")
    w("validWindows=%d highStallMoving=%d singleSegmentCount=%d "
      "identityHoldsCount=%d multiSegmentCount=%d multiStrictlyIncreasing=%s"
      % (len(rows), len(hsm), len(singles), len(ident_ok), len(multis),
         all_multi_ok))
    w("counterExamples CE1(单段主导恒等式不成立)=%d CE1b(主导段非末平台)=%d "
      "CE1c(多段却单段主导)=%d CE2(多次型帧号不严格递增/不互异)=%d"
      % (len(ce1), len(ce1b), len(ce1c), len(ce2)))

    print("\n".join(out))


if __name__ == "__main__":
    main()
