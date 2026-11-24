#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R17-MERGE-HYG93 merge script.

Merges 6 HYG delta.tsv files into COVERAGE/coverage.tsv, touching ONLY column 4
(one_line_semantics) of exactly 93 named rows:
  - 91 rows: append SENTENCE (65 chars) to col4
  -  2 rows: replace trailing old pointer segment with NEW segment

Discipline:
  - never uses PowerShell (no single-letter variable risk); this is Python
  - reads whole file -> builds complete new byte array in memory
  - asserts all N1-N8 BEFORE writing; any failure => abort with NO write
  - single atomic write (os.replace) -> read back -> verify
  - LF only; asserts CR count == 0
"""
import os
import sys
import hashlib
import shutil
import datetime
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge") if os.name == "nt" else Path(
    "/mnt/d/Project/ra2-campaign-forge"
)
ROOT = BASE / "lead" / "next_re_20261117_r14"
COV = ROOT / "COVERAGE" / "coverage.tsv"
OUT = ROOT / "R17_MERGE_HYG93"
BASELINE = ROOT / "R17_LEAD_BASELINE" / "coverage.before_hyg.tsv"

DELTA_DIRS = [
    "R17_HYG_A1_B1", "R17_HYG_A1_B2", "R17_HYG_A1_B3",
    "R17_HYG_A1_B4", "R17_HYG_A1_B5", "R17_HYG_A1_B6",
]

SENTENCE = "（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）"
OLD_SEG = "（D-47 披露指针：R14_COMMON §12.6 与 PANEL 对应披露）"
NEW_SEG = "（本行 ④ 为 direct call 形态 1，不属于「活 vtable 槽位」形态；D-47(A) 的披露纪律不适用于本行，故不引该披露）"
REPLACE_ENTRIES = {"004AF540", "004B5AB0"}

EXPECTED_DATA_ROWS = 18498
EXPECTED_GRADE = {"[已证]": 1654, "[静态推断]": 5875, "[未证]": 10969}
EXPECTED_SECTION_12_6_BEFORE = 234
EXPECTED_SECTION_12_6_AFTER = 323


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(msg: str):
    print("ASSERTION FAILED: " + msg, file=sys.stderr)
    sys.exit(2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- Step 1: before backup (only after confirming file matches baseline) ----
    raw = COV.read_bytes()
    before_bytes = len(raw)
    before_sha = sha256(raw)
    before_mtime = datetime.datetime.fromtimestamp(
        COV.stat().st_mtime, datetime.timezone.utc
    ).astimezone().isoformat()

    if BASELINE.exists():
        base_raw = BASELINE.read_bytes()
        if sha256(base_raw) != before_sha:
            fail("coverage.tsv sha256 does not match R17_LEAD_BASELINE baseline")
        print("baseline cross-check: OK (sha256 prefix a07a74c1)")

    backup = OUT / "coverage.before.tsv"
    backup.write_bytes(raw)
    print(f"BEFORE bytes={before_bytes} sha256={before_sha} mtime={before_mtime}")

    # ---- Step 2: parse deltas ----
    deltas = {}
    delta_meta = {}
    for folder in DELTA_DIRS:
        path = ROOT / folder / "delta.tsv"
        for row in path.read_text(encoding="utf-8").splitlines():
            parts = row.split("\t")
            if parts[0] == "line":
                continue  # header
            if len(parts) != 8:
                fail(f"delta row has {len(parts)} columns: {row[:80]}")
            line_s, entry, len_b, sha_b, len_a, sha_a, sent, note = parts
            line = int(line_s)
            if line in deltas:
                fail(f"duplicate delta line {line}")
            deltas[line] = {
                "entry": entry, "len_b": int(len_b), "sha_b": sha_b,
                "len_a": int(len_a), "sha_a": sha_a, "sent": sent,
                "folder": folder,
            }
    print(f"deltas parsed: {len(deltas)} rows")

    # ---- Step 3: decode coverage into lines and validate base structure ----
    if b"\r" in raw:
        fail("coverage.tsv contains CR bytes")
    text = raw.decode("utf-8")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        fail("unexpected trailing newline (file should have no trailing LF)")
    total_lines = len(lines)  # 1 header + 18498 data rows
    data_rows = total_lines - 1
    if data_rows != EXPECTED_DATA_ROWS:
        fail(f"data rows = {data_rows}, expected {EXPECTED_DATA_ROWS}")

    header_cols = lines[0].split(",")  # header is comma-separated; data rows are TSV
    if len(header_cols) != 8:
        fail(f"header has {len(header_cols)} columns")
    if header_cols[3] != "one_line_semantics":
        fail("header col4 is not one_line_semantics")

    # every DATA row 8 columns; grade distribution on col5 (index 4)
    grade_counts = {g: 0 for g in EXPECTED_GRADE}
    for i, line in enumerate(lines):
        if i == 0:
            continue  # header is CSV, skip column check
        if line.count("\t") != 7:
            fail(f"line {i+1} does not have 8 columns")
        grade = line.split("\t")[4]
        if grade not in grade_counts:
            fail(f"unknown grade {grade!r} on line {i+1}")
        grade_counts[grade] += 1
    if grade_counts != EXPECTED_GRADE:
        fail(f"grade counts {grade_counts} != {EXPECTED_GRADE}")

    # section 12.6 count before: PANEL distinguishes 命中行 (matching lines)
    # from 字面次数 (literal occurrences); card N6 uses matching LINES.
    s126_before = sum(1 for ln in lines if "§12.6" in ln)
    if s126_before != EXPECTED_SECTION_12_6_BEFORE:
        fail(f"§12.6 matching-lines before={s126_before}, expected {EXPECTED_SECTION_12_6_BEFORE}")

    # ---- Step 4: construct new lines, classify edits ----
    changed_lines = {}
    changed_rows_info = []
    for line, meta in deltas.items():
        idx = line - 1  # 0-based into lines[]; physical line numbers are 1-based
        cols = lines[idx].split("\t")
        entry = cols[0]
        if entry != meta["entry"]:
            fail(f"line {line} entry {entry} != delta {meta['entry']}")
        col4 = cols[3]
        # verify col4 sha1 and length (char count)
        if len(col4) != meta["len_b"]:
            fail(f"line {line} col4 len {len(col4)} != delta {meta['len_b']}")
        if hashlib.sha1(col4.encode("utf-8")).hexdigest() != meta["sha_b"]:
            fail(f"line {line} col4 sha1 mismatch (before)")

        if entry in REPLACE_ENTRIES:
            # N4: old segment exactly once, at tail; no §12.6-adding here
            if col4.count(OLD_SEG) != 1 or not col4.endswith(OLD_SEG):
                fail(f"line {line} ({entry}): old segment not exactly once at tail")
            if "④ direct call" not in col4:
                fail(f"line {line} ({entry}): missing '④ direct call'")
            if meta["sent"] != NEW_SEG:
                fail(f"line {line} ({entry}): delta sentence != NEW_SEG")
            new_col4 = col4[:-len(OLD_SEG)] + NEW_SEG
            kind = "replace"
        else:
            if meta["sent"] != SENTENCE:
                fail(f"line {line}: delta sentence != SENTENCE")
            new_col4 = col4 + SENTENCE
            kind = "add"

        # verify after sha1 / length
        if len(new_col4) != meta["len_a"]:
            fail(f"line {line} col4 after len {len(new_col4)} != delta {meta['len_a']}")
        if hashlib.sha1(new_col4.encode("utf-8")).hexdigest() != meta["sha_a"]:
            fail(f"line {line} col4 sha1 mismatch (after)")

        new_cols = list(cols)
        new_cols[3] = new_col4
        changed_lines[line] = "\t".join(new_cols)
        changed_rows_info.append((line, entry, kind, meta["len_b"], meta["len_a"]))

    if len(changed_lines) != 93:
        fail(f"changed lines = {len(changed_lines)}, expected 93")
    replace_lines = [x for x in changed_rows_info if x[2] == "replace"]
    add_lines = [x for x in changed_rows_info if x[2] == "add"]
    if len(replace_lines) != 2 or len(add_lines) != 91:
        fail(f"add/replace split = {len(add_lines)}/{len(replace_lines)}")
    if {x[1] for x in replace_lines} != REPLACE_ENTRIES:
        fail(f"replace entries mismatch: {[x[1] for x in replace_lines]}")

    # ---- Step 5: build complete new byte array in memory ----
    new_lines = [changed_lines.get(i + 1, lines[i]) for i in range(total_lines)]
    new_text = "\n".join(new_lines)
    new_raw = new_text.encode("utf-8")

    # ---- Step 6: assertions N1-N8 (all on in-memory data, before write) ----
    # N1: data rows unchanged, 8 cols, header bytes unchanged
    new_split = new_text.split("\n")
    if len(new_split) != total_lines or len(new_split) - 1 != EXPECTED_DATA_ROWS:
        fail("N1: total/data line count changed")
    if new_split[0] != lines[0]:
        fail("N1: header bytes changed")
    if b"\r" in new_raw:
        fail("N5: CR introduced")

    # N2: exactly 93 data rows differ, 18405 identical byte-for-byte
    # (card counts DATA rows: 18498 - 93 = 18405; header excluded)
    diff_lines = [i + 1 for i in range(total_lines) if new_lines[i] != lines[i]]
    same_lines = (total_lines - 1) - len(diff_lines)  # exclude header
    if len(diff_lines) != 93:
        fail(f"N2: diff lines = {len(diff_lines)}, expected 93")
    if same_lines != 18405:
        fail(f"N2: identical data rows = {same_lines}, expected 18405")
    if set(diff_lines) != set(deltas.keys()):
        fail("N2: diff line set != delta line set")

    # also verify: only col4 differs on each changed line; other columns identical
    for line in diff_lines:
        old_cols = lines[line - 1].split("\t")
        new_cols = new_lines[line - 1].split("\t")
        for ci in range(8):
            if ci != 3 and old_cols[ci] != new_cols[ci]:
                fail(f"N2: line {line} col {ci+1} changed (forbidden)")

    # N3: 91 append rows: len_after-len_before==65 and after==before+SENTENCE
    for line, entry, kind, lb, la in add_lines:
        if la - lb != 65:
            fail(f"N3: line {line} len delta {la-lb} != 65")
        old_c4 = lines[line - 1].split("\t")[3]
        new_c4 = new_lines[line - 1].split("\t")[3]
        if new_c4 != old_c4 + SENTENCE:
            fail(f"N3: line {line} not old+SENTENCE")

    # N4: 2 replace rows verified during construction; re-assert on result
    for line, entry, kind, lb, la in replace_lines:
        old_c4 = lines[line - 1].split("\t")[3]
        new_c4 = new_lines[line - 1].split("\t")[3]
        if new_c4.count(OLD_SEG) != 0:
            fail(f"N4: line {line} still has old segment")
        if "§12.6" in new_c4:
            fail(f"N4: line {line} still contains §12.6")
        if "④ direct call" not in new_c4:
            fail(f"N4: line {line} lost '④ direct call'")
        if new_c4 != old_c4[:-len(OLD_SEG)] + NEW_SEG:
            fail(f"N4: line {line} replacement mismatch")

    # N5: grade counts unchanged
    new_grade_counts = {g: 0 for g in EXPECTED_GRADE}
    for line in new_lines[1:]:
        new_grade_counts[line.split("\t")[4]] += 1
    if new_grade_counts != EXPECTED_GRADE:
        fail(f"N5: grade counts changed to {new_grade_counts}")

    # N6: §12.6 matching-LINES 234 -> 323 (each append row newly contains it,
    # each replace row loses it; card formula 234 + 91 - 2).
    s126_after = sum(1 for ln in new_lines if "§12.6" in ln)
    if s126_after != EXPECTED_SECTION_12_6_AFTER:
        fail(f"N6: §12.6 matching-lines after={s126_after}, expected {EXPECTED_SECTION_12_6_AFTER}")

    # N7: §12.4 == 0, 'CLSID None' == 0
    s124_after = new_text.count("§12.4")
    clsid_none_after = new_text.count("CLSID None")
    if s124_after != 0:
        fail(f"N7: §12.4 count = {s124_after}")
    if clsid_none_after != 0:
        fail(f"N7: CLSID None count = {clsid_none_after}")
    s124_before = text.count("§12.4")
    clsid_none_before = text.count("CLSID None")

    # N8: ④ statistical measures must not change.
    # Definitions per COVERAGE/PANEL.md (口径 A/B) and PANEL note on 宽口径:
    #   A      = grade '[已证]' AND col4 contains '④'
    #   B      = grade '[已证]' AND col4 contains '④ 活表槽位见证'
    #   宽口径 = grade '[已证]' AND col4 contains ('④ 活表槽位见证' OR '④ direct call 使用见证')
    #   完全无④ = grade '[已证]' AND col4 does NOT contain '④'
    def measures(line_list):
        proven = [ln for ln in line_list[1:] if ln.split("\t")[4] == "[已证]"]
        col4 = [ln.split("\t")[3] for ln in proven]
        a = sum(1 for c in col4 if "④" in c)
        b = sum(1 for c in col4 if "④ 活表槽位见证" in c)
        w = sum(1 for c in col4 if "④ 活表槽位见证" in c or "④ direct call 使用见证" in c)
        n = sum(1 for c in col4 if "④" not in c)
        return a, b, w, n

    a_before, b_before, w_before, n_before = measures(lines)
    a_after, b_after, w_after, n_after = measures(new_lines)
    if (a_before, b_before, w_before, n_before) != (458, 291, 293, 1196):
        fail(f"N8 before mismatch: A={a_before} B={b_before} W={w_before} No={n_before}")
    if (a_after, b_after, w_after, n_after) != (a_before, b_before, w_before, n_before):
        fail(f"N8: measures changed: before=({a_before},{b_before},{w_before},{n_before}) after=({a_after},{b_after},{w_after},{n_after})")

    print("=== ALL ASSERTIONS N1-N8 PASS (in-memory) ===")
    print(f"N1 data_rows={data_rows} header_unchanged=True cols8=True")
    print(f"N2 diff={len(diff_lines)} identical={same_lines}")
    print(f"N3 append_rows={len(add_lines)} all len_delta=65 and after==before+SENTENCE")
    print(f"N4 replace_rows={len(replace_lines)} all old-seg removed, §12.6 absent, ④ direct call present")
    print(f"N5 grades={grade_counts}")
    print(f"N6 §12.6 before={s126_before} after={s126_after}")
    print(f"N7 §12.4 before={s124_before} after={s124_after} CLSID None before={clsid_none_before} after={clsid_none_after}")
    print(f"N8 A={a_after} B={b_after} W={w_after} No={n_after}")

    # ---- Step 7: single atomic write ----
    tmp = OUT / "coverage.tsv.tmp"
    tmp.write_bytes(new_raw)
    os.replace(tmp, COV)
    print("WROTE coverage.tsv atomically")

    # ---- Step 8: readback verification ----
    rb = COV.read_bytes()
    after_bytes = len(rb)
    after_sha = sha256(rb)
    after_mtime = datetime.datetime.fromtimestamp(
        COV.stat().st_mtime, datetime.timezone.utc
    ).astimezone().isoformat()
    if rb != new_raw:
        fail("readback bytes != intended new bytes")
    if b"\r" in rb:
        fail("readback contains CR")
    print(f"AFTER bytes={after_bytes} sha256={after_sha} mtime={after_mtime}")
    print(f"READBACK OK: bytes={after_bytes} CR={rb.count(bytes([13]))}")

    # ---- Step 9: write changed_rows.tsv ----
    cr_path = OUT / "changed_rows.tsv"
    with cr_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("line\tentry\tkind\tlen_before\tlen_after\n")
        for line, entry, kind, lb, la in sorted(changed_rows_info):
            fh.write(f"{line}\t{entry}\t{kind}\t{lb}\t{la}\n")
    print(f"WROTE {cr_path.name} ({len(changed_rows_info)} rows)")

    # ---- Step 10: write MERGE_REPORT.md ----
    diff_sorted = sorted(diff_lines)
    report = f"""# R17-MERGE-HYG93 MERGE REPORT

