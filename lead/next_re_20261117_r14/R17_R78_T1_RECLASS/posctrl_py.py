#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""posctrl_py.py — R43-T1 Q5 正控 · 法 2（Python，与裁决器源码不共享任何函数）

独立实现要点：
  - 用 csv 模块（不是 split("\\t")）解析清单；
  - 用 dict 而不是 set 求差集；
  - 字节用 sum() 生成器，不使用逐行累加变量。
"""
import csv
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
A = BASE + r"\R17_R72_T1_CLEANSCALE\files_tier_A_snap2.tsv"
Cp = BASE + r"\R17_R78_T1_RECLASS\files_tier_Cprime.tsv"


def rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh, delimiter="\t")
        for d in r:
            yield d["rel"], int(d["bytes"])


_a = dict(rows(A))
_c = dict(rows(Cp))
only_a = [k for k in _a if k not in _c]
print(f"PY  nA={len(_a)} sumA={sum(_a.values())}  nCp={len(_c)} sumCp={sum(_c.values())}  "
      f"AminusCp_n={len(only_a)} AminusCp_b={sum(_a[k] for k in only_a)}")
