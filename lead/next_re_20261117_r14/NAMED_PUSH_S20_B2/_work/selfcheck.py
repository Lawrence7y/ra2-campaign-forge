# -*- coding: utf-8 -*-
"""交付自检：
 1 delta.tsv 格式（6 列、entry 大写 8 位无 0x、grade=[已证]、evidence_path 存在且指向本目录）
 2 delta 每行语义栏里的每个 8 位十六进制地址，都能在对应 EVIDENCE 文件里找到（引用与自家证据同数）
 3 不许整批共用同一段 reason（行间语义重复度）
 4 EVIDENCE 四环标题齐全
 5 base_rate.tsv 与 delta 行数自洽
"""
import json
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.dirname(WORK)
rows = [l.rstrip("\n").split("\t") for l in open(os.path.join(OUTDIR, "delta.tsv"), encoding="utf-8")][1:]
rows = [r for r in rows if r and r[0]]
fail = 0

print("== 1 delta 格式 ==")
print("   数据行 =", len(rows))
for r in rows:
    ok_col = len(r) == 6
    e = r[0]
    ok_entry = bool(re.fullmatch(r"[0-9A-F]{8}", e))
    ok_grade = r[4] == "[已证]"
    ev = r[5]
    ok_path = os.path.isfile(ev.replace("/", os.sep))
    print("   %s cols=%d entry_ok=%s grade=%s path=%s" % (e, len(r), ok_entry, ok_grade, ok_path))
    if not (ok_col and ok_entry and ok_grade and ok_path):
        fail += 1

print("== 2 语义栏地址必须能在自家 EVIDENCE 找到 ==")
for r in rows:
    e, sem, ev = r[0], r[3], r[5]
    txt = open(ev.replace("/", os.sep), encoding="utf-8").read().upper()
    addrs = set(re.findall(r"\b([0-9A-F]{8})\b", sem.upper()))
    # 允许 vt / COL / TD 这类只在 hex 形式出现；逐个核是否出现在证据文件
    missing = [a for a in sorted(addrs) if a not in txt]
    print("   %s 引用地址 %d 个，证据缺失 %d 个 %s" % (e, len(addrs), len(missing), missing[:6]))
    if missing:
        fail += 1

print("== 3 不许整批共用同一段 reason ==")
sems = [r[3] for r in rows]
for i in range(len(sems)):
    for j in range(i + 1, len(sems)):
        a, b = sems[i], sems[j]
        common = len(set(a) & set(b)) / max(1, len(set(a) | set(b)))
        # 中文字符集共享率很高，改用「相同 20 字长子串」判定
        grams_a = {a[k:k + 20] for k in range(max(1, len(a) - 19))}
        grams_b = {b[k:k + 20] for k in range(max(1, len(b) - 19))}
        dup = len(grams_a & grams_b) / max(1, len(grams_a | grams_b))
        flag = "SUSPECT" if dup > 0.30 else "ok"
        if dup > 0.30:
            fail += 1
        print("   %s vs %s  20-gram Jaccard=%.3f %s" % (rows[i][0], rows[j][0], dup, flag))

print("== 4 EVIDENCE 四环标题 ==")
for r in rows:
    txt = open(r[5].replace("/", os.sep), encoding="utf-8").read()
    need = ["## ① 入口", "## ② 类身份", "## ③ 整体合同", "## ④ 使用见证"]
    miss = [n for n in need if n not in txt]
    print("   %s %s" % (r[0], "OK" if not miss else "MISSING %s" % miss))
    if miss:
        fail += 1

print("== 5 base_rate 自洽 ==")
br = [l.rstrip("\n").split("\t") for l in open(os.path.join(OUTDIR, "base_rate.tsv"), encoding="utf-8")][1:]
b = br[0]
print("   base_rate:", b)
rows_checked, ring2_ok, ring3b_ok, ring4_ok, all_four = (int(x) for x in b[1:6])
ok = (rows_checked == 18 and all_four == len(rows) and ring3b_ok == len(rows)
      and all_four <= rows_checked and abs(float(b[6]) - all_four / rows_checked) < 5e-4)
print("   rows_checked=%d(=18) all_four=%d(==delta行数%d) ring3b=%d(==delta行数%d) rate=%s 自洽=%s" % (
    rows_checked, all_four, len(rows), ring3b_ok, len(rows), b[6], ok))
if not ok:
    fail += 1

print()
print("FAIL 计数 =", fail)
