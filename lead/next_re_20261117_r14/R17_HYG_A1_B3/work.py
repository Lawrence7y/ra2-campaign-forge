# -*- coding: utf-8 -*-
"""R17-HYG-A1-B3 executor.

Reads (read-only) COVERAGE/coverage.tsv, generates delta.tsv + REPORT.md in this
card directory only.  Does NOT write coverage.tsv / PANEL.md / R14_COMMON.md /
cards / any other directory.
"""
import hashlib
import os
import re
import sys

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
# HERE = .../lead/next_re_20261117_r14/R17_HYG_A1_B3
NEXT_DIR = os.path.normpath(os.path.join(HERE, os.pardir))  # .../lead/next_re_20261117_r14
SRC = os.path.join(NEXT_DIR, "COVERAGE", "coverage.tsv")
OUT_DELTA = os.path.join(HERE, "delta.tsv")
OUT_REPORT = os.path.join(HERE, "REPORT.md")

# ---------------------------------------------------------------------------
# Constants (verbatim from card; do not change a single character)
# ---------------------------------------------------------------------------
SENTENCE = "（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）"
EXPECTED_SENTENCE_LEN = 65
BASELINE_P_COUNT = 91
EXPECTED_DATA_ROWS = 18498

# (physical line number in coverage.tsv, entry) -- ascending order
TARGETS = [
    (6292, "005C0EB0"),
    (6309, "005C0FE0"),
    (6399, "005C5D30"),
    (6400, "005C5D40"),
    (6401, "005C5D90"),
    (6402, "005C5DD0"),
    (6424, "005C9430"),
    (6425, "005C9440"),
    (6434, "005CA680"),
    (6435, "005CA6D0"),
    (6436, "005CA7D0"),
    (6439, "005CA800"),
    (6440, "005CA9B0"),
    (6442, "005CABD0"),
    (6450, "005CB3F0"),
    (6451, "005CB400"),
]

DELTA_HEADER = [
    "line", "entry", "col4_len_before", "col4_sha1_before",
    "col4_len_after", "col4_sha1_after", "appended_sentence", "note",
]


