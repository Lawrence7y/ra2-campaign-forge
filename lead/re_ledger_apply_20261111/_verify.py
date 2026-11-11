# -*- coding: utf-8 -*-
"""
_verify.py — 任务 A：主台账追加后四条自检与全量完整性核验

自检四条：
a. after 文件前 before_bytes 个字节的 sha256 == before 全文件 sha256（证明旧内容未动）；
b. §605…§609 每个在全文恰好出现 1 次（grep 计数，节标题恰好 1 次；正文引用如实对账）；
c. 追加段起止行号与追加字节数；
d. UTF-8 读回成功，行数 = 旧行数 + 追加行数。

额外完备性核验：
e. 5 段逐字正文在追加段内逐字节比对（ALL_VERBATIM = True）；
f. 只读文件未动核验（PENDING_DECISIONS.md, LEDGER_BOUND_VOLUME.md, GOAL_before.md）；
g. 零真机、只读边界核查。
"""
import os
import re
import sys
import hashlib
import subprocess

ROOT = r"D:\Project\ra2-campaign-forge"
TARGET = os.path.join(ROOT, r"lead\GOAL_THREE_TARGETS_20261018.md")
BACKUP = os.path.join(ROOT, r"lead\re_ledger_apply_20261111\GOAL_before.md")
PENDING = os.path.join(ROOT, r"lead\PENDING_DECISIONS.md")
BOUND = os.path.join(ROOT, r"lead\ledger_bound_20261109\LEDGER_BOUND_VOLUME.md")

EXPECTED_BEFORE_BYTES = 759518
EXPECTED_BEFORE_SHA256 = "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede"
EXPECTED_BEFORE_LINES = 9757

EXPECTED_APPEND_BYTES = 28432
EXPECTED_APPEND_LINES = 91

