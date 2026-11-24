# -*- coding: utf-8 -*-
"""R15 裁决 D-38(A)/D-44(严格) 的双列复算。

输出：
  strict_panel.tsv     每子系统 atlas_n / named_L / named_S(R14) / named_S(strict) /
                       proved_n / proved_strict_n + 两个门槛 + 两个达标判定
  strict_panel.json    同上，另含 TOTAL 与判定汇总

定义（与 PANEL.md 表头口径逐条对齐，脚本自证复现现有三列）：
  named_L            name 非空且不以 sub_ 开头
  named_S(R14)       named_L 中排除 Class::sub_XXXXXXXX（atlas 内为 0 行 ⇒ 恒等于 L）
  named_S(strict)    named_S(R14) 中再排除 *::slotN / *::vslotN
  proved_n           atlas 内 grade == [已证]
  proved_strict_n    proved_n 中 one_line_semantics 不含 [未证]
 门槛             named = ceil(0.9*atlas_n)；proved = ceil(0.5*atlas_n)
"""
import csv, json, os, re, collections, sys, math
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_MERGE_EVID802_11\_strict_after"

RE_SLOT = re.compile(r"::v?slot\d+$")
# ★ 2026-11-19 修正：面板的排除规则不是字面 "Class::sub_XXXXXXXX"（8 位），
#   而是任意 "<X>::sub_<hex>"（含 6 位短形态，如 AudioController::sub_4060F0）。
#   按字面 8 位匹配会漏 7 行（S19 6 + S05 1），使 named_S(R14) 虚高 7。
#   首轮按字面匹配得 named_S(R14)=7210 vs 面板 7203，即此 7 行。
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")


def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def main():
    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                atlas.add(ne(p[0]))

    with open(COV, encoding="utf-8-sig", newline="") as f:
        cov = list(csv.reader(f, delimiter="\t"))[1:]

    d = collections.defaultdict(collections.Counter)
    for r in cov:
        if len(r) < 8:
            continue
        e = ne(r[0])
        s = r[1].strip()
        if e not in atlas:
            d[s]["cov_nonatlas"] += 1
            continue
        name = r[2].strip()
        sem = r[3]
        grade = r[4].strip()
        d[s]["atlas_n"] += 1
        if name and not name.startswith("sub_"):
            d[s]["named_L"] += 1
            if not RE_CSUB.search(name):
                d[s]["named_S14"] += 1
                if not RE_SLOT.search(name):
                    d[s]["named_strict"] += 1
        if grade == "[已证]":
            d[s]["proved_n"] += 1
            if "[未证]" not in sem:
                d[s]["proved_strict_n"] += 1

    rows, tot = [], collections.Counter()
    for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
        c = d[s]
        a = c["atlas_n"]
        tn, tp = math.ceil(0.9 * a), math.ceil(0.5 * a)
        ok_n = c["named_S14"] >= tn
        ok_s = c["named_strict"] >= tn
        ok_p = c["proved_n"] >= tp
        ok_ps = c["proved_strict_n"] >= tp
        rows.append(dict(
            S=s, atlas_n=a,
            named_L=c["named_L"], named_S14=c["named_S14"], named_strict=c["named_strict"],
            proved_n=c["proved_n"], proved_strict_n=c["proved_strict_n"],
            thu_named=tn, thu_proved=tp,
            pct_named_R14=round(100.0 * c["named_S14"] / a, 2) if a else 0.0,
            pct_named_strict=round(100.0 * c["named_strict"] / a, 2) if a else 0.0,
            pct_proved=round(100.0 * c["proved_n"] / a, 2) if a else 0.0,
            pct_proved_strict=round(100.0 * c["proved_strict_n"] / a, 2) if a else 0.0,
            dod_nominal=bool(ok_n and ok_p),
            dod_strict=bool(ok_n and ok_ps),
        ))
        for k in ("atlas_n", "named_L", "named_S14", "named_strict", "proved_n", "proved_strict_n"):
            tot[k] += c[k]
        tot["dod_nominal"] += int(ok_n and ok_p)
        tot["dod_strict"] += int(ok_n and ok_ps)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "strict_panel.tsv"), "w", encoding="utf-8", newline="") as f:
        cols = ["S", "atlas_n", "named_L", "named_S14", "named_strict", "proved_n",
                "proved_strict_n", "thu_named", "thu_proved", "pct_named_R14",
                "pct_named_strict", "pct_proved", "pct_proved_strict",
                "dod_nominal", "dod_strict"]
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r[c]) for c in cols) + "\n")

    summary = dict(rows=rows, total=dict(tot),
                   note="named_S(R14) 与 PANEL.md 的 named_pct_S(R14) 逐格比对用作口径自证")
    with open(os.path.join(OUT, "strict_panel.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    hdr = ("S     atlas_n  namedS14  namedStr  proved  provedStr  thr_n thr_p   "
           "n%(R14) n%(str)  p%  p%(str)  nominal strict")
    print(hdr)
    for r in rows:
        print("%-5s %7d %9d %9d %7d %10d %6d %5d %8.2f %7.2f %5.2f %7.2f   %-5s %-5s" % (
            r["S"], r["atlas_n"], r["named_S14"], r["named_strict"], r["proved_n"],
            r["proved_strict_n"], r["thu_named"], r["thu_proved"],
            r["pct_named_R14"], r["pct_named_strict"], r["pct_proved"],
            r["pct_proved_strict"], r["dod_nominal"], r["dod_strict"]))
    print("%-5s %7d %9d %9d %7d %10d %6s %5s %8.2f %7.2f %5.2f %7.2f   %d/22  %d/22" % (
        "TOTAL", tot["atlas_n"], tot["named_S14"], tot["named_strict"], tot["proved_n"],
        tot["proved_strict_n"], "-", "-",
        100.0 * tot["named_S14"] / tot["atlas_n"], 100.0 * tot["named_strict"] / tot["atlas_n"],
        100.0 * tot["proved_n"] / tot["atlas_n"], 100.0 * tot["proved_strict_n"] / tot["atlas_n"],
        tot["dod_nominal"], tot["dod_strict"]))
    print("\n名义达标:", ",".join(r["S"] for r in rows if r["dod_nominal"]))
    print("严格达标:", ",".join(r["S"] for r in rows if r["dod_strict"]))
    print("coverage 行数(全部)=%d，atlas 内=%d，atlas 外=%d" % (
        len([r for r in cov if len(r) >= 8]), tot["atlas_n"],
        len([r for r in cov if len(r) >= 8]) - tot["atlas_n"]))


main()
