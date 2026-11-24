# -*- coding: utf-8 -*-
"""M68 PANEL.md sync. Anchor-based edits with strict assertions."""
import os, sys, hashlib, datetime, json
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
P = os.path.join(ROOT, "COVERAGE", "PANEL.md")
MDIR = os.path.join(ROOT, "MERGE_M68")
BAK = os.path.join(MDIR, "PANEL.md.bak")

def sha256b(b):
    return hashlib.sha256(b).hexdigest().upper()

def utc_iso(p):
    ts = os.path.getmtime(p)
    dt = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

raw = open(P, "rb").read()
before = dict(bytes=len(raw), mtime_utc=utc_iso(P), sha256=sha256b(raw))
print("sha before:", before["sha256"], "bytes before:", before["bytes"], "mtime:", before["mtime_utc"])
open(BAK, "wb").write(raw)
assert sha256b(open(BAK, "rb").read()) == before["sha256"]

text = raw.decode("utf-8")
lines = text.split("\n")
print("split lines:", len(lines), "last:", repr(lines[-1][:40]))

# Card-mandated note, verbatim.
NOTE = (
    "M68 并表 NAMED_PUSH_AUDIT8 PASS 4 行（S12 00442230/00447210/00447F10/0044E8F0，"
    "evidence_path 改指 NAMED_PUSH_AUDIT8/VERDICT.md；"
    "00447210 与 00447F10 的 ③ 站点为「返回值搬入 ebx/ebp 再判」，"
    "审计独立枚举被调全部 ret 确认为多值状态码 {0,4,5,7,8,0x1A,0x37} 与 {0,1,3,5,6,8,9}，非 {0,1} 布尔）"
)

def edit_line(idx, old_anchor, new_anchor, insert_note_after=None):
    ln = lines[idx - 1]
    assert old_anchor in ln, f"L{idx}: anchor not found: {old_anchor!r}"
    ln = ln.replace(old_anchor, new_anchor, 1)
    if insert_note_after is not None:
        assert insert_note_after in ln, f"L{idx}: note anchor not found: {insert_note_after!r}"
        ln = ln.replace(insert_note_after, insert_note_after + NOTE + "；", 1)
    lines[idx - 1] = ln
    return ln

# ---- Line 1: title note prepend ----
TITLE_NOTE = (
    "M68 并表 4 行（NAMED_PUSH_AUDIT8 PASS 4 行 S12 00442230/00447210/00447F10/0044E8F0，"
    "均 atlas 内，仅改 coverage 第 4/5/6 列、第 1/2/3/7/8 列不动；coverage 18,498 行不变；"
    "全表 [已证] 1,569→1,573、atlas 内 1,563→1,567、atlas 外仍 6；"
    "面板 S12 proved 55→59、strict 40→44；"
    "00447210/00447F10 ③ 站点多值状态码非布尔，审计独立枚举被调全部 ret 确认；"
    "strict 按权威口径 [未证] 字面重算，达标判定不变（严格仍仅 S17）；不 git commit）；"
)
assert lines[0].startswith("# PANEL — R14 coverage"), lines[0][:40]
lines[0] = "# PANEL — R14 coverage" + TITLE_NOTE + lines[0][len("# PANEL — R14 coverage"):]

# ---- Line 17: 全表/atlas [已证] row ----
edit_line(17, "**1,569 / 1,563**", "**1,573 / 1,567**",
          insert_note_after="| **1,573 / 1,567** | ")

# ---- Main panel rows ----
# S12: proved 55->59 (19.71->21.15), named cols untouched
edit_line(66, "| 54 | 19.35 | 55 | 19.71 |", "| 54 | 19.35 | 59 | 21.15 |",
          insert_note_after="| 54 | 19.35 | 59 | 21.15 | ")
# TOTAL: atlas proved 1563->1567 (12.10->12.13)
edit_line(77, "| **1372** | **10.62** | **1563** | **12.10** |",
               "| **1372** | **10.62** | **1567** | **12.13** |",
          insert_note_after="| **1372** | **10.62** | **1567** | **12.13** | ")

# ---- Strict double table rows ----
# S12: proved 55->59 (19.71->21.15), strict 40->44 (14.34->15.77)
edit_line(116, "| S12 | 279 | 55 | 19.71 | **40** | **14.34** |",
                "| S12 | 279 | 59 | 21.15 | **44** | **15.77** |")
# TOTAL: proved 1563->1567 (12.10->12.13), strict 1246->1250 (9.65->9.68)
edit_line(127, "| **TOTAL** | **12916** | **1563** | **12.10** | **1246** | **9.65** |",
                "| **TOTAL** | **12916** | **1567** | **12.13** | **1250** | **9.68** |")

# ---- Strict narrative: add M68 note after M67 note ----
M68_STRICT_NOTE = (
    "> 📌 **M68 并表实算说明**：本表 S12 proved/strict 40→44（proved 55→59）、"
    "TOTAL 1,246→1,250（proved 1,563→1,567）均按盘上实算；"
    "本次并入 4 行新语义均不含字面 `[未证]`（核 delta 第 4 列），"
    "strict 随 proved 同增（S12 +4、TOTAL +4）。"
    "00447210/00447F10 的 ③ 站点为「返回值搬入 ebx/ebp 再判」，"
    "审计独立枚举被调全部 ret 确认为多值状态码（非 {0,1} 布尔）。"
    "严格口径仍仅 S17 达标（1/22），名义仍 S15/S16/S17（3/22），**达标判定未翻转**。"
    "strict 用 `strict_panel.py` 第 78 行 `if \"[未证]\" not in sem:` 的带方括号字面口径复算。"
)
m67_idx = None
for i, ln in enumerate(lines):
    if "M67 并表实算说明" in ln:
        m67_idx = i
        break
assert m67_idx is not None, "M67 note line not found"
lines.insert(m67_idx + 1, M68_STRICT_NOTE)

new_text = "\n".join(lines)
new_raw = new_text.encode("utf-8")
open(P, "wb").write(new_raw)
after = dict(bytes=len(new_raw), mtime_utc=utc_iso(P), sha256=sha256b(new_raw))
print("sha after:", after["sha256"], "bytes after:", after["bytes"], "mtime:", after["mtime_utc"])
print("inserted strict note after original line", m67_idx + 1)

# merge state
sp = os.path.join(MDIR, "_state.json")
st = json.load(open(sp, encoding="utf-8"))
st["panel"] = dict(before=before, after=after)
json.dump(st, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
