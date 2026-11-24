# -*- coding: utf-8 -*-
"""M72 full verification. Prints PASS lines and writes MERGE_M72/VERIFY.txt."""
import csv, os, sys, math, hashlib
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT  = os.path.join(ROOT, "MERGE_M72", "VERIFY.txt")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
CARD = os.path.join(ROOT, "_cards", "M72-MERGE.md")
FA   = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

A_VERDICT = os.path.join(ROOT, "NAMED_PUSH_AUDIT13", "verdict.tsv")
A_DELTA   = os.path.join(ROOT, "NAMED_PUSH_S07_B1", "delta.tsv")
B_VERDICT = os.path.join(ROOT, "NAMED_PUSH_AUDIT14", "verdict.tsv")
B_DELTA   = os.path.join(ROOT, "NAMED_PUSH_S11_B1", "delta.tsv")
S09_DELTA = os.path.join(ROOT, "NAMED_PUSH_S09_B1", "delta.tsv")

EXPECT_A = ["00421730","004370C0","00491210","005550C0","00555110","00555150","006DBD20"]
EXPECT_B = ["004AF720","004B62C0","004B6470","0054DC60"]

# panel (atlas_n, named_n_S(R14)) per subsystem — from current PANEL main table
PANEL_STAT = {
 "S01":(53,11),"S02":(330,41),"S03":(194,125),"S04":(316,104),"S05":(643,520),
 "S06":(847,388),"S07":(804,587),"S08":(22,20),"S09":(1051,681),"S10":(526,513),
 "S11":(368,358),"S12":(279,204),"S13":(240,216),"S14":(489,330),"S15":(158,144),
 "S16":(90,81),"S17":(102,94),"S18":(659,497),"S19":(355,40),"S20":(410,399),
 "S21":(129,91),"S22":(4851,1759),
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

def verdicts(path):
    rows = read_tsv(path)
    return {ne(r[0]): (r[1], r[2].strip()) for r in rows[1:] if r}

def deltas(path):
    rows = read_tsv(path)
    return {ne(r[0]): (r[1], r[2], r[3], r[4]) for r in rows[1:] if r}  # sub, name, sem, grade

av, bv = verdicts(A_VERDICT), verdicts(B_VERDICT)
ad, bd = deltas(A_DELTA), deltas(B_DELTA)
s09 = deltas(S09_DELTA)
checks = []
def chk(cond, msg):
    assert cond, "FAIL " + msg
    checks.append("PASS " + msg)

chk(len(av) == 7 and len(bv) == 4, "audit verdict rows A=7 B=4")
chk(all(v == ("S07","PASS") for v in av.values()), "AUDIT13 all 7 S07 PASS")
chk(all(v == ("S11","PASS") for v in bv.values()), "AUDIT14 all 4 S11 PASS")
chk(len(ad) == 7 and len(bd) == 4, "delta rows A=7 B=4")
chk(len(s09) == 1, "S09_B1 delta has exactly 1 row")
interA, interB = set(av) & set(ad), set(bv) & set(bd)
chk(len(interA) == 7 and sorted(interA) == sorted(ne(x) for x in EXPECT_A), "A intersection exactly 7 expected")
chk(len(interB) == 4 and sorted(interB) == sorted(ne(x) for x in EXPECT_B), "B intersection exactly 4 expected")
chk(not (interA & interB), "no overlap between groups")
chk(not (set(s09) & (interA | interB)), "S09 row not merged")
chk(not (set(av) - set(ad)) and not (set(ad) - set(av)), "A verdict/delta sets equal")
chk(not (set(bv) - set(bd)) and not (set(bd) - set(bv)), "B verdict/delta sets equal")

# atlas
atlas = set()
with open(FA, encoding="utf-8") as f:
    rd = csv.reader(f, delimiter="\t"); next(rd)
    for r in rd:
        if r and r[0].strip(): atlas.add(r[0].strip().lower())
chk(len(atlas) == 12916, "atlas data rows 12,916")
targets = interA | interB
chk(all(e.lower() in atlas for e in targets), "all 11 target entries atlas-in (lowercase normalized)")

# coverage live
with open(COV, "rb") as f:
    cov_text = f.read().decode("utf-8")
lines = cov_text.split("\n")
data = lines[1:]
chk(len(data) == 18498, "coverage data rows 18,498")
chk(all(len(ln.split("\t")) == 8 for ln in data), "all data rows 8 tab-separated cols")

sem_ev = {}
for e in interA: sem_ev[e] = (ad[e][2], "NAMED_PUSH_AUDIT13/VERDICT.md", ad[e][1])
for e in interB: sem_ev[e] = (bd[e][2], "NAMED_PUSH_AUDIT14/VERDICT.md", bd[e][1])

row_by_entry = {}
for i, ln in enumerate(data):
    c = ln.split("\t")
    if len(c) == 8:
        row_by_entry.setdefault(ne(c[0]), (i+2, c))  # 1-based line no = i+2 (header is line 1)
for e, (sem, ev, name) in sem_ev.items():
    ln, c = row_by_entry[e]
    assert c[3] == sem, ("sem mismatch", e)
chk(all(row_by_entry[e][1][3] == sem_ev[e][0] for e in targets), "11 rows col4 = delta original verbatim")
chk(all(row_by_entry[e][1][4] == "[已证]" for e in targets), "11 rows col5 = [已证]")
chk(all(row_by_entry[e][1][5] == sem_ev[e][1] for e in targets), "11 rows col6 = correct audit VERDICT path")
chk(all(row_by_entry[e][1][2] == sem_ev[e][2] for e in targets), "11 rows col3 = delta name (unchanged)")
chk(all(row_by_entry[e][1][1] in ("S07","S11") for e in targets), "11 rows col2 subsystem intact")
chk(all(row_by_entry[e][1][6] == "1" and row_by_entry[e][1][7] == "0" for e in targets), "11 rows col7/8 intact (1/0)")

# strict literal check: none of 11 new semantics contain bracketed [未证]
chk(all("[未证]" not in sem_ev[e][0] for e in targets), "no new semantics contains literal [未证]")

# recompute counts from live coverage
stat = {}
full = 0
for ln in data:
    c = ln.split("\t")
    if len(c) != 8: continue
    sub, g, e, sem = c[1], c[4], c[0].strip().lower(), c[3]
    d = stat.setdefault(sub, {"proved":0,"strict":0,"all_proved":0,"atlas_n":0})
    if e in atlas:
        d["atlas_n"] += 1
        if g == "[已证]":
            d["proved"] += 1
            if "[未证]" not in sem: d["strict"] += 1
    if g == "[已证]":
        full += 1; d["all_proved"] += 1
atlas_in = sum(d["proved"] for d in stat.values())
atlas_out = full - atlas_in
chk(full == 1613, "full [已证] = 1613")
chk(atlas_in == 1607, "atlas-in [已证] = 1607")
chk(atlas_out == 6, "atlas-out [已证] = 6 (unchanged)")

s07, s11 = stat["S07"], stat["S11"]
chk(s07["proved"] == 74 and s07["strict"] == 51, "S07 proved=74 strict=51")
chk(s11["proved"] == 32 and s11["strict"] == 31, "S11 proved=32 strict=31")
tot_proved = sum(d["proved"] for d in stat.values())
tot_strict = sum(d["strict"] for d in stat.values())
chk(tot_proved == 1607 and tot_strict == 1290, "TOTAL proved=1607 strict=1290")

# S09 row grade unchanged
s09e = ne("004F45B0")
chk(row_by_entry[s09e][1][4] == "[静态推断]", "S09_B1 entry 004F45B0 grade unchanged = [静态推断]")

# 达标 determination (no flip)
nom, strict_pass = [], []
for sub, (an, named) in PANEL_STAT.items():
    p, st = stat[sub]["proved"], stat[sub]["strict"]
    gate = math.ceil(0.5 * an)
    if named >= math.ceil(0.9 * an):
        if p >= gate: nom.append(sub)
        if st >= gate: strict_pass.append(sub)
chk(sorted(nom) == ["S15","S16","S17"], "nominal 达标 = S15/S16/S17 (3/22), no flip")
chk(strict_pass == ["S17"], "strict 达标 = S17 (1/22), no flip")

# PANEL content
with open(PANEL, "rb") as f:
    pt = f.read().decode("utf-8")
req = [
 "# PANEL — R14 coverageM72 并表 11 行（NAMED_PUSH_AUDIT13 PASS 7 行（S07）+ NAMED_PUSH_AUDIT14 PASS 4 行（S11）",
 "| 全表 `[已证]` / atlas 内 `[已证]` | **1,613 / 1,607** | M72 并表",
 "| S07 | 804 | 587 | 73.01 | 587 | 73.01 | 64 | 7.96 | 74 | 9.20 | M72 并表",
 "| S11 | 368 | 358 | 97.28 | 358 | 97.28 | 29 | 7.88 | 32 | 8.70 | M72 并表",
 "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1607** | **12.44** | M72 并表",
 "| S07 | 804 | 74 | 9.20 | **51** | **6.34** | 402 | — | — |",
 "| S11 | 368 | 32 | 8.70 | **31** | **8.42** | 184 | — | — |",
 "| **TOTAL** | **12916** | **1607** | **12.44** | **1290** | **9.99** | — | **3/22** | **1/22** |",
 "M72 并表 NAMED_PUSH_AUDIT13 PASS 7 行（S07）+ NAMED_PUSH_AUDIT14 PASS 4 行（S11），evidence_path 分别改指两审计 VERDICT；S09_B1 的 1 行未审不并",
]
for r in req:
    chk(pt.count(r) >= 1, "PANEL contains: " + r[:46])
old = [
 "| 全表 `[已证]` / atlas 内 `[已证]` | **1,602 / 1,596** | M71 并表",
 "| S07 | 804 | 587 | 73.01 | 587 | 73.01 | 64 | 7.96 | 67 | 8.33 | named",
 "| S11 | 368 | 358 | 97.28 | 358 | 97.28 | 29 | 7.88 | 28 | 7.61 | M34",
 "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1596** | **12.36** | M71",
 "| S07 | 804 | 67 | 8.33 | **44** | **5.47** | 402 | — | — |",
 "| S11 | 368 | 28 | 7.61 | **27** | **7.34** | 184 | — | — |",
 "| **TOTAL** | **12916** | **1596** | **12.36** | **1279** | **9.90** | — | **3/22** | **1/22** |",
]
for o in old:
    chk(pt.count(o) == 0, "PANEL old string gone: " + o[:46])

# verbatim ㉓ record from card
with open(CARD, encoding="utf-8") as f:
    clines = f.read().split("\n")
disc = [l for l in clines if l.strip().startswith("`S07 有 2 行真触发㉓陷阱")]
chk(len(disc) == 1, "card has exactly one ㉓ record line")
verbatim = disc[0].strip().strip("`")
chk(("> 📌 **M72 ㉓ 正向记录**：" + verbatim) in pt, "PANEL ㉓ note verbatim-identical to card")
chk(pt.count("> 📌 **M72 ㉓ 正向记录**：") == 1, "PANEL has exactly one M72 ㉓ note")
chk(pt.count("> 📌 **M72 并表实算说明**：") == 1, "PANEL has exactly one M72 strict note")

# sha of two files
cov_sha = hashlib.sha256(open(COV,"rb").read()).hexdigest()
pan_sha = hashlib.sha256(open(PANEL,"rb").read()).hexdigest()

# ---- write VERIFY.txt ----
pct = lambda a,b: "%.2f" % (a/b*100)
body = []
body.append("M72 VERIFY — 并表 NAMED_PUSH_AUDIT13 PASS 7 行（S07）+ NAMED_PUSH_AUDIT14 PASS 4 行（S11）")
body.append("复算时间：2026-11-20T15:28:15+08:00")
body.append("复算脚本：MERGE_M72\\verify.py；apply_coverage.py / apply_panel.py（含前置断言）")
body.append("")
body.append("="*69)
body.append("一、卡片硬指标（两组并行数必须 7 与 4，不符即停）")
body.append("="*69)
body.append("A 组并行数                    : 7（NAMED_PUSH_AUDIT13 verdict.tsv 7 行 / NAMED_PUSH_S07_B1 delta.tsv 7 行，交集正好 7）")
body.append("B 组并行数                    : 4（NAMED_PUSH_AUDIT14 verdict.tsv 4 行 / NAMED_PUSH_S11_B1 delta.tsv 4 行，交集正好 4）")
body.append("审计 verdict                  : A 组 7/7 全 S07 PASS；B 组 4/4 全 S11 PASS")
body.append("交集                          : A=7、B=4；两组不重叠；verdict 与 delta 两集合各自完全相等")
body.append("atlas 内（entry 小写归一）     : 11/11 全在 atlas 内（function_atlas.tsv 数据行 12,916）")
body.append("不进并表                      : NAMED_PUSH_S09_B1/delta.tsv 的 1 行（004F45B0）未审，不并")
body.append("")
body.append("="*69)
body.append("二、coverage.tsv 行数与列")
body.append("="*69)
body.append("数据行数                      : 18,498（不增不减）")
body.append("总行数（含表头 1 行）          : 18,499")
body.append("列结构                        : 数据行均 8 列、TAB 分隔（表头 1 行逗号）")
body.append("11 行改动                     : 仅第 4/5/6 列")
body.append("  第 4 列 one_line_semantics   ← 对应 delta.tsv 第 4 列原文照抄（逐字节一致）")
body.append("  第 5 列 grade                → [已证]（原均 [静态推断]）")
body.append("  第 6 列 evidence_path        → A 组 NAMED_PUSH_AUDIT13/VERDICT.md；B 组 NAMED_PUSH_AUDIT14/VERDICT.md")
body.append("  第 1/2/3/7/8 列              : 逐字节不动（apply_coverage.py 逐行断言 + 本脚本复核）")
body.append("")
body.append("="*69)
body.append("三、全表 / atlas 内 / atlas 外 [已证]（盘上实算）")
body.append("="*69)
body.append("全表 [已证]                   : %d（改前 1,602 → +11）" % full)
body.append("atlas 内 [已证]               : %d（改前 1,596 → +11）" % atlas_in)
body.append("atlas 外 [已证]               : %d（改前 6 → 不变）" % atlas_out)
body.append("")
body.append("="*69)
body.append("四、S07 / S11 的 atlas 内 proved 与 strict（strict 用带方括号字面 [未证] 口径）")
body.append("="*69)
body.append("S07 proved                    : %d（改前 67 → +7）= %s/804 = %s%%" % (s07["proved"],s07["proved"],pct(s07["proved"],804)))
body.append("S07 strict                    : %d（改前 44 → +7）= %s/804 = %s%%" % (s07["strict"],s07["strict"],pct(s07["strict"],804)))
body.append("S11 proved                    : %d（改前 28 → +4）= %s/368 = %s%%" % (s11["proved"],s11["proved"],pct(s11["proved"],368)))
body.append("S11 strict                    : %d（改前 27 → +4）= %s/368 = %s%%" % (s11["strict"],s11["strict"],pct(s11["strict"],368)))
body.append("  strict 口径                 : `if \"[未证]\" not in sem:` 带方括号字面 [未证]；")
body.append("                                11 行新语义逐行核 delta 第 4 列均不含字面 [未证]，strict 随 proved 同增。")
body.append("TOTAL atlas 内 proved         : %d（1,596 → +11）= %s/12,916 = %s%%" % (tot_proved,tot_proved,pct(tot_proved,12916)))
body.append("TOTAL atlas 内 strict         : %d（1,279 → +11）= %s/12,916 = %s%%" % (tot_strict,tot_strict,pct(tot_strict,12916)))
body.append("")
body.append("="*69)
body.append("五、有无达标翻转（不得改变；若翻转须停下报告）")
body.append("="*69)
body.append("有无达标翻转                  : 无")
body.append("名义达标（named_S(R14)∧proved）：3/22 = S15 / S16 / S17（未变）")
body.append("严格达标（named_S(R14)∧strict）：1/22 = S17（未变）")
body.append("S07 门槛 402（74/51 远低）、S11 门槛 184（32/31 远低），均不参与达标排名。")
body.append("")
body.append("="*69)
body.append("六、S09_B1 那 1 行 grade 未变")
body.append("="*69)
body.append("entry 004F45B0（NAMED_PUSH_S09_B1/delta.tsv 唯一行）")
body.append("  改前 grade                  : [静态推断]")
body.append("  改后 grade                  : [静态推断]（未变；整行不动）")
body.append("")
body.append("="*69)
body.append("七、PANEL ㉓ 正向记录")
body.append("="*69)
body.append("PANEL.md 第 161 行             : > 📌 **M72 ㉓ 正向记录**：" + verbatim)
body.append("逐字节核对                    : 与卡片 M72-MERGE.md 原文完全一致（含 00490406/006DC475、0048E93B/006D1D54）")
body.append("位置                          : 紧接 M72 并表实算说明（第 160 行）之后；M71 披露（第 155–159 行）之后")
body.append("")
body.append("="*69)
body.append("八、strict 口径字面")
body.append("="*69)
body.append("全程使用带方括号字面 [未证]（proved_strict = atlas 内 [已证] 且语义栏不含 [未证]）。")
body.append("")
body.append("="*69)
body.append("九、两文件 sha256（改后）")
body.append("="*69)
body.append("coverage.tsv sha256           : " + cov_sha)
body.append("PANEL.md sha256               : " + pan_sha)
body.append("")
body.append("="*69)
body.append("十、verify.py 全量 PASS 输出")
body.append("="*69)
body.extend(checks)
body.append("OVERALL: ALL PASS (%d checks)" % len(checks))

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(body) + "\n")

for c in checks:
    print(c)
print("OVERALL: ALL PASS (%d checks)" % len(checks))
print("VERIFY.txt written:", OUT)
