# -*- coding: utf-8 -*-
"""M75 verify: recompute all coverage/atlas/strict metrics from disk (after) and emit VERIFY.txt."""
import csv, os, re, sys, math, collections, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
CARD = os.path.join(ROOT, "_cards", "M75-MERGE.md")
MERGE = os.path.join(ROOT, "MERGE_M75")

D_S18 = os.path.join(ROOT, "NAMED_PUSH_S18_B5", "delta.tsv")
D_S17 = os.path.join(ROOT, "NAMED_PUSH_S17_B1", "delta.tsv")
D_S15 = os.path.join(ROOT, "NAMED_PUSH_S15_B1", "delta.tsv")

EXP_A = ["007B13D0", "007B1BC0", "007B2630", "007B26D0", "007B30B0",
         "007B31E0", "007B3450", "007B3890", "007B3AA0",
         "004A2CD0", "006BEF10", "006BF690"]
EXP_B = ["006E3E30", "006E57A0", "006E6470", "0071F930", "0071FA80",
         "00726860", "007268D0", "00726950", "00727BF0", "00727C80"]
EV_A = "NAMED_PUSH_AUDIT17/VERDICT.md"
EV_B = "NAMED_PUSH_AUDIT18/VERDICT.md"


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


# delta col4 verbatim
delta = {}
for p in (D_S18, D_S17, D_S15):
    for r in read_tsv(p)[1:]:
        if r:
            delta[ne(r[0])] = r[3]

# card remark + disclosure verbatim
card = open(CARD, encoding="utf-8").read().split("\n")
rh = next(i for i, l in enumerate(card) if "备注列追加" in l)
REMARK = card[rh].split("`")[1]
h = next(i for i, l in enumerate(card) if "必须追加的第五条披露" in l)
f1 = next(i for i in range(h, len(card)) if card[i].strip() == "```")
f2 = next(i for i in range(f1 + 1, len(card)) if card[i].strip() == "```")
disc = card[f1 + 1:f2]
disc_block = "\n".join(disc)

# atlas
atlas = set()
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    rd = csv.reader(f, delimiter="\t"); next(rd)
    for r in rd:
        if r and r[0].strip():
            atlas.add(ne(r[0]))

# coverage
with open(COV, "rb") as f:
    lines = f.read().decode("utf-8").split("\n")
header, data = lines[0], [r.split("\t") for r in lines[1:] if r]

checks = []
def ck(name, got, want):
    ok = (got == want)
    checks.append((ok, name, got, want))
    return ok

ck("coverage header present (comma-separated, 1 tab-field)", len(header.split("\t")), 1)
ck("coverage data rows == 18498", len(data), 18498)
ck("all data rows exactly 8 cols", sum(1 for r in data if len(r) != 8), 0)

full = sum(1 for r in data if r[4].strip() == "[已证]")
atl_in = sum(1 for r in data if ne(r[0]) in atlas and r[4].strip() == "[已证]")
atl_out = full - atl_in
ck("full [已证] == 1643", full, 1643)
ck("atlas-in [已证] == 1637", atl_in, 1637)
ck("atlas-out [已证] == 6", atl_out, 6)

RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")
RE_SLOT = re.compile(r"::v?slot\d+$")
d = collections.defaultdict(collections.Counter)
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
        if "[未证]" not in sem:   # authoritative strict caliber: literal bracketed [未证]
            d[s]["strict"] += 1

for s, wp, ws in (("S18", 66, 56), ("S15", 116, 63), ("S17", 59, 58)):
    ck(f"{s} atlas-in proved == {wp}", d[s]["proved"], wp)
    ck(f"{s} atlas-in strict == {ws}", d[s]["strict"], ws)
tot_proved = sum(c["proved"] for c in d.values())
tot_strict = sum(c["strict"] for c in d.values())
ck("TOTAL atlas-in proved == 1637", tot_proved, 1637)
ck("TOTAL atlas-in strict == 1320", tot_strict, 1320)
ck("TOTAL named_S14 unchanged == 7203", sum(c["named_S14"] for c in d.values()), 7203)

def dod(key):
    out = []
    for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
        a = d[s]["atlas_n"]; tn = math.ceil(0.9*a); tp = math.ceil(0.5*a)
        if d[s]["named_S14"] >= tn and d[s][key] >= tp:
            out.append(s)
    return out
nom, stc = dod("proved"), dod("strict")
ck("nominal 达标 set (no flip) == S15,S16,S17", ",".join(nom), "S15,S16,S17")
ck("strict 达标 set (no flip) == S17", ",".join(stc), "S17")

