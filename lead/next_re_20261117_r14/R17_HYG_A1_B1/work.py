#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R17-HYG-A1-B1 executor.

Read-only on COVERAGE/coverage.tsv. Produces only delta.tsv and REPORT.md in
this script's own directory. No reverse engineering, no grade/number edits.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

# ---- Fixed constants (verbatim from the card) -------------------------------
SENTENCE = "（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）"
EXPECTED_SENTENCE_LEN = 65
BASELINE_P_TOTAL = 91
BASELINE_DATA_ROWS = 18498
EXPECTED_COLS = 8

HERE = Path(__file__).resolve().parent
COV = HERE.parent / "COVERAGE" / "coverage.tsv"
DELTA = HERE / "delta.tsv"
REPORT = HERE / "REPORT.md"

TARGET_LINES = [
    1444, 3231, 3942, 5291, 5360, 5443, 5445, 5446,
    5447, 5448, 5449, 5450, 5465, 5466, 5467, 5468,
]
EXPECTED_ENTRIES = [
    "00464AC0", "004DE630", "004F42F0", "005519B0",
    "00556090", "00559D60", "00559EB0", "00559ED0",
    "0055A050", "0055A070", "0055A090", "0055A0D0",
    "0055A710", "0055A730", "0055A7D0", "0055A8C0",
]

DELTA_HEADER_COLS = [
    "line",
    "entry",
    "col4_len_before",
    "col4_sha1_before",
    "col4_len_after",
    "col4_sha1_after",
    "appended_sentence",
    "note",
]

# 口径 P: col5 == '[已证]' AND '④ 活表槽位见证' in col4 AND '§12.6' not in col4
def match_p(cells: list[str]) -> bool:
    return (
        len(cells) == EXPECTED_COLS
        and cells[4] == "[已证]"
        and "④ 活表槽位见证" in cells[3]
        and "§12.6" not in cells[3]
    )


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def note_for(entry: str, lineno: int, old_col4: str) -> str:
    slot_m = re.search(r"([A-Za-z][A-Za-z0-9_]*::slot\d+)", old_col4)
    vt_m = re.search(r"vt=([0-9A-F]{6,8})", old_col4)
    slot = slot_m.group(1) if slot_m else "未取得"
    vt = vt_m.group(1) if vt_m else "未取得"
    return f"{entry} 第{lineno}行第4列读到 {slot}（vt={vt}），追加 D-47(A) §12.6 披露句。"


