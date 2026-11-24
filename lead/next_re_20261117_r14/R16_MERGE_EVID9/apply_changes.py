# -*- coding: utf-8 -*-
"""Apply R16-MERGE-EVID9 edits. Byte-precise; edits ONLY col6 of 9 rows in coverage.tsv
and inserts a disclosure block into PANEL.md. Copies originals to own dir first."""
import os, sys, shutil, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
R14 = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(R14, "COVERAGE", "PANEL.md")
DELTA = os.path.join(R14, "R16_EVID9", "coverage_delta.tsv")
OUT = os.path.join(R14, "R16_MERGE_EVID9")

def sha(b):
    return hashlib.sha256(b).hexdigest().upper()

COV_BEFORE = os.path.join(OUT, "coverage_before.tsv")
PANEL_BEFORE = os.path.join(OUT, "PANEL_before.md")

# ---- keep pristine copies in own dir (read-only on originals until the edit) ----
shutil.copyfile(COV, COV_BEFORE)
shutil.copyfile(PANEL, PANEL_BEFORE)
print("copied originals to own dir")

raw_before = open(COV_BEFORE, "rb").read()
assert sha(raw_before) == "325158B588636AA3AA170B74B6F4F0E7E5020CA0AC3960232C1DFEAD42CFCEA2"
assert raw_before.count(b"\r\n") == 0 and not raw_before.startswith(b"\xef\xbb\xbf")

# ---- read 3 delta col6 verbatim ----
delta_raw = open(DELTA, "rb").read().decode("utf-8")
delta_lines = delta_raw.split("\n")
delta_hdr = delta_lines[0].split("\t")
di6 = delta_hdr.index("evidence_path")
di0 = delta_hdr.index("entry")
delta_col6 = {}
for ln in delta_lines[1:]:
    if not ln.strip():
        continue
    c = ln.split("\t")
    if len(c) != 8:
        continue
    delta_col6[c[di0]] = c[di6]
print("delta col6 entries:", list(delta_col6.keys()))

BASE_NOTE = ("M85 指针修复：原记缺卡目录层；两候选该 entry 锚点段落逐字节相同，"
             "但 S10_K8F 对 S10_K8 构成支配（K8 独有 4 行全为叙述行、证据载荷独有数 0）"
             "且 K8 头部跳表行自相矛盾，故取 S10_K8F")

K8F_PATH = "S10_K8F\\EVIDENCE\\QUEUE_DISPATCH_AND_FALSE_KILLS.txt#"

# per-entry differentiator (must be distinct; fullwidth punctuation only — no ASCII ; , |)
DIFF = {
    "004DF320": "本行锚点 004DF320（QueueMissionId2ElseId1：清 +0x5D1 后按 0x5C8 / 0x5CC 分派 id=2 或 id=1），吞写块首行正落在 K8 头部 inner index 0 指向 41BADE 说反处。",
    "004DF3A0": "本行锚点 004DF3A0（QueueMissionId1：cell-target 校验后入队 id=1、target=1），吞写 cur==1 且 queued 为 1 或 -1，对应 K8 头部 queued==-1 说反处。",
    "004DFB70": "本行锚点 004DFB70（QueueMissionId7：nearby-filter 后入队 id=7、target=0），吞写 cur==7 且 queued 为 7 或 -1；K8 头部同段早退规则亦说反。",
    "004DFCB0": "本行锚点 004DFCB0（QueueMissionId8：House-filter 后入队 id=8、target=1），吞写 cur==8 且 queued 为 8 或 -1，且 cur=30 跳过 +0x6D2 清位。",
    "004DFE00": "本行锚点 004DFE00（QueueMissionId8：global-filter 后入队 id=8、target=1），全局表 0xA8EB44 / 0xA8EB50，与 004DFCB0 同 id 但过滤源不同。",
    "006F4960": "本行锚点 006F4960（QueueMissionId15：mission14 分支入队 id=15、target=0），吞写 cur==15 且 queued 为 15 或 -1，target=0 不触发晋级。",
}

new_col6 = {}
for e, v in delta_col6.items():
    new_col6[e] = v
for e, d in DIFF.items():
    note = BASE_NOTE + "。" + d
    new_col6[e] = K8F_PATH + e + ";" + note

# sanity: no ASCII separators inside the note part of K8F rows (path;note split yields exactly 2 parts)
for e in DIFF:
    parts = new_col6[e].split(";")
    assert len(parts) == 2, (e, len(parts))
    assert "," not in parts[1] and "|" not in parts[1] and ";" not in parts[1]

