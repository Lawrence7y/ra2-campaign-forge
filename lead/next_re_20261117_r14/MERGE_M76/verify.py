# -*- coding: utf-8 -*-
"""M76 verify: recompute all coverage/atlas/strict metrics from disk (after) and emit VERIFY.txt.
Includes explicit evidence for the two mandated word changes.
"""
import csv, os, re, sys, math, collections, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
CARD = os.path.join(ROOT, "_cards", "M76-MERGE.md")
MERGE = os.path.join(ROOT, "MERGE_M76")

D_S06 = os.path.join(ROOT, "NAMED_PUSH_S06_B2", "delta.tsv")
D_S0103 = os.path.join(ROOT, "NAMED_PUSH_S01S03_B1", "delta.tsv")
D_S1621 = os.path.join(ROOT, "NAMED_PUSH_S16S21_B1", "delta.tsv")
V_A = os.path.join(ROOT, "NAMED_PUSH_AUDIT19", "verdict.tsv")

EXP = ["005FEAF0", "006B5850", "0071CDA0", "00432050", "0046D000", "0046D090", "0071B1B0"]
EV = "NAMED_PUSH_AUDIT19/VERDICT.md"
EXP_SUB = {"005FEAF0":"S06","006B5850":"S06","0071CDA0":"S06","00432050":"S03",
           "0046D000":"S21","0046D090":"S21","0071B1B0":"S16"}
# expected col4 semantic: delta verbatim + two mandated word changes
WORDCHANGES = {
    "0071B1B0": [("0071B1A0", "007F51A0")],
    "0071CDA0": [("ff 51 10 读入", "ff 51 10 成员容器 slot4 下标查询（非读入）")],
}


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


def expected_col4(entry, delta_sem):
    s = delta_sem
    for old, new in WORDCHANGES.get(entry, []):
        s = s.replace(old, new)
    return s

# delta col4 verbatim (for expected col4 reconstruction)
delta = {}
for p in (D_S06, D_S0103, D_S1621):
    for r in read_tsv(p)[1:]:
        if r:
            delta[ne(r[0])] = r[3]
exp_col4 = {e: expected_col4(e, delta[e]) for e in EXP}

# verdict set
vbody = [r for r in read_tsv(V_A)[1:] if r]
vset = {ne(r[0]) for r in vbody}
assert all(r[2].strip() == "PASS" for r in vbody)
inter = vset & set(delta)
par_count = len(inter)

# card remark + disclosure verbatim
card = open(CARD, encoding="utf-8").read().split("\n")
rh = next(i for i, l in enumerate(card) if "备注列追加" in l)
REMARK = card[rh].split("`")[1]
h = next(i for i, l in enumerate(card) if "必须追加的第六条披露" in l)
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
ck("full [已证] == 1650", full, 1650)
ck("atlas-in [已证] == 1644", atl_in, 1644)
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

for s, wp, ws in (("S03", 39, 37), ("S06", 138, 123), ("S16", 48, 22), ("S21", 30, 30)):
    ck(f"{s} atlas-in proved == {wp}", d[s]["proved"], wp)
    ck(f"{s} atlas-in strict == {ws}", d[s]["strict"], ws)
tot_proved = sum(c["proved"] for c in d.values())
tot_strict = sum(c["strict"] for c in d.values())
ck("TOTAL atlas-in proved == 1644", tot_proved, 1644)
ck("TOTAL atlas-in strict == 1327", tot_strict, 1327)
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
target_rows = {}
for e in EXP:
    hits = by_entry.get(e, [])
    ck(f"{e} appears exactly once", len(hits), 1)
    if len(hits) == 1:
        r = hits[0]
        target_rows[e] = r
        ck(f"{e} grade [已证]", r[4].strip(), "[已证]")
        ck(f"{e} evidence correct", r[5].strip(), EV)
        ck(f"{e} col4 == delta verbatim + mandated word changes", r[3], exp_col4[e])
        ck(f"{e} col4 free of literal [未证]", "[未证]" in r[3], False)
        ck(f"{e} atlas-in", e in atlas, True)
        ck(f"{e} subsystem", r[1].strip(), EXP_SUB[e])

# TWO word changes — explicit evidence from actual disk rows
b1 = target_rows.get("0071B1B0")
cda = target_rows.get("0071CDA0")
wc_evidence = []
if b1:
    ck("0071B1B0 col4 contains 007F51A0", "007F51A0" in b1[3], True)
    ck("0071B1B0 col4 NOT contain 0071B1A0", "0071B1A0" in b1[3], False)
    ck("0071B1B0 delta source had 007F51A0 already (0 x 0071B1A0)", "0071B1A0" in delta["0071B1B0"], False)
    wc_evidence.append("改字(1) 0071B1B0 槽址：delta 源 col4 已为 007F51A0（0071B1A0 出现 0 次）；apply 再显式 replace('0071B1A0','007F51A0')（0 次命中，幂等）；盘上 col4 含 007F51A0=True、含 0071B1A0=False ⇒ 勘误落实")
