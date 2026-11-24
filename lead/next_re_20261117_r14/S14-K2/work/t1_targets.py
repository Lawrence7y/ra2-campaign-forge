#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T1: 生成 S14 靶子清单。
    coverage.tsv  subsystem==S14  ∩  function_atlas.tsv
    关键: atlas entry 小写 hex, coverage entry 大写 -> 必须统一大小写 (§990)
    按 R14-R14 S 口径算真实 named, 算 proved, 算差几个到 50%。
"""
import csv, re, sys

ROOT = r"D:\Project\ra2-campaign-forge"
COV  = ROOT + r"\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATL  = ROOT + r"\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
OUT  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S14-K2\TARGETS.tsv"

def norm(e):
    """统一 hex 大小写, 去 0x 前缀, 补 8 位"""
    e = e.strip().lower()
    if e.startswith("0x"):
        e = e[2:]
    return e.zfill(8)

# atlas 集合 (entry -> row)
atl = {}
with open(ATL, "r", encoding="utf-8", newline="") as f:
    r = csv.DictReader(f, delimiter="\t")
    for row in r:
        atl[norm(row["entry"])] = row

# coverage 全表统计
cov_rows = []
with open(COV, "r", encoding="utf-8", newline="") as f:
    r = csv.DictReader(f, delimiter="\t")
    for row in r:
        cov_rows.append(row)

print("coverage data rows:", len(cov_rows))
print("atlas data rows   :", len(atl))

# S14 全量 (coverage 内 subsystem==S14)
s14_all = [row for row in cov_rows if row["subsystem"].strip() == "S14"]
print("S14 in coverage (all):", len(s14_all))

# S14 ∩ atlas (归一化大小写)
s14_atlas = [row for row in s14_all if norm(row["entry"]) in atl]
print("S14 ∩ atlas (case-normalized):", len(s14_atlas))

# 若不归一化的错误交集(演示 §990)
s14_bad = [row for row in s14_all if row["entry"].strip() in atl]
print("S14 ∩ atlas (NO normalization, WRONG):", len(s14_bad))

# 分母: atlas 分母 = ∩ 后的条数
N = len(s14_atlas)

# named L / S 口径
def named_L(name):
    n = (name or "").strip()
    return bool(n) and not n.startswith("sub_")

RE_CLASS_SUB = re.compile(r"^[A-Za-z_][\w:<>,*&~]*::sub_[0-9A-Fa-f]{8}$")
def named_S(name):
    n = (name or "").strip()
    if not named_L(n):
        return False
    # 排除 Class::sub_XXXXXXXX 自造占位名
    if RE_CLASS_SUB.match(n):
        return False
    return True

namedL = sum(1 for row in s14_atlas if named_L(row["name"]))
namedS = sum(1 for row in s14_atlas if named_S(row["name"]))
proved = sum(1 for row in s14_atlas if row["grade"].strip() == "[已证]")

# 差几个 proved 到 50% (门槛按 atlas 分母 N, 也按卡面 491 各给)
thr_N = -(-N // 4) * 2  # ceil(N*0.5) 但用整数: (N+1)//2
thr_N = (N + 1) // 2
thr_491 = 246

print()
print("=== S14 面板口径 (盘上自算, 分母 N=%d) ===" % N)
print("named_L = %d (%.2f%%)" % (namedL, 100.0*namedL/N))
print("named_S = %d (%.2f%%)" % (namedS, 100.0*namedS/N))
print("proved  = %d (%.2f%%)" % (proved, 100.0*proved/N))
print("50%% threshold on N   = %d, gap = %d" % (thr_N, max(0, thr_N-proved)))
print("50%% threshold on 491 = 246, gap = %d" % max(0, thr_491-proved))

# 输出 TARGETS.tsv: entry, size, name, grade, semantics, evidence_path
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["entry", "size", "name", "grade", "one_line_semantics", "evidence_path"])
    for row in sorted(s14_atlas, key=lambda r: norm(r["entry"])):
        e = norm(row["entry"])
        a = atl[e]
        w.writerow([e.upper(), a["size"], row["name"], row["grade"],
                    row["one_line_semantics"], row["evidence_path"]])
print("\nwrote", OUT)
