#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""measure_clean.py — R40-T1-CLEANSCALE 测量器（只读 lead，只写本目录）

约束（卡 §〇）：
  - 不 import / 不执行 mev675.py；本文件是**独立重写**的遍历器。
  - 打开 lead 下任何文件一律 mode="rb"；唯一写目标是 --out（本卡目录）。
  - 只做 os.walk + os.stat，不跟随目录符号链接（reparse point），与 os.walk 默认一致。

口径来源：R16_MEASURE_EVID675/mev675.py:49 PRIMARY_EXT、:251-289 stage_scale()。
档 A/B/C 的排除集全部由 --exclude-tier 选择，逐档独立遍历、独立累加。

产物（全部落在 --out）：
  files_tier_<A|B|C>.tsv   逐文件：rel / ext / bytes / mtime_ns / selfkind
  summary.json             各档汇总 + 扩展名分布 + 自产物分类汇总
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import fnmatch
import json
import os
import sys

PRIMARY_EXT = {".tsv", ".txt", ".json", ".md", ".csv", ".log"}
SCALE_FILES_MAX = 50_000
SCALE_BYTES_MAX = 2 * 1024 * 1024 * 1024

# ---- Q2 分类：文件名模式（只作用于 basename） ------------------------------
PAT_HITS = ["_hits_*.tsv"]
PAT_TMP = ["_pats_*.tmp", "*.tmp"]
PAT_R35_39 = ["_r35", "_r36", "_r37", "_r38", "_r39"]          # 目录名前缀
PAT_R4X = []                                                    # 目录名前缀，运行时枚举
PAT_REPORT = ["*_report.md"]
PAT_OUT_TXT = ["*_out.txt"]
PAT_S_RERUN = ["s_rerun_*"]
PAT_FILE_SCALE = ["files_scale_*.tsv"]
PAT_SCALE_JSON = ["scale_*.json"]


def walk_lead(lead, out_excl):
    """与 os.walk 默认同：不跟随目录符号链接/.junction；跳过 .git 与 --out。"""
    for root, dirs, fnames in os.walk(lead):
        dirs[:] = [d for d in dirs
                   if d.lower() != ".git"
                   and not os.path.islink(os.path.join(root, d))
                   and os.path.normcase(os.path.abspath(os.path.join(root, d))) != out_excl]
        yield root, dirs, fnames


def classify(rel_posix):
    """返回 (selfkind, is_artifact_by_category)。selfkind 只用于报表，不影响档 C 排除集。"""
    parts = rel_posix.split("/")
    base = parts[-1]
    dirs = parts[:-1]
    hits = []
    if any(fnmatch.fnmatch(base, p) for p in PAT_HITS):
        hits.append("C1_hits_tsv")
    if any(fnmatch.fnmatch(base, p) for p in PAT_TMP):
        hits.append("C2_tmp")
    lowdirs = [d.lower() for d in dirs]
    if any(any(dd.startswith(p) for dd in lowdirs) for p in PAT_R35_39):
        hits.append("C3_r35_r39_dir")
    if any(any(dd.startswith(p) for dd in lowdirs) for p in PAT_R4X):
        hits.append("C4_r4x_dir")
    if any(fnmatch.fnmatch(base.lower(), p) for p in PAT_REPORT):
        hits.append("C5_report_md")
    if any(fnmatch.fnmatch(base, p) for p in PAT_OUT_TXT):
        hits.append("C6_out_txt")
    if any(fnmatch.fnmatch(base, p) for p in PAT_S_RERUN):
        hits.append("C7_s_rerun")
    if any(fnmatch.fnmatch(base, p) for p in PAT_FILE_SCALE):
        hits.append("C8_files_scale")
    if any(fnmatch.fnmatch(base, p) for p in PAT_SCALE_JSON):
        hits.append("C9_scale_json")
    return "+".join(hits) if hits else ""


def scan(lead, out_excl, exts, exclude_kinds):
    rows = []
    skipped = 0
    for root, dirs, fnames in walk_lead(lead, out_excl):
        for fn in fnames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in exts:
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, lead).replace("\\", "/")
            kind = classify(rel)
            if exclude_kinds == "B":
                drop = bool(kind) and all(k in ("C1_hits_tsv", "C2_tmp")
                                          for k in kind.split("+"))
                if drop:
                    continue
            elif exclude_kinds == "C":
                if kind:
                    continue
            try:
                st = os.stat(full, follow_symlinks=False)
            except OSError:
                skipped += 1
                continue
            rows.append((rel, ext, st.st_size, st.st_mtime_ns, kind))
    rows.sort()
    return rows, skipped


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lead", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scope", default="primary", choices=["primary"])
    ap.add_argument("--tiers", default="A,B,C")
    args = ap.parse_args(argv)

    # 运行时枚举 _r4* 目录名，避免写死
    r4x = sorted({d.name.lower() for d in os.scandir(args.lead)
                  if d.is_dir() and d.name.lower().startswith("_r4")})
    PAT_R4X[:] = r4x

    out_excl = os.path.normcase(os.path.abspath(args.out))
    exts = set(PRIMARY_EXT)

    tiers = [t.strip() for t in args.tiers.split(",") if t.strip()]
    result = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "lead": os.path.abspath(args.lead),
              "out": os.path.abspath(args.out),
              "scope": args.scope,
              "exts": sorted(exts),
              "tiers": {}}
    for t in tiers:
        rows, skipped = scan(args.lead, out_excl, exts, t)
        total = sum(r[2] for r in rows)
        by_ext_n = collections.Counter(r[1] for r in rows)
        by_ext_b = collections.Counter()
        for r in rows:
            by_ext_b[r[1]] += r[2]
        kind_n = collections.Counter()
        kind_b = collections.Counter()
        for r in rows:
            if r[4]:
                for k in r[4].split("+"):
                    kind_n[k] += 1
                    kind_b[k] += r[2]
        tsv = os.path.join(args.out, f"files_tier_{t}.tsv")
        with open(tsv, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("rel\text\tbytes\tmtime_ns\tselfkind\n")
            for rel, ext, sz, mt, kind in rows:
                fh.write(f"{rel}\t{ext}\t{sz}\t{mt}\t{kind}\n")
        result["tiers"][t] = dict(
            files=len(rows), bytes=total,
            GB_decimal=round(total / 1e9, 6), GiB=round(total / 1024 ** 3, 6),
            MB_decimal=round(total / 1e6, 3), MiB=round(total / 1024 ** 2, 3),
            by_ext_counts=dict(by_ext_n.most_common()),
            by_ext_bytes=dict(by_ext_b.most_common()),
            selfkind_counts=dict(kind_n.most_common()),
            selfkind_bytes=dict(kind_b.most_common()),
            skipped_oserr=skipped, tsv=os.path.basename(tsv),
        )
        print(f"[tier {t}] files={len(rows):,} bytes={total:,} "
              f"= {total/1e9:.6f} GB(10^9) = {total/1024**3:.6f} GiB(2^30)",
              flush=True)

    result["r4x_dirs_matched"] = r4x
    with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("[done] summary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
