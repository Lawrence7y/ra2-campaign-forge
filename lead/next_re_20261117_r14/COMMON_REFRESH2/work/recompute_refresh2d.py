# -*- coding: utf-8 -*-
"""COMMON-REFRESH-2 第四组复算：S13 候选 6 行现态、S15/S16 池漂移溯源（M59 并入）。只读。"""
import csv, json, os, sys, collections

sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
POOL = os.path.join(ROOT, "S15S16_3B2", "work", "pool.json")


def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


with open(COV, encoding="utf-8-sig", newline="") as f:
    cov = list(csv.reader(f, delimiter="\t"))[1:]

row = {}
for r in cov:
    if len(r) >= 8:
        row[ne(r[0])] = r

print("== G. S13-PUSH 六个候选行在 coverage 的现态 ==")
for e in ("004684E0", "00629FD0", "0075E0C0", "0075E2C0", "00772CD0", "00772EB0"):
    r = row.get(e)
    if not r:
        print("  %s  不在 coverage" % e)
        continue
    print("  %s  %-3s %-28s grade=%-6s evidence_path=%s" %
          (e, r[1], r[2], r[4], r[5]))

print("\n== H. S15S16_3B2 池（work/pool.json）对照现盘 grade ==")
pool = json.load(open(POOL, encoding="utf-8"))
print("  pool.json 行数 = %d（%s）" % (len(pool), dict(collections.Counter(p["subsystem"] for p in pool))))
now = collections.Counter()
moved = []
for p in pool:
    r = row.get(p["entry"])
    g = r[4].strip() if r else "缺失"
    now[(p["subsystem"], g)] += 1
    if g != "[静态推断]":
        moved.append((p["subsystem"], p["entry"], p["name"], g))
print("  现盘 grade 分布 = %s" % dict(now))
print("  已离开池的行（现非 [静态推断]）= %d：" % len(moved))
for m in moved:
    print("    %s  %s  %-34s -> %s" % m)

print("\n== I. 现盘 S15/S16 池（同口径：subsystem ∧ [静态推断]，不设 atlas 过滤） ==")
c = collections.Counter()
for r in cov:
    if len(r) >= 8 and r[1].strip() in ("S15", "S16") and r[4].strip() == "[静态推断]":
        c[r[1].strip()] += 1
print("  %s 合计 %d" % (dict(c), sum(c.values())))
