# -*- coding: utf-8 -*-
"""M77 PANEL.md edits: numeric/remark updates + verbatim M77 disclosure after M76 disclosure.
All target numbers recomputed from disk (post coverage edit), strict per authoritative [未证] literal caliber.
"""
import csv, os, re, sys, hashlib, math, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

REMARK = ("M77 并表 NAMED_PUSH_AUDIT20 PASS 4 行（S07 006DBE00 + S11 0069EE30/00719E30/0075C7F0，"
          "evidence_path 改指 NAMED_PUSH_AUDIT20/VERDICT.md）；具名通道至此收口（剩余预期 < 3 行）")

# verbatim 4-line disclosure from the task
DISC = [
    "> ⚠️ **M77 披露：006DBE00 的两个边界（未收紧）**",
    "> `a-final4` 审计指出两点，均不影响本轮判 PASS，但引用时须同读：",
    "> 1. `006DBE00` 是 `0x1C` 字节的 HRESULT 归一化包装，**映射近似恒等**，形态贴近「纯转发」；若取「恒等映射即 ③a」的严口径，此行应改判 FAIL。",
    "> 2. `006DBE00` **找不到静态 slot-6 派发点**（无直接调用者、无 `push imm`；沿 Tactical 单例 `[0x887324]` 窗口内无 `call [reg+0x18]`），④ 依赖 ctor 装活表 + `new` 堆实例 + 全局被读 447 次——**弱于另 3 行可见的 `ff 10` 派发**。",
]
assert len(DISC) == 4


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
assert (full, atl_in, atl_out) == (1654, 1648, 6)

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

for s, wp, ws in (("S07", 75, 52), ("S11", 35, 34)):
    print(f"{s} atlas_n={d[s]['atlas_n']} proved={d[s]['proved']} strict={d[s]['strict']} "
          f"pct={pct(d[s]['proved'], d[s]['atlas_n'])} strictpct={pct(d[s]['strict'], d[s]['atlas_n'])}")
    assert d[s]["proved"] == wp and d[s]["strict"] == ws, (s, d[s]["proved"], d[s]["strict"])

tot_proved = sum(c["proved"] for c in d.values())
tot_strict = sum(c["strict"] for c in d.values())
print("TOTAL atlas-in proved=%d strict=%d pct=%s strictpct=%s" %
      (tot_proved, tot_strict, pct(tot_proved, 12916), pct(tot_strict, 12916)))
assert tot_proved == 1648 and tot_strict == 1331, (tot_proved, tot_strict)

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

S07_pc, S07_sc = pct(d["S07"]["proved"], d["S07"]["atlas_n"]), pct(d["S07"]["strict"], d["S07"]["atlas_n"])
S11_pc, S11_sc = pct(d["S11"]["proved"], d["S11"]["atlas_n"]), pct(d["S11"]["strict"], d["S11"]["atlas_n"])
TOT_pc, TOT_sc = pct(tot_proved, 12916), pct(tot_strict, 12916)

M77_TITLE = (
    "# PANEL — R14 coverageM77 并表 4 行（"
    "NAMED_PUSH_AUDIT20 PASS 4 行（S07 006DBE00 + S11 0069EE30/00719E30/0075C7F0），均 atlas 内，"
    "仅改 coverage 第 4/5/6 列、第 1/2/3/7/8 列不动；coverage 18,498 行不变；"
    "全表 [已证] 1,650→1,654、atlas 内 1,644→1,648、atlas 外仍 6；"
    "面板 S07 proved 74→75、strict 51→52，S11 proved 32→35、strict 31→34；"
    "strict 按权威口径 [未证] 字面重算，达标判定不变（严格仍仅 S17，名义仍 S15/S16/S17）；"
    + REMARK + "；不 git commit）；"
)

