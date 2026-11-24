# -*- coding: utf-8 -*-
"""COMMON-REFRESH-2 独立复算：只读盘点，不出任何写操作。

口径完全照 RULING_R15_20261119/work/strict_panel.py（面板表头口径）：
  atlas entry 归一为大写 8 位；coverage 数据行 8 列
  named_L      name 非空且不以 sub_ 开头
  named_S(R14) named_L 中排除 *::sub_<hex>
  named_strict named_S(R14) 中再排除 *::v?slotN
  proved_n     atlas 内 grade == [已证]
  proved_str   proved_n 中 one_line_semantics 不含子串 [未证]
门槛 named = ceil(0.9*n)；proved = ceil(0.5*n)
"""
import csv, json, os, re, collections, math, sys, hashlib

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")

RE_SLOT = re.compile(r"::v?slot\d+$")
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")


def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest().upper()


print("[文件指纹]")
for p in (COV, ATLAS, PANEL):
    print("  %s  %s  %d B" % (os.path.basename(p), sha(p), os.path.getsize(p)))

atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i == 0:
            continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip():
            atlas.add(ne(p[0]))
print("[atlas] 数据行 entry 数 = %d" % len(atlas))

with open(COV, encoding="utf-8-sig", newline="") as f:
    rd = list(csv.reader(f, delimiter="\t"))
hdr, cov = rd[0], rd[1:]
print("[coverage] 表头列 = %s" % hdr)
print("[coverage] 数据行 = %d" % len(cov))

d = collections.defaultdict(collections.Counter)
grade_all = collections.Counter()
for r in cov:
    if len(r) < 8:
        continue
    e = ne(r[0])
    s = r[1].strip()
    grade_all[r[4].strip()] += 1
    if e not in atlas:
        d[s]["cov_nonatlas"] += 1
        continue
    name = r[2].strip()
    sem = r[3]
    grade = r[4].strip()
    d[s]["atlas_n"] += 1
    if name and not name.startswith("sub_"):
        d[s]["named_L"] += 1
        if not RE_CSUB.search(name):
            d[s]["named_S14"] += 1
            if not RE_SLOT.search(name):
                d[s]["named_strict"] += 1
    if grade == "[已证]":
        d[s]["proved_n"] += 1
        if "[未证]" not in sem:
            d[s]["proved_strict_n"] += 1

print("[coverage] grade 直方图 = %s" % dict(grade_all))

print("\n[逐子系统] S  atlas_n  named_L  named_S14  named_strict  proved_n  proved_strict  thu_n  thu_p")
rows = {}
for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
    c = d[s]
    a = c["atlas_n"]
    tn, tp = math.ceil(0.9 * a), math.ceil(0.5 * a)
    rows[s] = dict(atlas_n=a, named_L=c["named_L"], named_S14=c["named_S14"],
                   named_strict=c["named_strict"], proved_n=c["proved_n"],
                   proved_strict_n=c["proved_strict_n"], thu_named=tn, thu_proved=tp,
                   pool=c["proved_n"] and 0)
    print("  %s  %5d  %5d  %5d  %5d  %5d  %5d  %5d  %5d" %
          (s, a, c["named_L"], c["named_S14"], c["named_strict"], c["proved_n"],
           c["proved_strict_n"], tn, tp))

# ---- 关注三条线 ----
print("\n[三条线定点核对]")
for s in ("S13", "S15", "S16"):
    r = rows[s]
    gap_n = r["thu_named"] - r["named_S14"]
    gap_p = r["thu_proved"] - r["proved_n"]
    gap_ps = r["thu_proved"] - r["proved_strict_n"]
    print("  %s: n=%d named_S(R14)=%d(thu %d, gap %d) proved=%d(thu %d, gap %d) "
          "proved_strict=%d(gap %d)" %
          (s, r["atlas_n"], r["named_S14"], r["thu_named"], gap_n, r["proved_n"],
           r["thu_proved"], gap_p, r["proved_strict_n"], gap_ps))

# ---- S13 池 = 非 [已证] 且 atlas 内 ----
print("\n[S13 池]")
for s in ("S13", "S15", "S16"):
    pool = 0
    for r in cov:
        if len(r) < 8:
            continue
        if ne(r[0]) not in atlas or r[1].strip() != s:
            continue
        if r[4].strip() != "[已证]":
            pool += 1
    print("  %s 非[已证] 且 atlas 内 = %d" % (s, pool))

# ---- 全表 ----
tot = collections.Counter()
for r in rows.values():
    for k in ("atlas_n", "named_L", "named_S14", "named_strict", "proved_n", "proved_strict_n"):
        tot[k] += r[k]
print("\n[TOTAL S01-S22] %s" % dict(tot))

json.dump({k: v for k, v in rows.items()},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rows.json"), "w",
               encoding="utf-8"), ensure_ascii=False, indent=1)
