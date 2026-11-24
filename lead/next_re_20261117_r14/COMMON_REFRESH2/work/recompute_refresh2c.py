# -*- coding: utf-8 -*-
"""COMMON-REFRESH-2 第三组独立复算：池口径（含 atlas 外）+ 族编号。只读。"""
import csv, os, re, sys, collections

sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")


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
    next(f)
    for line in f:
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip():
            atlas.add(ne(p[0]))

with open(COV, encoding="utf-8-sig", newline="") as f:
    cov = list(csv.reader(f, delimiter="\t"))[1:]

print("== A'. S15S16-3B2 池口径（subsystem∈{S15,S16} ∧ grade=[静态推断]，不设 atlas 过滤） ==")
c1 = collections.Counter()
c2 = collections.Counter()
for r in cov:
    if len(r) < 8 or r[1].strip() not in ("S15", "S16"):
        continue
    if r[4].strip() != "[静态推断]":
        continue
    c1[r[1].strip()] += 1
    c2[(r[1].strip(), "in" if ne(r[0]) in atlas else "out")] += 1
print("  按 subsystem：%s  合计 %d" % (dict(c1), sum(c1.values())))
print("  细分（atlas 内/外）：%s" % dict(c2))

print("\n== A''. S13 池口径（S13 ∧ 非[已证]，atlas 内） ==")
c3 = collections.Counter()
for r in cov:
    if len(r) < 8 or r[1].strip() != "S13" or ne(r[0]) not in atlas:
        continue
    c3[r[4].strip()] += 1
print("  %s ⇒ 池（[静态推断]+[未证]）= %d" % (dict(c3), c3["[静态推断]"] + c3["[未证]"]))

print("\n== E'. Save_VectorBlock_NN 族编号（coverage name 列） ==")
fam = [(ne(r[0]), r[2].strip(), r[4].strip(), r[1].strip()) for r in cov
       if len(r) >= 8 and "Save_VectorBlock" in r[2]]
print("  name 含 Save_VectorBlock 的行 = %d" % len(fam))
nums = sorted(int(m.group(1)) for _, n, _, _ in fam if (m := re.search(r"Save_VectorBlock_(\d+)", n)))
print("  编号 = %d..%d，共 %d 个编号，缺号 = %s" %
      (nums[0], nums[-1], len(nums), [i for i in range(nums[0], nums[-1] + 1) if i not in nums]))
print("  全部 subsystem = %s；grade 分布 = %s" %
      (sorted({s for *_, s in fam}), dict(collections.Counter(g for _, _, g, _ in fam))))
print("  前 3 与后 3：%s ... %s" % ([f[:2] for f in fam[:3]], [f[:2] for f in fam[-3:]]))

print("\n== E''. 英文措辞族（(?i)unproven|unverified|not proven）全表命中 ==")
pat = re.compile(r"unproven|unverified|not proven", re.I)
hit = [r for r in cov if len(r) >= 8 and pat.search(r[3])]
print("  命中行 = %d；subsystem = %s；grade = %s" % (
    len(hit), sorted({r[1].strip() for r in hit}), sorted({r[4].strip() for r in hit})))
print("  含中文子串 [未证] 的 = %d" % sum(1 for r in hit if "[未证]" in r[3]))
print("  其中 name 含 Save_VectorBlock 的 = %d" % sum(1 for r in hit if "Save_VectorBlock" in r[2]))

print("\n== F. 三条线现态 vs 门槛（口径同 PANEL 表头） ==")
d = collections.defaultdict(collections.Counter)
for r in cov:
    if len(r) < 8 or ne(r[0]) not in atlas:
        continue
    s = r[1].strip()
    d[s]["n"] += 1
    if r[4].strip() == "[已证]":
        d[s]["p"] += 1
        if "[未证]" not in r[3]:
            d[s]["ps"] += 1
import math
for s in ("S13", "S15", "S16"):
    c = d[s]
    t = math.ceil(0.5 * c["n"])
    print("  %s n=%d 门槛=%d proved=%d(strict %d) 差=%d(严格差 %d)"
          % (s, c["n"], t, c["p"], c["ps"], t - c["p"], t - c["ps"]))
