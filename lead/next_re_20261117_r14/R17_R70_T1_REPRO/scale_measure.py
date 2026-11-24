#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scale_measure.py — 把 mev675.py:stage_scale() **丢弃的返回值**落盘成可事后复核的 TSV/JSON。

背景：`mev675.py:913-914` 调用 `stage_scale(args)` 后把返回的
`dict(scope, files, bytes, over, by_ext)` 直接丢掉，只 print。所以 F24 的
23,791 文件 / 1,383,739,755 B / 1.29 GB 从来没有任何数值产物。

本脚本**只读** lead 树（os.walk + os.path.getsize），把同一算法每一步写盘：
  files_scale.tsv   每个被计入的文件一行：rel / ext / bytes / mtime_ns
  scale_summary.json 汇总：scope / files / bytes / by_ext / 阈值判定 / 生成时刻

与 stage_scale() 的口径差异（必须写明）：
  - 只排除 `.git` 与**本卡产物目录（--out）**，与 stage_scale():259-261 同；
    不排除 R16_MEASURE_EVID675 —— 这正是原脚本口径，也是原数的口径。
  - `total` 用整数累加（原脚本也是 int 累加，无浮点误差）。
  - 单位换算在 summary 里同时给 GB(10^9) 与 GiB(2^30)，**不再沿用 /1024^3 却标 GB**（mev675.py:281 的错）。

用法：python scale_measure.py --lead <lead> --out <本目录> [--scope primary|wide]
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import sys

PRIMARY_EXT = {".tsv", ".txt", ".json", ".md", ".csv", ".log"}
CODE_EXT = {".py", ".asm", ".s", ".c", ".cpp", ".h", ".inc", ".ps1", ".sh",
            ".js", ".ts", ".java", ".go", ".rs", ".bat", ".cmd"}
SCALE_FILES_MAX = 50_000
SCALE_BYTES_MAX = 2 * 1024 * 1024 * 1024


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lead", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scope", default="primary", choices=["primary", "wide"])
    ap.add_argument("--label", default="today")
    args = ap.parse_args(argv)

    exts = set(PRIMARY_EXT) | (set(CODE_EXT) if args.scope == "wide" else set())
    out_excl = os.path.normcase(os.path.abspath(args.out))
    rows = []
    total = 0
    by_ext = collections.Counter()
    by_ext_bytes = collections.Counter()
    skipped_oserr = 0
    for root, dirs, fnames in os.walk(args.lead):
        dirs[:] = [d for d in dirs if d.lower() != ".git"
                   and os.path.normcase(os.path.abspath(os.path.join(root, d))) != out_excl]
        for fn in fnames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in exts:
                continue
            full = os.path.join(root, fn)
            try:
                sz = os.path.getsize(full)
                mt = os.stat(full).st_mtime_ns
            except OSError:
                skipped_oserr += 1
                continue
            rel = os.path.relpath(full, args.lead).replace("\\", "/")
            rows.append((rel, ext, sz, mt))
            total += sz
            by_ext[ext] += 1
            by_ext_bytes[ext] += sz

    rows.sort()
    tsv = os.path.join(args.out, f"files_scale_{args.label}.tsv")
    with open(tsv, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("rel\text\tbytes\tmtime_ns\n")
        for rel, ext, sz, mt in rows:
            fh.write(f"{rel}\t{ext}\t{sz}\t{mt}\n")

    over = len(rows) > SCALE_FILES_MAX or total > SCALE_BYTES_MAX
    summary = dict(
        label=args.label,
        generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        lead=os.path.abspath(args.lead),
        scope=args.scope,
        exts=sorted(exts),
        exclusions=["*.git*", os.path.abspath(args.out) + " (this card's own out dir)"],
        files=len(rows),
        bytes=total,
        # 两个进制各写各的标签，禁止混用
        GB_decimal=round(total / 1e9, 6),          # 10^9，标签 GB
        GiB=round(total / 1024 ** 3, 6),           # 2^30，标签 GiB
        MB_decimal=round(total / 1e6, 3),
        MiB=round(total / 1024 ** 2, 3),
        by_ext_counts=dict(by_ext.most_common()),
        by_ext_bytes=dict(by_ext_bytes.most_common()),
        skipped_oserr=skipped_oserr,
        threshold_files=SCALE_FILES_MAX,
        threshold_bytes=SCALE_BYTES_MAX,
        threshold_bytes_GiB=SCALE_BYTES_MAX / 1024 ** 3,
        over_threshold=over,
        source_code="R16_MEASURE_EVID675/mev675.py:251-289 stage_scale() (返回值在 :914 被丢弃)",
    )
    jsp = os.path.join(args.out, f"scale_summary_{args.label}.json")
    with open(jsp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print(f"[scale_measure] files={len(rows):,} bytes={total:,} "
          f"= {summary['GB_decimal']} GB(10^9) = {summary['GiB']} GiB(2^30)")
    print(f"[scale_measure] -> {tsv}\n[scale_measure] -> {jsp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
