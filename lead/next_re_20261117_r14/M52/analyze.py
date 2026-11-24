# -*- coding: utf-8 -*-
"""M52: refined named criteria, validate against M47, then compute full stats."""
import re, collections, math

COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATL = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"


def load_cov():
    with open(COV, "r", encoding="utf-8-sig", newline="") as f:
        lines = f.read().split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    hdr = lines[0]
    assert hdr == "entry,subsystem,name,one_line_semantics,grade,evidence_path,n_sources,conflict"
    out = []
    for ln in lines[1:]:
        cols = ln.split("\t")
        assert len(cols) == 8
        out.append(cols)
    return out


def load_atl():
    with open(ATL, "r", encoding="utf-8-sig", newline="") as f:
        lines = f.read().split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    return set(ln.split("\t")[0].strip().upper() for ln in lines[1:])


cov = load_cov()
atl = load_atl()
inatl = [r for r in cov if r[0].upper() in atl]
outatl = [r for r in cov if r[0].upper() not in atl]


def L(n):
    return n != "" and not n.startswith("sub_")


def R14(n):
    return L(n) and not re.search(r"::sub_[0-9A-Fa-f]+$", n)


def STRICT(n):
    return R14(n) and not re.search(r"::v?slot\d+$", n)


M47 = {
    "S01": (53, 11, 11, 9, 6), "S02": (330, 41, 41, 34, 34), "S03": (194, 125, 125, 12, 38),
    "S04": (316, 104, 104, 88, 91), "S05": (643, 521, 520, 157, 165), "S06": (847, 388, 388, 123, 126),
    "S07": (804, 587, 587, 64, 67), "S08": (22, 20, 20, 1, 9), "S09": (1051, 681, 681, 82, 106),
    "S10": (526, 513, 513, 82, 130), "S11": (368, 358, 358, 29, 28), "S12": (279, 204, 204, 54, 55),
    "S13": (240, 216, 216, 108, 89), "S14": (489, 330, 330, 135, 107), "S15": (158, 144, 144, 102, 101),
    "S16": (90, 81, 81, 54, 46), "S17": (102, 94, 94, 58, 54), "S18": (659, 497, 497, 57, 54),
    "S19": (355, 46, 40, 20, 20), "S20": (410, 399, 399, 42, 46), "S21": (129, 91, 91, 27, 28),
}
print("=== validate refined criteria vs M47 ===")
allok = True
for s, m in M47.items():
    rs = [r for r in inatl if r[1].strip() == s]
    v = (len(rs), sum(L(r[2]) for r in rs), sum(R14(r[2]) for r in rs),
         sum(STRICT(r[2]) for r in rs), sum(r[4].strip() == "[已证]" for r in rs))
    ok = v == m
    allok &= ok
    print(f"{s}: {v} | M47 {m} {'OK' if ok else 'DIFF'}")
print("ALL 21 match M47:", allok)

print("\n=== final recompute table ===")
rows = []
for i in range(1, 22):
    s = f"S{i:02d}"
    rs = [r for r in inatl if r[1].strip() == s]
    n = len(rs)
    l = sum(L(r[2]) for r in rs)
    r14 = sum(R14(r[2]) for r in rs)
    st = sum(STRICT(r[2]) for r in rs)
    pv = sum(r[4].strip() == "[已证]" for r in rs)
    t90 = math.ceil(0.9 * n)
    t50 = math.ceil(0.5 * n)
    ok = (r14 >= t90 and pv >= t50)
    rows.append((s, n, l, r14, st, pv, t90, t50, "是" if ok else "否"))
    print(f"| {s} | {n} | {l} | {r14} | {st} | {pv} | {t90} | {t50} | {'是' if ok else '否'} |")
print("达标:", [r[0] for r in rows if r[8] == "是"])

t21 = [sum(r[i] for r in rows) for i in range(1, 6)]
print("21-subsys totals (n,L,R14,STRICT,proved):", t21)
s22 = [r for r in inatl if r[1].strip() == "S22"]
s22t = (len(s22), sum(L(r[2]) for r in s22), sum(R14(r[2]) for r in s22),
        sum(STRICT(r[2]) for r in s22), sum(r[4].strip() == "[已证]" for r in s22))
print("S22 in atlas:", s22t)
print("TOTAL (21+S22):", tuple(t21[i] + s22t[i] for i in range(5)))

print("\n=== key stats ===")
print("cov data rows:", len(cov))
print("atlas data rows (unique upper):", len(atl))
print("cov in atlas:", len(inatl), "out atlas:", len(outatl))
print("grade:", dict(collections.Counter(r[4] for r in cov)))
print("conflict==1:", sum(r[7].strip() == "1" for r in cov))
print("proved all:", sum(r[4].strip() == "[已证]" for r in cov),
      "proved atlas:", sum(r[4].strip() == "[已证]" for r in inatl))
print("S22 all:", sum(r[1].strip() == "S22" for r in cov),
      "S22 out-atlas:", sum(r[1].strip() == "S22" for r in outatl),
      "S22 in-atlas:", len(s22))