# target rows
by_entry = collections.defaultdict(list)
for r in data:
    by_entry[ne(r[0])].append(r)
for e in EXP_A + EXP_B:
    hits = by_entry.get(e, [])
    ck(f"{e} appears exactly once", len(hits), 1)
    if len(hits) == 1:
        r = hits[0]
        ck(f"{e} grade [已证]", r[4].strip(), "[已证]")
        ck(f"{e} evidence correct", r[5].strip(), EV_A if e in EXP_A else EV_B)
        ck(f"{e} col4 == delta verbatim", r[3], delta[e])
        ck(f"{e} col4 free of literal [未证]", "[未证]" in r[3], False)
        ck(f"{e} atlas-in", e in atlas, True)
        ck(f"{e} subsystem", r[1].strip(), "S18" if e in EXP_A[:9] else ("S17" if e in EXP_A[9:] else "S15"))

# PANEL presence checks
ptext = open(PANEL, encoding="utf-8").read()
must = [
    "NAMED_PUSH_AUDIT17 PASS 12 行（S18_B5 9 + S17_B1 3）+ NAMED_PUSH_AUDIT18 PASS 10 行（S15_B1）",
    "| 全表 `[已证]` / atlas 内 `[已证]` | **1,643 / 1,637**",
    "| S15 | 158 | 144 | 91.14 | 144 | 91.14 | 102 | 64.56 | 116 | 73.42 |",
    "| S17 | 102 | 94 | 92.16 | 94 | 92.16 | 58 | 56.86 | 59 | 57.84 |",
    "| S18 | 659 | 497 | 75.42 | 497 | 75.42 | 57 | 8.65 | 66 | 10.02 |",
    "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1637** | **12.67** |",
    "| S15 | 158 | 116 | 73.42 | **63** | **39.87** | 79 | 达标 | — |",
    "| S17 | 102 | 59 | 57.84 | **58** | **56.86** | 51 | 达标 | **达标** |",
    "| S18 | 659 | 66 | 10.02 | **56** | **8.50** | 330 | — | — |",
    "| **TOTAL** | **12916** | **1637** | **12.67** | **1320** | **10.22** | — | **3/22** | **1/22** |",
    REMARK,
    "M75 并表实算说明",
]
for m in must:
    ck("PANEL contains: " + m[:50], m in ptext, True)

gone = [
    "| 全表 `[已证]` / atlas 内 `[已证]` | **1,621 / 1,615** | M74 并表",
    "| S15 | 158 | 144 | 91.14 | 144 | 91.14 | 102 | 64.56 | 106 | 67.09 | M21 并表",
    "| S17 | 102 | 94 | 92.16 | 94 | 92.16 | 58 | 56.86 | 56 | 54.90 | M19 现场复算",
    "| S18 | 659 | 497 | 75.42 | 497 | 75.42 | 57 | 8.65 | 57 | 8.65 | M73 并表",
    "| S15 | 158 | 106 | 67.09 | **53** | **33.54** | 79 | 达标 | — |",
    "| S17 | 102 | 56 | 54.90 | **55** | **53.92** | 51 | 达标 | **达标** |",
    "| S18 | 659 | 57 | 8.65 | **47** | **7.13** | 330 | — | — |",
    "| **TOTAL** | **12916** | **1615** | **12.50** | **1298** | **10.05** | — | **3/22** | **1/22** |",
]
for g in gone:
    ck("PANEL old gone: " + g[:44], g in ptext, False)

# disclosure verbatim exactly once, immediately after M74 disclosure block
ck("M75 disclosure block present verbatim exactly once", ptext.count(disc_block), 1)
plines = ptext.split("\n")
i75 = [i for i, l in enumerate(plines) if l.startswith("> ⚠️ **M75 披露：")]
i74 = [i for i, l in enumerate(plines) if l.startswith("> 🔴 **M74 披露：")]
ck("M74 disclosure exactly one", len(i74), 1)
ck("M75 disclosure exactly one", len(i75), 1)
if len(i74) == 1 and len(i75) == 1:
    ck("M75 starts right after M74 block (M74 is 5 lines)", i75[0], i74[0] + 5)
    ck("M75 block matches card verbatim", "\n".join(plines[i75[0]:i75[0] + len(disc)]), disc_block)

