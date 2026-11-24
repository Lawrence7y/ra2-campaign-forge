# -*- coding: utf-8 -*-
"""M76 PANEL.md edits: numeric/remark updates + verbatim M76 disclosure after M75 disclosure.
All target numbers recomputed from disk (post coverage edit), strict per authoritative [未证] literal caliber.
"""
import csv, os, re, sys, hashlib, math, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
CARD_M76 = os.path.join(ROOT, "_cards", "M76-MERGE.md")
CARD_M75 = os.path.join(ROOT, "_cards", "M75-MERGE.md")


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


# ---------- extract REMARK + M76 disclosure verbatim from card ----------
card = open(CARD_M76, "rb").read().decode("utf-8").split("\n")
rh = next(i for i, l in enumerate(card) if "备注列追加" in l)
parts = card[rh].split("`")
assert len(parts) >= 3, ("remark backticks", repr(card[rh]))
REMARK = parts[1]
assert REMARK.startswith("M76 并表 NAMED_PUSH_AUDIT19 PASS 7 行"), REMARK[:80]
assert REMARK.endswith("NAMED_PUSH_S07S11_B2 的 4 行未审不并"), REMARK[-50:]
print("REMARK:", REMARK)

h = next(i for i, l in enumerate(card) if "必须追加的第六条披露" in l)
f1 = next(i for i in range(h, len(card)) if card[i].strip() == "```")
f2 = next(i for i in range(f1 + 1, len(card)) if card[i].strip() == "```")
disc = card[f1 + 1:f2]
print("M76 disclosure lines:", len(disc))
assert len(disc) == 4, len(disc)
assert disc[0].startswith("> ⚠️ **M76 披露："), disc[0]
assert disc[-1].endswith("**"), disc[-1]

# M75 disclosure block verbatim from M75 card (locate insertion point robustly)
card75 = open(CARD_M75, "rb").read().decode("utf-8").split("\n")
h75 = next(i for i, l in enumerate(card75) if "必须追加的第五条披露" in l)
f175 = next(i for i in range(h75, len(card75)) if card75[i].strip() == "```")
f275 = next(i for i in range(f175 + 1, len(card75)) if card75[i].strip() == "```")
disc75 = card75[f175 + 1:f275]
assert len(disc75) == 4
disc75_block = "\n".join(disc75)

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
assert (full, atl_in, atl_out) == (1650, 1644, 6)

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

# expected post-merge (before=38/135/47/28 proved, 36/120/21/28 strict; adds 1/3/1/2)
for s, wp, ws in (("S03", 39, 37), ("S06", 138, 123), ("S16", 48, 22), ("S21", 30, 30)):
    print(f"{s} atlas_n={d[s]['atlas_n']} proved={d[s]['proved']} strict={d[s]['strict']} "
          f"pct={pct(d[s]['proved'], d[s]['atlas_n'])} strictpct={pct(d[s]['strict'], d[s]['atlas_n'])}")
    assert d[s]["proved"] == wp and d[s]["strict"] == ws, (s, d[s]["proved"], d[s]["strict"])

tot_proved = sum(c["proved"] for c in d.values())
tot_strict = sum(c["strict"] for c in d.values())
print("TOTAL atlas-in proved=%d strict=%d pct=%s strictpct=%s" %
      (tot_proved, tot_strict, pct(tot_proved, 12916), pct(tot_strict, 12916)))
assert tot_proved == 1644 and tot_strict == 1327, (tot_proved, tot_strict)

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

# ---------- build numeric strings from disk ----------
def main_row(sub, a, nl, np_, ns14, ns14p, strictc, strictp, provedc, provedp, oldtail):
    # only proved count/% change; rest stays; REMARK prepended to remark column
    return (
        f"| {sub} | {a} | {nl} | {np_} | {ns14} | {ns14p} | {strictc} | {strictp} | "
        f"{provedc} | {provedp} | "
    )

