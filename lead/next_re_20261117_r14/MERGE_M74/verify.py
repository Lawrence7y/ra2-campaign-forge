# -*- coding: utf-8 -*-
"""M74 verify: recompute all coverage/atlas/strict metrics from disk state (after)."""
import csv, os, re, sys, math, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "NAMED_PUSH_S13_B1", "delta.tsv")
CARD = os.path.join(ROOT, "_cards", "M74-MERGE.md")

EXPECT = ["004684E0", "00629FD0", "0075E0C0", "0075E2C0", "00772CD0", "00772EB0"]
EV = "NAMED_PUSH_AUDIT16/VERDICT.md"


def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def read_tsv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.reader(f, delimiter="\t")]


# delta expected col4 verbatim
drows = read_tsv(DELTA)
delta = {ne(r[0]): r[3] for r in drows[1:] if r}

# card disclosure verbatim
clines = open(CARD, encoding="utf-8").read().split("\n")
h = next(i for i, l in enumerate(clines) if "必须追加的第四条披露" in l)
f1 = next(i for i in range(h, len(clines)) if clines[i].strip() == "```")
f2 = next(i for i in range(f1 + 1, len(clines)) if clines[i].strip() == "```")
disc = clines[f1 + 1:f2]

# atlas
atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    rd = csv.reader(f, delimiter="\t"); next(rd)
    for r in rd:
        if r and r[0].strip():
            atlas.add(ne(r[0]))

rows = read_tsv(COV)
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
ck("full [已证] = 1621", full, 1621)
ck("atlas-in [已证] = 1615", atl_in, 1615)
ck("atlas-out [已证] = 6", atl_out, 6)

# per-subsystem proved/strict/named (authoritative strict_panel.py line 78)
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
        if "[未证]" not in sem:
            d[s]["strict"] += 1

ck("S13 atlas-in proved = 106", d["S13"]["proved"], 106)
ck("S13 atlas-in strict = 105", d["S13"]["strict"], 105)
ck("S13 atlas-in named_S14 unchanged = 216", d["S13"]["named_S14"], 216)
ck("S13 atlas-in named_strict unchanged = 108", d["S13"]["named_strict"], 108)
tot_proved = sum(c["proved"] for c in d.values())
tot_strict = sum(c["strict"] for c in d.values())
ck("TOTAL atlas-in proved = 1615", tot_proved, 1615)
ck("TOTAL atlas-in strict = 1298", tot_strict, 1298)

# flip check (DoD: named_S(R14) >= ceil(0.9n) AND proved >= ceil(0.5n))
nominal, strict_ok = [], []
for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
    a = d[s]["atlas_n"]; tn = math.ceil(0.9*a); tp = math.ceil(0.5*a)
    if d[s]["named_S14"] >= tn and d[s]["proved"] >= tp:
        nominal.append(s)
    if d[s]["named_S14"] >= tn and d[s]["strict"] >= tp:
        strict_ok.append(s)
ck("nominal 达标 set (no flip)", ",".join(nominal), "S15,S16,S17")
ck("strict 达标 set (no flip)", ",".join(strict_ok), "S17")

# target rows
for ent in EXPECT:
    hits = [r for r in data if ne(r[0]) == ent]
    ck(f"{ent} appears exactly once in coverage", len(hits), 1)
    if not hits:
        continue
    r = hits[0]
    ck(f"{ent} after grade [已证]", r[4].strip(), "[已证]")
    ck(f"{ent} after evidence {EV}", r[5].strip(), EV)
    ck(f"{ent} col4 == delta verbatim", r[3], delta[ent])
    ck(f"{ent} subsystem S13", r[1].strip(), "S13")
    ck(f"{ent} atlas-in", ne(r[0]) in atlas, True)
    ck(f"{ent} col4 free of literal [未证]", "[未证]" in r[3], False)

# PANEL presence checks
ptext = open(PANEL, encoding="utf-8").read()
must = [
    "M74 并表 NAMED_PUSH_AUDIT16 PASS 6 行",
    "| 全表 `[已证]` / atlas 内 `[已证]` | **1,621 / 1,615**",
    "| S13 | 240 | 216 | 90.00 | 216 | 90.00 | 108 | 45.00 | 106 | 44.17",
    "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1615** | **12.50**",
    "| S13 | 240 | 106 | 44.17 | **105** | **43.75** | 120 | — | — |",
    "| **TOTAL** | **12916** | **1615** | **12.50** | **1298** | **10.05** | — | **3/22** | **1/22** |",
    "evidence_path 改指 NAMED_PUSH_AUDIT16/VERDICT.md；这 6 行曾被 S13-PUSH 否决",
    "PASS 依据为 D-43(A) 口径 + M69 整批裁定，非「④ 已独立」",
]
for m in must:
    ck("PANEL contains: " + m[:48], m in ptext, True)
gone = [
    "| 全表 `[已证]` / atlas 内 `[已证]` | **1,615 / 1,609**",
    "| S13 | 240 | 216 | 90.00 | 216 | 90.00 | 108 | 45.00 | 100 | 41.67",
    "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1609** | **12.46**",
    "| S13 | 240 | 100 | 41.67 | **99** | **41.25** | 120 | — | — |",
    "| **TOTAL** | **12916** | **1609** | **12.46** | **1292** | **10.00** | — | **3/22** | **1/22** |",
]
# NOTE: old TOTAL strict string also appears in stale line-206 table; scope gone checks to exact full strings only.
for g in gone:
    ck("PANEL old gone: " + g[:48], g in ptext, False)

# disclosure verbatim present exactly once and right after M71 disclosure
disc_block = "\n".join(disc)
ck("M74 disclosure block present verbatim exactly once", ptext.count(disc_block), 1)
plines = ptext.split("\n")
i71 = [i for i, l in enumerate(plines) if l.startswith("> ⚠️ **M71 披露：")]
i74 = [i for i, l in enumerate(plines) if l.startswith("> 🔴 **M74 披露：")]
ck("M71 disclosure exactly one", len(i71), 1)
ck("M74 disclosure exactly one", len(i74), 1)
if len(i71) == 1 and len(i74) == 1:
    # M71 block is 5 lines (155-159); M74 must start immediately after its last line
    m71_last = "> 另需账：该族 `AddRef`/`Release` 是 `mov eax,1; ret 4` 桩，**Release 实际不释放**；「失败 Release 新建对象」走的是 vt+0x20（slot8 删除析构器，`push 1`），不是 Release。"
    ck("M74 immediately after M71 (no gap)", plines[i71[0] + 4], m71_last)
    ck("M74 starts right after M71 last line", i74[0], i71[0] + 5)
    ck("M74 block matches card verbatim", "\n".join(plines[i74[0]:i74[0] + len(disc)]), disc_block)

npass = sum(1 for c in checks if c[0])
for ok, name, got, want in checks:
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  got={got!r} want={want!r}"))
print(f"OVERALL: {'ALL PASS' if npass == len(checks) else 'HAS FAIL'} ({npass}/{len(checks)} checks)")
print(f"SUMMARY full={full} atlas_in={atl_in} atlas_out={atl_out} "
      f"S13_proved={d['S13']['proved']} S13_strict={d['S13']['strict']} "
      f"TOTAL_proved={tot_proved} TOTAL_strict={tot_strict} "
      f"nominal={'|'.join(nominal)} strict={'|'.join(strict_ok)} "
      f"M74_disc_line={i74[0]+1 if i74 else 'NA'}")
sys.exit(0 if npass == len(checks) else 1)
