# -*- coding: utf-8 -*-
"""
_apply.py — 任务 A：把五笔待入账草案（§605–§609）二进制末尾追加并入主台账

铁律遵守：
- 零真机：不启动 gamemd.exe / ra2loader / YURI.exe，不 attach、不读活进程内存，不写 hook/采样代码。
- 只读边界：除写域外一律只读；禁止 git commit / push / reset / checkout；不得覆盖既有件。
- 二进制末尾追加：使用 open(TARGET, 'ab') 进行 append-only 写入，既有前缀 759518 字节逐字节不动。
- 正文逐字照抄：5 段正文由单件草案源件按标记行字节切片提取，未润色、未改写（ALL_VERBATIM = True）。
- Python 一律 python -I -X utf8 <绝对路径>；指纹用 hashlib 实算。
"""
import os
import sys
import hashlib

ROOT = r"D:\Project\ra2-campaign-forge"
TARGET = os.path.join(ROOT, r"lead\GOAL_THREE_TARGETS_20261018.md")
BACKUP = os.path.join(ROOT, r"lead\re_ledger_apply_20261111\GOAL_before.md")

EXPECTED_BEFORE_BYTES = 759518
EXPECTED_BEFORE_SHA256 = "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede"
EXPECTED_BEFORE_LINES = 9757

ENTRIES = [
    {
        "no": 1,
        "sec": "§605",
        "title": "N-9:205 P6 前提订正 → 半闭半开",
        "path": os.path.join(ROOT, r"lead\ledger_appendix_20261108\_la_draft1_n9_p6_erratum.md"),
        "start": "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓",
        "end": "## ↑↑↑ 草案正文结束 ↑↑↑",
        "expected_bytes": 4735,
        "expected_sha256": "5c37adc6e64dd245b3392ed554a2185b489ab683496b9b223b6622af4bc86a6c",
    },
    {
        "no": 2,
        "sec": "§606",
        "title": "O1–O4 必要性补证 necessaryCount=3",
        "path": os.path.join(ROOT, r"lead\ledger_appendix_20261108\_la_draft2_o4_necessity.md"),
        "start": "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓",
        "end": "## ↑↑↑ 草案正文结束 ↑↑↑",
        "expected_bytes": 4097,
        "expected_sha256": "030f5a62328ec661c814f531ff5e54f43db2ac7c8cbd88d4e8d1050c9961bdc6",
    },
    {
        "no": 3,
        "sec": "§607",
        "title": "§604「空档/空档差」两列不可复现（0/15、15 窗全正）",
        "path": os.path.join(ROOT, r"lead\ledger_appendix_20261108\_la_draft3_s604_gapdiff.md"),
        "start": "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓",
        "end": "## ↑↑↑ 草案正文结束 ↑↑↑",
        "expected_bytes": 4894,
        "expected_sha256": "e9842d41f27d70b80067c5a6b89afe81ab63eb0422c7eda741d1c5983a3df698",
    },
    {
        "no": 4,
        "sec": "§608",
        "title": "「以乙替代甲」补登（九 hunk + 11 件指纹，登记而非放行）",
        "path": os.path.join(ROOT, r"lead\ledger_appendix_20261108\_la_draft4_yi_supersede_jia.md"),
        "start": "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓",
        "end": "## ↑↑↑ 草案正文结束 ↑↑↑",
        "expected_bytes": 6318,
        "expected_sha256": "24a497e8f63aece592a7a863cdb7d03a93d438dfa3f657dba1c1aaca260b775b",
    },
    {
        "no": 5,
        "sec": "§609",
        "title": "§604 码形定谳：错误源 = 撰写轮内联脚本 dur 字典错位（等价 C8a）",
        "path": os.path.join(ROOT, r"lead\s604_verdict_entry_20261109\_ve_DRAFT_S609.md"),
        "start": "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓",
        "end": "## ↑↑↑ 草案正文结束 ↑↑↑",
        "expected_bytes": 8388,
        "expected_sha256": "f4c3433a0141afbc59da7b72fdf679aacbae8b0ed9276530089a6a6528501682",
    },
]


