# -*- coding: utf-8 -*-
"""M73 复核：从盘上现态重算 coverage / atlas / strict 全部指标。
用法: python verify.py before|after
"""
import csv, os, re, sys, math, json, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")

TARGETS = {"007B10C0": "S18", "004F45B0": "S09"}


def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def load_atlas():
    s = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                s.add(ne(p[0]))
    return s


def load_cov():
    with open(COV, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f, delimiter="\t"))


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "after"
    atlas = load_atlas()
    rows = load_cov()
    header, data = rows[0], [r for r in rows[1:] if len(r) >= 8]

    checks = []
    def ck(name, got, want):
        ok = (got == want)
        checks.append((ok, name, got, want))
        return ok

    ck("coverage header present (comma-separated, 1 tab-field)", len(header), 1)
    ck("coverage data rows 18,498", len(data), 18498)
    ck("all data rows exactly 8 cols", sum(1 for r in data if len(r) != 8), 0)

    full = sum(1 for r in data if r[4].strip() == "[已证]")
    atl_in = sum(1 for r in data if ne(r[0]) in atlas and r[4].strip() == "[已证]")
    atl_out = full - atl_in
    ck("full [已证]", full, 1613 if phase == "before" else 1615)
    ck("atlas-in [已证]", atl_in, 1607 if phase == "before" else 1609)
    ck("atlas-out [已证]", atl_out, 6)

    # per-subsystem proved / strict / named (authoritative strict_panel.py line 78)
    d = collections.defaultdict(collections.Counter)
    RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")
    RE_SLOT = re.compile(r"::v?slot\d+$")
    for r in data:
        e = ne(r[0]); s = r[1].strip()
        if e not in atlas:
            continue
        name, sem, grade = r[2].strip(), r[3], r[4].strip()
        d[s]["atlas_n"] += 1
        if name and not name.startswith("sub_"):
            d[s]["named_L"] += 1
            if not RE_CSUB.search(name):
                d[s]["named_S14"] += 1
                if not RE_SLOT.search(name):
                    d[s]["named_strict"] += 1
        if grade == "[已证]":
            d[s]["proved"] += 1
            if "[未证]" not in sem:   # strict_panel.py:78
                d[s]["strict"] += 1

    want_proved = {"S18": 56, "S09": 114} if phase == "before" else {"S18": 57, "S09": 115}
    want_strict = {"S18": 46, "S09": 97} if phase == "before" else {"S18": 47, "S09": 98}
    for s in ("S18", "S09"):
        ck(f"{s} atlas-in proved", d[s]["proved"], want_proved[s])
        ck(f"{s} atlas-in strict", d[s]["strict"], want_strict[s])
    tot_proved = sum(c["proved"] for c in d.values())
    tot_strict = sum(c["strict"] for c in d.values())
    ck("TOTAL atlas-in proved", tot_proved, 1607 if phase == "before" else 1609)
    ck("TOTAL atlas-in strict", tot_strict, 1290 if phase == "before" else 1292)

    # flip check (DoD: named_S14 >= ceil(0.9n) AND proved >= ceil(0.5n); strict uses strict)
    nominal, strict_ok = [], []
    for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
        a = d[s]["atlas_n"]; tn = math.ceil(0.9*a); tp = math.ceil(0.5*a)
        if d[s]["named_S14"] >= tn and d[s]["proved"] >= tp:
            nominal.append(s)
        if d[s]["named_S14"] >= tn and d[s]["strict"] >= tp:
            strict_ok.append(s)
    ck("nominal 达标 set", ",".join(nominal), "S15,S16,S17")
    ck("strict 达标 set", ",".join(strict_ok), "S17")
    for s in ("S18", "S09"):
        a = d[s]["atlas_n"]
        print(f"INFO {s}: atlas_n={a} named_S14={d[s]['named_S14']} thr_named={math.ceil(0.9*a)} "
              f"proved_thr={math.ceil(0.5*a)} proved={d[s]['proved']} strict={d[s]['strict']}")

    # target rows
    for ent in TARGETS:
        hits = [r for r in data if ne(r[0]) == ent]
        ck(f"{ent} appears exactly once in coverage", len(hits), 1)
        if not hits:
            continue
        r = hits[0]
        print(f"INFO {ent} row: subsystem={r[1]} name={r[2]}")
        print(f"      col4={r[3]}")
        print(f"      col5={r[4]}  col6={r[5]}  col7={r[6]} col8={r[7]}")
        print(f"      atlas-in={ne(r[0]) in atlas}  strict-literal-[未证]={'[未证]' in r[3]}")
        if phase == "before":
            ck(f"{ent} before grade [静态推断]", r[4].strip(), "[静态推断]")
        else:
            ck(f"{ent} after grade [已证]", r[4].strip(), "[已证]")
            ck(f"{ent} after evidence NAMED_PUSH_AUDIT15/VERDICT.md", r[5].strip(), "NAMED_PUSH_AUDIT15/VERDICT.md")

    # PANEL presence checks (after only)
    if phase == "after":
        ptext = open(PANEL, encoding="utf-8").read()
        must = [
            "M73 并表 NAMED_PUSH_AUDIT15 PASS 2 行",
            "| 全表 `[已证]` / atlas 内 `[已证]` | **1,615 / 1,609**",
            "| S18 | 659 | 497 | 75.42 | 497 | 75.42 | 57 | 8.65 | 57 | 8.65",
            "| S09 | 1051 | 681 | 64.80 | 681 | 64.80 | 82 | 7.80 | 115 | 10.94",
            "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1609**",
            "| S18 | 659 | 57 | 8.65 | **47** | **7.13** | 330",
            "| S09 | 1051 | 115 | 10.94 | **98** | **9.32** | 526",
            "| **TOTAL** | **12916** | **1609** | **12.46** | **1292** | **10.00** | — | **3/22** | **1/22**",
        ]
        for m in must:
            ck("PANEL contains: " + m[:48], m in ptext, True)
        gone = [
            "| 全表 `[已证]` / atlas 内 `[已证]` | **1,613 / 1,607**",
            "| S18 | 659 | 497 | 75.42 | 497 | 75.42 | 57 | 8.65 | 56 | 8.50",
            "| S09 | 1051 | 681 | 64.80 | 681 | 64.80 | 82 | 7.80 | 114 | 10.85",
            "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1607**",
            "| S18 | 659 | 56 | 8.50 | **46** | **6.98** | 330",
            "| S09 | 1051 | 114 | 10.85 | **97** | **9.23** | 526",
            "| **TOTAL** | **12916** | **1607** | **12.44** | **1290** | **9.99** | — | **3/22** | **1/22**",
        ]
        for g in gone:
            ck("PANEL old gone: " + g[:48], g in ptext, False)

    npass = sum(1 for c in checks if c[0])
    for ok, name, got, want in checks:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  got={got!r} want={want!r}"))
    print(f"OVERALL: {'ALL PASS' if npass==len(checks) else 'HAS FAIL'} ({npass}/{len(checks)} checks)")
    print(f"SUMMARY phase={phase} full={full} atlas_in={atl_in} atlas_out={atl_out} "
          f"S18_proved={d['S18']['proved']} S09_proved={d['S09']['proved']} "
          f"nominal={'|'.join(nominal)} strict={'|'.join(strict_ok)}")
    sys.exit(0 if npass == len(checks) else 1)


main()
