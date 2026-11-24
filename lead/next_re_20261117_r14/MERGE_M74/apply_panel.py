# -*- coding: utf-8 -*-
"""M74 PANEL.md edits: numeric/remark updates + verbatim M74 disclosure after M71 disclosure."""
import os, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
CARD = os.path.join(ROOT, "_cards", "M74-MERGE.md")

# --- extract REMARK verbatim from card (backticked string after '备注列追加：') ---
with open(CARD, "rb") as f:
    card_lines = f.read().decode("utf-8").split("\n")
rh = next(i for i, l in enumerate(card_lines) if "备注列追加" in l)
remark_line = card_lines[rh]
parts = remark_line.split("`")
assert len(parts) >= 3, ("remark backticks", repr(remark_line))
REMARK = parts[1]
print("REMARK extracted:", REMARK[:80], "...")
assert REMARK.startswith("M74 并表 NAMED_PUSH_AUDIT16 PASS 6 行"), REMARK[:60]
assert REMARK.endswith("非「④ 已独立」）"), REMARK[-40:]

# --- extract M74 disclosure block verbatim from card (fenced block under '必须追加的第四条披露') ---
h = next(i for i, l in enumerate(card_lines) if "必须追加的第四条披露" in l)
fence1 = next(i for i in range(h, len(card_lines)) if card_lines[i].strip() == "```")
fence2 = next(i for i in range(fence1 + 1, len(card_lines)) if card_lines[i].strip() == "```")
disc = card_lines[fence1 + 1:fence2]   # verbatim lines
print("extracted disclosure lines:", len(disc))
for i, l in enumerate(disc):
    print(f"  D{i+1}: {l[:90]!r}")
assert len(disc) == 5, len(disc)
assert disc[0].startswith("> 🔴 **M74 披露："), disc[0]
assert disc[-1].endswith("不得零散改判。"), disc[-1]

# --- M74 title (composed following the M72/M73 merge convention) ---
M74_TITLE = (
    "# PANEL — R14 coverageM74 并表 6 行（NAMED_PUSH_AUDIT16 PASS 6 行"
    "（S13 004684E0/00629FD0/0075E0C0/0075E2C0/00772CD0/00772EB0），均 atlas 内，"
    "仅改 coverage 第 4/5/6 列、第 1/2/3/7/8 列不动；coverage 18,498 行不变；"
    "全表 [已证] 1,615→1,621、atlas 内 1,609→1,615、atlas 外仍 6；"
    "面板 S13 proved 100→106、strict 99→105；"
    "strict 按权威口径 [未证] 字面重算，达标判定不变（严格仍仅 S17）；"
    "D-43(A) 与 §12.3 正面冲突列为待裁项 D-47 并披露；"
    + REMARK + "；不 git commit）；"
)

with open(PANEL, "rb") as f:
    text = f.read().decode("utf-8")

repls = [
    # 1) title line prepend M74 before M73
    ("# PANEL — R14 coverageM73 并表 2 行（",
     M74_TITLE + "M73 并表 2 行（"),
    # 2) 全表/atlas cell + remark
    ("| 全表 `[已证]` / atlas 内 `[已证]` | **1,615 / 1,609** | M73 并表",
     "| 全表 `[已证]` / atlas 内 `[已证]` | **1,621 / 1,615** | " + REMARK + "；M73 并表"),
    # 3) S13 main row: proved 100->106, pct 41.67->44.17
    ("| S13 | 240 | 216 | 90.00 | 216 | 90.00 | 108 | 45.00 | 100 | 41.67 | M55 并表",
     "| S13 | 240 | 216 | 90.00 | 216 | 90.00 | 108 | 45.00 | 106 | 44.17 | " + REMARK + "；M55 并表"),
    # 4) TOTAL main row: proved 1609->1615, pct 12.46->12.50
    ("| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1609** | **12.46** | M73 并表",
     "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1615** | **12.50** | " + REMARK + "；M73 并表"),
    # 5) S13 strict row: proved 100->106/44.17, strict 99->105/43.75
    ("| S13 | 240 | 100 | 41.67 | **99** | **41.25** | 120 | — | — |",
     "| S13 | 240 | 106 | 44.17 | **105** | **43.75** | 120 | — | — |"),
    # 6) TOTAL strict row: proved 1609->1615/12.50, strict 1292->1298/10.05
    ("| **TOTAL** | **12916** | **1609** | **12.46** | **1292** | **10.00** | — | **3/22** | **1/22** |",
     "| **TOTAL** | **12916** | **1615** | **12.50** | **1298** | **10.05** | — | **3/22** | **1/22** |"),
]
for old, new in repls:
    cnt = text.count(old)
    assert cnt == 1, (cnt, old[:80])
    text = text.replace(old, new, 1)
    print("replaced (1x): %r" % old[:60])

# --- insert M74 disclosure immediately after M71 disclosure block (last line) ---
m71_last = ("> 另需账：该族 `AddRef`/`Release` 是 `mov eax,1; ret 4` 桩，"
            "**Release 实际不释放**；「失败 Release 新建对象」走的是 vt+0x20"
            "（slot8 删除析构器，`push 1`），不是 Release。")
cnt = text.count(m71_last)
assert cnt == 1, cnt
text = text.replace(m71_last, m71_last + "\n" + "\n".join(disc), 1)
print("inserted M74 disclosure after M71 disclosure last line")

with open(PANEL, "wb") as f:
    f.write(text.encode("utf-8"))

new_lines = text.split("\n")
idx74 = [i + 1 for i, l in enumerate(new_lines) if l.startswith("> 🔴 **M74 披露：")]
print("M74 disclosure line numbers (1-based):", idx74)
assert len(idx74) == 1
print("M74 disclosure block line range:", idx74[0], "-", idx74[0] + len(disc) - 1)
print("AFTER bytes:", os.path.getsize(PANEL))
print("AFTER sha256:", hashlib.sha256(open(PANEL, "rb").read()).hexdigest())
