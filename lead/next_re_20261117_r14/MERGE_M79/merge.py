# -*- coding: utf-8 -*-
"""M79 MERGE - document upgrade only: col4 & col6 for 91 rows; append M79 disclosure to PANEL.md."""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R4_FILL_91_R3", "fill_delta.tsv")

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

# ---------------- delta ----------------
draw = open(DELTA, "rb").read()
dtext = draw.decode("utf-8-sig").replace("\r\n", "\n")
dlines = dtext.split("\n")
dtrailing = dlines[-1] == ""
ddata = dlines[1:-1] if dtrailing else dlines[1:]
drows = [ln.split("\t") for ln in ddata]
assert len(drows) == 91, f"delta rows {len(drows)} != 91"
assert all(len(r) == 6 for r in drows)
assert all(r[4].strip() == "[已证]" for r in drows)
dmap = {}
for r in drows:
    e = ne(r[0])
    assert e not in dmap, f"dup delta entry {e}"
    dmap[e] = r
print("delta loaded:", len(dmap), "entries, all [已证], 6 cols")

# ---------------- coverage ----------------
raw = open(COV, "rb").read()
text = raw.decode("utf-8")
assert not raw.startswith(b"\xef\xbb\xbf")
assert "\r" not in text
lines = text.split("\n")
trailing = lines[-1] == ""
header = lines[0]
data = lines[1:-1] if trailing else lines[1:]
assert len(data) == 18498, f"cov data rows {len(data)} != 18498"
assert all(len(ln.split("\t")) == 8 for ln in data)

changed = []
new_data = []
for ln in data:
    cols = ln.split("\t")
    e = ne(cols[0])
    if e in dmap:
        d = dmap[e]
        before = list(cols)
        # only col4 (index 3) and col6 (index 5) change
        cols[3] = d[3]
        cols[5] = d[5]
        # assert cols 1/2/3/5/7/8 (idx 0,1,2,4,6,7) byte-identical
        for idx in (0, 1, 2, 4, 6, 7):
            assert before[idx] == cols[idx], f"{e} col{idx+1} changed unexpectedly"
        assert cols[4].strip() == "[已证]"
        assert "④" in cols[3]
        changed.append(e)
    new_data.append("\t".join(cols))

assert len(changed) == 91, f"changed {len(changed)} != 91"
assert set(changed) == set(dmap)
new_text = "\n".join([header] + new_data) + ("\n" if trailing else "")
new_raw = new_text.encode("utf-8")
assert len(new_raw) > 0
open(COV, "wb").write(new_raw)
print("coverage.tsv written: changed", len(changed), "rows (col4+col6 only); bytes", len(new_raw))

# ---------------- PANEL.md ----------------
praw = open(PANEL, "rb").read()
ptext = praw.decode("utf-8")
assert not praw.startswith(b"\xef\xbb\xbf")
assert "\r" not in ptext
plines = ptext.split("\n")
pend = plines[-1] == ""  # ends with newline

M78_START = "> 🔴 **M78 披露"
M77_SHI = "> 📌 **M77 并表实算说明**"
i78 = [i for i, l in enumerate(plines) if l.startswith(M78_START)]
ishi = [i for i, l in enumerate(plines) if l.startswith(M77_SHI)]
assert len(i78) == 1, f"M78 disclosure markers: {len(i78)}"
assert len(ishi) >= 1, "no M77 并表实算说明 anchor"
i78, ishi = i78[0], ishi[0]
assert ishi > i78, "anchor order wrong"
# M78 block runs from i78 up to (not incl) ishi; all its lines are blockquote lines
for i in range(i78, ishi):
    assert plines[i].startswith("> "), f"line {i+1} in M78 block not blockquote: {plines[i][:40]!r}"
print("M78 block lines:", i78+1, "-", ishi, "(1-based); anchor M77实算说明 at", ishi+1)

M79_DISC = [
    "> ✅ **M79 补记：91 行的 ④ 已补写成文（`[已证]` 计数不变）**",
    "> `R4_DERIVABILITY` 全量扫描 848 行 `name_only_no_ring4`，其中 **91 行（10.73%）的 ④ 机械可补**（entry 真被活虚表槽持有、RTTI 解出 COL/槽位、装表点在 entry 体外）；已由 `R4_FILL_91_R2` 写成、`R4_FILL_AUDIT` 抽 12 行全 PASS（60/60 项、0 编造）、`R4_FILL_91_R3` 补齐措辞后并入。",
    "> ⇒ 全表「④ 已成文」由 **228 / 1,654（13.78%）升至 319 / 1,654（19.29%）**。注意：**这不是 91 行新增 proved**，这 91 行本来就是 `[已证]`，本次只补写了它们缺失的 ④。",
    "> 另：其余 **746 行**为 direct-only（D-40 不足）、**11 行**全镜像 0 引用（entry 或名字可疑，属另一类卫生问题）。",
]
assert not any("M79 补记" in l for l in plines), "M79 disclosure already present!"
new_plines = plines[:ishi] + M79_DISC + plines[ishi:]
new_ptext = "\n".join(new_plines)
new_praw = new_ptext.encode("utf-8")
open(PANEL, "wb").write(new_praw)
print("PANEL.md written: M79 disclosure 4 lines inserted at", ishi+1, "-", ishi+4, "(1-based); bytes", len(new_praw))
print("M79 block:")
for l in M79_DISC:
    print("  ", l[:80])
