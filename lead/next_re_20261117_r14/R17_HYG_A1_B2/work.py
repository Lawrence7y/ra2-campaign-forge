#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R17-HYG-A1-B2 executor (re-runnable).

Reads ONLY  lead/next_re_20261117_r14/COVERAGE/coverage.tsv
Writes ONLY lead/next_re_20261117_r14/R17_HYG_A1_B2/{delta.tsv,REPORT.md}

This card never writes coverage.tsv / grade / any number.
"""
import hashlib
import os
import re

# ---------------------------------------------------------------- paths ----
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SRC = os.path.join(ROOT, "lead", "next_re_20261117_r14", "COVERAGE", "coverage.tsv")
DELTA = os.path.join(HERE, "delta.tsv")
REPORT = os.path.join(HERE, "REPORT.md")

# ------------------------------------------------------------- constants ---
# Verbatim sentence from the card. Length must be exactly 65 characters.
SENTENCE = "（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）"
LEN_SENTENCE = 65
BASELINE_P = 91
BASELINE_ROWS = 18498
NCOLS = 8

# (physical line number in coverage.tsv, expected entry) -- ascending order.
TARGETS = [
    (5473, "0055A950"),
    (5474, "0055A970"),
    (5475, "0055A9B0"),
    (5476, "0055AA60"),
    (5478, "0055AB40"),
    (5506, "0055B880"),
    (5507, "0055BAA0"),
    (5873, "00597760"),
    (5875, "00597A30"),
    (5876, "00597D50"),
    (5877, "00597D60"),
    (5878, "00597F80"),
    (5879, "00597FA0"),
    (5880, "00597FC0"),
    (5955, "005AC270"),
    (6291, "005C0E90"),
]

# Per-line note: must be unique and mention this line's entry plus concrete
# content read from column 4 (Class::slotN / vt address / owning class).
NOTES = {
    5473: "0055A950：④ 见证 FlyLocomotionClass::slot1（vt=007E8AC0，槽1值=0055A950），行名 LocomotionClass::AddRef，同址另见 LocomotionClass vt=007EAEC0 slot1",
    5474: "0055A970：④ 见证 FlyLocomotionClass::slot2（vt=007E8AC0，槽2值=0055A970），行名 LocomotionClass::Release，同址另见 LocomotionClass vt=007EAEC0 slot2",
    5475: "0055A9B0：④ 见证 FlyLocomotionClass::slot0（vt=007E8AC0，槽0值=0055A9B0），行名 LocomotionClass::QueryInterface，同址另见 LocomotionClass vt=007EAEC0 slot0",
    5476: "0055AA60：④ 见证 FlyLocomotionClass::slot6（vt=007E8AC0，槽6值=0055AA60），行名 LocomotionClass::Save，同址另见 LocomotionClass vt=007EAEC0 slot6",
    5478: "0055AB40：④ 见证 DriveLocomotionClass::slot7（vt=007E7F7C，槽7值=0055AB40，COL=007FFEB0），行名 LocomotionClass::GetSizeMax，同址另见 LocomotionClass vt=007EAEC0 slot7",
    5506: "0055B880：④ 见证 LogicClass::slot10（vt=007E18FC，槽10值=0055B880），行名 MapClass::PointerGotInvalid；行名类 MapClass 无该槽，宿主 0040CB80 为 initterm 项 00812130、vt 写入 0087F778",
    5507: "0055BAA0：④ 见证 LogicClass::slot7（vt=007E18FC，槽7值=0055BAA0），行名 MapClass::AddObject；行名类 MapClass 无该槽，宿主 0040CB80 为 initterm 项 00812130、vt 写入 0087F778",
    5873: "00597760：④ 见证 MapSeedClass::slot2（vt=007ED8E4，槽2值=00597760），行名 MapSeedClass::SaveMission，表属类与行名类一致、无归属歧义",
    5875: "00597A30：④ 见证 MapSeedClass::slot1（vt=007ED8E4，槽1值=00597A30），行名 MapSeedClass::LoadMission，表属类与行名类一致、无归属歧义",
    5876: "00597D50：④ 见证 MapSeedClass::slot3（vt=007ED8E4，槽3值=00597D50），行名 MapSeedClass::DeleteMission，表属类与行名类一致、无归属歧义",
    5877: "00597D60：④ 见证 MapSeedClass::slot4（vt=007ED8E4，槽4值=00597D60），行名 MapSeedClass::GetFileEntry，表属类与行名类一致、无归属歧义",
    5878: "00597F80：④ 见证 MapSeedClass::slot5（vt=007ED8E4，槽5值=00597F80），行名 MapSeedClass::GetUIString_Load，表属类与行名类一致、无归属歧义",
    5879: "00597FA0：④ 见证 MapSeedClass::slot6（vt=007ED8E4，槽6值=00597FA0），行名 MapSeedClass::GetUIString_Save，表属类与行名类一致、无归属歧义",
    5880: "00597FC0：④ 见证 MapSeedClass::slot7（vt=007ED8E4，槽7值=00597FC0），行名 MapSeedClass::GetUIString_Delete，表属类与行名类一致、无归属歧义",
    5955: "005AC270：④ 见证 MapSeedClass::slot0（vt=007ED8E4，槽0值=005AC270），行名 MapSeedClass::MapSeedClass 构造函数本体，表属类与行名类一致",
    6291: "005C0E90：④ 见证 MultiplayerBattle::slot22（vt=007EE184，槽22值=005C0E90），行名 MPGameModeClass::vt_entry_58；行名类在本镜像无 RTTI 表，另见 MultiplayerGameMode vt=007EED60 slot22",
}

DELTA_HEADER = [
    "line", "entry", "col4_len_before", "col4_sha1_before",
    "col4_len_after", "col4_sha1_after", "appended_sentence", "note",
]


def sha1(text):
    """SHA-1 of the UTF-8 bytes of a str -> 40 lowercase hex chars."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def read_table():
    with open(SRC, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    lines = text.split("\n")
    return lines[0], lines[1:]  # header, data rows (physical line 2 ..)


def write_report(blocks):
    with open(REPORT, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(blocks).rstrip("\n") + "\n")


def main():
    header, data = read_table()

    # ---- structural facts -------------------------------------------------
    row_count = len(data)
    colcounts = sorted({len(r.split("\t")) for r in data})
    rows_all_8 = (colcounts == [NCOLS])

    # ---- 口径 P -----------------------------------------------------------
    # 第5列 == [已证] 且 第4列含 '④ 活表槽位见证' 且 第4列不含 '§12.6'
    p_rows = []
    for idx, row in enumerate(data):
        c = row.split("\t")
        if len(c) != NCOLS:
            continue
        if c[4] == "[已证]" and "④ 活表槽位见证" in c[3] and "§12.6" not in c[3]:
            p_rows.append((idx + 2, c[0]))  # physical line = data idx + 2
    p_total = len(p_rows)

    # ---- stop condition 1: 口径 P count ------------------------------------
    if p_total != BASELINE_P:
        write_report([
            "# R17-HYG-A1-B2 REPORT (STOPPED)",
            "",
            "## 停止原因：口径 P 全表总数与基线不符",
            "",
            f"- 基线：{BASELINE_P}",
            f"- 实测：{p_total}",
            f"- 差异：{p_total - BASELINE_P:+d}",
            "- 差异原因：脚本口径 P 与卡面基线不一致；按卡面要求停止，不自行调和。",
            f"- 数据行数：{row_count}；列数分布：{colcounts}",
            "",
            "本卡未改 `coverage.tsv`、未改 grade、未改任何数字。",
        ])
        print(f"STOP: 口径 P = {p_total} != {BASELINE_P}; see REPORT.md")
        return 1

    # ---- stop condition 2: target rows / entries --------------------------
    entry_mismatches = []
    for ln, expected in TARGETS:
        if ln - 2 < 0 or ln - 2 >= len(data):
            entry_mismatches.append((ln, expected, "<OUT OF RANGE>"))
            continue
        c = data[ln - 2].split("\t")
        if len(c) != NCOLS or c[0] != expected:
            entry_mismatches.append((ln, expected, c[0] if c else "<EMPTY>"))
    # also verify sorted ascending
    targets_sorted = TARGETS == sorted(TARGETS, key=lambda t: t[0])

    if entry_mismatches or not targets_sorted:
        lines_block = ["| line | expected | actual |", "|---|---|---|"]
        for ln, exp, act in entry_mismatches:
            lines_block.append(f"| {ln} | {exp} | {act} |")
        write_report([
            "# R17-HYG-A1-B2 REPORT (STOPPED)",
            "",
            "## 停止原因：本批 16 行与卡面清单不一致",
            "",
            f"- 行号升序：{'OK' if targets_sorted else 'FAIL'}",
            f"- 不一致行数：{len(entry_mismatches)}",
            "",
            *lines_block,
            "",
            f"- 口径 P 全表总数：{p_total}（基线 {BASELINE_P}）",
            "",
            "本卡未改 `coverage.tsv`、未改 grade、未改任何数字。",
        ])
        print("STOP: target entries mismatch; see REPORT.md")
        return 1

    # ---- trailing-whitespace scan (on the 16 col4 values) -----------------
    trailing_ws_lines = []
    for ln, _ in TARGETS:
        col4 = data[ln - 2].split("\t")[3]
        if re.search(r"\s$", col4):
            trailing_ws_lines.append(ln)

    # ---- build delta rows (in memory) -------------------------------------
    delta_rows = []
    for ln, entry in TARGETS:
        c = data[ln - 2].split("\t")
        old_col4 = c[3]
        new_col4 = old_col4 + SENTENCE
        delta_rows.append({
            "line": ln,
            "entry": entry,
            "col4_len_before": len(old_col4),
            "col4_sha1_before": sha1(old_col4),
            "col4_len_after": len(new_col4),
            "col4_sha1_after": sha1(new_col4),
            "appended_sentence": SENTENCE,
            "note": NOTES[ln],
            "_old_col4": old_col4,
            "_new_col4": new_col4,
            "_old_cols": c,
        })

    # ---- virtual application: simulate applying delta to an in-memory copy
    virtual = list(data)
    for d in delta_rows:
        idx = d["line"] - 2
        c = list(d["_old_cols"])
        c[3] = d["_new_col4"]
        virtual[idx] = "\t".join(c)

    # ---- per-line assertions a-e against the generated delta -------------
    fail_lines = []
    sentence_count_bad = []
    for d in delta_rows:
        ln = d["line"]
        old = d["_old_col4"]
        new = d["_new_col4"]
        vrow = virtual[ln - 2].split("\t")
        failed = []

        # a) new_col4 == old_col4 + SENTENCE, byte-for-byte
        if new.encode("utf-8") != (old + SENTENCE).encode("utf-8"):
            failed.append("a")
        if d["col4_sha1_after"] != sha1(new) or d["col4_len_after"] != len(new):
            failed.append("a-meta")

        # b) SENTENCE appears exactly once and at the end
        cnt = new.count(SENTENCE)
        if cnt != 1 or not new.endswith(SENTENCE):
            failed.append("b")
        if cnt != 1:
            sentence_count_bad.append(ln)

        # c) length difference exactly 65 characters
        if len(new) - len(old) != LEN_SENTENCE:
            failed.append("c")

        # d) other 7 columns byte-for-byte unchanged
        for i in (0, 1, 2, 4, 5, 6, 7):
            if vrow[i].encode("utf-8") != d["_old_cols"][i].encode("utf-8"):
                failed.append("d")
                break

        # e) whole-table structure preserved in virtual application
        if len(virtual) != BASELINE_ROWS or any(len(r.split("\t")) != NCOLS for r in virtual):
            failed.append("e")

        if failed:
            fail_lines.append((ln, ",".join(failed)))

    # note uniqueness guard
    notes_unique = len({d["note"] for d in delta_rows}) == len(delta_rows)
    entry_format_ok = all(
        len(d["entry"]) == 8 and d["entry"] == d["entry"].upper()
        and all(ch in "0123456789ABCDEF" for ch in d["entry"])
        and not d["entry"].startswith("0x")
        for d in delta_rows
    )
    sha_format_ok = all(
        len(d["col4_sha1_before"]) == 40 and len(d["col4_sha1_after"]) == 40
        and all(ch in "0123456789abcdef" for ch in d["col4_sha1_before"] + d["col4_sha1_after"])
        for d in delta_rows
    )

    # ---- write delta.tsv --------------------------------------------------
    with open(DELTA, "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(DELTA_HEADER) + "\n")
        for d in delta_rows:
            fh.write("\t".join([
                str(d["line"]), d["entry"],
                str(d["col4_len_before"]), d["col4_sha1_before"],
                str(d["col4_len_after"]), d["col4_sha1_after"],
                d["appended_sentence"], d["note"],
            ]) + "\n")

    # ---- write REPORT.md --------------------------------------------------
    fail_summary = "0 行" if not fail_lines else \
        ", ".join(f"line {ln} [{why}]" for ln, why in fail_lines)
    trailing_summary = "0 行" if not trailing_ws_lines else \
        ", ".join(str(ln) for ln in trailing_ws_lines)
    sent_bad_summary = "0 行" if not sentence_count_bad else \
        ", ".join(str(ln) for ln in sentence_count_bad)

    report = [
        "# R17-HYG-A1-B2 REPORT",
        "",
        "## FAIL 汇总（报告首段）",
        "",
        f"- FAIL 行数：**{len(fail_lines)}**",
        f"- 明细：{fail_summary}",
        "",
        "## 3.1 口径 P 全表总数",
        "",
        f"- 口径：第5列 == `[已证]` 且 第4列含 `④ 活表槽位见证` 且 第4列不含 `§12.6`",
        f"- 实测：**{p_total}**；基线：{BASELINE_P}；差异：{p_total - BASELINE_P:+d}（一致，未停止）",
        "",
        "## 3.2 本批 16 行 entry 一致性",
        "",
        f"- 本批行数：**{len(TARGETS)}**（基线 16）",
        f"- 物理行号升序：{'一致' if targets_sorted else 'FAIL'}",
        f"- 与卡面 entry 列表逐行一致：**{'是' if not entry_mismatches else '否'}**；不一致行数：{len(entry_mismatches)}",
        "",
        "## 3.3 行尾空白扫描（正则 `\\s$`，仅这 16 行第4列）",
        "",
        f"- 行尾空白行数：**{len(trailing_ws_lines)}**（基线 0）",
        f"- 明细：{trailing_summary}",
        "",
        "## 3.4 逐行断言（对生成的 delta 做断言，未改动盘上 coverage.tsv）",
        "",
        f"- a) `new_col4 == old_col4 + SENTENCE`（逐字节）：{'全部为真' if not any(x[1].startswith('a') for x in fail_lines) else '存在 FAIL'}",
        f"- b) SENTENCE 恰好出现 1 次且位于末尾：**出现次数 ≠1 的行数 = {len(sentence_count_bad)}**；明细：{sent_bad_summary}",
        f"- c) `len(new_col4) - len(old_col4) == {LEN_SENTENCE}`（字符数）：{'全部为真' if not any('c' in x[1].split(',') for x in fail_lines) else '存在 FAIL'}",
        f"- d) 其余 7 列逐字节不变：{'全部为真' if not any('d' in x[1].split(',') for x in fail_lines) else '存在 FAIL'}",
        f"- e) 整表数据行数仍为 {BASELINE_ROWS}、每行仍为 {NCOLS} 列：实测行数 {row_count}，列数分布 {colcounts}，全 8 列 = {rows_all_8}；虚拟应用后仍为 {len(virtual)} 行 / 全 8 列 = {all(len(r.split(chr(9))) == NCOLS for r in virtual)}",
        "",
        "## 其它自检",
        "",
        f"- `len(SENTENCE)` = {len(SENTENCE)}（基线 {LEN_SENTENCE}）",
        f"- delta 数据行数：**{len(delta_rows)}**；列数：{len(DELTA_HEADER)}",
        f"- note 逐行互不相同：{notes_unique}",
        f"- entry 为 8 位大写十六进制且不带 0x：{entry_format_ok}",
        f"- sha1 为 40 位小写 hex：{sha_format_ok}",
        f"- SHA-1 口径：对第4列 str 的 UTF-8 字节求 sha1，取 40 位小写 hex",
        "",
        "## 自证",
        "",
        "本卡未改 `coverage.tsv`、未改 grade、未改任何数字。",
    ]
    write_report(report)

    print(f"口径 P 全表总数: {p_total}")
    print(f"本批行数: {len(TARGETS)}")
    print(f"FAIL 行数: {len(fail_lines)}")
    print(f"行尾空白行数: {len(trailing_ws_lines)}")
    print(f"SENTENCE 出现次数 !=1 的行数: {len(sentence_count_bad)}")
    print(f"delta 行数: {len(delta_rows)}")
    return 0 if not fail_lines else 2


if __name__ == "__main__":
    raise SystemExit(main())
