#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""q4_decomp.py — Q4 漂移分解（只读 lead 与本卡目录，只写本卡目录）

输入：
  <out>/files_tier_A_snap1.tsv   本卡第一次档 A 快照
  <out>/files_tier_A_snap2.tsv   本卡第二次档 A 快照（间隔 ≥60s）
  --base <tsv>                   上一轮的档 A 逐文件清单（R17_R70_T1_REPRO/files_scale_today.tsv）
另：直接对 --base 自身的 mtime 做分布统计，用来判断「基线列出时有多少文件还没写定」。

输出：q4_decomp.json + 人工可读 stdout
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import sys

# 上一轮 R17_R70_T1_REPRO/scale_vs_baseline.json 里的干净值（只有汇总，无逐文件表）
PRIOR_CLEAN = dict(files=24692, bytes=1506032984)
PRIOR_ARTIFACTS = [("next_re_20261117_r14/_hits_primary.tsv", 80580525)]


def load(path):
    d = {}
    with open(path, "r", encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) < 4:
                continue
            d[p[0]] = (p[1], int(p[2]), int(p[3]))
    return d


def summarize(a, b, label):
    ka, kb = set(a), set(b)
    added = kb - ka
    removed = ka - kb
    ab = sum(b[k][1] for k in added)
    rb = sum(a[k][1] for k in removed)
    grow = []
    for k in (ka & kb):
        delta = b[k][1] - a[k][1]
        if delta:
            grow.append((delta, k, a[k][1], b[k][1]))
    grow.sort(reverse=True)
    return dict(
        label=label,
        files_a=len(a), bytes_a=sum(v[1] for v in a.values()),
        files_b=len(b), bytes_b=sum(v[1] for v in b.values()),
        added_files=len(added), added_bytes=ab,
        removed_files=len(removed), removed_bytes=rb,
        changed_files=len(grow), changed_bytes=sum(g[0] for g in grow),
        top_added=sorted(((b[k][1], k) for k in added), reverse=True)[:15],
        top_removed=sorted(((a[k][1], k) for k in removed), reverse=True)[:15],
        top_grown=grow[:15],
        top_shrunk=sorted(grow)[:10],
    )


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--snap1", default="files_tier_A_snap1.tsv")
    ap.add_argument("--snap2", default="files_tier_A_snap2.tsv")
    ap.add_argument("--base", required=True)
    ap.add_argument("--base-snapshot-epoch", type=float, required=True)
    args = ap.parse_args(argv)

    s1 = load(os.path.join(args.out, args.snap1))
    s2 = load(os.path.join(args.out, args.snap2))
    bs = load(args.base)

    res = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "snap1_vs_snap2": summarize(s1, s2, "snap1->snap2"),
           "base_vs_snap1": summarize(bs, s1, "base->snap1"),
           "prior_clean_summary": PRIOR_CLEAN,
           "prior_artifacts": [dict(rel=r, bytes=b) for r, b in PRIOR_ARTIFACTS]}

    # 基线自身的 mtime 分布：基线清单是 walk 过程中一边走一边写的，
    # 晚于「写入时刻」的文件不可能出现在基线里；早于但接近的，字节数可能是写了一半的。
    mts = sorted(v[2] for v in bs.values())
    base_epoch = args.base_snapshot_epoch
    res["base_mtime"] = dict(
        base_snapshot_epoch=base_epoch,
        base_snapshot_utc=dt.datetime.fromtimestamp(base_epoch, dt.timezone.utc).isoformat(timespec="seconds"),
        max_mtime_ns=mts[-1], max_mtime_utc=dt.datetime.fromtimestamp(mts[-1] / 1e9, dt.timezone.utc).isoformat(timespec="seconds"),
        min_mtime_ns=mts[0], min_mtime_utc=dt.datetime.fromtimestamp(mts[0] / 1e9, dt.timezone.utc).isoformat(timespec="seconds"),
        files_with_mtime_after_base=sum(1 for m in mts if m / 1e9 > base_epoch),
        files_within_120s_before_base=sum(1 for m in mts if base_epoch - 120 <= m / 1e9 <= base_epoch),
        files_within_3600s_before_base=sum(1 for m in mts if base_epoch - 3600 <= m / 1e9 <= base_epoch),
    )
    # 这 120s 内写过的文件，其「基线字节」与「现在字节」的差即可能的部分写入
    near = [k for k, v in bs.items() if base_epoch - 120 <= v[2] / 1e9 <= base_epoch]
    part = []
    for k in near:
        if k in s1:
            d = s1[k][1] - bs[k][1]
            if d:
                part.append((d, k, bs[k][1], s1[k][1]))
    part.sort(reverse=True)
    res["partial_write_window"] = dict(window_s=120, files=len(near),
                                      changed_files=len(part),
                                      changed_bytes=sum(p[0] for p in part),
                                      top=part[:15])

    jsp = os.path.join(args.out, "q4_decomp.json")
    with open(jsp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=str)
        fh.write("\n")

    for key in ("snap1_vs_snap2", "base_vs_snap1"):
        s = res[key]
        print(f"== {key}: files {s['files_a']:,}->{s['files_b']:,} "
              f"bytes {s['bytes_a']:,}->{s['bytes_b']:,} "
              f"| added {s['added_files']} ({s['added_bytes']:,} B) "
              f"removed {s['removed_files']} ({s['removed_bytes']:,} B) "
              f"changed {s['changed_files']} (+{s['changed_bytes']:,} B)")
        for d, k, x, y in s["top_grown"][:8]:
            print(f"   grown {d:+,} B {k}")
        for sz, k in s["top_added"][:8]:
            print(f"   added {sz:+,} B {k}")
        for sz, k in s["top_removed"][:8]:
            print(f"   removed {-sz:+,} B {k}")
    print("[base_mtime]", json.dumps(res["base_mtime"], ensure_ascii=False))
    print("[partial_write_window]", json.dumps({k: v for k, v in res["partial_write_window"].items() if k != "top"}, ensure_ascii=False))
    for d, k, x, y in res["partial_write_window"]["top"][:10]:
        print(f"   partial {d:+,} B {k} ({x:,} -> {y:,})")
    print("[done]", jsp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
