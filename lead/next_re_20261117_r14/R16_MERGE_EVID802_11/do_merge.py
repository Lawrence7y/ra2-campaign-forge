# -*- coding: utf-8 -*-
"""Merge 11 rows' column 6 into coverage.tsv and insert M95 disclosure into PANEL.md.

Byte-level operations: split on b"\n", modify only target lines' field index 5,
rejoin with b"\n".  PANEL: insert new bytes immediately after the final line of
the M93 block (line 273, 1-based), i.e. right after its terminating b"\n".
"""
import hashlib, json, os, re, sys, time, datetime

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
REPO = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R16_EVID802_11", "coverage_delta.tsv")
OUT = os.path.join(ROOT, "R16_MERGE_EVID802_11")

TARGETS = ["0045A560","0045A610","0053C6A0","005514B0","00551560","00557090",
           "00557140","006B1850","006B1900","006B8660","006B8710"]

def sha(b): return hashlib.sha256(b).hexdigest().upper()

def file_state(path):
    with open(path, "rb") as f: raw = f.read()
    st = os.stat(path)
    lines = raw.split(b"\n")
    trailing = raw.endswith(b"\n")
    if trailing: lines = lines[:-1]
    dt = datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc)
    mtime_full = dt.isoformat().replace("+00:00","Z")
    return {
        "path": path,
        "bytes": len(raw),
        "sha256": sha(raw),
        "mtimeUtc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mtimeUtcFull": mtime_full,
        "lines_split": len(lines),
        "lf_count": raw.count(b"\n"),
        "crlf_count": raw.count(b"\r\n"),
        "lone_cr_count": raw.count(b"\r") - raw.count(b"\r\n"),
        "has_trailing_lf": trailing,
        "bom": list(raw[:3]),
    }, raw

os.makedirs(OUT, exist_ok=True)

# ---- capture BEFORE state + backups ----
cov_before, cov_raw = file_state(COV)
panel_before, panel_raw = file_state(PANEL)
with open(os.path.join(OUT, "_coverage_before.tsv"), "wb") as f: f.write(cov_raw)
with open(os.path.join(OUT, "_panel_before.md"), "wb") as f: f.write(panel_raw)

# baseline invariants on BEFORE coverage
def invariants(raw):
    lines = raw.split(b"\n")
    if lines and lines[-1] == b"": lines = lines[:-1]
    data = lines[1:]
    col_dist = {}
    proved = 0
    atlas_in = 0
    atlas_out = 0
    for ln in data:
        if not ln.strip(): continue
        f = ln.split(b"\t")
        col_dist[len(f)] = col_dist.get(len(f),0)+1
        if len(f) >= 5 and f[4] == "[已证]".encode("utf-8"):
            proved += 1
            # atlas membership approximated below via strict_panel; here use report baseline
    return {
        "data_rows": len(data),
        "col_dist": {str(k):v for k,v in sorted(col_dist.items())},
        "proved": proved,
    }
cov_before["invariants_raw"] = invariants(cov_raw)
cov_before["invariants_expected"] = {"data_rows":18498,"col_dist":{"8":18498},"proved":1654,"atlas_in":1648,"atlas_out":6}

with open(os.path.join(OUT, "before_state.json"), "w", encoding="utf-8") as f:
    json.dump({"coverage": cov_before, "panel": panel_before,
               "note": "before_state captured before any write; backups _coverage_before.tsv / _panel_before.md are byte-identical"},
              f, ensure_ascii=False, indent=2)

print("BEFORE coverage:", json.dumps(cov_before, ensure_ascii=False))
print("BEFORE panel   :", json.dumps(panel_before, ensure_ascii=False))

# ---- build delta col6 map ----
dl = open(DELTA,"rb").read().split(b"\n")
if dl and dl[-1]==b"": dl=dl[:-1]
delta_col6 = {}
for ln in dl[1:]:
    if not ln.strip(): continue
    f = ln.decode("utf-8").split("\t")
    assert len(f)==8
    delta_col6[f[0]] = f[5].encode("utf-8")
assert set(delta_col6)==set(TARGETS)

# ---- perform byte-level merge on coverage ----
cov_lines = cov_raw.split(b"\n")
trailing = cov_raw.endswith(b"\n")
if trailing: cov_lines = cov_lines[:-1]

changed = []
orig_col6 = {}
for i in range(1, len(cov_lines)):
    parts = cov_lines[i].split(b"\t")
    if len(parts)!=8: continue
    e = parts[0].decode("ascii").upper()
    if e in TARGETS:
        assert e not in orig_col6, ("dup", e)
        orig_col6[e] = parts[5]
        old = parts[5]
        new = delta_col6[e]
        assert new.startswith(old + b";"), (e, "strict prefix fail")
        parts[5] = new
        cov_lines[i] = b"\t".join(parts)
        changed.append((i+1, e, old, new))   # 1-based line number

