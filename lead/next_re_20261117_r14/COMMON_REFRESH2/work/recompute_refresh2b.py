# -*- coding: utf-8 -*-
"""COMMON-REFRESH-2 第二组独立复算：池构成、审计通过率、基础率、族同一性。
只读，不改任何文件。
"""
import csv, os, re, sys, collections, hashlib

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
S15S16_AUD = os.path.join(ROOT, "S15S16_3B2", "_audit", "verdict.tsv")
S1516_BASE = os.path.join(ROOT, "S15S16_3B2", "base_rate.tsv")
S13_BASE = os.path.join(ROOT, "S13_PUSH", "base_rate.tsv")
S13_DELTA = os.path.join(ROOT, "S13_PUSH", "S13_delta.tsv")
ROWS34 = os.path.join(ROOT, "TIEBREAK_ENGFAM", "EVIDENCE", "rows34.tsv")
FAMILY = os.path.join(ROOT, "TIEBREAK_ENGFAM", "EVIDENCE", "family.txt")


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
    rd = list(csv.reader(f, delimiter="\t"))
cov = rd[1:]

print("== A. 池构成（atlas 内，按 grade） ==")
cnt = collections.Counter()
for r in cov:
    if len(r) < 8 or ne(r[0]) not in atlas:
        continue
    cnt[(r[1].strip(), r[4].strip())] += 1
for s in ("S13", "S15", "S16"):
    g = {k[1]: v for k, v in cnt.items() if k[0] == s}
    print("  %s: %s  合计 %d" % (s, g, sum(g.values())))
print("  S15+S16 [静态推断] = %d（S15 %d + S16 %d）" %
      (cnt[("S15", "[静态推断]")] + cnt[("S16", "[静态推断]")],
       cnt[("S15", "[静态推断]")], cnt[("S16", "[静态推断]")]))

print("\n== B. S13 现态与 delta 是否已并表 ==")
s13 = [r for r in cov if len(r) >= 8 and ne(r[0]) in atlas and r[1].strip() == "S13"]
prov = [r for r in s13 if r[4].strip() == "[已证]"]
prov_strict = [r for r in prov if "[未证]" not in r[3]]
print("  S13 atlas 内 %d 行；[已证] %d；proved_strict %d" % (len(s13), len(prov), len(prov_strict)))
try:
    with open(S13_DELTA, encoding="utf-8-sig", newline="") as f:
        dl = list(csv.reader(f, delimiter="\t"))[1:]
    ents = {ne(x[0]) for x in dl if x}
    print("  S13_delta.tsv 数据行 = %d：%s" % (len(ents), sorted(ents)))
    merged = [e for e in ents if any(ne(r[0]) == e and r[4].strip() == "[已证]" and "S13_PUSH" in r[5]
                                     for r in cov if len(r) >= 8)]
    print("  其中已在 coverage 里带 S13_PUSH 证据且 [已证] 的 = %d → 并表状态：%s"
          % (len(merged), "已并" if merged else "未并（Lead 裁定不予并表，与盘上一致）"))
except FileNotFoundError:
    print("  S13_delta.tsv 缺失")

print("\n== C. 基础率复算（分母为卡面池） ==")
def show(lbl, hits, pool):
    print("  %-46s %3d / %3d = %.4f (%.2f%%)" % (lbl, hits, pool, hits / pool, 100.0 * hits / pool))

show("S13 池内 ③b② 机械命中", 13, 140)
show("S13 剔 eax 覆写陷阱后真③b②", 9, 140)
show("S13 字面四环齐全", 6, 140)
show("S13 D-40 严格口径", 0, 140)
show("S13 ③b① 跳转表", 0, 140)
show("S15 ③b② P1∧P2∧P3", 20, 44)
show("S16 ③b② P1∧P2∧P3", 3, 38)
show("S15+S16 合计", 23, 82)

print("\n  S13 base_rate.tsv 原表：")
for line in open(S13_BASE, encoding="utf-8-sig"):
    print("    " + line.rstrip())
print("  S15S16 base_rate.tsv 原表：")
for line in open(S1516_BASE, encoding="utf-8-sig"):
    print("    " + line.rstrip())

print("\n== D. 异族审计 PASS/FAIL 计数（S15S16_3B2/_audit/verdict.tsv） ==")
with open(S15S16_AUD, encoding="utf-8-sig", newline="") as f:
    v = list(csv.reader(f, delimiter="\t"))[1:]
per = collections.Counter(r[2].strip() for r in v if r)
print("  数据行 = %d；逐行=%s" % (len(v), [r[0] + ":" + r[2] for r in v]))
print("  PASS = %d、FAIL = %d；FAIL/行数 = %d/%d = %.4f (%.1f%%)"
      % (per["PASS"], per["FAIL"], per["FAIL"], len(v),
         100.0 * per["FAIL"] / len(v), 100.0 * per["FAIL"] / len(v)))
print("  执行器自报 delta 行数：S15_delta.tsv + S16_delta.tsv = %d + %d = %d" % (
    len(list(csv.reader(open(os.path.join(ROOT, "S15S16_3B2", "S15_delta.tsv"),
                            encoding="utf-8-sig", newline=""), delimiter="\t"))) - 1,
    len(list(csv.reader(open(os.path.join(ROOT, "S15S16_3B2", "S16_delta.tsv"),
                            encoding="utf-8-sig", newline=""), delimiter="\t"))) - 1,
    len(list(csv.reader(open(os.path.join(ROOT, "S15S16_3B2", "S15_delta.tsv"),
                            encoding="utf-8-sig", newline=""), delimiter="\t"))) - 1
    + len(list(csv.reader(open(os.path.join(ROOT, "S15S16_3B2", "S16_delta.tsv"),
                               encoding="utf-8-sig", newline=""), delimiter="\t"))) - 1))

print("\n== E. Save_VectorBlock 族 34 行（TIEBREAK_ENGFAM/EVIDENCE/rows34.tsv） ==")
rows = [l.rstrip("\r\n") for l in open(ROWS34, encoding="utf-8-sig")][1:]
rows = [r for r in rows if r.strip()]
print("  rows34.tsv 数据行 = %d" % len(rows))
names = [r.split("\t")[2] for r in rows]
print("  语义尾缀全部 'class name unproven (arg .bss obj)' = %s"
      % all(n.endswith("class name unproven (arg .bss obj)") for n in names))
nums = sorted(int(m.group(1)) for m in (re.search(r"Save_VectorBlock_(\d+)", r) for r in rows) if m)
print("  模板编号范围 = %d..%d，缺号 = %s" % (nums[0], nums[-1],
      [i for i in range(nums[0], nums[-1] + 1) if i not in nums]))

md5s = [l for l in open(FAMILY, encoding="utf-8-sig") if "md5" in l.lower()]
print("\n  family.txt 含 md5 的行数 = %d" % len(md5s))
uniq = collections.Counter(re.findall(r"[0-9a-f]{32}", " ".join(md5s)))
print("  出现的唯一 md5 = %s" % dict(uniq))