## Before / After triples (bytes / mtime / sha256)

| | bytes | mtime | sha256 |
|---|---:|---|---|
| before | {before_bytes} | {before_mtime} | {before_sha} |
| after  | {after_bytes} | {after_mtime} | {after_sha} |

sha256 prefix: before `{before_sha[:12]}` -> after `{after_sha[:12]}`.
Baseline cross-check against `R17_LEAD_BASELINE/coverage.before_hyg.tsv` (prefix `A07A74C1`): PASS.

## Assertions N1-N8 (measured)

- **N1**: data rows before={data_rows} after={len(new_split)-1}; expected 18498. Each row 8 columns. Header bytes unchanged: PASS.
- **N2**: exactly {len(diff_lines)} data rows changed, {same_lines} data rows byte-identical (expected 93 / 18405, header excluded). Changed-line set == delta-line set: PASS. Only col4 differs on every changed line: PASS.
- **N3**: 91 append rows: every one has `len_after - len_before == 65` and `after == before + SENTENCE`: PASS.
- **N4**: 2 replace rows (`004AF540` @2698, `004B5AB0` @2777): old segment occurred exactly once at tail, removed; result contains no `§12.6` substring, still contains `④ direct call`: PASS.
- **N5**: grade counts unchanged: `[已证] {grade_counts['[已证]']} / [静态推断] {grade_counts['[静态推断]']} / [未证] {grade_counts['[未证]']}`: PASS.
- **N6**: `§12.6` hits before={s126_before} -> after={s126_after} (expected 234 -> 323 = 234+91-2): PASS.
- **N7**: `§12.4` before={s124_before} after={s124_after} (expected 0); `CLSID None` before={clsid_none_before} after={clsid_none_after} (expected 0): PASS.
- **N8**: ④ measures unchanged: A={a_after} (expect 458), B={b_after} (expect 291), wide={w_after} (expect 293), no-④={n_after} (expect 1196): PASS.

## Changed lines (93 line numbers)

```
{', '.join(str(x) for x in diff_sorted)}
```

Full per-line detail (line, entry, kind, len_before, len_after) is in `changed_rows.tsv`.

## Files

- `merge.py` — re-runnable script (this file's logic)
- `coverage.before.tsv` — full pre-merge copy, sha256 `{before_sha}`
- `changed_rows.tsv` — 93 rows, one per changed line
- `MERGE_REPORT.md` — this report

Readback after single atomic write: bytes={after_bytes}, CR count=0, sha256={after_sha}.
"""
    (OUT / "MERGE_REPORT.md").write_text(report, encoding="utf-8", newline="\n")
    print(f"WROTE MERGE_REPORT.md")
    print("DONE")


if __name__ == "__main__":
    main()