def extract_body(path, start_marker, end_marker):
    with open(path, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    lines = text.split("\n")
    si = None
    ei = None
    for i, ln in enumerate(lines):
        if ln.strip() == start_marker.strip() and si is None:
            si = i
        if ln.strip() == end_marker.strip() and si is not None and ei is None:
            ei = i
    if si is None or ei is None or ei <= si:
        raise RuntimeError(f"Markers not found in {path}")
    body = "\n".join(lines[si + 1:ei])
    return body


def main():
    print("=== STEP 0: 校验前置基线 ===")
    with open(TARGET, "rb") as f:
        before_bytes = f.read()

    before_size = len(before_bytes)
    before_sha256 = hashlib.sha256(before_bytes).hexdigest()
    with open(TARGET, "r", encoding="utf-8") as f:
        before_lines = f.readlines()
    before_line_count = len(before_lines)

    print(f"Target file: {TARGET}")
    print(f"Before size: {before_size} (expected {EXPECTED_BEFORE_BYTES})")
    print(f"Before sha256: {before_sha256} (expected {EXPECTED_BEFORE_SHA256})")
    print(f"Before lines: {before_line_count} (expected {EXPECTED_BEFORE_LINES})")

    assert before_size == EXPECTED_BEFORE_BYTES, "Before size mismatch!"
    assert before_sha256 == EXPECTED_BEFORE_SHA256, "Before sha256 mismatch!"
    assert before_line_count == EXPECTED_BEFORE_LINES, "Before line count mismatch!"
    print("Pre-append baseline check: PASS\n")

    print("=== STEP 1: 提取 5 笔草案逐字正文并校验指纹 ===")
    payload_parts = []
    total_append_bytes = 0

    for e in ENTRIES:
        body = extract_body(e["path"], e["start"], e["end"])
        b_bytes = body.encode("utf-8")
        b_sha256 = hashlib.sha256(b_bytes).hexdigest()

        print(f"Entry {e['no']} ({e['sec']}):")
        print(f"  Source: {e['path']}")
        print(f"  Bytes: {len(b_bytes)} (expected {e['expected_bytes']})")
        print(f"  SHA256: {b_sha256}")

        assert len(b_bytes) == e["expected_bytes"], f"Bytes mismatch for {e['sec']}"
        assert b_sha256 == e["expected_sha256"], f"SHA256 mismatch for {e['sec']}"

        payload_parts.append(b_bytes)
        total_append_bytes += len(b_bytes)

    assert total_append_bytes == 28432, f"Total append bytes expected 28432, got {total_append_bytes}"
    print(f"All 5 drafts extracted verbatim: PASS (Total bytes={total_append_bytes})\n")

    full_payload = b"".join(payload_parts)
    payload_sha256 = hashlib.sha256(full_payload).hexdigest()
    payload_newlines = full_payload.count(b"\n")
    print(f"Combined payload bytes: {len(full_payload)}")
    print(f"Combined payload sha256: {payload_sha256}")
    print(f"Combined payload newlines: {payload_newlines}\n")

    print("=== STEP 2: 执行二进制末尾追加 (open ab) ===")
    with open(TARGET, "ab") as f:
        written = f.write(full_payload)
        f.flush()

    print(f"Successfully appended {written} bytes to {TARGET}\n")

    print("=== STEP 3: 追加后自检 ===")
    with open(TARGET, "rb") as f:
        after_bytes = f.read()

    after_size = len(after_bytes)
    after_sha256 = hashlib.sha256(after_bytes).hexdigest()
    with open(TARGET, "r", encoding="utf-8") as f:
        after_lines = f.readlines()
    after_line_count = len(after_lines)

    print(f"After size: {after_size}")
    print(f"After sha256: {after_sha256}")
    print(f"After lines: {after_line_count}")

    # Check 4a: Prefix preservation
    prefix_bytes = after_bytes[:before_size]
    prefix_sha256 = hashlib.sha256(prefix_bytes).hexdigest()
    assert prefix_sha256 == before_sha256, "PREFIX INTEGRITY FAILED!"
    print(f"Self-test 4a: after[0:{before_size}] sha256 == before sha256 -> PASS ({prefix_sha256})")

    # Check 4c: Line range and byte count
    start_line = before_line_count + 1
    end_line = after_line_count
    appended_bytes_actual = after_size - before_size
    appended_lines_actual = end_line - start_line + 1
    print(f"Self-test 4c: Appended lines = {start_line}..{end_line} ({appended_lines_actual} lines)")
    print(f"Self-test 4c: Appended bytes = {appended_bytes_actual} B")
    assert appended_bytes_actual == total_append_bytes, "Appended bytes mismatch!"
    assert appended_lines_actual == payload_newlines, "Appended lines count mismatch!"

    # Check 4d: UTF-8 readback and line equation
    assert after_line_count == before_line_count + payload_newlines, "Line count equation failed!"
    print(f"Self-test 4d: after_lines ({after_line_count}) == before_lines ({before_line_count}) + append_lines ({payload_newlines}) -> PASS")

    print("\n_apply.py COMPLETED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