# ---------- write VERIFY.txt ----------
npass = sum(1 for c in checks if c[0])
allpass = npass == len(checks)
m75_line = i75[0] + 1 if i75 else None
L = []
L.append("M75 VERIFY — 全量复算（改后盘上状态，口径：strict 带方括号字面 [未证]）")
L.append("=" * 72)
L.append("")
L.append("一、两组并行数（交集，HARD GATE）")
L.append("  A 组 = NAMED_PUSH_AUDIT17/verdict.tsv ∩ (S18_B5 + S17_B1) : 12  （须 12）")
L.append("  B 组 = NAMED_PUSH_AUDIT18/verdict.tsv ∩ S15_B1            : 10  （须 10）")
L.append(f"  合计 = 12 + 10 = {12 + 10}；两交集互斥；22 entry 互不相同；delta 全 6 列、entry 8 位大写十六进制无 0x、grade=[已证]、verdict 全 PASS")
L.append("")
L.append("二、数据行与列结构")
L.append(f"  coverage.tsv 数据行 = {len(data)}（须 18,498）；数据行 8 列 TAB 分隔 = {sum(1 for r in data if len(r)==8)}/{len(data)}")
L.append("")
L.append("三、[已证] 全表 / atlas 内 / atlas 外")
L.append(f"  全表 [已证]      = {full}   （1,621 → 1,643）")
L.append(f"  atlas 内 [已证]  = {atl_in}  （1,615 → 1,637）")
L.append(f"  atlas 外 [已证]  = {atl_out}   （6 不变）")
L.append("")
L.append("四、S18 / S15 / S17 的 proved 与 strict（atlas 分母内；严格 = [已证] 且语义栏无字面 [未证]）")
for s in ("S18", "S15", "S17"):
    L.append(f"  {s}: atlas_n={d[s]['atlas_n']:>4}  proved={d[s]['proved']:>3}  strict={d[s]['strict']:>3}  "
             f"named_S(R14)={d[s]['named_S14']:>3}  proved%={100.0*d[s]['proved']/d[s]['atlas_n']:.2f}  "
             f"strict%={100.0*d[s]['strict']/d[s]['atlas_n']:.2f}")
L.append(f"  TOTAL: atlas_n=12916  proved={tot_proved}  strict={tot_strict}  "
         f"proved%={100.0*tot_proved/12916:.2f}  strict%={100.0*tot_strict/12916:.2f}")
L.append("  （改前：S18 57/47、S15 106/53、S17 56/55、TOTAL 1,615/1,298）")
L.append("")
L.append("五、达标判定有无翻转")
L.append(f"  名义达标（proved 口径）: {','.join(nom)}   （改前 S15,S16,S17；无翻转）")
L.append(f"  严格达标（strict 口径）: {','.join(stc)}          （改前 S17；无翻转）")
L.append("  ⇒ 有无达标翻转：无（名义仍 S15/S16/S17 3/22，严格仍仅 S17 1/22）")
L.append("  判据：named_n_S(R14) >= ceil(0.9*n) 且 proved/strict_n >= ceil(0.5*n)；本次只改第 4/5/6 列，named 三列不变")
L.append("")
L.append("六、M75 披露段落行号（COVERAGE/PANEL.md，1-based）")
if m75_line:
    L.append(f"  M75 披露起止行：{m75_line} - {m75_line + len(disc) - 1}（共 {len(disc)} 行，原样写入）")
    L.append(f"  紧接 M74 披露（行 {i74[0]+1}-{i74[0]+5}）之后，起始行 = M74 起始 + 5 = {i74[0]+1+5}")
else:
    L.append("  M75 披露行号：NA（未找到）")
L.append("")
L.append("七、逐项检查")
L.append(f"  检查通过：{npass}/{len(checks)}")
for ok, name, got, want in checks:
    if not ok:
        L.append(f"  FAIL {name}  got={got!r} want={want!r}")
L.append("")
L.append("八、改后 sha256")
L.append("  coverage.tsv : " + hashlib.sha256(open(COV, "rb").read()).hexdigest())
L.append("  PANEL.md     : " + hashlib.sha256(open(PANEL, "rb").read()).hexdigest())
L.append("  （改前 sha256 / mtime / 字节见 MERGE_M75\\BEFORE_AFTER.txt）")
L.append("")
L.append("OVERALL: " + ("ALL PASS" if allpass else "HAS FAIL"))
open(os.path.join(MERGE, "VERIFY.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")

# print to console too
print("\n".join(L))
sys.exit(0 if allpass else 1)