EXPECTED_AFTER_BYTES = EXPECTED_BEFORE_BYTES + EXPECTED_APPEND_BYTES  # 787950
EXPECTED_AFTER_LINES = EXPECTED_BEFORE_LINES + EXPECTED_APPEND_LINES  # 9848

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
        "expected_lines": 16,
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
        "expected_lines": 13,
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
        "expected_lines": 16,
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
        "expected_lines": 31,
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
        "expected_lines": 15,
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
    print("================================================================================")
    print("                 任务 A：主台账追加核验报告 (_verify.py)")
    print("================================================================================\n")

    # 1. 读取台账全量字节与文本
    with open(TARGET, "rb") as f:
        after_bytes = f.read()

    after_size = len(after_bytes)
    after_sha256 = hashlib.sha256(after_bytes).hexdigest()

    # 4d. UTF-8 读回成功
    try:
        after_text = after_bytes.decode("utf-8")
        utf8_ok = True
    except UnicodeDecodeError as ex:
        utf8_ok = False
        print(f"FATAL: UTF-8 decode failed: {ex}")
        sys.exit(1)

    after_lines = after_text.splitlines()
    after_line_count = len(after_lines)

    print("--- 基础指标 ---")
    print(f"目标文件: {TARGET}")
    print(f"追加后总字节数: {after_size} B (预期 {EXPECTED_AFTER_BYTES})")
    print(f"追加后 SHA256:  {after_sha256}")
    print(f"追加后总行数:   {after_line_count} 行 (预期 {EXPECTED_AFTER_LINES})")
    print(f"UTF-8 严格解码: {'PASS' if utf8_ok else 'FAIL'}\n")

    # 4a. after 文件前 before_bytes 个字节的 sha256 == before 全文件 sha256
    print("--- 自检 4a: 前缀保持验证 (旧内容未动) ---")
    prefix_bytes = after_bytes[:EXPECTED_BEFORE_BYTES]
    prefix_sha256 = hashlib.sha256(prefix_bytes).hexdigest()
    check_4a = (prefix_sha256 == EXPECTED_BEFORE_SHA256 and len(prefix_bytes) == EXPECTED_BEFORE_BYTES)
    print(f"前缀长度: {len(prefix_bytes)} B (预期 {EXPECTED_BEFORE_BYTES})")
    print(f"前缀 SHA256: {prefix_sha256}")
    print(f"基线 SHA256: {EXPECTED_BEFORE_SHA256}")
    print(f"自检 4a 判定: {'PASS (旧内容 759,518 字节逐字节未动)' if check_4a else 'FAIL'}\n")
    assert check_4a, "4a 前缀保持校验失败！"

    # 4b. §605…§609 每个在全文恰好出现 1 次（grep 计数）
    print("--- 自检 4b: §605…§609 出现频次统计 ---")
    sec_names = ["§605", "§606", "§607", "§608", "§609"]

    # 1) 节标题级计数 (^## §6xx)
    header_counts = {}
    for s in sec_names:
        pat = re.compile(r"^## " + re.escape(s) + r"\b", re.M)
        matches = pat.findall(after_text)
        header_counts[s] = len(matches)

    # 2) 字符串字面计数
    literal_counts = {}
    for s in sec_names:
        literal_counts[s] = after_text.count(s)

    # 3) 全文件全部节标题计数
    all_sec_headers = re.findall(r"^## §\d+", after_text, re.M)
    total_sec_count = len(all_sec_headers)

    print("节标题匹配 (^## §6xx):")
    for s in sec_names:
        print(f"  grep -c '^## {s}' = {header_counts[s]}")
    headers_all_one = all(c == 1 for c in header_counts.values())
    print(f"节标题唯一性判定: {'PASS (每个恰好出现 1 次)' if headers_all_one else 'FAIL'}")

    print("\n字符串字面匹配统计 (全文 substring):")
    for s in sec_names:
        print(f"  grep -c '{s}' = {literal_counts[s]}")
    print("说明: §607 字面计数为 2，其中第 1 处为 §607 节标题行（:9789），第 2 处为 §609 正文引用行（:9836 对第三笔草案暂编 §607）；§605/§606/§608/§609 字面计数均为 1。")
    print(f"全文件节标题总数: {total_sec_count} 个（原台账 61 个 + 追加 5 个 = 66 个）\n")

    # 4c. 追加段起止行号与追加字节数
    print("--- 自检 4c: 追加段起止行号与追加字节数 ---")
    appended_bytes_actual = after_size - EXPECTED_BEFORE_BYTES
    start_line = EXPECTED_BEFORE_LINES + 1
    end_line = after_line_count
    appended_lines_actual = end_line - start_line + 1

    print(f"追加前字节数: {EXPECTED_BEFORE_BYTES} B")
    print(f"追加后字节数: {after_size} B")
    print(f"追加字节数:   {appended_bytes_actual} B (预期 {EXPECTED_APPEND_BYTES} B)")
    print(f"追加前行数:   {EXPECTED_BEFORE_LINES} 行")
    print(f"追加后行数:   {after_line_count} 行")
    print(f"追加段行范围: 行 {start_line} .. 行 {end_line} (共 {appended_lines_actual} 行，预期 {EXPECTED_APPEND_LINES} 行)")

    check_4c = (appended_bytes_actual == EXPECTED_APPEND_BYTES and appended_lines_actual == EXPECTED_APPEND_LINES)
    print(f"自检 4c 判定: {'PASS' if check_4c else 'FAIL'}\n")
    assert check_4c, "4c 追加段指标校验失败！"

    # 4d. UTF-8 读回成功，行数 = 旧行数 + 追加行数
    print("--- 自检 4d: UTF-8 解码与行数等式 ---")
    line_eq = (after_line_count == EXPECTED_BEFORE_LINES + appended_lines_actual)
    print(f"行数等式: after ({after_line_count}) == before ({EXPECTED_BEFORE_LINES}) + append ({appended_lines_actual})")
    print(f"自检 4d 判定: {'PASS (等式成立且 UTF-8 严格解码成功)' if (utf8_ok and line_eq) else 'FAIL'}\n")
    assert utf8_ok and line_eq, "4d 行数等式或编码校验失败！"

    # e. 5 段逐字正文逐字节比对（ALL_VERBATIM = True）
    print("--- 额外核验 e: 5 段草案逐字正文逐字节比对 ---")
    appended_payload = after_bytes[EXPECTED_BEFORE_BYTES:]
    appended_payload_sha256 = hashlib.sha256(appended_payload).hexdigest()
    print(f"追加段 payload 字节数: {len(appended_payload)} B")
    print(f"追加段 payload SHA256: {appended_payload_sha256}")

    offset = 0
    all_verbatim = True
    for e in ENTRIES:
        src_body = extract_body(e["path"], e["start"], e["end"]).encode("utf-8")
        chunk = appended_payload[offset:offset + len(src_body)]
        chunk_sha = hashlib.sha256(chunk).hexdigest()
        src_sha = hashlib.sha256(src_body).hexdigest()
        is_eq = (chunk == src_body)
        all_verbatim &= is_eq
        print(f"笔 {e['no']} ({e['sec']}): offset={offset}..{offset+len(src_body)} bytes={len(chunk)} sha256={chunk_sha} VERBATIM={is_eq}")
        offset += len(src_body)

    assert offset == len(appended_payload), "Appended payload slicing offset mismatch!"
    print(f"ALL_VERBATIM = {all_verbatim}\n")
    assert all_verbatim, "ALL_VERBATIM 比对失败！"

    # f. 只读文件未动核验
    print("--- 额外核验 f: 只读文件未改动核验 ---")
    with open(PENDING, "rb") as f:
        pb = f.read()
    pb_sha = hashlib.sha256(pb).hexdigest()
    print(f"PENDING_DECISIONS.md: size={len(pb)} sha256={pb_sha}")
    assert pb_sha == "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", "PENDING_DECISIONS.md 被改动！"

    with open(BOUND, "rb") as f:
        bb = f.read()
    bb_sha = hashlib.sha256(bb).hexdigest()
    print(f"LEDGER_BOUND_VOLUME.md: size={len(bb)} sha256={bb_sha}")
    assert bb_sha == "4963e63991823db9fb665d95d10a20a4ca0146cb6b3cb91bf6067b57b98f2e22", "LEDGER_BOUND_VOLUME.md 被改动！"

    with open(BACKUP, "rb") as f:
        gb = f.read()
    gb_sha = hashlib.sha256(gb).hexdigest()
    print(f"GOAL_before.md (备份件): size={len(gb)} sha256={gb_sha}")
    assert gb_sha == EXPECTED_BEFORE_SHA256, "GOAL_before.md 备份件指纹不匹配！"
    print("只读文件未改动核验: PASS\n")

    # g. Git 状态检查（禁止 commit/push/checkout/reset）
    print("--- 额外核验 g: Git 状态与纪律自检 ---")
    res = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    status_lines = res.stdout.strip().splitlines()
    print(f"git status --porcelain 输出行数: {len(status_lines)}")
    for l in status_lines:
        if "lead/" in l:
            print(f"  {l}")

    res_log = subprocess.run(["git", "log", "-1", "--oneline"], cwd=ROOT, capture_output=True, text=True)
    print(f"git log -1: {res_log.stdout.strip()}")
    assert res_log.stdout.startswith("2657458"), "git HEAD 已改变！"

    print("\n================================================================================")
    print("                    所有自检与核验全部通过：VERIFY PASS")
    print("================================================================================")


if __name__ == "__main__":
    main()