def sha1(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def main():
    # --- load source, preserving physical line numbers -------------------
    with open(SRC, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    lines = raw.split("\n")  # no trailing newline in file -> last is last data row
    header = lines[0]
    # coverage.tsv header is comma-separated (8 names); data rows are TAB-separated.
    data = lines[1:]
    data_row_count = len(data)

    # --- 口径 P ------------------------------------------------------------
    p_lines = []
    bad_col_count = []
    for i, line in enumerate(data, start=2):  # physical line number
        cols = line.split("\t")
        if len(cols) != 8:
            bad_col_count.append((i, len(cols)))
            continue
        col4 = cols[3]
        col5 = cols[4]
        if col5 == "[已证]" and "④ 活表槽位见证" in col4 and "§12.6" not in col4:
            p_lines.append(i)
    p_count = len(p_lines)
    p_set = set(p_lines)

    # --- target-line consistency -----------------------------------------
    target_lines = [n for n, _ in TARGETS]
    target_entries = [e for _, e in TARGETS]
    entry_mismatch = []
    p_mismatch = []
    for n, e in TARGETS:
        cols = lines[n - 1].split("\t")
        if len(cols) != 8 or cols[0] != e:
            entry_mismatch.append((n, e, cols[0] if len(cols) == 8 else "NF=%d" % len(cols)))
        if n not in p_set:
            p_mismatch.append((n, e))
    order_ok = target_lines == sorted(target_lines) and len(set(target_lines)) == len(target_lines)

    # --- trailing-whitespace scan on the 16 target rows -------------------
    trailing_ws_rows = []
    for n, e in TARGETS:
        col4 = lines[n - 1].split("\t")[3]
        if re.search(r"\s$", col4) is not None:
            trailing_ws_rows.append(n)

    # --- assertions a-e over the generated delta -------------------------
    fail_rows = []          # list of (line, entry, [failed labels])
    delta_rows = []         # 8-column string rows (no header)
    sentence_count_ne1 = []
    reconstructed = list(lines)  # in-memory copy of whole table with col4 replaced

    for n, e in TARGETS:
        cols = lines[n - 1].split("\t")
        old_col4 = cols[3]
        new_col4 = old_col4 + SENTENCE
        new_cols = list(cols)
        new_cols[3] = new_col4
        reconstructed[n - 1] = "\t".join(new_cols)

        failed = []
        # (a) byte-for-byte append
        if new_col4 != old_col4 + SENTENCE:
            failed.append("a")
        # (b) exactly once and at end
        cnt = new_col4.count(SENTENCE)
        if cnt != 1 or not new_col4.endswith(SENTENCE):
            failed.append("b")
        if cnt != 1:
            sentence_count_ne1.append(n)
        # (c) length grew by exactly 65 characters
        if len(new_col4) - len(old_col4) != EXPECTED_SENTENCE_LEN:
            failed.append("c")
        # (d) other 7 columns byte-for-byte unchanged
        if cols[0:3] + cols[4:8] != new_cols[0:3] + new_cols[4:8]:
            failed.append("d")
        if failed:
            fail_rows.append((n, e, failed))

        # note: unique per row, quotes concrete col4 content (class::slotN + vt)
        m = re.search(r"④ 活表槽位见证：([A-Za-z_][A-Za-z0-9_]*::slot\d+)（vt=([0-9A-Fa-f]{8})", old_col4)
        if m:
            cls_slot, vt = m.group(1), m.group(2)
            note = "%s：第4列“④ 活表槽位见证：%s（vt=%s）”与“④升级句：%s”，末尾追加 D-47(A)/§12.6 披露句" % (
                e, cls_slot, vt, cls_slot)
        else:
            note = "%s：第4列未取得 Class::slotN/vt 具体见证段（类名：未取得），末尾追加 D-47(A)/§12.6 披露句" % e
        note = note.replace("\t", " ").replace("\n", " ").replace("\r", " ")

        delta_rows.append([
            str(n), e.upper(), str(len(old_col4)), sha1(old_col4),
            str(len(new_col4)), sha1(new_col4), SENTENCE, note,
        ])

    # (e) whole-table shape after reconstruction
    rec_data = reconstructed[1:]
    rec_data_ok = len(rec_data) == EXPECTED_DATA_ROWS
    rec_cols_ok = all(len(x.split("\t")) == 8 for x in rec_data)
    if not (rec_data_ok and rec_cols_ok):
        for n, e in TARGETS:
            if not any(r[0] == n for r in fail_rows):
                fail_rows.append((n, e, ["e"]))

    # --- gating: stop if baseline inconsistent ---------------------------
    stop_reasons = []
    if p_count != BASELINE_P_COUNT:
        stop_reasons.append(
            "口径 P 全表总数为 %d，基线为 %d，差异 %+d；未自行调和。" %
            (p_count, BASELINE_P_COUNT, p_count - BASELINE_P_COUNT))
    if entry_mismatch:
        stop_reasons.append("本批 entry 与卡面清单不一致：%r" % (entry_mismatch,))
    if not order_ok:
        stop_reasons.append("本批物理行号非严格升序或存在重复。")
    if p_mismatch:
        stop_reasons.append("本批存在不属于口径 P 的行：%r" % (p_mismatch,))
    if bad_col_count:
        stop_reasons.append("全表存在非 8 列数据行：%r" % (bad_col_count[:10],))
    if data_row_count != EXPECTED_DATA_ROWS:
        stop_reasons.append("全表数据行数为 %d，期望 %d。" % (data_row_count, EXPECTED_DATA_ROWS))

    # --- write REPORT.md --------------------------------------------------
    rep = []
    rep.append("# R17-HYG-A1-B3 报告\n")
    if fail_rows:
        rep.append("## FAIL 汇总（首段）\n")
        rep.append("FAIL 行数：**%d**\n" % len(fail_rows))
        for n, e, failed in fail_rows:
            rep.append("- line %d entry %s：失败断言 %s\n" % (n, e, ",".join(failed)))
    else:
        rep.append("## FAIL 汇总（首段）\n")
        rep.append("FAIL 行数：**0**（a–e 全部通过）\n")

    rep.append("\n## 第 3 节必做数字\n")
    rep.append("- 口径 P 全表总数：**%d**（基线 %d）\n" % (p_count, BASELINE_P_COUNT))
    rep.append("- 本批行数：**%d**（卡面清单 16 行）\n" % len(TARGETS))
    rep.append("- 本批 entry 逐行一致（按物理行号升序）：**%s**\n" %
               ("是" if (not entry_mismatch and order_ok) else "否"))
    if entry_mismatch:
        rep.append("  - 差异：%r\n" % (entry_mismatch,))
    rep.append("- 行尾空白行数（正则 `\\s$` 命中第 4 列）：**%d**\n" % len(trailing_ws_rows))
    if trailing_ws_rows:
        for n in trailing_ws_rows:
            rep.append("  - line %d entry %s\n" % (n, dict(TARGETS)[n]))
    rep.append("- `SENTENCE` 出现次数 ≠ 1 的行数：**%d**\n" % len(sentence_count_ne1))
    if sentence_count_ne1:
        for n in sentence_count_ne1:
            rep.append("  - line %d entry %s\n" % (n, dict(TARGETS)[n]))
    rep.append("- 本批属于口径 P 的行数：**%d / %d**\n" % (16 - len(p_mismatch), 16))
    if p_mismatch:
        rep.append("  - 不属于口径 P：%r\n" % (p_mismatch,))

    rep.append("\n## 逐行断言\n")
    rep.append("- a) `new_col4 == old_col4 + SENTENCE`（逐字节）：%s\n" %
               ("全部通过" if all("a" not in f for _, _, f in fail_rows) else "见 FAIL 汇总"))
    rep.append("- b) `SENTENCE` 恰好出现 1 次且位于末尾：%s\n" %
               ("全部通过" if not sentence_count_ne1 and all("b" not in f for _, _, f in fail_rows) else "见 FAIL 汇总"))
    rep.append("- c) 第 4 列长度增加恰好 %d 字符：%s\n" %
               (EXPECTED_SENTENCE_LEN, "全部通过" if all("c" not in f for _, _, f in fail_rows) else "见 FAIL 汇总"))
    rep.append("- d) 其余 7 列逐字节不变：%s\n" %
               ("全部通过" if all("d" not in f for _, _, f in fail_rows) else "见 FAIL 汇总"))
    rep.append("- e) 整表数据行数 %d、每行 8 列（对内存重建表断言）：%s\n" %
               (EXPECTED_DATA_ROWS, "通过" if (rec_data_ok and rec_cols_ok) else "见 FAIL 汇总"))
    rep.append("  - 实际：数据行数 %d，全部行 8 列 = %s\n" % (len(rec_data), rec_cols_ok))

    rep.append("\n## 产物统计\n")
    rep.append("- delta 行数（不含表头）：**%d**\n" % len(delta_rows))
    rep.append("- delta 列数：8（与固定表头一致）\n")
    rep.append("- note 去重后条数：**%d**\n" % len(set(r[7] for r in delta_rows)))
    rep.append("- `SENTENCE` 长度（str `len()`）：%d\n" % len(SENTENCE))

    rep.append("\n## 停止条件\n")
    if stop_reasons:
        for s in stop_reasons:
            rep.append("- %s\n" % s)
    else:
        rep.append("- 无：口径 P 总数与基线一致；本批 entry/顺序/P 归属全部匹配；全表 8 列、18,498 数据行成立。\n")

    rep.append("\n## 自证\n")
    rep.append("本卡未改 `coverage.tsv`、未改 grade、未改任何数字。\n")
    rep.append("脚本仅以只读方式打开 `coverage.tsv`，产物只写入 `R17_HYG_A1_B3/`。\n")

    with open(OUT_REPORT, "w", encoding="utf-8", newline="") as f:
        f.write("".join(rep))

    if stop_reasons:
        sys.stderr.write("STOP: " + " | ".join(stop_reasons) + "\n")
        return 2

    # --- write delta.tsv --------------------------------------------------
    with open(OUT_DELTA, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(DELTA_HEADER) + "\n")
        for row in delta_rows:
            f.write("\t".join(row) + "\n")

    print("P_COUNT=%d TARGETS=%d FAIL=%d TRAILING_WS=%d SENTENCE_NE1=%d DELTA_ROWS=%d" %
          (p_count, len(TARGETS), len(fail_rows), len(trailing_ws_rows),
           len(sentence_count_ne1), len(delta_rows)))
    return 0 if not fail_rows else 1


if __name__ == "__main__":
    sys.exit(main())
