#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R92-T1-REJUDGE / Q3 : 转移矩阵（旧\\新），逐格闭合。
R92-T1-REJUDGE / Q5① : 第二套独立实现（PowerShell 读盘 + 独立重算）复算矩阵总件数/总字节。

Q3 矩阵四类行/列 = 对象抄本 / 过程输出 / 无法判定 / 永久判不了
  —— 旧侧四类中「无法判定」= R44 的 266 件；新侧四类中「无法判定」本轮 = 0 件
  —— 为让矩阵仍然成为 4x4 方阵并且逐格可解释，新侧保留该列并填 0。
"""
import csv, os, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.dirname(os.path.abspath(__file__))

CLS = ["对象抄本", "过程输出", "无法判定", "永久判不了"]


def load():
    return list(csv.DictReader(open(os.path.join(OUT, "rejudge1242.tsv"), encoding="utf-8"),
                               delimiter="\t"))


rows = load()

# ---------- 矩阵：件数 / 字节 ----------
cnt = defaultdict(int)
byt = defaultdict(int)
for r in rows:
    k = (r["old_verdict"], r["new_verdict"])
    cnt[k] += 1
    byt[k] += int(r["bytes"])

lines = []
lines.append("=== Q3 转移矩阵（旧裁决 \\ 新口径）===")
lines.append("")
hdr = "旧\\新".ljust(14) + "".join(c.rjust(14) for c in CLS) + "合计".rjust(14)
lines.append("【件数】")
lines.append(hdr)
for o in CLS:
    cells = [cnt.get((o, n), 0) for n in CLS]
    lines.append(o.ljust(14) + "".join(str(x).rjust(14) for x in cells)
                 + str(sum(cells)).rjust(14))
colsum = [sum(cnt.get((o, n), 0) for o in CLS) for n in CLS]
lines.append("合计".ljust(14) + "".join(str(x).rjust(14) for x in colsum)
             + str(sum(colsum)).rjust(14))
mat_total = sum(cnt.values())
lines.append("")
lines.append(f"件数闭合：矩阵所有格子之和 = {mat_total} ；全集件数 = {len(rows)} ；"
             f"闭合 = {'是' if mat_total == len(rows) else '否'}")
lines.append("")

hdr2 = "旧\\新".ljust(14) + "".join(c.rjust(16) for c in CLS) + "合计".rjust(16)
lines.append("【字节】")
lines.append(hdr2)
for o in CLS:
    cells = [byt.get((o, n), 0) for n in CLS]
    lines.append(o.ljust(14) + "".join(str(x).rjust(16) for x in cells)
                 + str(sum(cells)).rjust(16))
colsum_b = [sum(byt.get((o, n), 0) for o in CLS) for n in CLS]
lines.append("合计".ljust(14) + "".join(str(x).rjust(16) for x in colsum_b)
             + str(sum(colsum_b)).rjust(16))
mat_total_b = sum(byt.values())
all_b = sum(int(r["bytes"]) for r in rows)
lines.append("")
lines.append(f"字节闭合：矩阵所有格子之和 = {mat_total_b} ；全集字节 = {all_b} ；"
             f"闭合 = {'是' if mat_total_b == all_b else '否'}")
lines.append("")

# ---------- 单列：对象→过程 / 过程→对象 ----------
a = ("对象抄本", "过程输出")
b = ("过程输出", "对象抄本")
lines.append("=== 旧判据误判的直接度量 ===")
lines.append(f"对象 → 过程：{cnt.get(a,0)} 件 / {byt.get(a,0)} B")
lines.append(f"过程 → 对象：{cnt.get(b,0)} 件 / {byt.get(b,0)} B")
lines.append(f"两向合计  ：{cnt.get(a,0)+cnt.get(b,0)} 件 / {byt.get(a,0)+byt.get(b,0)} B")
lines.append(f"未变动件数：{sum(cnt.get((c,c),0) for c in CLS)} 件 / "
             f"{sum(byt.get((c,c),0) for c in CLS)} B")
lines.append("")

# ---------- 新分布 / 旧分布 ----------
lines.append("=== 两侧分布 ===")
old_c, old_b, new_c, new_b = defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)
for r in rows:
    old_c[r["old_verdict"]] += 1
    old_b[r["old_verdict"]] += int(r["bytes"])
    new_c[r["new_verdict"]] += 1
    new_b[r["new_verdict"]] += int(r["bytes"])
for c in CLS:
    lines.append(f"  {c}\t旧 {old_c.get(c,0):5d} 件 / {old_b.get(c,0):10d} B"
                 f"\t新 {new_c.get(c,0):5d} 件 / {new_b.get(c,0):10d} B")

with open(os.path.join(OUT, "q3_matrix.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))

# 机器可读版，供 Q5① 第二实现对照
with open(os.path.join(OUT, "q3_matrix.tsv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["old", "new", "n", "bytes"])
    for o in CLS:
        for n in CLS:
            w.writerow([o, n, cnt.get((o, n), 0), byt.get((o, n), 0)])
    w.writerow(["TOTAL", "", mat_total, mat_total_b])
    w.writerow(["SHIFT", "obj2proc", cnt.get(a, 0), byt.get(a, 0)])
    w.writerow(["SHIFT", "proc2obj", cnt.get(b, 0), byt.get(b, 0)])
