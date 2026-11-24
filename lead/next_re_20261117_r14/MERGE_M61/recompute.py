# -*- coding: utf-8 -*-
"""M61 独立重算：全表 [已证] / atlas 内 [已证] / atlas 外 [已证]。
口径与 RULING_R15/work/strict_panel.py 一致（entry 统一大写 + %08X 归一）。
只读，不写任何项目文件。
"""
import csv, sys
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
COV = PROJ + r"\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATLAS = PROJ + r"\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"


def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i == 0:
            continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip():
            atlas.add(ne(p[0]))

all_rows = 0
total_proved = 0
atlas_proved = 0
nonatlas_proved = 0
atlas_in_rows = 0
with open(COV, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.reader(f, delimiter="\t"))[1:]
for r in rows:
    if len(r) < 8:
        continue
    all_rows += 1
    e = ne(r[0])
    grade = r[4].strip()
    in_a = e in atlas
    if in_a:
        atlas_in_rows += 1
    if grade == "[已证]":
        total_proved += 1
        if in_a:
            atlas_proved += 1
        else:
            nonatlas_proved += 1

print("coverage 数据行 =", all_rows)
print("atlas 内行数 =", atlas_in_rows)
print("全表 [已证] =", total_proved)
print("atlas 内 [已证] =", atlas_proved)
print("atlas 外 [已证] =", nonatlas_proved)
print("校验 全表 = atlas内 + atlas外 :", total_proved == atlas_proved + nonatlas_proved)
