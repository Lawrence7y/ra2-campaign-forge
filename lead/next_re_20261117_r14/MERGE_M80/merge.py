# -*- coding: utf-8 -*-
"""M80 MERGE — name correction on 3 rows (name + append col4 note) and PANEL.md M80 disclosure.

Strict rules:
- coverage.tsv: change col3 (name) old->new for 3 entries; append M80 note to end of col4.
- Do NOT touch col1(subsystem)/col2 existing text/col4 existing text (append only)/col5 grade/col6/col7/col8.
- Data row count must stay 18,498; file stays UTF-8 no BOM, LF only.
- PANEL.md: insert the M80 disclosure block right after the M79 disclosure block, before the M77 anchor.
"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")

# entry -> (old_name, new_name, subsystem)
FIX = {
    "004CC680": ("MapClass::MapClass",              "TrajectoryHelper::IsCliffHit", "S06"),
    "0054E690": ("Kamikaze::Kamikaze",              "KamikazeControl::~Kamikaze",   "S13"),
    "004C6800": ("NetworkEvents::FillEvent_Animation","NetworkEvent::FillEvent_Animation","S18"),
}

def note(old, new):
    return f"；M80 名更正：原记 {old}，据 HYGIENE_R11 与 YRpp 同址声明更正为 {new}（该行 name/地址原可信，仅名不符）"

# ---------------- coverage.tsv ----------------
raw = open(COV, "rb").read()
assert not raw.startswith(b"\xef\xbb\xbf"), "coverage has BOM"
text = raw.decode("utf-8")
assert "\r" not in text, "coverage has CR"
lines = text.split("\n")
trailing = lines[-1] == ""
data = lines[1:-1] if trailing else lines[1:]
assert len(data) == 18498, f"data rows {len(data)}"
header = lines[0]
# header is comma-separated (data rows are TAB-separated) — a long-standing quirk of this file
assert header == "entry,subsystem,name,one_line_semantics,grade,evidence_path,n_sources,conflict", repr(header)

row_idx = {}
for i, ln in enumerate(data):
    e = ln.split("\t", 1)[0]
    row_idx.setdefault(e, []).append(i)

for e, (old, new, sub) in FIX.items():
    assert len(row_idx.get(e, [])) == 1, f"{e} not unique"
    i = row_idx[e][0]
    c = data[i].split("\t")
    assert len(c) == 8, f"{e} not 8 cols"
    assert c[1] == sub, f"{e} subsystem {c[1]} != {sub}"
    assert c[2] == old, f"{e} name {c[2]!r} != old {old!r}"
    assert c[4].strip() == "[已证]", f"{e} grade {c[4]!r}"
    before_cols = list(c)
    # apply edits
    c[2] = new
    c[3] = c[3] + note(old, new)
    # assertions: only col3 changed, col4 appended; cols 0,1,5,6,7 untouched
    assert c[0] == before_cols[0] and c[1] == before_cols[1], f"{e} col0/1 changed"
    assert c[3].startswith(before_cols[3]), f"{e} col4 not pure-append"
    assert c[3][len(before_cols[3]):] == note(old, new), f"{e} col4 appended text mismatch"
    for k in (4, 5, 6, 7):
        assert c[k] == before_cols[k], f"{e} col{k+1} changed"
    data[i] = "\t".join(c)
    print(f"[OK] {e}: name {old!r} -> {new!r}; col4 appended {len(note(old,new))} chars")

new_text = "\n".join([header] + data) + ("\n" if trailing else "")
open(COV, "wb").write(new_text.encode("utf-8"))
print(f"wrote coverage.tsv ({len(new_text.encode('utf-8'))} bytes, trailing={trailing})")

# ---------------- PANEL.md ----------------
M80_DISC = [
    "> ✅ **M80 名更正：3 行的 name 与 YRpp 同址声明不符，已更正（grade 与 named 计数均不变）**",
    "> `HYGIENE_R11` 核查 11 行「全镜像 0 引用」的行，结论是**地址全部可信**（`in_atlas=yes`、`looks_like_func=yes`、`prologue_within_16=none`、`real_func_start` 即 entry 本身），问题在**名字**：",
    "> - `004CC680`：原记 `MapClass::MapClass` → 实为 `TrajectoryHelper::IsCliffHit`（YRpp 同址声明）",
    "> - `0054E690`：原记 `Kamikaze::Kamikaze` → 实为 `KamikazeControl::~Kamikaze`",
    "> - `004C6800`：原记 `NetworkEvents::FillEvent_Animation` → 实为 `NetworkEvent::FillEvent_Animation`（单复数之差）",
    "> ⇒ 「构造函数 0 引用」这个矛盾的解释是**名字错**、不是地址错。这也揭示一类数据质量风险：**错的 name 仍会被 `named_S(R14)` 计为一个名字**。",
    "> 其余 8 行的名字与 YRpp 同址声明一致（均为 `NOVTABLE` 抽象类方法），未改。",
]
praw = open(PANEL, "rb").read()
assert not praw.startswith(b"\xef\xbb\xbf"), "PANEL has BOM"
ptext = praw.decode("utf-8")
assert "\r" not in ptext, "PANEL has CR"
plines = ptext.split("\n")
ptrailing = plines[-1] == ""

i79 = [i for i, l in enumerate(plines) if l.startswith("> ✅ **M79 补记")]
ishi = [i for i, l in enumerate(plines) if l.startswith("> 📌 **M77 并表实算说明**")]
assert len(i79) == 1, f"M79 anchor count {len(i79)}"
assert len(ishi) >= 1, "M77 anchor missing"
assert i79[0] > 0 and ishi[0] > i79[0], "anchor order wrong"
# M79 block is 4 lines starting at i79[0]; insert M80 right after it
insert_at = i79[0] + 4
assert insert_at == ishi[0], f"M80 insert point {insert_at} != M77 anchor {ishi[0]}"
assert all(l.startswith("> ✅ **M80 名更正") or l.startswith("> ") for l in M80_DISC), "M80_DISC format"
assert not any(l.startswith("> ✅ **M80 名更正") for l in plines), "M80 already present"
plines_new = plines[:insert_at] + M80_DISC + plines[insert_at:]
pnew = "\n".join(plines_new)
open(PANEL, "wb").write(pnew.encode("utf-8"))
print(f"wrote PANEL.md: inserted {len(M80_DISC)} M80 lines at 1-based L{insert_at+1}-{insert_at+len(M80_DISC)} (before M77 anchor L{ishi[0]+1})")
print(f"PANEL lines {len(plines)-(1 if ptrailing else 0)} -> {len(plines_new)-(1 if ptrailing else 0)}")