repls = [
    # 1) title line prepend M77 before M76
    ("# PANEL — R14 coverageM76 并表 7 行（", M77_TITLE + "M76 并表 7 行（"),
    # 2) 全表/atlas cell
    ("| 全表 `[已证]` / atlas 内 `[已证]` | **1,650 / 1,644** | M76 并表",
     "| 全表 `[已证]` / atlas 内 `[已证]` | **1,654 / 1,648** | " + REMARK + "；M76 并表"),
    # 3) S07 main row
    ("| S07 | 804 | 587 | 73.01 | 587 | 73.01 | 64 | 7.96 | 74 | 9.20 | M72 并表",
     f"| S07 | 804 | 587 | 73.01 | 587 | 73.01 | 64 | 7.96 | 75 | {S07_pc} | " + REMARK + "；M72 并表"),
    # 4) S11 main row
    ("| S11 | 368 | 358 | 97.28 | 358 | 97.28 | 29 | 7.88 | 32 | 8.70 | M72 并表",
     f"| S11 | 368 | 358 | 97.28 | 358 | 97.28 | 29 | 7.88 | 35 | {S11_pc} | " + REMARK + "；M72 并表"),
    # 5) TOTAL main row
    ("| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1644** | **12.73** | M76 并表",
     f"| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1648** | **{TOT_pc}** | " + REMARK + "；M76 并表"),
    # 6) S07 strict row
    ("| S07 | 804 | 74 | 9.20 | **51** | **6.34** | 402 | — | — |",
     f"| S07 | 804 | 75 | {S07_pc} | **52** | **{S07_sc}** | 402 | — | — |"),
    # 7) S11 strict row
    ("| S11 | 368 | 32 | 8.70 | **31** | **8.42** | 184 | — | — |",
     f"| S11 | 368 | 35 | {S11_pc} | **34** | **{S11_sc}** | 184 | — | — |"),
    # 8) TOTAL strict row
    ("| **TOTAL** | **12916** | **1644** | **12.73** | **1327** | **10.27** | — | **3/22** | **1/22** |",
     f"| **TOTAL** | **12916** | **1648** | **{TOT_pc}** | **1331** | **{TOT_sc}** | — | **3/22** | **1/22** |"),
]

with open(PANEL, "rb") as f:
    text = f.read().decode("utf-8")

for old, new in repls:
    cnt = text.count(old)
    assert cnt == 1, ("replace count", cnt, old[:90])
    text = text.replace(old, new, 1)
    print("replaced (1x): %r" % old[:64])

# ---------- insert M77 disclosure immediately after M76 disclosure block ----------
plines = text.split("\n")
i76 = next(i for i, l in enumerate(plines) if l.startswith("> ⚠️ **M76 披露："))
assert plines[i76+3].endswith("**"), plines[i76+3][:60]  # 4-line block: i76..i76+3
disc76_block = "\n".join(plines[i76:i76+4])
assert text.count(disc76_block) == 1, "M76 disclosure block not unique"
m77_block = "\n".join(DISC)
text = text.replace(disc76_block, disc76_block + "\n" + m77_block, 1)
print("inserted M77 disclosure after M76 disclosure block (4 lines)")

# ---------- add M77 实算说明 note after M77 disclosure block ----------
M77_NOTE = (
    "> 📌 **M77 并表实算说明**：本表 S07 proved/strict 74→75 / 51→52（75/804=9.33%、52/804=6.47%）、"
    "S11 proved/strict 32→35 / 31→34（35/368=9.51%、34/368=9.24%）、"
    "TOTAL proved/strict 1,644→1,648 / 1,327→1,331（1,648/12,916=12.76%、1,331/12,916=10.31%）均按盘上实算；"
    "本次并入 4 行新语义均不含字面 `[未证]`（核 delta 第 4 列），strict 随 proved 同增（S07 +1、S11 +3、TOTAL +4）。"
    "四行全在 atlas 内，全表 `[已证]` 1,650→1,654、atlas 内 1,644→1,648、atlas 外仍 6。"
    "严格口径仍仅 S17 达标（1/22），名义仍 S15/S16/S17（3/22），**达标判定未翻转**。"
    "strict 用 `strict_panel.py` 第 78 行 `if \"[未证]\" not in sem:` 的带方括号字面口径复算。"
    "`006DBE00` 的两个边界见上方 M77 披露（未收紧）。"
)
assert text.count(m77_block) == 1
text = text.replace(m77_block, m77_block + "\n" + M77_NOTE, 1)
print("added M77 实算说明 note")

with open(PANEL, "wb") as f:
    f.write(text.encode("utf-8"))

new_lines = text.split("\n")
i77 = [i + 1 for i, l in enumerate(new_lines) if l.startswith("> ⚠️ **M77 披露：")]
print("M77 disclosure line (1-based):", i77, "block range:", (i77[0], i77[0] + len(DISC) - 1) if i77 else "NA")
assert len(i77) == 1
print("AFTER bytes:", os.path.getsize(PANEL))
print("AFTER sha256:", hashlib.sha256(open(PANEL, "rb").read()).hexdigest())
