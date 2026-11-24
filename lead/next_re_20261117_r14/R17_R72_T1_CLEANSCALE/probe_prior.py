#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_prior.py — 判别上一轮那串数字的算术是否自洽（只读本卡目录内的 tsv，不碰 lead）

上一轮 `R17_R70_T1_REPRO/REPORT.md` §3.5 的时间线里有一组数：
  11:53  24,650 / 1,503,651,599 B   （注释：_hits_primary.tsv 已在树上）
  12:19  24,691 / 1,507,135,243 B
  12:23  24,693 / 1,586,613,509 B
  落盘   24,676 行清单 / 1,586,426,788 B
  clean  24,692 / 1,506,032,984 B

本脚本只用算术核对：这些数彼此之间、以及与我本卡实测之间，能不能对上。
"""
from __future__ import annotations

import json
import os
import sys

OUT = os.path.dirname(os.path.abspath(__file__))
PRIOR = dict(
    t1153_files=24650, t1153_bytes=1503651599,
    t1219_files=24691, t1219_bytes=1507135243,
    t1223_files=24693, t1223_bytes=1586613509,
    dumped_files=24676, dumped_bytes=1586426788,
    dumped_clean_after_hits=24675,
    clean_files=24692, clean_bytes=1506032984,
    hits_bytes=80580525,
    prior_by_ext={".csv": 24, ".json": 6709, ".log": 2223, ".md": 4987, ".tsv": 1466, ".txt": 9284},
)


def load(path):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            rows.append((p[0], p[1], int(p[2])))
    return rows


def main():
    rows = load(os.path.join(OUT, "files_tier_A_snap2.tsv"))
    total_n, total_b = len(rows), sum(r[2] for r in rows)
    # _hits_primary.tsv 的真实相对路径在 lead 树里带两层前缀（本机路径含路径占位符被替换后的实际目录名）
    hits = [r for r in rows if r[0].endswith("_hits_primary.tsv")]
    HITS_BYTES = hits[0][2] if hits else 0
    no_hits = [r for r in rows if r not in hits]
    nh_n, nh_b = len(no_hits), sum(r[2] for r in no_hits)
    by_ext = {}
    for _, e, b in no_hits:
        d = by_ext.setdefault(e, [0, 0])
        d[0] += 1
        d[1] += b

    checks = []
    P = PRIOR
    checks.append(dict(name="prior dumped_clean = dumped_files - 1",
                       claim=P["clean_files"], computed=P["dumped_files"] - 1))
    checks.append(dict(name="prior dropped a card dir after dumping yet files went UP by +16 vs 12:23",
                       claim=P["clean_files"],
                       computed_from_1223=P["t1223_files"] - 1))
    checks.append(dict(name="prior clean_bytes - computed '24,691-no-hits' claim is impossible to satisfy: "
                            "24,691 bytes already BELOW clean_bytes + hits_bytes",
                       claim=P["clean_bytes"],
                       lower_bound_if_baseline_was_24691=P["t1219_bytes"] - P["hits_bytes"]))
    checks.append(dict(name="prior by_ext count sum must equal files_total",
                       claim=P["t1223_files"], computed=P["dumped_files"]))
    checks.append(dict(name="prior by_ext sum of my fresh minus hits must not match prior by_ext",
                       claim=P["prior_by_ext"],
                       computed={k: v[0] for k, v in sorted(by_ext.items())}))
    checks.append(dict(name="11:53 -> 12:19 file growth exceeds what 26 min of observed rate allows",
                       claim=P["t1219_files"] - P["t1153_files"],
                       computed_rate_per_min=(24723 - 24722) / (78.1 / 60.0)))

    res = dict(
        prior=PRIOR,
        fresh_tierA=dict(files=total_n, bytes=total_b),
        fresh_hits_rows=[r[0] for r in hits],
        fresh_A_minus_hits=dict(files=nh_n, bytes=nh_b),
        fresh_by_ext_minus_hits={k: dict(files=v[0], bytes=v[1]) for k, v in sorted(by_ext.items())},
        prior_by_ext_sum=sum(P["prior_by_ext"].values()),
        deltas=dict(
            clean_files_minus_fresh=nh_n - P["clean_files"],
            clean_bytes_minus_fresh=nh_b - P["clean_bytes"],
            prior_1223_bytes_minus_1153_bytes=P["t1223_bytes"] - P["t1153_bytes"],
            prior_hits_is_one_file=P["hits_bytes"],
        ),
        checks=checks,
    )
    with open(os.path.join(OUT, "probe_prior.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print(f"fresh tierA            : {total_n:,} / {total_b:,} B")
    print(f"fresh tierA minus hits : {nh_n:,} / {nh_b:,} B")
    print(f"prior by_ext sum       : {sum(P['prior_by_ext'].values()):,} (its files_total=24693, dumped=24676)")
    for c in checks:
        print(f"- {c['name']}\n    claim={c['claim']}  computed={c['computed'] if 'computed' in c else c.get('computed_from_1223')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