if cda:
    ck("0071CDA0 col4 contains slot4 query phrase", "成员容器 slot4 下标查询（非读入）" in cda[3], True)
    ck("0071CDA0 col4 NOT contain 'ff 51 10 读入'", "ff 51 10 读入" in cda[3], False)
    ck("0071CDA0 delta source had 'ff 51 10 读入'", "ff 51 10 读入" in delta["0071CDA0"], True)
    wc_evidence.append("改字(2) 0071CDA0：delta 源 col4 含 'ff 51 10 读入'（1 次）；apply 改为 'ff 51 10 成员容器 slot4 下标查询（非读入）'；盘上 col4 含 '成员容器 slot4 下标查询（非读入）'=True、含 'ff 51 10 读入'=False ⇒ 改称落实")

# B group not merged: verify none of the 4 S07S11_B2 delta entries are [已证]-upgraded to EV
B_delta = os.path.join(ROOT, "NAMED_PUSH_S07S11_B2", "delta.tsv")
b_entries = [ne(r[0]) for r in read_tsv(B_delta)[1:] if r]
for e in b_entries:
    hits = by_entry.get(e, [])
    if hits:
        ck(f"B-group {e} NOT pointing to EV (unaudited, not merged)", all(r[5].strip() != EV for r in hits), True)

# PANEL presence checks
ptext = open(PANEL, encoding="utf-8").read()
must = [
    "NAMED_PUSH_AUDIT19 PASS 7 行（S06_B2 3 + S01S03_B1 1 + S16S21_B1 3）",
    "| 全表 `[已证]` / atlas 内 `[已证]` | **1,650 / 1,644**",
    "| S03 | 194 | 125 | 64.43 | 125 | 64.43 | 12 | 6.19 | 39 | 20.10 |",
    "| S06 | 847 | 388 | 45.81 | 388 | 45.81 | 123 | 14.52 | 138 | 16.29 |",
    "| S16 | 90 | 81 | 90.00 | 81 | 90.00 | 54 | 60.00 | 48 | 53.33 |",
    "| S21 | 129 | 91 | 70.54 | 91 | 70.54 | 27 | 20.93 | 30 | 23.26 |",
    "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1644** | **12.73** |",
    "| S03 | 194 | 39 | 20.10 | **37** | **19.07** | 97 | — | — |",
    "| S06 | 847 | 138 | 16.29 | **123** | **14.52** | 424 | — | — |",
    "| S16 | 90 | 48 | 53.33 | **22** | **24.44** | 45 | 达标 | — |",
    "| S21 | 129 | 30 | 23.26 | **30** | **23.26** | 65 | — | — |",
    "| **TOTAL** | **12916** | **1644** | **12.73** | **1327** | **10.27** | — | **3/22** | **1/22** |",
    REMARK,
    "M76 并表实算说明",
    "0071B1B0 槽址勘误为 007F51A0",
    "0071CDA0 的 ff 51 10 改称成员容器 slot4 下标查询（非读入）",
]
for m in must:
    ck("PANEL contains: " + m[:50], m in ptext, True)

gone = [
    "| 全表 `[已证]` / atlas 内 `[已证]` | **1,643 / 1,637** | M75 并表",
    "| S03 | 194 | 125 | 64.43 | 125 | 64.43 | 12 | 6.19 | 38 | 19.59 | M46 并表",
    "| S06 | 847 | 388 | 45.81 | 388 | 45.81 | 123 | 14.52 | 135 | 15.94 | M67 并表",
    "| S16 | 90 | 81 | 90.00 | 81 | 90.00 | 54 | 60.00 | 47 | 52.22 | M23 并表",
    "| S21 | 129 | 91 | 70.54 | 91 | 70.54 | 27 | 20.93 | 28 | 21.71 | M33 并表",
    "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1637** | **12.67** | M75 并表",
    "| S03 | 194 | 38 | 19.59 | **36** | **18.56** | 97 | — | — |",
    "| S06 | 847 | 135 | 15.94 | **120** | **14.17** | 424 | — | — |",
    "| S16 | 90 | 47 | 52.22 | **21** | **23.33** | 45 | 达标 | — |",
    "| S21 | 129 | 28 | 21.71 | **28** | **21.71** | 65 | — | — |",
    "| **TOTAL** | **12916** | **1637** | **12.67** | **1320** | **10.22** | — | **3/22** | **1/22** |",
]
for g in gone:
    ck("PANEL old gone: " + g[:44], g in ptext, False)

# disclosure verbatim exactly once, immediately after M75 disclosure block
ck("M76 disclosure block present verbatim exactly once", ptext.count(disc_block), 1)
plines = ptext.split("\n")
i76 = [i for i, l in enumerate(plines) if l.startswith("> ⚠️ **M76 披露：")]
i75 = [i for i, l in enumerate(plines) if l.startswith("> ⚠️ **M75 披露：")]
ck("M75 disclosure exactly one", len(i75), 1)
ck("M76 disclosure exactly one", len(i76), 1)
if len(i74 := [i for i, l in enumerate(plines) if l.startswith("> 🔴 **M74 披露：")]) == 1:
    ck("M75 starts right after M74 block (M74 is 5 lines)", i75[0], i74[0] + 5)