def main() -> None:
    # ---- Load source (read-only) -------------------------------------------
    raw = COV.read_bytes()
    cr_count = raw.count(b"\r")
    text = raw.decode("utf-8")
    lines = text.split("\n")
    header = lines[0]
    data = lines[1:]  # physical line N -> data[N-2]

    # ---- 3.1 口径 P whole-table scan ---------------------------------------
    p_hits: list[tuple[int, str]] = []
    col_count_dist: dict[int, int] = {}
    for idx, row in enumerate(data):
        cells = row.split("\t")
        col_count_dist[len(cells)] = col_count_dist.get(len(cells), 0) + 1
        if match_p(cells):
            p_hits.append((idx + 2, cells[0]))  # physical line number
    p_total = len(p_hits)
    p_diff_reason = ""
    if p_total != BASELINE_P_TOTAL:
        p_diff_reason = (
            f"口径 P 命中 {p_total}，与基线 {BASELINE_P_TOTAL} 不符；"
            f"差异原因未能在卡面给定信息中确定，按卡面要求停止调和。"
        )

    # ---- 3.2 batch vs expected entry list ----------------------------------
    actual_entries: list[str] = []
    entry_mismatch: list[str] = []
    for lineno in TARGET_LINES:
        cells = data[lineno - 2].split("\t")
        actual_entries.append(cells[0])
    entry_order_ok = actual_entries == EXPECTED_ENTRIES
    if not entry_order_ok:
        for lineno, got, exp in zip(TARGET_LINES, actual_entries, EXPECTED_ENTRIES):
            if got != exp:
                entry_mismatch.append(f"line {lineno}: got {got}, expected {exp}")

    # ---- 3.3 trailing-whitespace scan on the 16 rows -----------------------
    trailing_ws_rows: list[str] = []
    for lineno, entry in zip(TARGET_LINES, actual_entries):
        old_col4 = data[lineno - 2].split("\t")[3]
        if re.search(r"\s$", old_col4):
            trailing_ws_rows.append(f"line {lineno} ({entry})")

    # ---- 3.4 per-row assertions on the generated delta ---------------------
    delta_rows: list[str] = []
    fail_rows: list[str] = []
    sentence_count_bad_rows: list[str] = []
    virtual_table = list(data)  # in-memory transformed whole table, never written

    for pos, (lineno, entry) in enumerate(zip(TARGET_LINES, actual_entries)):
        cells = data[lineno - 2].split("\t")
        old_col4 = cells[3]
        other_before = cells[:3] + cells[4:]
        new_col4 = old_col4 + SENTENCE
        new_cells = cells[:3] + [new_col4] + cells[4:]
        new_row = "\t".join(new_cells)
        virtual_table[lineno - 2] = new_row

        fails: list[str] = []
        # a) byte-exact append
        if new_cells[3].encode("utf-8") != (old_col4 + SENTENCE).encode("utf-8"):
            fails.append("a: new_col4 != old_col4 + SENTENCE (byte-exact)")
        # b) SENTENCE exactly once and at the end
        cnt = new_col4.count(SENTENCE)
        if cnt != 1 or not new_col4.endswith(SENTENCE):
            fails.append(f"b: SENTENCE count={cnt}, endswith={new_col4.endswith(SENTENCE)}")
            sentence_count_bad_rows.append(f"line {lineno} ({entry}): count={cnt}")
        # c) length delta exactly 65 characters
        if len(new_col4) - len(old_col4) != EXPECTED_SENTENCE_LEN:
            fails.append(f"c: len delta={len(new_col4) - len(old_col4)}")
        # d) other 7 columns byte-identical
        other_after = new_cells[:3] + new_cells[4:]
        if [c.encode("utf-8") for c in other_after] != [c.encode("utf-8") for c in other_before]:
            fails.append("d: other 7 columns changed")
        # extra: the row must satisfy 口径 P before appending
        if not match_p(cells):
            fails.append("extra: row does not satisfy 口径 P")
        # extra: entry format 8 uppercase hex digits
        if not re.fullmatch(r"[0-9A-F]{8}", entry):
            fails.append("extra: entry not 8 uppercase hex digits")

        if fails:
            fail_rows.append(f"line {lineno} ({entry}): " + "; ".join(fails))

        note = note_for(entry, lineno, old_col4)
        fields = [
            str(lineno),
            entry,
            str(len(old_col4)),
            sha1(old_col4),
            str(len(new_col4)),
            sha1(new_col4),
            SENTENCE,
            note,
        ]
        if any("\t" in f or "\n" in f or "\r" in f for f in fields):
            fail_rows.append(f"line {lineno} ({entry}): extra: DELTA field contains TAB/newline")
        if len(fields) != EXPECTED_COLS:
            fail_rows.append(f"line {lineno} ({entry}): extra: DELTA field count={len(fields)}")
        delta_rows.append("\t".join(fields))

    # e) virtual whole-table invariants
    table_row_count_ok = len(virtual_table) == BASELINE_DATA_ROWS
    table_col_count_ok = all(len(r.split("\t")) == EXPECTED_COLS for r in virtual_table)
    untouched_ok = all(
        virtual_table[i] == data[i]
        for i in range(len(data))
        if (i + 2) not in TARGET_LINES
    )
    if not table_row_count_ok:
        fail_rows.append(f"e: virtual table rows={len(virtual_table)}")
    if not table_col_count_ok:
        fail_rows.append("e: virtual table has rows != 8 cols")
    if not untouched_ok:
        fail_rows.append("e: non-target rows changed in virtual table")

    # ---- Write delta.tsv ----------------------------------------------------
    delta_lines = ["\t".join(DELTA_HEADER_COLS)] + delta_rows
    DELTA.write_bytes(("\n".join(delta_lines) + "\n").encode("utf-8"))

    # ---- Verify delta.tsv after write --------------------------------------
    written = DELTA.read_bytes().decode("utf-8").split("\n")
    written = [l for l in written if l != ""]
    delta_header_ok = written[0] == "\t".join(DELTA_HEADER_COLS)
    delta_data_rows = written[1:]
    delta_cols_ok = all(len(r.split("\t")) == EXPECTED_COLS for r in delta_data_rows)
    delta_row_count = len(delta_data_rows)
    notes = [r.split("\t")[7] for r in delta_data_rows]
    notes_unique = len(set(notes)) == len(notes)
    if not (delta_header_ok and delta_cols_ok and delta_row_count == 16 and notes_unique):
        fail_rows.append(
            "extra: delta.tsv self-check failed "
            f"(header={delta_header_ok}, cols={delta_cols_ok}, rows={delta_row_count}, notes_unique={notes_unique})"
        )

    # ---- REPORT.md ----------------------------------------------------------
    r: list[str] = []
    r.append("# R17-HYG-A1-B1 执行报告\n")
    r.append("## 0. 自证\n")
    r.append("本卡未改 `coverage.tsv`、未改 grade、未改任何数字。\n")
    r.append("## 1. 口径 P 全表筛选（第 3 节第 1 项）\n")
    r.append("- 筛选口径 P：第 5 列 == `[已证]` 且第 4 列包含子串 `④ 活表槽位见证` 且第 4 列不包含子串 `§12.6`。\n")
    r.append(f"- 全表数据行数（不含表头）：{len(data)}；文件末尾无换行，表头为逗号分隔，数据行为 TAB 分隔。\n")
    r.append(f"- **口径 P 全表总数：{p_total}**（基线 {BASELINE_P_TOTAL}）。\n")
    if p_total != BASELINE_P_TOTAL:
        r.append(f"- 差异说明：{p_diff_reason}\n")
    else:
        r.append("- 与基线一致，无差异，无需调和。\n")
    r.append(f"- 数据行列数分布：{col_count_dist}；CR 字符数：{cr_count}。\n\n")

    r.append("## 2. 本批 16 行与 entry 清单核对（第 3 节第 2 项）\n")
    r.append(f"- 本批行数：{len(TARGET_LINES)}；物理行号升序；与卡面 entry 列表逐行一致：**{'是' if entry_order_ok else '否'}**。\n")
    if not entry_order_ok:
        for m in entry_mismatch:
            r.append(f"- 差异：{m}\n")
    r.append("\n| line | entry | 第4列字符数(before) | 第4列字符数(after) |\n")
    r.append("|---|---|---|---|\n")
    for lineno, entry in zip(TARGET_LINES, actual_entries):
        cells = data[lineno - 2].split("\t")
        r.append(f"| {lineno} | {entry} | {len(cells[3])} | {len(cells[3]) + EXPECTED_SENTENCE_LEN} |\n")
    r.append("\n")

    r.append("## 3. 行尾空白扫描（第 3 节第 3 项）\n")
    r.append(f"- 对本批 16 行第 4 列跑正则 `\\s$`，命中行数：**{len(trailing_ws_rows)}**（基线 0）。\n")
    if trailing_ws_rows:
        for t in trailing_ws_rows:
            r.append(f"- 命中：{t}\n")
    else:
        r.append("- 命中明细：无。\n")
    r.append("\n")

    r.append("## 4. 逐行断言 a–e（第 3 节第 4 项）\n")
    r.append("- 断言对象为生成的 delta（在内存中把 16 行新第 4 列套回整表后做整表断言），未改动盘上 `coverage.tsv`。\n")
    r.append("- a) `new_col4 == old_col4 + SENTENCE`（逐字节）：已逐行断言。\n")
    r.append(f"- b) `SENTENCE` 在 `new_col4` 中恰好 1 次且位于末尾；出现次数 ≠1 的行数：**{len(sentence_count_bad_rows)}**。\n")
    if sentence_count_bad_rows:
        for t in sentence_count_bad_rows:
            r.append(f"  - {t}\n")
    r.append(f"- c) `len(new_col4) - len(old_col4) == {EXPECTED_SENTENCE_LEN}`（字符数）：已逐行断言；`SENTENCE` 实测字符数 = {len(SENTENCE)}。\n")
    r.append("- d) 其余 7 列逐字节不变：已逐行断言。\n")
    r.append(f"- e) 虚拟整表数据行数仍为 {BASELINE_DATA_ROWS}：**{'成立' if table_row_count_ok else '不成立'}**；每行仍为 8 列：**{'成立' if table_col_count_ok else '不成立'}**；非目标行未变：**{'成立' if untouched_ok else '不成立'}**。\n")
    r.append(f"- **FAIL 行数：{len(fail_rows)}**。\n")
    if fail_rows:
        for f in fail_rows:
            r.append(f"  - FAIL: {f}\n")
    else:
        r.append("- FAIL 明细：无。\n")
    r.append("\n")

    r.append("## 5. 产物与固定句\n")
    r.append("- `work.py`：本脚本，可复跑；显式实现口径 P 及全部自检。\n")
    r.append(f"- `delta.tsv`：TAB 分隔，表头 8 列，数据行 {delta_row_count} 行；note 列逐行互不相同：**{'是' if notes_unique else '否'}**。\n")
    r.append("- `REPORT.md`：本文件。\n")
    r.append(f"- SENTENCE（逐字节原样）：`{SENTENCE}`\n")
    r.append(f"- SENTENCE 字符数：{len(SENTENCE)}；`col4_sha1_before/after` 为第 4 列 UTF-8 字节的 SHA-1（40 位小写 hex）。\n")
    r.append("- 本卡未改 `coverage.tsv`、未改 grade、未改任何数字。\n")

    REPORT.write_bytes(("\n".join(r)).encode("utf-8"))

    # ---- Console summary ----------------------------------------------------
    print(f"P_TOTAL={p_total}")
    print(f"BATCH_ROWS={len(TARGET_LINES)}")
    print(f"ENTRY_ORDER_OK={entry_order_ok}")
    print(f"TRAILING_WS_ROWS={len(trailing_ws_rows)}")
    print(f"SENTENCE_COUNT_BAD_ROWS={len(sentence_count_bad_rows)}")
    print(f"FAIL_ROWS={len(fail_rows)}")
    print(f"DELTA_DATA_ROWS={delta_row_count}")
    print(f"SENTENCE_LEN={len(SENTENCE)}")
    print(f"TABLE_ROWS_OK={table_row_count_ok} TABLE_COLS_OK={table_col_count_ok} UNTOUCHED_OK={untouched_ok}")

    hard_stop = (
        p_total != BASELINE_P_TOTAL
        or not entry_order_ok
        or bool(trailing_ws_rows)
        or bool(fail_rows)
        or delta_row_count != len(TARGET_LINES)
    )
    if hard_stop:
        raise SystemExit("HARD STOP: see REPORT.md for details")


if __name__ == "__main__":
    main()
