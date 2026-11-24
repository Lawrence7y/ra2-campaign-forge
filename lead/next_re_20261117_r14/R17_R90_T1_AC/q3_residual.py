#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Q3 · 两笔合计的账（residual_ac.tsv）。
  A 笔 114 件：由 majority_114.tsv 的 verdict 列汇总（对象抄本 / 过程输出）。
  C 笔 126 件：由 u1_126.tsv 的 verdict 列汇总（孤本=>应留 / 非孤本=>应排）。
「应排 / 应留」口径：
  对象抄本 = 应留（是被测对象的记载） ; 过程输出 = 应排（是过程痕迹，不承载对象事实）
  非孤本(旧版副本) = 应排 ; 孤本 = 应留 ; 未取得 = 单列
"""
from __future__ import annotations
import json, os
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))


def rows(p):
    with open(os.path.join(HERE, p), encoding="utf-8", newline="") as f:
        head = f.readline().rstrip("\r\n").split("\t")
        for line in f:
            yield dict(zip(head, line.rstrip("\r\n").split("\t")))


bucket = OrderedDict()


def add(book, verdict, dispose, n, b):
    k = (book, verdict, dispose)
    bucket.setdefault(k, [0, 0])
    bucket[k][0] += n
    bucket[k][1] += b


for r in rows("majority_114.tsv"):
    v = r["verdict"]
    disp = "应留" if v == "对象抄本" else ("应排" if v == "过程输出" else "单列")
    add("A", v, disp, 1, int(r["bytes"]))
for r in rows("u1_126.tsv"):
    v = r["verdict"]
    disp = "应排" if v.startswith("非孤本") else ("应留" if v.startswith("孤本") else "单列")
    add("C", v, disp, 1, int(r["bytes"]))

out = os.path.join(HERE, "residual_ac.tsv")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write("book\tverdict\tdisposition\tfiles\tbytes\n")
    for (book, v, d), (n, b) in bucket.items():
        f.write(f"{book}\t{v}\t{d}\t{n}\t{b}\n")
    # 分笔小计
    for book in ("A", "C"):
        for d in ("应排", "应留", "单列"):
            n = sum(x[0] for (bk, _, dd), x in bucket.items() if bk == book and dd == d)
            b = sum(x[1] for (bk, _, dd), x in bucket.items() if bk == book and dd == d)
            if n:
                f.write(f"{book}\t(小计)\t{d}\t{n}\t{b}\n")
    for d in ("应排", "应留", "单列"):
        n = sum(x[0] for (bk, v, dd), x in bucket.items() if dd == d)
        b = sum(x[1] for (bk, v, dd), x in bucket.items() if dd == d)
        f.write(f"A+C\t(合计)\t{d}\t{n}\t{b}\n")

tot = {"n": 0, "b": 0}
tally = {"应排": [0, 0], "应留": [0, 0], "单列": [0, 0]}
by_book = {}
for (book, v, d), (n, b) in bucket.items():
    tot["n"] += n
    tot["b"] += b
    tally[d][0] += n
    tally[d][1] += b
    by_book.setdefault(book, {})[v] = {"n": n, "bytes": b}
summary = {"total": tot, "tally": tally, "by_book": by_book}
with open(os.path.join(HERE, "q3_residual.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
print(open(out, encoding="utf-8").read())
