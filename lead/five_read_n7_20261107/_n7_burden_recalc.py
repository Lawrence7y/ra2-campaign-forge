# -*- coding: utf-8 -*-
"""N-7 五读负担第二方独立复算（不与 D21_RULING/_d21_burden5.py 共享任何代码）。

只读既有 measure_w*.json 离线数据。零真机、零采样代码、无任何进程/游戏路径。
口径全部取自上游定义（详见输出头注释）：
  - 数据源 glob 语义：qc161_u0400_trip/<一级子目录>/measure_w*.json
  - 纳入规则：span_s == 25.0 且 stats.samples > 0
  - 分母（基线）：87 窗 Σ stats.samples（既有 500 Hz 轮询 CurrentFrame 读数）
  - 沿表口径：Σ stats.n_edges（含每窗首采样点）
  - 跳变口径：Σ max(0, n_edges - 1)（首样不触发）
  - 双窗口集合：87 窗整体 与 最坏单窗（按 n_edges 最大者）
  - 公式：负担% = 100 × 每沿读次 n × 沿数 / 基线读数
  - 字节：每读 4 B（u32）
"""
import json
import os
import re
from fractions import Fraction

ROOT = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
NAME_RE = re.compile(r"^measure_w.*\.json$")

def pct(n_reads, edges, samples):
    """负担百分比，用精确分数，避免浮点中间误差。"""
    return Fraction(100 * n_reads * edges, samples)

def fmt(fr, dp):
    """Fraction -> 固定小数位字符串（十进制截断+手写四舍五入，不用 float）。"""
    scaled = fr * (10 ** dp)
    q, r = divmod(scaled.numerator, scaled.denominator)
    # 四舍五入：2*r 与分母比较
    if 2 * r >= scaled.denominator:
        q += 1
    sign = "-" if q < 0 else ""
    q = abs(q)
    s = str(q).rjust(dp + 1, "0")
    if dp == 0:
        return sign + s
    return sign + s[:-dp] + "." + s[-dp:]

