# -*- coding: utf-8 -*-
"""M75 PANEL.md edits: numeric/remark updates + verbatim M75 disclosure after M74 disclosure.
All target numbers recomputed from disk (post coverage edit), strict per authoritative [未证] literal caliber.
"""
import csv, os, re, sys, hashlib, math, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
CARD_M75 = os.path.join(ROOT, "_cards", "M75-MERGE.md")
CARD_M74 = os.path.join(ROOT, "_cards", "M74-MERGE.md")


def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def pct(n, d):
    return "%.2f" % (100.0 * n / d)


# ---------- extract REMARK and M75 disclosure verbatim from card ----------
card = open(CARD_M75, "rb").read().decode("utf-8").split("\n")
rh = next(i for i, l in enumerate(card) if "备注列追加" in l)
parts = card[rh].split("`")
assert len(parts) >= 3, ("remark backticks", repr(card[rh]))
REMARK = parts[1]
assert REMARK.startswith("M75 并表 NAMED_PUSH_AUDIT17 PASS 12 行"), REMARK[:70]
assert REMARK.endswith("本批换 ③ 依据后过审"), REMARK[-40:]
print("REMARK:", REMARK)

h = next(i for i, l in enumerate(card) if "必须追加的第五条披露" in l)
f1 = next(i for i in range(h, len(card)) if card[i].strip() == "```")
f2 = next(i for i in range(f1 + 1, len(card)) if card[i].strip() == "```")
disc = card[f1 + 1:f2]
print("M75 disclosure lines:", len(disc))
assert len(disc) == 4, len(disc)
assert disc[0].startswith("> ⚠️ **M75 披露："), disc[0]
assert disc[-1].endswith("**引用这两行时须同时引用本披露。**"), disc[-1]

# M74 disclosure block verbatim from M74 card (to locate insertion point robustly)
card74 = open(CARD_M74, "rb").read().decode("utf-8").split("\n")
h74 = next(i for i, l in enumerate(card74) if "必须追加的第四条披露" in l)
f174 = next(i for i in range(h74, len(card74)) if card74[i].strip() == "```")
f274 = next(i for i in range(f174 + 1, len(card74)) if card74[i].strip() == "```")
disc74 = card74[f174 + 1:f274]
assert len(disc74) == 5
disc74_block = "\n".join(disc74)

# ---------- recompute from disk (post coverage edit) ----------
atlas = set()
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    rd = csv.reader(f, delimiter="\t"); next(rd)
    for r in rd:
        if r and r[0].strip():
            atlas.add(ne(r[0]))

with open(COV, "rb") as f:
    lines = f.read().decode("utf-8").split("\n")
rows = [ln.split("\t") for ln in lines[1:] if ln]
assert len(rows) == 18498 and all(len(r) == 8 for r in rows)

full = sum(1 for r in rows if r[4].strip() == "[已证]")
atl_in = sum(1 for r in rows if ne(r[0]) in atlas and r[4].strip() == "[已证]")
atl_out = full - atl_in
print("DISK full=%d atlas_in=%d atlas_out=%d" % (full, atl_in, atl_out))
assert (full, atl_in, atl_out) == (1643, 1637, 6)

RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")
RE_SLOT = re.compile(r"::v?slot\d+$")
d = collections.defaultdict(collections.Counter)
for r in rows:
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
        if "[未证]" not in sem:   # authoritative strict_panel.py line 78 literal bracketed caliber
            d[s]["strict"] += 1

for s, wp, ws in (("S18", 66, 56), ("S15", 116, 63), ("S17", 59, 58)):
    print(f"{s} atlas_n={d[s]['atlas_n']} proved={d[s]['proved']} strict={d[s]['strict']} "
          f"pct={pct(d[s]['proved'], d[s]['atlas_n'])} strictpct={pct(d[s]['strict'], d[s]['atlas_n'])}")
    assert d[s]["proved"] == wp and d[s]["strict"] == ws, (s, d[s]["proved"], d[s]["strict"])