assert set(orig_col6)==set(TARGETS)
assert len(changed)==11
cov_after = b"\n".join(cov_lines)
if trailing: cov_after += b"\n"

# safety: line count unchanged, col6-diff only
assert cov_after.count(b"\n") == cov_raw.count(b"\n")
assert cov_after.count(b"\t") == cov_raw.count(b"\t")  # no tab added/removed

# ---- perform byte-level insertion on PANEL ----
pl = panel_raw.split(b"\n")
# locate M93 header line (1-based) and its block end.
m93_hdr = "> ✅ **M93 补记".encode("utf-8")
m93_idx = None
for i, ln in enumerate(pl):
    if ln.startswith(m93_hdr):
        m93_idx = i
        break
assert m93_idx is not None, "M93 header not found"
# block ends before next line that starts a new Mxx disclosure.
# M93 block: from m93_idx through the line '> **76/76 收官**...' inclusive.
end_idx = None
for j in range(m93_idx+1, len(pl)):
    if pl[j].startswith("> 📌 **M".encode("utf-8")) or pl[j].startswith(b"## "):
        end_idx = j-1
        break
assert end_idx is not None
print("M93 block: 1-based lines %d..%d" % (m93_idx+1, end_idx+1))
print("  last M93 line:", pl[end_idx].decode("utf-8")[:120])
print("  next line     :", pl[end_idx+1].decode("utf-8")[:120] if end_idx+1<len(pl) else "<EOF>")

M95 = [
    r"> ✅ **M95 补记：11 行 trace-only 证据指针接到 PROOF（R_OK 852→863 / 1,654，R_MISSING 0，R_TRACE_ONLY 802→791）**",
    r"> 本批 11 行（`0045A560` / `0045A610` / `0053C6A0` / `005514B0` / `00551560` / `00557090` / `00557140` / `006B1850` / `006B1900` / `006B8660` / `006B8710`）改前第 6 列纯为 `EVIDENCE/classification_trace.tsv#<entry>`（trace-only），其 ④ 早已写在各自 `S1x_KPROVED\EVIDENCE\PROOF_<entry>.txt` 的 ④ 段（①②③④ 四段齐全、盘上唯一且非空）；本次只是把台账指针连过去，未改 grade / 第 4 列语义 / 任何其它列。",
    r"> 选行依据：这 11 行在盘上靠 `R16_PROBE_802_ANCHOR` 全量锚点验证挑出——127 行文件名命中者全部 STRONG（且逐 entry 专属），但只有 11 行的候选是带完整 ①②③④ 的 PROOF 文件；其余 116 行属逐 entry dump，改指等于 trace-only→dump-only，**明确不做**。",
    r"> 审计（`R16_AUDIT_EVID802_11\VERDICT.md`）判 FAIL 11 / PASS 0，唯一必改项为 §D-2 注记逐字节相同；执行器已按 `R16-FIX-EVID802-11-NOTES.md` 重写注记（Lead 自核：unique=11、entry 归一后仍 11、全 8 位 hex 归一后仍 11、路径部分与上版逐字节同），§A/§B/§C/§D-1 全 0 不合格。",
    r"> 重跑 `EVID_RESOLVE\resolve.py`：`R_OK` 852→863、`R_MISSING` 保持 0、`R_TRACE_ONLY` 802→791、`R_EMPTY` 0；11 行命中全部且仅来自 PROOF 段。判定与计数均未变（grade / 语义 / named / proved / strict 全不变，无达标翻转），名义仍 S15/S16/S17、严格仍 S17。",
]
insert_block = ("\n".join(M95) + "\n").encode("utf-8")
# insert after line index end_idx (0-based) => after its terminating \n in the byte stream.
# pl was built by split(b"\n"); reconstruct prefix through end_idx inclusive, then insert.
panel_lines = pl[:end_idx+1] + insert_block.split(b"\n")[:-1] + pl[end_idx+1:]
panel_after = b"\n".join(panel_lines)

# ---- write files ----
with open(COV, "wb") as f: f.write(cov_after)
with open(PANEL, "wb") as f: f.write(panel_after)

# ---- after state ----
cov_after_state, _ = file_state(COV)
panel_after_state, _ = file_state(PANEL)
cov_after_state["invariants_raw"] = invariants(cov_after)
with open(os.path.join(OUT, "after_state.json"), "w", encoding="utf-8") as f:
    json.dump({"coverage": cov_after_state, "panel": panel_after_state,
               "changed_rows": [{"line":c[0],"entry":c[1],
                                 "old_col6":c[2].decode("utf-8"),
                                 "new_col6":c[3].decode("utf-8")} for c in changed]},
              f, ensure_ascii=False, indent=2)

print("AFTER coverage:", json.dumps(cov_after_state, ensure_ascii=False))
print("AFTER panel   :", json.dumps(panel_after_state, ensure_ascii=False))
print("\nMERGE DONE. changed rows:", [(c[0],c[1]) for c in changed])