NINE = ["004E0E80", "006B6EA0", "006B6FA0",
        "004DF320", "004DF3A0", "004DFB70", "004DFCB0", "004DFE00", "006F4960"]

# ---- edit coverage.tsv at byte level ----
lines = raw_before.split(b"\n")
old_col6_bytes = {}
changed_lines = []
for idx, ln in enumerate(lines):
    if idx == 0:
        continue
    cols = ln.split(b"\t")
    if len(cols) != 8:
        continue
    e = cols[0].decode("utf-8")
    if e in NINE:
        old = cols[5].decode("utf-8")
        old_col6_bytes[e] = old
        cols[5] = new_col6[e].encode("utf-8")
        lines[idx] = b"\t".join(cols)
        changed_lines.append((idx, e, old, new_col6[e]))

assert len(changed_lines) == 9, len(changed_lines)
assert set(old_col6_bytes.keys()) == set(NINE)
raw_after = b"\n".join(lines)

# byte-level restore check: put old col6 back -> must equal before bytes exactly
restore = raw_after
for idx, e, old, new in changed_lines:
    # rebuild this specific line with old col6
    ln = restore.split(b"\n")[idx]
    cols = ln.split(b"\t")
    cols[5] = old.encode("utf-8")
    newln = b"\t".join(cols)
    rlines = restore.split(b"\n")
    rlines[idx] = newln
    restore = b"\n".join(rlines)
assert restore == raw_before, "restore mismatch"
print("byte restore check PASS")

with open(COV, "wb") as f:
    f.write(raw_after)
print("coverage.tsv written; bytes", len(raw_after), "sha", sha(raw_after))

# ---- PANEL.md insertion ----
praw_before = open(PANEL_BEFORE, "rb").read()
assert praw_before.count(b"\r\n") == 0 and not praw_before.startswith(b"\xef\xbb\xbf")
plines = praw_before.split(b"\n")
m83_marker = "> M82 后剩 13 行因同名文件跨卡目录而歧义".encode("utf-8")
m83_idx = [i for i, ln in enumerate(plines) if ln.startswith(m83_marker)]
assert len(m83_idx) == 1, m83_idx
mi = m83_idx[0]
# next line must be the M77 note (to confirm insertion point is right after M83 block)
assert plines[mi+1].startswith("> 📌 **M77".encode("utf-8")), plines[mi+1][:60]

INSERT = [
    "> ✅ **M85 补记：9 行歧义证据指针全部落定（R_OK → 852 / 1,654，R_MISSING → 0）**",
    "> M83 后剩 9 行歧义证据指针本轮全部落定：3 行（`004E0E80` / `006B6EA0` / `006B6FA0`）两候选**字节完全一致**（`BOTH_IDENTICAL`），照交付原样取 `S10_K8`；6 行（`004DF320` / `004DF3A0` / `004DFB70` / `004DFCB0` / `004DFE00` / `006F4960`）按**锚点段落逐字节相同**（6/6）判等价，但**不取字典序较小者**——审计实测 `S10_K8F` 对 `S10_K8` 构成支配（K8 独有 4 行全为叙述行、证据载荷独有数 0）且 K8 头部跳表行与自身反汇编自相矛盾，故 6 行**统一并入 `S10_K8F`**。证据可解析率（`R_OK`）由 843 / 1,654（50.97%）升至 **852 / 1,654（51.51%）**，`R_MISSING` 由 9 归 **0**。",
    "> ⇒ **判定与计数均未变**：grade / 语义 / named / proved / strict 全不变，无达标翻转；本次只让证据指针重新可用。",
    "> 📌 引用纪律：今后引用这 9 行时须知「`S10_K8` 头部有已知自相矛盾，不作为证据源」；6 行统一以 `S10_K8F` 为准，3 行两候选字节全同（`BOTH_IDENTICAL`）取任一等价。",
]
insert_bytes = [s.encode("utf-8") for s in INSERT]
new_plines = plines[:mi+1] + insert_bytes + plines[mi+1:]
praw_after = b"\n".join(new_plines)
# restore check for panel
assert b"\n".join(praw_after.split(b"\n")[:mi+1] + praw_after.split(b"\n")[mi+1+len(insert_bytes):]) == praw_before
with open(PANEL, "wb") as f:
    f.write(praw_after)
print("PANEL.md written; bytes", len(praw_after), "sha", sha(praw_after), "insert after line", mi+1)

# ---- report changed lines ----
print("\nCHANGED ROWS (line 1-based | entry | old col6 -> new col6):")
for idx, e, old, new in sorted(changed_lines):
    print(f"  L{idx+1} {e}\n     OLD: {old}\n     NEW: {new}")