S03_pc, S03_sc = pct(d["S03"]["proved"], d["S03"]["atlas_n"]), pct(d["S03"]["strict"], d["S03"]["atlas_n"])
S06_pc, S06_sc = pct(d["S06"]["proved"], d["S06"]["atlas_n"]), pct(d["S06"]["strict"], d["S06"]["atlas_n"])
S16_pc, S16_sc = pct(d["S16"]["proved"], d["S16"]["atlas_n"]), pct(d["S16"]["strict"], d["S16"]["atlas_n"])
S21_pc, S21_sc = pct(d["S21"]["proved"], d["S21"]["atlas_n"]), pct(d["S21"]["strict"], d["S21"]["atlas_n"])
TOT_pc, TOT_sc = pct(tot_proved, 12916), pct(tot_strict, 12916)

M76_TITLE = (
    "# PANEL — R14 coverageM76 并表 7 行（"
    "NAMED_PUSH_AUDIT19 PASS 7 行（S06_B2 3 + S01S03_B1 1 + S16S21_B1 3），均 atlas 内，"
    "仅改 coverage 第 4/5/6 列、第 1/2/3/7/8 列不动；coverage 18,498 行不变；"
    "全表 [已证] 1,643→1,650、atlas 内 1,637→1,644、atlas 外仍 6；"
    "面板 S03 proved 38→39、strict 36→37，S06 proved 135→138、strict 120→123，"
    "S16 proved 47→48、strict 21→22，S21 proved 28→30、strict 28→30；"
    "strict 按权威口径 [未证] 字面重算，达标判定不变（严格仍仅 S17，名义仍 S15/S16/S17）；"
    "0071B1B0 槽址按审计勘误改 007F51A0、0071CDA0 的 ff 51 10 改称成员容器 slot4 下标查询（非读入）"
    "均已在第 4 列落实；NAMED_PUSH_S07S11_B2 的 4 行未审不并；"
    + REMARK + "；不 git commit）；"
)

repls = [
    # 1) title line prepend M76 before M75
    ("# PANEL — R14 coverageM75 并表 22 行（", M76_TITLE + "M75 并表 22 行（"),
    # 2) 全表/atlas cell
    ("| 全表 `[已证]` / atlas 内 `[已证]` | **1,643 / 1,637** | M75 并表",
     "| 全表 `[已证]` / atlas 内 `[已证]` | **1,650 / 1,644** | " + REMARK + "；M75 并表"),
    # 3) S03 main row
    ("| S03 | 194 | 125 | 64.43 | 125 | 64.43 | 12 | 6.19 | 38 | 19.59 | M46 并表",
     f"| S03 | 194 | 125 | 64.43 | 125 | 64.43 | 12 | 6.19 | 39 | {S03_pc} | " + REMARK + "；M46 并表"),
    # 4) S06 main row
    ("| S06 | 847 | 388 | 45.81 | 388 | 45.81 | 123 | 14.52 | 135 | 15.94 | M67 并表",
     f"| S06 | 847 | 388 | 45.81 | 388 | 45.81 | 123 | 14.52 | 138 | {S06_pc} | " + REMARK + "；M67 并表"),
    # 5) S16 main row
    ("| S16 | 90 | 81 | 90.00 | 81 | 90.00 | 54 | 60.00 | 47 | 52.22 | M23 并表",
     f"| S16 | 90 | 81 | 90.00 | 81 | 90.00 | 54 | 60.00 | 48 | {S16_pc} | " + REMARK + "；M23 并表"),
    # 6) S21 main row
    ("| S21 | 129 | 91 | 70.54 | 91 | 70.54 | 27 | 20.93 | 28 | 21.71 | M33 并表",
     f"| S21 | 129 | 91 | 70.54 | 91 | 70.54 | 27 | 20.93 | 30 | {S21_pc} | " + REMARK + "；M33 并表"),
    # 7) TOTAL main row
    ("| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1637** | **12.67** | M75 并表",
     f"| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1644** | **{TOT_pc}** | " + REMARK + "；M75 并表"),
    # 8) S03 strict row
    ("| S03 | 194 | 38 | 19.59 | **36** | **18.56** | 97 | — | — |",
     f"| S03 | 194 | 39 | {S03_pc} | **37** | **{S03_sc}** | 97 | — | — |"),
    # 9) S06 strict row
    ("| S06 | 847 | 135 | 15.94 | **120** | **14.17** | 424 | — | — |",
     f"| S06 | 847 | 138 | {S06_pc} | **123** | **{S06_sc}** | 424 | — | — |"),
    # 10) S16 strict row
    ("| S16 | 90 | 47 | 52.22 | **21** | **23.33** | 45 | 达标 | — |",
     f"| S16 | 90 | 48 | {S16_pc} | **22** | **{S16_sc}** | 45 | 达标 | — |"),
    # 11) S21 strict row
    ("| S21 | 129 | 28 | 21.71 | **28** | **21.71** | 65 | — | — |",
     f"| S21 | 129 | 30 | {S21_pc} | **30** | **{S21_sc}** | 65 | — | — |"),
    # 12) TOTAL strict row
    ("| **TOTAL** | **12916** | **1637** | **12.67** | **1320** | **10.22** | — | **3/22** | **1/22** |",
     f"| **TOTAL** | **12916** | **1644** | **{TOT_pc}** | **1327** | **{TOT_sc}** | — | **3/22** | **1/22** |"),
]

