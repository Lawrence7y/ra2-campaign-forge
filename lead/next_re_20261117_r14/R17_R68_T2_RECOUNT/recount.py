#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# R17_R68_T2_RECOUNT / recount.py
# R37-T2-RECOUNT 复算脚本。只读源文件；产物只写本脚本所在目录。
# 用法: python recount.py    (打印所有复算数字; 不写任何文件)
import csv, pathlib, collections

BASE = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14")
R19  = BASE / "R17_R19_RTTI_XCHECK"
R24  = BASE / "R17_R24_RECON_FINAL"
R17  = BASE / "R17_R17_SLOT73_MAP"

def read_tsv(p):
    with p.open("r", encoding="utf-8", newline="") as f:
        r = csv.reader(f, delimiter="\t")
        rows = list(r)
    return rows[0], [x for x in rows[1:] if x and any(c for c in x)]

def main():
    print("=== Q1: R19 reconcile.tsv 直接按 bucket 列取值计数 ===")
    h, d = read_tsv(R19 / "reconcile.tsv")
    print("表头/列名:", h, "数据行数:", len(d))
    c = collections.Counter(row[1] for row in d)
    for k in ("BOTH", "COVERAGE_ONLY", "RTTI_ONLY"):
        print(f"  {k} = {c[k]}")
    print("  三桶合计 =", sum(c.values()), " 全表数据行 =", len(d),
          " 相等?", sum(c.values()) == len(d))

    print("\n=== Q1b: 口径 S 权威数 (R24 reconcile_final.tsv / S_bucket 列) ===")
    h2, d2 = read_tsv(R24 / "reconcile_final.tsv")
    print("表头/列名:", h2, "数据行数:", len(d2))
    sc = collections.Counter(row[2] for row in d2)
    print("  S_bucket: BOTH =", sc["BOTH"], " COVERAGE_ONLY =", sc["COVERAGE_ONLY"])
    sm = collections.Counter(row[3] for row in d2 if row[2] == "BOTH")
    print("  S BOTH 机制拆分:", dict(sm), " 合计 =", sum(sm.values()))
    cc = collections.Counter(row[4] for row in d2)
    print("  C_bucket: BOTH =", cc["BOTH"], " COVERAGE_ONLY =", cc["COVERAGE_ONLY"])

    print("\n=== Q2: 口径 C 实现规则 (R24 work.py) ===")
    print("  C=严格基名S之上加 X_Y/X_Y_Z 下划线整体替换为 @ ,与 非模板复合TD 的 X@Y/X@Y@Z 大小写不敏感精确相等; 禁止丢段取基名; 模板态@不适用。")
    print("  compound_names.tsv 数据行数(含模板+非模板复合名):")
    hc, dc = read_tsv(R24 / "compound_names.tsv")
    print("   ", len(dc), " 列名:", hc)

    print("\n=== Q3: reverse_map.tsv 0x004264C0 ===")
    h3, d3 = read_tsv(R17 / "reverse_map.tsv")
    print("表头/列名:", h3, "数据行数:", len(d3))
    allrows = [r for r in d3 if r[0] == "0x004264C0"]
    s107 = [r for r in allrows if r[3] == "107"]
    print("  全slot出现次数 =", len(allrows))
    print("  涉及不同类(全slot) =", len({r[1] for r in allrows}))
    print("  @107 行数 =", len(s107), " 不同类 =", len({r[1] for r in s107}))
    print("  使用到的slot =", sorted({r[3] for r in allrows}))

    print("\n=== Q4: 220 来源 ===")
    print("  R19 reconcile.tsv bucket=COVERAGE_ONLY 行数 =", c["COVERAGE_ONLY"])

    print("\n=== Q5: 正控 — 口径S BOTH 两独立法 ===")
    print("  法A (reconcile_final.tsv S_bucket列值为BOTH的行数):", sc["BOTH"])
    print("  法B (S_bucket=BOTH行的S_mechanism分组求和 exact+prefix+template_base):", sum(sm.values()), dict(sm))
    print("  两法相同?", sc["BOTH"] == sum(sm.values()))

    print("\n=== 正控2: R19 BOTH 两独立法 ===")
    # 法A: csv 列取值; 法B: 原始文本行 split, 计数 note 含固定串 "coverage第4列命中；Q1裸名集合命中"
    raw = (R19 / "reconcile.tsv").read_text(encoding="utf-8").splitlines()[1:]
    both_note = sum(1 for ln in raw if ln and ln.split("\t")[1] == "BOTH")
    print("  法A (csv bucket列):", c["BOTH"], " 法B (原始文本split bucket列):", both_note,
          " 相同?", c["BOTH"] == both_note)

if __name__ == "__main__":
    main()