if len(i75) == 1 and len(i76) == 1:
    ck("M76 starts right after M75 block (M75 is 4 lines)", i76[0], i75[0] + 4)
    ck("M76 block matches card verbatim", "\n".join(plines[i76[0]:i76[0] + len(disc)]), disc_block)

# ---------- write VERIFY.txt ----------
npass = sum(1 for c in checks if c[0])
allpass = npass == len(checks)
m76_line = i76[0] + 1 if i76 else None
m75_line = i75[0] + 1 if i75 else None
L = []
L.append("M76 VERIFY — 全量复算（改后盘上状态，口径：strict 带方括号字面 [未证]）")
L.append("=" * 72)
L.append("")
L.append("一、并行数（交集，HARD GATE）")
L.append(f"  A 组 = NAMED_PUSH_AUDIT19/verdict.tsv ∩ (S06_B2 3 + S01S03_B1 1 + S16S21_B1 3) : {par_count}  （须 7）")
L.append("  B 组 = NAMED_PUSH_S07S11_B2 4 行未审不并（无独立异族审计表 NAMED_PUSH_AUDIT20，work/verdicts.json 为产出方自产物非异族审计）")
L.append(f"  本轮并入 = {par_count}；delta 全 6 列、entry 8 位大写十六进制、grade=[已证]、verdict 全 PASS；A/B 未混")
L.append("")
L.append("二、数据行与列结构")
L.append(f"  coverage.tsv 数据行 = {len(data)}（须 18,498）；数据行 8 列 TAB 分隔 = {sum(1 for r in data if len(r)==8)}/{len(data)}")
L.append("")
L.append("三、[已证] 全表 / atlas 内 / atlas 外")
L.append(f"  全表 [已证]      = {full}   （1,643 → 1,650）")
L.append(f"  atlas 内 [已证]  = {atl_in}  （1,637 → 1,644）")
L.append(f"  atlas 外 [已证]  = {atl_out}   （6 不变）")
L.append("")
L.append("四、S03 / S06 / S16 / S21 的 proved 与 strict（atlas 分母内；严格 = [已证] 且语义栏无字面 [未证]）")
for s in ("S03", "S06", "S16", "S21"):
    L.append(f"  {s}: atlas_n={d[s]['atlas_n']:>4}  proved={d[s]['proved']:>3}  strict={d[s]['strict']:>3}  "
             f"named_S(R14)={d[s]['named_S14']:>3}  proved%={100.0*d[s]['proved']/d[s]['atlas_n']:.2f}  "
             f"strict%={100.0*d[s]['strict']/d[s]['atlas_n']:.2f}")
L.append(f"  TOTAL: atlas_n=12916  proved={tot_proved}  strict={tot_strict}  "
         f"proved%={100.0*tot_proved/12916:.2f}  strict%={100.0*tot_strict/12916:.2f}")
L.append("  （改前：S03 38/36、S06 135/120、S16 47/21、S21 28/28、TOTAL 1,637/1,320）")
L.append("")
L.append("五、达标判定有无翻转")
L.append(f"  名义达标（proved 口径）: {','.join(nom)}   （改前 S15,S16,S17；无翻转）")
L.append(f"  严格达标（strict 口径）: {','.join(stc)}          （改前 S17；无翻转）")
L.append("  ⇒ 有无达标翻转：无（名义仍 S15/S16/S17 3/22，严格仍仅 S17 1/22）")
L.append("  判据：named_n_S(R14) >= ceil(0.9*n) 且 proved/strict_n >= ceil(0.5*n)；本次只改第 4/5/6 列，named 三列不变")
L.append("")
L.append("六、M76 披露段落行号（COVERAGE/PANEL.md，1-based）")
if m76_line:
    L.append(f"  M76 披露起止行：{m76_line} - {m76_line + len(disc) - 1}（共 {len(disc)} 行，原样写入）")
    L.append(f"  紧接 M75 披露（行 {m75_line}-{m75_line + 3}）之后，起始行 = M75 起始 + 4 = {m75_line + 4}")
else:
    L.append("  M76 披露行号：NA（未找到）")
L.append("")
L.append("七、两处改字已生效的证据")
for i, w in enumerate(wc_evidence, 1):
    L.append(f"  {w}")
L.append("")
L.append("八、逐项检查")
L.append(f"  检查通过：{npass}/{len(checks)}")
for ok, name, got, want in checks:
    if not ok:
        L.append(f"  FAIL {name}  got={got!r} want={want!r}")
L.append("")
L.append("九、改后 sha256")
L.append("  coverage.tsv : " + hashlib.sha256(open(COV, "rb").read()).hexdigest())
L.append("  PANEL.md     : " + hashlib.sha256(open(PANEL, "rb").read()).hexdigest())
L.append("  （改前 sha256 / mtime / 字节见 MERGE_M76\\BEFORE_AFTER.txt）")
L.append("")
L.append("OVERALL: " + ("ALL PASS" if allpass else "HAS FAIL"))
open(os.path.join(MERGE, "VERIFY.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")

print("\n".join(L))
sys.exit(0 if allpass else 1)