tot_proved = sum(c["proved"] for c in d.values())
tot_strict = sum(c["strict"] for c in d.values())
print("TOTAL atlas-in proved=%d strict=%d pct=%s strictpct=%s" %
      (tot_proved, tot_strict, pct(tot_proved, 12916), pct(tot_strict, 12916)))
assert tot_proved == 1637 and tot_strict == 1320

# DoD after
def dod(key):
    out = []
    for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
        a = d[s]["atlas_n"]; tn = math.ceil(0.9*a); tp = math.ceil(0.5*a)
        if d[s]["named_S14"] >= tn and d[s][key] >= tp:
            out.append(s)
    return out
nom, stc = dod("proved"), dod("strict")
print("DoD AFTER nominal=%s strict=%s" % (",".join(nom), ",".join(stc)))
assert ",".join(nom) == "S15,S16,S17" and ",".join(stc) == "S17"

# ---------- PANEL replacements ----------
with open(PANEL, "rb") as f:
    text = f.read().decode("utf-8")

S18_atn, S15_atn, S17_atn = d["S18"]["atlas_n"], d["S15"]["atlas_n"], d["S17"]["atlas_n"]

M75_TITLE = (
    "# PANEL — R14 coverageM75 并表 22 行（"
    "NAMED_PUSH_AUDIT17 PASS 12 行（S18_B5 9 + S17_B1 3）+ NAMED_PUSH_AUDIT18 PASS 10 行（S15_B1），"
    "均 atlas 内，仅改 coverage 第 4/5/6 列、第 1/2/3/7/8 列不动；coverage 18,498 行不变；"
    "全表 [已证] 1,621→1,643、atlas 内 1,615→1,637、atlas 外仍 6；"
    f"面板 S18 proved 57→66、strict 47→56，S15 proved 106→116、strict 53→63，S17 proved 56→59、strict 55→58；"
    "strict 按权威口径 [未证] 字面重算，达标判定不变（严格仍仅 S17，名义仍 S15/S16/S17）；"
    "007B26D0 为 ④ 最弱行（仅构造器安装点、无可证派发），006E3E30/006E57A0 旧 FAIL 换 ③ 依据后过审，均已披露；"
    + REMARK + "；不 git commit）；"
)

repls = [
    # 1) title line prepend M75 before M74
    ("# PANEL — R14 coverageM74 并表 6 行（", M75_TITLE + "M74 并表 6 行（"),
    # 2) 全表/atlas cell
    ("| 全表 `[已证]` / atlas 内 `[已证]` | **1,621 / 1,615** | M74 并表",
     "| 全表 `[已证]` / atlas 内 `[已证]` | **1,643 / 1,637** | " + REMARK + "；M74 并表"),
    # 3) S15 main row 106/67.09 -> 116/73.42
    ("| S15 | 158 | 144 | 91.14 | 144 | 91.14 | 102 | 64.56 | 106 | 67.09 | M21 并表",
     "| S15 | 158 | 144 | 91.14 | 144 | 91.14 | 102 | 64.56 | 116 | 73.42 | " + REMARK + "；M21 并表"),
    # 4) S17 main row 56/54.90 -> 59/57.84
    ("| S17 | 102 | 94 | 92.16 | 94 | 92.16 | 58 | 56.86 | 56 | 54.90 | M19 现场复算",
     "| S17 | 102 | 94 | 92.16 | 94 | 92.16 | 58 | 56.86 | 59 | 57.84 | " + REMARK + "；M19 现场复算"),
    # 5) S18 main row 57/8.65 -> 66/10.02
    ("| S18 | 659 | 497 | 75.42 | 497 | 75.42 | 57 | 8.65 | 57 | 8.65 | M73 并表",
     "| S18 | 659 | 497 | 75.42 | 497 | 75.42 | 57 | 8.65 | 66 | 10.02 | " + REMARK + "；M73 并表"),
    # 6) TOTAL main row 1615/12.50 -> 1637/12.67
    ("| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1615** | **12.50** | M74 并表",
     "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1637** | **12.67** | " + REMARK + "；M74 并表"),
    # 7) S15 strict row
    ("| S15 | 158 | 106 | 67.09 | **53** | **33.54** | 79 | 达标 | — |",
     "| S15 | 158 | 116 | 73.42 | **63** | **39.87** | 79 | 达标 | — |"),
    # 8) S17 strict row
    ("| S17 | 102 | 56 | 54.90 | **55** | **53.92** | 51 | 达标 | **达标** |",
     "| S17 | 102 | 59 | 57.84 | **58** | **56.86** | 51 | 达标 | **达标** |"),
    # 9) S18 strict row
    ("| S18 | 659 | 57 | 8.65 | **47** | **7.13** | 330 | — | — |",
     "| S18 | 659 | 66 | 10.02 | **56** | **8.50** | 330 | — | — |"),
    # 10) TOTAL strict row
    ("| **TOTAL** | **12916** | **1615** | **12.50** | **1298** | **10.05** | — | **3/22** | **1/22** |",
     "| **TOTAL** | **12916** | **1637** | **12.67** | **1320** | **10.22** | — | **3/22** | **1/22** |"),
]