with open(PANEL, "rb") as f:
    text = f.read().decode("utf-8")

for old, new in repls:
    cnt = text.count(old)
    assert cnt == 1, ("replace count", cnt, old[:90])
    text = text.replace(old, new, 1)
    print("replaced (1x): %r" % old[:64])

# ---------- insert M76 disclosure immediately after M75 disclosure block ----------
cnt = text.count(disc75_block)
assert cnt == 1, ("M75 disclosure block count", cnt)
text = text.replace(disc75_block, disc75_block + "\n" + "\n".join(disc), 1)
print("inserted M76 disclosure after M75 disclosure block")

# ---------- add M76 实算说明 note after M76 disclosure block ----------
M76_NOTE = (
    "> 📌 **M76 并表实算说明**：本表 S03 proved/strict 38→39 / 36→37（39/194=20.10%、37/194=19.07%）、"
    "S06 proved/strict 135→138 / 120→123（138/847=16.29%、123/847=14.52%）、"
    "S16 proved/strict 47→48 / 21→22（48/90=53.33%、22/90=24.44%）、"
    "S21 proved/strict 28→30 / 28→30（30/129=23.26%、30/129=23.26%）、"
    "TOTAL proved/strict 1,637→1,644 / 1,320→1,327（1,644/12,916=12.73%、1,327/12,916=10.27%）均按盘上实算；"
    "本次并入 7 行新语义均不含字面 `[未证]`（核三 delta 第 4 列），strict 随 proved 同增（S03 +1、S06 +3、S16 +1、S21 +2、TOTAL +7）。"
    "两处改字已落实：0071B1B0 槽址勘误为 007F51A0、0071CDA0 的 ff 51 10 改称成员容器 slot4 下标查询（非读入）；"
    "NAMED_PUSH_S07S11_B2 的 4 行未审不并。"
    "严格口径仍仅 S17 达标（1/22），名义仍 S15/S16/S17（3/22），**达标判定未翻转**。"
    "strict 用 `strict_panel.py` 第 78 行 `if \"[未证]\" not in sem:` 的带方括号字面口径复算。"
)
m76_block = "\n".join(disc)
assert text.count(m76_block) == 1
text = text.replace(m76_block, m76_block + "\n" + M76_NOTE, 1)
print("added M76 实算说明 note")

with open(PANEL, "wb") as f:
    f.write(text.encode("utf-8"))

new_lines = text.split("\n")
i76 = [i + 1 for i, l in enumerate(new_lines) if l.startswith("> ⚠️ **M76 披露：")]
i75 = [i + 1 for i, l in enumerate(new_lines) if l.startswith("> ⚠️ **M75 披露：")]
print("M75 disclosure line (1-based):", i75)
print("M76 disclosure line (1-based):", i76, "block range:", (i76[0], i76[0] + len(disc) - 1) if i76 else "NA")
assert len(i76) == 1 and len(i75) == 1
print("AFTER bytes:", os.path.getsize(PANEL))
print("AFTER sha256:", hashlib.sha256(open(PANEL, "rb").read()).hexdigest())