def main():
    # ---------- 1. 文件清单（手工实现 glob 语义：仅一级子目录） ----------
    all_files = []          # 与历史 glob 同集（一级子目录内）
    pattern_excluded = []   # 数据树内但不在 glob 语义内（如 qc161_u0400_trip 根直下）
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel = os.path.relpath(dirpath, ROOT)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        dirnames.sort()
        for fn in sorted(filenames):
            if not NAME_RE.match(fn):
                continue
            full = os.path.join(dirpath, fn)
            if depth == 1:
                all_files.append(full)
            else:
                pattern_excluded.append((full, depth))
    all_files.sort()
    print("[1] 数据源盘点（glob 语义 = qc161_u0400_trip/<一级子目录>/measure_w*.json）")
    print("    一级子目录内 measure_w*.json 文件数 = %d" % len(all_files))
    print("    glob 语义外（根直下/更深）同名文件数 = %d" % len(pattern_excluded))
    for p, d in pattern_excluded:
        print("      [模式外] depth=%d %s" % (d, os.path.relpath(p, ROOT)))

    # ---------- 2. 解析与纳排 ----------
    rows = []
    excluded = []
    parse_errors = 0
    schemas = {}
    hashes = set()
    hz_set = set()
    for p in all_files:
        try:
            with open(p, "r", encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception as e:  # pragma: no cover
            parse_errors += 1
            excluded.append((p, "PARSE_ERROR: %r" % e))
            continue
        st = d.get("stats") or {}
        span = d.get("span_s")
        samples = st.get("samples") or 0
        edges = st.get("n_edges")
        schemas[d.get("schema")] = schemas.get(d.get("schema"), 0) + 1
        if d.get("gamemd_sha256"):
            hashes.add(d.get("gamemd_sha256"))
        if d.get("hz"):
            hz_set.add(d.get("hz"))
        ok = (span == 25.0) and (samples > 0)
        if ok:
            rows.append(dict(
                rel=os.path.relpath(p, ROOT),
                trip=d.get("trip_id"), w=d.get("window"),
                span=span, samples=samples, edges=edges,
            ))
        else:
            reason = []
            if span != 25.0:
                reason.append("span_s=%r" % span)
            if samples <= 0:
                reason.append("samples=%r" % samples)
            excluded.append((p, " ; ".join(reason)))

    print("[2] 解析与纳排（纳入 = span_s==25.0 且 samples>0）")
    print("    JSON 解析错误数 = %d" % parse_errors)
    print("    纳入完整窗数 = %d" % len(rows))
    print("    排除窗数 = %d" % len(excluded))
    for p, why in excluded:
        print("      [排除] %s  (%s)" % (os.path.relpath(p, ROOT), why))
    print("    schema 分布 = %r" % (schemas,))
    print("    hz 取值 = %r" % (sorted(hz_set),))
    print("    数据文件内 gamemd_sha256 去重数 = %d" % len(hashes))
    for h in sorted(hashes):
        print("      %s" % h)

    # ---------- 3. 基线与沿数（两套口径） ----------
    S = sum(r["samples"] for r in rows)
    E = sum(r["edges"] for r in rows)
    T = sum(max(0, r["edges"] - 1) for r in rows)
    print("[3] 87 窗基数（分母与两套沿数口径）")
    print("    S = Σsamples（基线分母，既有500Hz轮询读数） = %d" % S)
    print("    E = Σn_edges（沿表口径，含每窗首样）     = %d" % E)
    print("    T = Σmax(0,n_edges-1)（跳变口径，首样不触发） = %d" % T)

    # 逐窗 samples 应为 12501~12502 的带内校验
    odd = [r for r in rows if not (12501 <= r["samples"] <= 12502)]
    print("    逐窗 sanity：samples 不在 [12501,12502] 的窗数 = %d" % len(odd))
    bad2 = [r for r in rows if not (1 <= r["edges"] <= r["samples"])]
    print("    逐窗 sanity：n_edges 不在 [1,samples] 的窗数 = %d" % len(bad2))
    frozen = [r for r in rows if r["edges"] == 1]
    print("    冻结窗（n_edges==1）个数 = %d" % len(frozen))

    # ---------- 4. 双窗口集合 ----------
    max_e = max(r["edges"] for r in rows)
    worst_list = [r for r in rows if r["edges"] == max_e]
    print("[4] 最坏单窗独立判定（按 n_edges 最大，并列则全列）")
    for r in worst_list:
        print("    %s w%s edges=%d samples=%d" % (r["trip"], r["w"], r["edges"], r["samples"]))
    worst = worst_list[0]
    print("    n_edges=最大值 的窗并列数 = %d" % len(worst_list))
    min_e = min(r["edges"] for r in rows)
    min_list = [r["rel"] for r in rows if r["edges"] == min_e]
    print("    最省 n_edges=%d 的窗数 = %d（首窗 %s）" % (min_e, len(min_list), min_list[0]))

    # ---------- 5. 负担复算：87 窗整体 × 3 读次 × 2 口径 ----------
    print("[5] 负担百分比复算（精确分数 → 十进制）")
    print("    87 窗整体：负担%% = 100 × n × 沿数 / %d" % S)
    hist = {
        (4, "edge"): "+10.475%", (4, "trans"): "+10.443%",
        (5, "edge"): "+13.094%", (5, "trans"): "+13.054%",
        (6, "edge"): "+15.713%", (6, "trans"): "+15.665%",
    }
    for n in (4, 5, 6):
        a = pct(n, E, S)
        b = pct(n, T, S)
        for lbl, fr in (("沿表", a), ("跳变", b)):
            v3 = fmt(fr, 3)
            v4 = fmt(fr, 4)
            key = (n, "edge" if lbl == "沿表" else "trans")
            h = hist.get(key)
            mark = "HIT " if h and ("+" + v3 + "%") == h else ("hit4" if h and ("+" + v4 + "%") == h else "MISS")
            print("    %d读 %-4s = %s%%  (4dp %s%%)  历史 %s  [%s]"
                  % (n, lbl, v3, v4, h or "—", mark))
    print("    精确分数：5读沿表 = 100×5×%d/%d = %s" % (E, S, pct(5, E, S)))
    print("            5读跳变 = 100×5×%d/%d = %s" % (T, S, pct(5, T, S)))

    # ---------- 6. 最坏单窗复算 ----------
    print("[6] 最坏单窗（edges=%d / samples=%d）" % (worst["edges"], worst["samples"]))
    histw = {
        (4, "edge"): "+25.0840%", (4, "trans"): "+25.0520%",
        (5, "edge"): "+31.3550%", (5, "trans"): "+31.3150%",
        (6, "edge"): "+37.6260%", (6, "trans"): "+37.5780%",
    }
    for n in (4, 5, 6):
        a = pct(n, worst["edges"], worst["samples"])
        b = pct(n, max(0, worst["edges"] - 1), worst["samples"])
        for lbl, fr in (("沿表", a), ("跳变", b)):
            v4 = fmt(fr, 4)
            key = (n, "edge" if lbl == "沿表" else "trans")
            h = histw.get(key)
            mark = "HIT " if h and ("+" + v4 + "%") == h else "MISS"
            print("    %d读 %-4s = %s%%  (6dp %s%%)  历史 %s  [%s]"
                  % (n, lbl, v4, fmt(fr, 6), h or "—", mark))
    print("    精确分数：5读沿表 = 100×5×%d/%d = %s" % (worst["edges"], worst["samples"], pct(5, worst["edges"], worst["samples"])))
    print("            5读跳变 = 100×5×%d/%d = %s" % (worst["edges"] - 1, worst["samples"], pct(5, worst["edges"] - 1, worst["samples"])))

    # ---------- 7. 字节口径 ----------
    print("[7] 字节口径（每读 4 B，u32）")
    for n in (5, 6):
        tot = 4 * n * E
        wtot = 4 * n * worst["edges"]
        rate = Fraction(wtot, 25)
        print("    %d读：每沿 %d B；87窗合计 %d B；最坏窗 %d B；最坏窗 %s B/s"
              % (n, 4 * n, tot, wtot, fmt(rate, 1)))

    # ---------- 8. 对照历史账判定 ----------
    print("[8] 与历史账比对（EXECUTION_D21.md:89-113 / _d21_burden5_out.txt:12,17,26）")
    checks = [
        ("87窗5读沿表", pct(5, E, S), 3, "+13.094%"),
        ("87窗5读跳变", pct(5, T, S), 3, "+13.054%"),
        ("最坏窗5读沿表", pct(5, worst["edges"], worst["samples"]), 4, "+31.3550%"),
        ("最坏窗5读跳变", pct(5, worst["edges"] - 1, worst["samples"]), 4, "+31.3150%"),
    ]
    all_hit = True
    for name, fr, dp, h in checks:
        v = "+" + fmt(fr, dp) + "%"
        ok = (v == h)
        all_hit = all_hit and ok
        print("    %s：复算 %s vs 历史 %s  => %s" % (name, v, h, "REPRODUCED" if ok else "DIFF"))
    print("    两口径（沿表+跳变）× 双窗口（87窗+最坏窗）四项全部复现 = %s" % all_hit)
    print("DONE")

if __name__ == "__main__":
    main()