for old, new in repls:
    cnt = text.count(old)
    assert cnt == 1, ("replace count", cnt, old[:90])
    text = text.replace(old, new, 1)
    print("replaced (1x): %r" % old[:64])

# ---------- insert M75 disclosure immediately after M74 disclosure block ----------
cnt = text.count(disc74_block)
assert cnt == 1, ("M74 disclosure block count", cnt)
text = text.replace(disc74_block, disc74_block + "\n" + "\n".join(disc), 1)
print("inserted M75 disclosure after M74 disclosure block")

# ---------- add M75 实算说明 note after M75 disclosure block ----------
M75_NOTE = (
    "> 📌 **M75 并表实算说明**：本表 S18 proved/strict 57→66 / 47→56（66/659=10.02%、56/659=8.50%）、"
    "S15 proved/strict 106→116 / 53→63（116/158=73.42%、63/158=39.87%）、"
    "S17 proved/strict 56→59 / 55→58（59/102=57.84%、58/102=56.86%）、"
    "TOTAL proved/strict 1,615→1,637 / 1,298→1,320（1,637/12,916=12.67%、1,320/12,916=10.22%）均按盘上实算；"
    "本次并入 22 行新语义均不含字面 `[未证]`（核三 delta 第 4 列），strict 随 proved 同增（S18 +9、S15 +10、S17 +3、TOTAL +22）。"
    "严格口径仍仅 S17 达标（1/22），名义仍 S15/S16/S17（3/22），**达标判定未翻转**。"
    "strict 用 `strict_panel.py` 第 78 行 `if \"[未证]\" not in sem:` 的带方括号字面口径复算。"
)
m75_block = "\n".join(disc)
assert text.count(m75_block) == 1
text = text.replace(m75_block, m75_block + "\n" + M75_NOTE, 1)
print("added M75 实算说明 note")

with open(PANEL, "wb") as f:
    f.write(text.encode("utf-8"))

new_lines = text.split("\n")
i75 = [i + 1 for i, l in enumerate(new_lines) if l.startswith("> ⚠️ **M75 披露：")]
i74 = [i + 1 for i, l in enumerate(new_lines) if l.startswith("> 🔴 **M74 披露：")]
print("M74 disclosure line (1-based):", i74)
print("M75 disclosure line (1-based):", i75, "block range:", (i75[0], i75[0] + len(disc) - 1) if i75 else "NA")
assert len(i75) == 1 and len(i74) == 1
print("AFTER bytes:", os.path.getsize(PANEL))
print("AFTER sha256:", hashlib.sha256(open(PANEL, "rb").read()).hexdigest())
