#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rollback_extra.py — 补充分类：**回滚/备份类**文件（`*_before_*` / `*.before*` / `*_bak*` /
`backup/` 目录）与**滚动台账快照**（R17_LEAD_BASELINE 里 LEDGER/BOARD_ARCHIVE/STATUS_BOARD/R14_COMMON 的
历史副本）。这些是「记录动作的副产物」，但不落在卡 §二 Q2 点名的 10 个模式里。

只读本卡目录里的 files_tier_A_snap2.tsv，不碰 lead。输出 rollback_extra.json。
"""
from __future__ import annotations

import json
import os
import re
import sys

OUT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(OUT, "files_tier_A_snap2.tsv")

RX_BACKUP = re.compile(r"(_before_|\.before|before_|_bak|\bbak\b|backup/|_backup)", re.I)
RX_LEDGER_SNAP = re.compile(r"R17_LEAD_BASELINE/.*(LEDGER\.before_|BOARD_ARCHIVE\.before_|"
                            r"STATUS_BOARD\.before_|R14_COMMON\.(before|bad)|PENDING_DECISIONS)", re.I)


def main():
    rows = []
    with open(SRC, "r", encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            rows.append((p[0], int(p[2])))

    bk = [(r, b) for r, b in rows if RX_BACKUP.search(r)]
    lb = [(r, b) for r, b in rows if RX_LEDGER_SNAP.search(r)]
    # 交集：R17_LEAD_BASELINE 中的那些也命中 RX_BACKUP，注意去重后合并
    union = {r: b for r, b in bk}
    union.update({r: b for r, b in lb})
    res = dict(
        source=os.path.basename(SRC),
        pattern_backup=RX_BACKUP.pattern,
        pattern_ledger_snapshot=RX_LEDGER_SNAP.pattern,
        backup_like=dict(files=len(bk), bytes=sum(b for _, b in bk),
                         GB_decimal=round(sum(b for _, b in bk) / 1e9, 6),
                         GiB=round(sum(b for _, b in bk) / 1024 ** 3, 6)),
        ledger_snapshot=dict(files=len(lb), bytes=sum(b for _, b in lb),
                             GB_decimal=round(sum(b for _, b in lb) / 1e9, 6),
                             GiB=round(sum(b for _, b in lb) / 1024 ** 3, 6)),
        union=dict(files=len(union), bytes=sum(union.values()),
                   GB_decimal=round(sum(union.values()) / 1e9, 6),
                   GiB=round(sum(union.values()) / 1024 ** 3, 6)),
        top=sorted(((b, r) for r, b in union.items()), reverse=True)[:25],
    )
    with open(os.path.join(OUT, "rollback_extra.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    for k in ("backup_like", "ledger_snapshot", "union"):
        v = res[k]
        print(f"[{k}] files={v['files']:,} bytes={v['bytes']:,} = {v['GB_decimal']} GB(10^9) = {v['GiB']} GiB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
