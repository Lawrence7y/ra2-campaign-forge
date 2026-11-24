#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""band_c_wide.py — 扩展档 C（记作 档 C+）：在档 C 基础上再排「回滚/备份副本」类。

两组，用来给 lead 一个下界：
  set1  回滚副本 = 文件名含 before/bak/bad 或位于 backup 目录，**且**不是 `*_out.txt`（原始输出流保留）
  set2  set1 + R17_LEAD_BASELINE/ 下全部 LEDGER/BOARD_ARCHIVE/STATUS_BOARD/R14_COMMON/PENDING_DECISIONS 副本

只读本卡目录内的 files_tier_A_snap2.tsv，不碰 lead。结果落 band_c_wide.json。
"""
from __future__ import annotations

import json
import os
import re
import sys

OUT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(OUT, "files_tier_A_snap2.tsv")

RX_BACKUP = re.compile(r"(_before_|\.before|before_|_bak|backup/)", re.I)
RX_OUT = re.compile(r"/[^/]*_out\.txt$", re.I)
RX_LEDGER_SNAP = re.compile(r"R17_LEAD_BASELINE/.*(LEDGER\.before_|BOARD_ARCHIVE\.before_|"
                            r"STATUS_BOARD\.before_|R14_COMMON\.(before|bad)|PENDING_DECISIONS)", re.I)
# 档 C 已排的（与 measure_clean.classify 同义），这里用「不在档 C 表里」判定，不需要重复那份正则
TIER_C = os.path.join(OUT, "files_tier_C.tsv")


def load(path):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            rows.append((p[0], int(p[2])))
    return rows


def main():
    a = load(SRC)
    cset = {r for r, _ in load(TIER_C)}
    a_map = dict(a)
    a_n, a_b = len(a), sum(b for _, b in a)

    excluded_c = [(r, b) for r, b in a if r not in cset]
    rest = [(r, b) for r, b in a if r in cset]          # 档 C 语料

    set1 = [(r, b) for r, b in rest if RX_BACKUP.search(r) and not RX_OUT.search(r)]
    set2 = [(r, b) for r, b in rest if (RX_BACKUP.search(r) and not RX_OUT.search(r)) or RX_LEDGER_SNAP.search(r)]

    def band(sel):
        n = a_n - len(excluded_c) - len(sel)
        b = a_b - sum(x for _, x in excluded_c) - sum(x for _, x in sel)
        return dict(files=n, bytes=b, GB_decimal=round(b / 1e9, 6), GiB=round(b / 1024 ** 3, 6),
                    excluded_extra_files=len(sel), excluded_extra_bytes=sum(x for _, x in sel))

    res = dict(
        source_a=os.path.basename(SRC),
        tier_A_files=a_n, tier_A_bytes=a_b,
        tier_C_excluded_files=len(excluded_c), tier_C_excluded_bytes=sum(x for _, x in excluded_c),
        pattern_backup=RX_BACKUP.pattern, pattern_ledger_snap=RX_LEDGER_SNAP.pattern,
        set1_rollback_only=dict(files=len(set1), bytes=sum(x for _, x in set1)),
        set1_bandCplus=band(set1),
        set2_rollback_plus_ledger=dict(files=len(set2), bytes=sum(x for _, x in set2)),
        set2_bandCplus=band(set2),
        set2_top=sorted(((x, r) for r, x in set2), reverse=True)[:10],
    )
    with open(os.path.join(OUT, "band_c_wide.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    for k in ("set1_rollback_only", "set2_rollback_plus_ledger"):
        print(f"[{k}] {res[k]['files']:,} files / {res[k]['bytes']:,} B")
    for k in ("set1_bandCplus", "set2_bandCplus"):
        v = res[k]
        print(f"[{k}] files={v['files']:,} bytes={v['bytes']:,} = {v['GB_decimal']} GB(10^9) = {v['GiB']} GiB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
