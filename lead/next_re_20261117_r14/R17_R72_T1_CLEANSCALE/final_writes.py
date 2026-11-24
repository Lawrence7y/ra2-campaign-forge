#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""final_writes.py — 收尾：为档 B / 档 C 各取新快照（自产物文件计数增长了一轮），
并把「自身产物」四个粒度算成可核的数字（明细表落 tsv）。

只读 lead，只写本卡目录。
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import subprocess
import sys

# 四个粒度都在档 A 的逐文件表上算，互不套嵌：
#   G1 baseline   R17_R70_T1_REPRO/scale_vs_baseline.json 实际剔除的那 1 个文件
#   G2 cardlist   卡 §二 Q2 点名的 10 个模式（_hits_* / _pats_* / *.tmp / _r3[5-9]* / _r4* /
#                 *_report.md / *_out.txt / s_rerun_* / files_scale_*.tsv / scale_*.json）
#   G3 dirwide    G2 + 同目录族（凡目录名以 'R17_R68_T1_' / 'R17_R70_T1_' 开头者整目录计）
#   G4 tierC      G3 + F24 度量器本身与同类度量 script 目录（R16_MEASURE_*、R16_AUDIT_EVID675、
#                 R17_LEAD_BASELINE 等，见 --extra-dir-prefix）
DEFAULT_EXTRA = ["R16_MEASURE_", "R16_AUDIT_EVID675", "R17_LEAD_BASELINE"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary", default="summary_snap2.json")
    ap.add_argument("--extra-dir-prefix", nargs="*", default=DEFAULT_EXTRA)
    args = ap.parse_args(argv)

    # 用最新一次 summary 的档 A 表
    sump = os.path.join(args.out, args.summary)
    with open(sump, "r", encoding="utf-8") as fh:
        summary = json.load(fh)
    a_tsv = os.path.join(args.out, summary["tiers"]["A"]["tsv"])

    sys.path.insert(0, args.out)
    from measure_clean import classify  # 同一套分类函数，避免口径漂移

    rows = []
    with open(a_tsv, "r", encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            rows.append(dict(rel=p[0], ext=p[1], bytes=int(p[2]), mtime_ns=int(p[3]), kind=p[4]))

    extra = tuple(x.lower() for x in args.extra_dir_prefix)

    def family(rel):
        dirs = [d.lower() for d in rel.split("/")[:-1]]
        return any(d.startswith(("r17_r68_t1_", "r17_r70_t1_")) for d in dirs)

    def tierC(rel):
        if classify(rel):
            return True
        dirs = [d.lower() for d in rel.split("/")[:-1]]
        return any(d.startswith(extra) for d in dirs)

    groups = {
        "G1_baseline_one_file": lambda r: r == "next_re_20261117_r14/_hits_primary.tsv",
        "G2_cardlist_patterns": lambda r: bool(classify(r)),
        "G3_cardlist_plus_family": lambda r: bool(classify(r)) or family(r),
        "G4_tierC_incl_measure_dirs": tierC,
    }
    total_a_files = len(rows)
    total_a_bytes = sum(r["bytes"] for r in rows)
    res = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "source_tier_a": os.path.basename(a_tsv),
           "extra_dir_prefix": list(extra),
           "tier_a": dict(files=total_a_files, bytes=total_a_bytes),
           "groups": {}}
    detail = []
    for name, fn in groups.items():
        sel = [r for r in rows if fn(r["rel"])]
        b = sum(r["bytes"] for r in sel)
        # 按 Q2 类目拆分（只对 G2/G3/G4 有意义；G4 的目录族另计）
        cat_n = collections.Counter()
        cat_b = collections.Counter()
        for r in sel:
            k = classify(r["rel"]) or "C10_measure_dir"
            for kk in k.split("+"):
                cat_n[kk] += 1
                cat_b[kk] += r["bytes"]
        res["groups"][name] = dict(files=len(sel), bytes=b,
                                   GB_decimal=round(b / 1e9, 6), GiB=round(b / 1024 ** 3, 6),
                                   cat_counts=dict(cat_n.most_common()),
                                   cat_bytes=dict(cat_b.most_common()))
        for r in sel:
            detail.append((name, r["rel"], r["ext"], r["bytes"], classify(r["rel"]) or "C10_measure_dir"))
        print(f"[{name}] files={len(sel):,} bytes={b:,} = {b/1e9:.6f} GB(10^9) = {b/1024**3:.6f} GiB")

    det = os.path.join(args.out, "selfartifacts_detail.tsv")
    detail.sort()
    with open(det, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("group\trel\text\tbytes\tselfkind\n")
        for d in detail:
            fh.write("\t".join(str(x) for x in d) + "\n")

    # ---- 收尾快照：档 B / 档 C 重跑（含本轮新写的自产物） ----
    for tier in ("B", "C"):
        subprocess.run([sys.executable, os.path.join(args.out, "measure_clean.py"),
                        "--lead", summary["lead"], "--out", args.out, "--tiers", tier],
                       check=True)
    with open(os.path.join(args.out, "summary.json"), "r", encoding="utf-8") as fh:
        final = json.load(fh)
    for t in final["tiers"]:
        s = final["tiers"][t]
        if t in summary["tiers"]:
            pa = summary["tiers"][t]
            print(f"[tier {t}] snap1 files={pa['files']:,} bytes={pa['bytes']:,} -> "
                  f"now files={s['files']:,} bytes={s['bytes']:,} "
                  f"(delta files {s['files']-pa['files']:+,} bytes {s['bytes']-pa['bytes']:+,})")

    res["final_tiers"] = {t: {k: v for k, v in s.items()} for t, s in final["tiers"].items()}
    res["snap_earlier_tiers"] = summary["tiers"]
    with open(os.path.join(args.out, "q2q3_final.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("[done] q2q3_final.json, selfartifacts_detail.tsv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
