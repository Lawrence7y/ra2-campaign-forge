# -*- coding: utf-8 -*-
"""MEASURE-F3A step 9: final per-subsystem table, three scenarios.

S1 现状                        proved as recorded
S2 严格按 §8.6 处理 273 行乙   proved - 乙        <- the card's (乙) branch
S3 最宽救回                    proved - 乙 + 字节可找到 ③b 的乙行数
                               (an upper bound; shows the conclusion is not
                                sensitive to the 甲/乙 reading)
"""
import csv, json, os, sys, math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from pelib import PE
from thirdb import conds, thirdb, which

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
BASE = os.path.join(ROOT, r"lead\next_re_20261117_r14\MEASURE_F3A")
work = os.path.join(BASE, "work")
COLS = ["entry", "subsystem", "name", "one_line_semantics",
        "grade", "evidence_path", "n_sources", "conflict"]
JIA = {"00522340"}

pe = PE(EXE)
size_of = {}
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        size_of[r["entry"].upper()] = int(r["size"])

rows = []
for i, line in enumerate(open(COV, encoding="utf-8-sig", newline="")):
    line = line.rstrip("\r\n")
    if not line or i == 0:
        continue
    rows.append(dict(zip(COLS, line.split("\t"))))

def named_S(r):
    nm = (r["name"] or "").strip()
    return bool(nm) and not nm.startswith("sub_") and "::sub_" not in nm

dom = [r for r in rows if r["grade"] == "[已证]"
       and "[未证]" in r["one_line_semantics"] and r["subsystem"] != "S22"]
thirds = {}
for r in dom:
    e = r["entry"].upper()
    thirds[e] = thirdb(conds(pe, int(e, 16), size_of[e]))

subs = sorted({r["subsystem"] for r in rows if r["subsystem"] != "S22"})
T = {}
for s in subs:
    at = [r for r in rows if r["subsystem"] == s and r["entry"].upper() in size_of]
    n = len(at)
    proved = sum(1 for r in at if r["grade"] == "[已证]")
    f3 = [r for r in dom if r["subsystem"] == s]
    jia = sum(1 for r in f3 if r["entry"].upper() in JIA)
    yi = len(f3) - jia
    rescue = sum(1 for r in f3 if r["entry"].upper() not in JIA and thirds[r["entry"].upper()])
    nm = sum(1 for r in at if named_S(r))
    tn, tp = math.ceil(0.9 * n), math.ceil(0.5 * n)
    T[s] = dict(n=n, named_S=nm, thr_named=tn, thr_proved=tp, proved=proved,
                f3a=len(f3), jia=jia, yi=yi, rescue=rescue,
                s1=proved, s2=proved - yi, s3=proved - yi + rescue,
                p1=proved >= tp and nm >= tn,
                p2=(proved - yi) >= tp and nm >= tn,
                p3=(proved - yi + rescue) >= tp and nm >= tn,
                need=max(0, tp - (proved - yi)),
                pct1=round(100.0 * proved / n, 1),
                pct2=round(100.0 * (proved - yi) / n, 1),
                pct3=round(100.0 * (proved - yi + rescue) / n, 1))

hdr = ("| subsystem | n | F3a | 甲 | 乙 | 现proved | §8.6降级后 | 门槛 | 降级后达标 | 字节可找到③b(救回上限) | 最宽救回后 |")
print(hdr)
print("|" + "---|" * 11)
for s in subs:
    d = T[s]
    print("| %s | %d | %d | %d | %d | %d/%d (%.1f%%) | **%d/%d (%.1f%%)** | %d | %s | %d | %d/%d (%.1f%%) |" % (
        s, d["n"], d["f3a"], d["jia"], d["yi"], d["proved"], d["n"], d["pct1"],
        d["s2"], d["n"], d["pct2"], d["thr_proved"],
        "✅" if d["p2"] else "❌", d["rescue"], d["s3"], d["n"], d["pct3"]))

p1 = [s for s in subs if T[s]["p1"]]
p2 = [s for s in subs if T[s]["p2"]]
p3 = [s for s in subs if T[s]["p3"]]
print("\n达标 S1 现状      : %d %s" % (len(p1), p1))
print("达标 S2 §8.6 严格 : %d %s" % (len(p2), p2))
print("达标 S3 最宽救回   : %d %s" % (len(p3), p3))
print("\nrobustness: 降级后每家还缺多少 proved 才能回到门槛")
for s in ("S15", "S16", "S17"):
    d = T[s]
    print("  %s: 降级后 %d/%d, 门槛 %d, 还缺 %d; 字节可救回上限 %d; 最宽救回后 %d -> %s"
          % (s, d["s2"], d["n"], d["thr_proved"], d["need"], d["rescue"], d["s3"],
             "PASS" if d["p3"] else "FAIL"))
print("\nnamed 线不受 grade 影响，故降级不改 named：")
for s in ("S15", "S16", "S17"):
    d = T[s]
    print("  %s named_S %d/%d 门槛 %d -> %s" % (s, d["named_S"], d["n"],
                                                d["thr_named"], "OK" if d["named_S"] >= d["thr_named"] else "FAIL"))
json.dump(T, open(os.path.join(work, "s14_table.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
