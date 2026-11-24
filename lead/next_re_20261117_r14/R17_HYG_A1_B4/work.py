#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R17-HYG-A1-B4  --  D-47(A) col4 disclosure append (16 rows).

Scope / absolute boundaries (from the card):
  * READ  : lead/next_re_20261117_r14/COVERAGE/coverage.tsv  (read-only)
            lead/next_re_20261117_r14/_cards/R17-HYG-A1-B4.md (read-only)
  * WRITE : ONLY lead/next_re_20261117_r14/R17_HYG_A1_B4/{delta.tsv,REPORT.md}
  * NEVER writes coverage.tsv / PANEL.md / R14_COMMON.md / ledger / cards / other dirs.
  * NEVER touches grade (col5) or any numeric column.
  * No reverse engineering, no gamemd.exe, no capstone/Ghidra/pefile.

The script implements criterion P explicitly, reproduces all baseline numbers,
builds the delta in memory, runs assertions a-e, then emits delta.tsv + REPORT.md.
"""
from pathlib import Path
import re
import hashlib
import sys

# ----------------------------------------------------------------------------
# paths (relative to this script, so it is re-runnable from any cwd)
# ----------------------------------------------------------------------------
HERE      = Path(__file__).resolve().parent
CARD_DIR  = HERE.parent                       # lead/next_re_20261117_r14
COVERAGE  = CARD_DIR / 'COVERAGE' / 'coverage.tsv'
CARD      = CARD_DIR / '_cards' / 'R17-HYG-A1-B4.md'
DELTA     = HERE / 'delta.tsv'
REPORT    = HERE / 'REPORT.md'

# ----------------------------------------------------------------------------
# exact sentence (byte-for-byte from the card's single fenced code block).
# Cross-checked against the card at runtime; len(str) must be 65.
# ----------------------------------------------------------------------------
SENTENCE = "（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）"

# physical line numbers in coverage.tsv (header = line 1), ascending + expected entry
BATCH = [
    (6452, '005CB430'),
    (6453, '005CB440'),
    (6454, '005CB540'),
    (6699, '005D5DE0'),
    (6704, '005D62C0'),
    (6711, '005D6370'),
    (6713, '005D6430'),
    (6715, '005D6450'),
    (6716, '005D64C0'),
    (6717, '005D6540'),
    (6719, '005D6690'),
    (6721, '005D6790'),
    (6724, '005D6890'),
    (6725, '005D6BE0'),
    (6726, '005D6C70'),
    (6728, '005D7030'),
]

BASELINE_P_TOTAL   = 91
BASELINE_DATA_ROWS = 18498
BASELINE_COLS      = 8

DELTA_HEADER = ('line', 'entry', 'col4_len_before', 'col4_sha1_before',
                'col4_len_after', 'col4_sha1_after', 'appended_sentence', 'note')

NOTE_TEMPLATES = [
    'entry={e}｜④ 槽位见证 {slot}，vt={vt}；本行按 D-47(A) 补 §12.6 尾注',
    '{e} 的 ④ 段读到 {slot}（vt={vt}），追加 D-47(A)/§12.6 披露',
    '行 {ln} / entry {e}：col4 标注 {slot}、vt={vt}，尾补 §12.6 裁决句',
    '{e}｜第4列给出 {slot} 与 vt={vt}；D-47(A) 披露写入末尾',
]


def sha1hex(s: str) -> str:
    """SHA-1 of the UTF-8 bytes of s, 40 lowercase hex chars."""
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


def main() -> int:
    global_errors = []          # non-row-specific setup/baseline errors

    # ---- cross-check SENTENCE with the card -------------------------------
    try:
        card_text = CARD.read_text(encoding='utf-8')
        blocks = re.findall(r'```[^\n]*\n(.*?)\n```', card_text, re.S)
        if len(blocks) != 1:
            global_errors.append(f'card fenced-block count = {len(blocks)} (expected 1)')
        elif blocks[0] != SENTENCE:
            global_errors.append('hardcoded SENTENCE differs from card fenced block')
    except Exception as exc:
        global_errors.append(f'cannot read card: {exc}')

    if len(SENTENCE) != 65:
        global_errors.append(f'len(SENTENCE) = {len(SENTENCE)} (expected 65)')

    # ---- read coverage.tsv as read-only -----------------------------------
    raw = COVERAGE.read_bytes()
    text = raw.decode('utf-8')
    if '\r' in text:
        global_errors.append(f'coverage.tsv contains {text.count(chr(13))} CR characters')
    all_lines = text.split('\n')
    header_line = all_lines[0]
    data = all_lines[1:]
    if data and data[-1] == '':
        data = data[:-1]        # file has no trailing newline; guard anyway

    if len(data) != BASELINE_DATA_ROWS:
        global_errors.append(f'data row count = {len(data)} (expected {BASELINE_DATA_ROWS})')

    bad_col_rows = [i for i, l in enumerate(data, start=2) if len(l.split('\t')) != BASELINE_COLS]
    if bad_col_rows:
        global_errors.append(f'{len(bad_col_rows)} rows are not {BASELINE_COLS} columns; '
                             f'first few: {bad_col_rows[:5]}')

    # ---- criterion P: explicit implementation -----------------------------
    #   第5列 == [已证]  AND  第4列 contains "④ 活表槽位见证"  AND  第4列 NOT contains "§12.6"
    p_rows = []                 # list of (physical_line, entry)
    for i, line in enumerate(data, start=2):
        cols = line.split('\t')
        if len(cols) != BASELINE_COLS:
            continue
        c4, c5 = cols[3], cols[4]
        if c5 == '[已证]' and '④ 活表槽位见证' in c4 and '§12.6' not in c4:
            p_rows.append((i, cols[0]))
    p_total = len(p_rows)
    if p_total != BASELINE_P_TOTAL:
        global_errors.append(f'criterion P total = {p_total} (expected {BASELINE_P_TOTAL})')

    p_line_set = {ln for ln, _ in p_rows}

    # ---- batch entry consistency (ascending physical line order) ---------
    batch_order = [ln for ln, _ in BATCH]
    batch_ascending = batch_order == sorted(batch_order)
    if not batch_ascending:
        global_errors.append('BATCH is not in ascending physical-line order')

    batch_mismatch = []         # (line, expected, actual)
    for ln, expected_entry in BATCH:
        if not (2 <= ln <= len(data) + 1):
            batch_mismatch.append((ln, expected_entry, '<out of range>'))
            continue
        actual_entry = data[ln - 2].split('\t')[0]
        if actual_entry != expected_entry:
            batch_mismatch.append((ln, expected_entry, actual_entry))
        if ln not in p_line_set:
            global_errors.append(f'batch line {ln} ({expected_entry}) is NOT in criterion P')

    # ---- trailing whitespace scan over the 16 rows' col4 ------------------
    trail_ws_lines = []
    for ln, _ in BATCH:
        if 2 <= ln <= len(data) + 1:
            c4 = data[ln - 2].split('\t')[3]
            if re.search(r'\s$', c4):
                trail_ws_lines.append(ln)

    # ---- build delta in memory + per-row assertions a-e -------------------
    new_data = list(data)       # full table in memory; only 16 col4 cells change
    delta_rows = []
    fail_lines = []
    sent_count_ne1_lines = []
    note_strings = []

    for idx, (ln, entry) in enumerate(BATCH):
        row_errs = []
        cols = data[ln - 2].split('\t')
        old4 = cols[3]
        new4 = old4 + SENTENCE

        # (a) byte-for-byte concatenation
        if new4.encode('utf-8') != old4.encode('utf-8') + SENTENCE.encode('utf-8'):
            row_errs.append('a')

        # (b) SENTENCE occurs exactly once and sits at the end
        cnt = new4.count(SENTENCE)
        if cnt != 1 or not new4.endswith(SENTENCE):
            row_errs.append('b')
            sent_count_ne1_lines.append(ln)

        # (c) str-length grows by exactly 65
        if len(new4) - len(old4) != 65:
            row_errs.append('c')

        # (d) the other 7 columns are byte-for-byte unchanged
        others_before = cols[:3] + cols[4:]
        new_cols = cols[:3] + [new4] + cols[4:]
        others_after = new_cols[:3] + new_cols[4:]
        if len(new_cols) != BASELINE_COLS or others_after != others_before:
            row_errs.append('d')
        # also verify via raw bytes of the untouched cells
        if '\t'.join(others_before).encode('utf-8') != '\t'.join(others_after).encode('utf-8'):
            row_errs.append('d-bytes')

        new_data[ln - 2] = '\t'.join(new_cols)

        # (e) global table invariants are checked after the loop
        if len(new_data) != len(data):
            row_errs.append('e-rows')

        # unique note: entry + concrete col4 content (slot / vt)
        slots = re.findall(r'[A-Za-z_][A-Za-z0-9_]*::slot\d+', old4)
        vts = re.findall(r'vt=([0-9A-F]{8})', old4)
        slot = slots[0] if slots else '未取得'
        vt = vts[0] if vts else '未取得'
        tmpl = NOTE_TEMPLATES[idx % len(NOTE_TEMPLATES)]
        note = tmpl.format(e=entry, ln=ln, slot=slot, vt=vt)
        if '\t' in note or '\n' in note or '\r' in note:
            row_errs.append('note-char')
        note_strings.append(note)

        if row_errs:
            fail_lines.append((ln, entry, ','.join(row_errs)))

        delta_rows.append((
            str(ln), entry,
            str(len(old4)), sha1hex(old4),
            str(len(new4)), sha1hex(new4),
            SENTENCE, note,
        ))

    # (e) whole-table invariants on the in-memory delta result
    e_errors = []
    if len(new_data) != BASELINE_DATA_ROWS:
        e_errors.append(f'new data row count = {len(new_data)}')
    bad_new = [i for i, l in enumerate(new_data, start=2) if len(l.split('\t')) != BASELINE_COLS]
    if bad_new:
        e_errors.append(f'{len(bad_new)} new rows not {BASELINE_COLS} cols')
    changed = [i for i in range(len(data)) if new_data[i] != data[i]]
    expected_changed = [ln - 2 for ln in batch_order]   # 0-based data indices
    if changed != expected_changed:
        e_errors.append(f'changed data indices {changed[:20]} != expected {expected_changed[:20]}')
    if e_errors:
        for ln, entry in BATCH:
            if all(ln != f[0] for f in fail_lines):
                fail_lines.append((ln, entry, 'e:' + ';'.join(e_errors)))

    # note uniqueness
    if len(set(note_strings)) != len(note_strings):
        global_errors.append('delta notes are not unique')

    # ---- write delta.tsv ---------------------------------------------------
    delta_text = '\t'.join(DELTA_HEADER) + '\n'
    for row in delta_rows:
        delta_text += '\t'.join(row) + '\n'
    DELTA.write_bytes(delta_text.encode('utf-8'))

    # ---- write REPORT.md ---------------------------------------------------
    r = []
    r.append('# R17-HYG-A1-B4 执行报告')
    r.append('')
    r.append('## 1. 口径 P 复现与基线数字')
    r.append('')
    r.append('筛选口径 P（脚本显式实现）：第 5 列 `== [已证]` 且第 4 列包含子串 `④ 活表槽位见证` '
             '且第 4 列**不**包含子串 `§12.6`。')
    r.append('')
    r.append('| 项目 | 本脚本实测 | 基线 | 结论 |')
    r.append('|---|---:|---:|---|')
    r.append(f'| 口径 P 全表总数 | {p_total} | {BASELINE_P_TOTAL} | {"OK" if p_total==BASELINE_P_TOTAL else "DIFF"} |')
    r.append(f'| 整表数据行数（表头除外） | {len(data)} | {BASELINE_DATA_ROWS} | {"OK" if len(data)==BASELINE_DATA_ROWS else "DIFF"} |')
    r.append(f'| 非 8 列的行数 | {len(bad_col_rows)} | 0 | {"OK" if not bad_col_rows else "DIFF"} |')
    r.append(f'| `len(SENTENCE)` (str) | {len(SENTENCE)} | 65 | {"OK" if len(SENTENCE)==65 else "DIFF"} |')
    r.append('')
    if p_total != BASELINE_P_TOTAL:
        r.append(f'**差异说明**：脚本筛得 {p_total} 行，与基线 {BASELINE_P_TOTAL} 不符，停止调和，'
                 '按卡面要求在此如实记录差异，不自行修正数据。')
        r.append('')
    r.append('## 2. 本批 16 行核对')
    r.append('')
    r.append(f'- 本批行数：{len(BATCH)}')
    r.append(f'- 物理行号按升序：{"是" if batch_ascending else "否"}')
    r.append(f'- entry 逐行一致（顺序按物理行号升序）：'
             f'{"是（16/16）" if not batch_mismatch else "否"}')
    if batch_mismatch:
        r.append('')
        r.append('| line | 期望 entry | 实际 entry |')
        r.append('|---|---|---|')
        for ln, exp, act in batch_mismatch:
            r.append(f'| {ln} | {exp} | {act} |')
        r.append('')
        r.append('**停止**：本批与清单不一致，已记录差异，未生成可用 delta。')
    r.append(f'- 16 行全部命中口径 P：{"是" if not global_errors or all("is NOT in criterion P" not in e for e in global_errors) else "否"}')
    r.append('')
    r.append('## 3. 行尾空白扫描')
    r.append('')
    r.append(f'- 全表扫描这 16 行第 4 列行尾空白（正则 `\\s$`）：**{len(trail_ws_lines)} 行**')
    if trail_ws_lines:
        r.append(f'- 命中物理行号：{trail_ws_lines}')
    r.append('')
    r.append('## 4. 逐行断言 a–e（对生成的 delta）')
    r.append('')
    r.append('- a) `new_col4 == old_col4 + SENTENCE`（逐字节）：逐行校验')
    r.append('- b) `SENTENCE` 在 `new_col4` 中恰好出现 1 次且位于末尾：逐行校验')
    r.append('- c) `len(new_col4) - len(old_col4) == 65`（`len()` on str）：逐行校验')
    r.append('- d) 其余 7 列逐字节不变：逐行校验')
    r.append('- e) 内存结果整表仍为 18,498 行 × 8 列，且仅这 16 行发生变化：整体校验')
    r.append('')
    r.append(f'- **FAIL 行数：{len(fail_lines)}**')
    if fail_lines:
        r.append('')
        r.append('| line | entry | failed assertions |')
        r.append('|---|---|---|')
        for ln, ent, errs in fail_lines:
            r.append(f'| {ln} | {ent} | {errs} |')
        r.append('')
    r.append(f'- `SENTENCE` 出现次数 ≠ 1 的行数：**{len(sent_count_ne1_lines)}**'
             + (f'（行号 {sent_count_ne1_lines}）' if sent_count_ne1_lines else ''))
    r.append(f'- delta 行数：**{len(delta_rows)}**')
    r.append('')
    r.append('> 说明：`col4_len_before/after` 采用 Python `len(str)`（Unicode 码点数），'
             '与断言 c) 的口径一致；`col4_sha1_before/after` 为第 4 列 UTF-8 字节的 SHA-1，40 位小写 hex。')
    r.append('')
    r.append('## 5. 全局错误汇总')
    r.append('')
    if global_errors or e_errors:
        for msg in global_errors + e_errors:
            r.append(f'- {msg}')
    else:
        r.append('- 0（无全局错误）')
    r.append('')
    r.append('## 6. 自证')
    r.append('')
    r.append('本卡未改 `coverage.tsv`、未改 grade、未改任何数字。')
    r.append('本卡只写 `lead\\next_re_20261117_r14\\R17_HYG_A1_B4\\` 目录内的 `delta.tsv` 与 `REPORT.md`。')
    r.append('')
    REPORT.write_text('\n'.join(r), encoding='utf-8')

    # ---- console summary (the 6 required numbers) -------------------------
    print('P_TOTAL', p_total)
    print('BATCH_ROWS', len(BATCH))
    print('FAIL_ROWS', len(fail_lines))
    print('TRAILING_WS_ROWS', len(trail_ws_lines))
    print('SENT_COUNT_NE1_ROWS', len(sent_count_ne1_lines))
    print('DELTA_ROWS', len(delta_rows))
    print('BATCH_MATCH', not batch_mismatch)
    print('GLOBAL_ERRORS', len(global_errors) + len(e_errors))

    return 0 if not (global_errors or e_errors or fail_lines or batch_mismatch) else 2


if __name__ == '__main__':
    sys.exit(main())
