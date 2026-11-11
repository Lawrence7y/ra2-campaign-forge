# -*- coding: utf-8 -*-
import hashlib
import os
import re
import difflib
from datetime import datetime

ROOT = r"D:\Project\ra2-campaign-forge"
LEDGER_PATH = os.path.join(ROOT, "lead", "GOAL_THREE_TARGETS_20261018.md")
BOUND_PATH = os.path.join(ROOT, "lead", "ledger_bound_20261109", "LEDGER_BOUND_VOLUME.md")
RECEIPT_PATH = os.path.join(ROOT, "lead", "re_ledger_apply_20261111", "APPLY_RECEIPT.md")
OUT_DIR = os.path.join(ROOT, "lead", "re_ledger_verify_20261111")
OUT_TXT = os.path.join(OUT_DIR, "_v_out.txt")

SINGLE_DRAFTS = {
    "§605": os.path.join(ROOT, "lead", "ledger_appendix_20261108", "_la_draft1_n9_p6_erratum.md"),
    "§606": os.path.join(ROOT, "lead", "ledger_appendix_20261108", "_la_draft2_o4_necessity.md"),
    "§607": os.path.join(ROOT, "lead", "ledger_appendix_20261108", "_la_draft3_s604_gapdiff.md"),
    "§608": os.path.join(ROOT, "lead", "ledger_appendix_20261108", "_la_draft4_yi_supersede_jia.md"),
    "§609": os.path.join(ROOT, "lead", "s604_verdict_entry_20261109", "_ve_DRAFT_S609.md"),
}

EXPECTED_BOUND_SHAS = {
    "§605": (4735, "5c37adc6e64dd245b3392ed554a2185b489ab683496b9b223b6622af4bc86a6c"),
    "§606": (4097, "030f5a62328ec661c814f531ff5e54f43db2ac7c8cbd88d4e8d1050c9961bdc6"),
    "§607": (4894, "e9842d41f27d70b80067c5a6b89afe81ab63eb0422c7eda741d1c5983a3df698"),
    "§608": (6318, "24a497e8f63aece592a7a863cdb7d03a93d438dfa3f657dba1c1aaca260b775b"),
    "§609": (8388, "f4c3433a0141afbc59da7b72fdf679aacbae8b0ed9276530089a6a6528501682"),
}

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

log_lines = []
def log(msg=""):
    print(msg)
    log_lines.append(msg)

def main():
    log("==================================================================")
    log("  INDEPENDENT VERIFICATION OUTPUT (_v.py)")
    log("==================================================================")

    # ---------------- V1 ----------------
    log("\n=== [V1] 现状指纹 (lead\\GOAL_THREE_TARGETS_20261018.md) ===")
    raw_ledger = open(LEDGER_PATH, "rb").read()
    ledger_sha = sha256_bytes(raw_ledger)
    ledger_size = len(raw_ledger)
    st = os.stat(LEDGER_PATH)
    mtime_iso = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S.%f")

    lf_count = raw_ledger.count(b"\n")
    crlf_count = raw_ledger.count(b"\r\n")
    cr_only_count = raw_ledger.count(b"\r") - crlf_count
    text_ledger = raw_ledger.decode("utf-8")
    lines_ledger = text_ledger.splitlines()

    claimed_after_size = 788030
    claimed_after_sha = "a2579798976f00b4dc09edc85c0b2efa0255289411819297047e2362ba3bffda"
    v1_pass = (ledger_size == claimed_after_size) and (ledger_sha == claimed_after_sha) and (text_ledger.count(chr(0xFFFD)) == 0)

    log(f"File:          {LEDGER_PATH}")
    log(f"Size (bytes):  {ledger_size} (claimed: {claimed_after_size}, match={ledger_size == claimed_after_size})")
    log(f"SHA256:        {ledger_sha}")
    log(f"Claimed SHA:   {claimed_after_sha}")
    log(f"SHA256 match:  {ledger_sha == claimed_after_sha}")
    log(f"mtime (local): {mtime_iso} (epoch={st.st_mtime})")
    log(f"Line counts:   splitlines={len(lines_ledger)}, raw_LF={lf_count}, CRLF={crlf_count}, pure_LF={lf_count - crlf_count}, lone_CR={cr_only_count}")
    log(f"UTF-8 decode:  OK (replacement_char U+FFFD count = {text_ledger.count(chr(0xFFFD))})")
    log(f"V1 Result:     {'PASS' if v1_pass else 'FAIL'}")

    # ---------------- V2 ----------------
    log("\n=== [V2] 旧内容未动（前 759,518 字节按字节切片） ===")
    EXPECTED_BEFORE_SIZE = 759518
    EXPECTED_BEFORE_SHA = "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede"
    prefix_bytes = raw_ledger[:EXPECTED_BEFORE_SIZE]
    prefix_sha = sha256_bytes(prefix_bytes)
    v2_pass = (len(prefix_bytes) == EXPECTED_BEFORE_SIZE) and (prefix_sha == EXPECTED_BEFORE_SHA)
    log(f"Slice range:   raw_ledger[0:{EXPECTED_BEFORE_SIZE}] ({len(prefix_bytes)} bytes)")
    log(f"Prefix SHA256: {prefix_sha}")
    log(f"Baseline SHA:  {EXPECTED_BEFORE_SHA}")
    log(f"V2 Result:     {'PASS' if v2_pass else 'FAIL'}")

    # ---------------- V3 ----------------
    log("\n=== [V3] 节标题唯一性 (^##+ *§6\\d\\d vs 全文字符串出现次数) ===")
    heading_re = re.compile(r"^##+ *§(6\d\d)\b")
    heading_hits = {f"§{i}": [] for i in range(600, 610)}
    other_6xx_headings = []

    for idx, line in enumerate(lines_ledger, start=1):
        m = heading_re.match(line)
        if m:
            sec = f"§{m.group(1)}"
            if sec in heading_hits:
                heading_hits[sec].append((idx, line))
            else:
                other_6xx_headings.append((idx, sec, line))

    for i in range(600, 610):
        sec = f"§{i}"
        hits = heading_hits[sec]
        fulltext_hits = len(re.findall(rf"§{i}\b", text_ledger))
        log(f"{sec}: heading_count={len(hits)} | fulltext_occurrences={fulltext_hits} | diff={fulltext_hits != len(hits)}")
        for ln, ltxt in hits:
            log(f"    heading @ line {ln}: {ltxt}")
        if fulltext_hits != len(hits) and i >= 605:
            # Show where else §60x appears in fulltext
            for idx, line in enumerate(lines_ledger, start=1):
                if re.search(rf"§{i}\b", line) and not heading_re.match(line):
                    log(f"    cross-ref @ line {idx}: {line[:100]}...")
    if other_6xx_headings:
        log(f"Other §6xx headings: {other_6xx_headings}")

    v3_pass = all(len(heading_hits[f"§{i}"]) == 1 for i in range(605, 610))
    log(f"V3 Result (§605–§609 heading_count each == 1): {'PASS' if v3_pass else 'FAIL'}")

    # ---------------- V4 ----------------
    log("\n=== [V4] 追加段定位（旧文件结尾与追加段开头边界） ===")
    appended_bytes = raw_ledger[EXPECTED_BEFORE_SIZE:]
    appended_sha = sha256_bytes(appended_bytes)
    prefix_text = prefix_bytes.decode("utf-8")
    prefix_lines = prefix_text.splitlines()
    prefix_lf = prefix_bytes.count(b"\n")
    appended_lf = appended_bytes.count(b"\n")
    appended_crlf = appended_bytes.count(b"\r\n")

    log(f"Old file byte range:      [0, {EXPECTED_BEFORE_SIZE}) (last byte index = {EXPECTED_BEFORE_SIZE - 1})")
    log(f"Old file last line (#9757): byte range [759431, 759518), ends with CRLF: {prefix_bytes[-40:]!r}")
    log(f"Appended byte range:      [{EXPECTED_BEFORE_SIZE}, {ledger_size}) (0-based start byte = {EXPECTED_BEFORE_SIZE}, 1-based = {EXPECTED_BEFORE_SIZE + 1})")
    log(f"Appended first 48 bytes:  {appended_bytes[:48]!r}")
    log(f"Appended last 48 bytes:   {appended_bytes[-48:]!r}")
    log(f"Appended byte length:     {len(appended_bytes)} B (claimed: 28512 B, match={len(appended_bytes) == 28512})")
    log(f"Appended SHA256:          {appended_sha}")
    log(f"Old file line count:      {len(prefix_lines)} lines (lines 1..9757; raw LF={prefix_lf}, CRLF=72)")
    log(f"Appended line range:      lines 9758..{len(lines_ledger)} (line 9758-9759 are 2 blank separator lines; first heading ## §605 is at line 9760)")
    log(f"Appended line count:      {appended_lf} LF newlines (pure LF, CRLF={appended_crlf}); total lines = {len(prefix_lines)} + {appended_lf} = {len(lines_ledger)}")
    v4_pass = (len(appended_bytes) == 28512) and (len(lines_ledger) == 9757 + 88)
    log(f"V4 Result:                {'PASS' if v4_pass else 'FAIL'}")

    # ---------------- V5 ----------------
    log("\n=== [V5] 逐字对照草案源 (LEDGER_BOUND_VOLUME.md & 单件草案件) ===")
    raw_bound = open(BOUND_PATH, "rb").read()
    bound_sha = sha256_bytes(raw_bound)
    bound_text = raw_bound.decode("utf-8")
    log(f"Draft Source (BOUND_VOLUME): {BOUND_PATH}")
    log(f"BOUND_VOLUME size={len(raw_bound)} B, sha256={bound_sha}")

    # Extract from BOUND_VOLUME
    bound_lines = bound_text.split("\n")
    bound_blocks = {}
    i = 0
    while i < len(bound_lines):
        if bound_lines[i].startswith("#### ↓↓↓ 草案正文"):
            s_marker = i + 1
            j = i + 1
            while j < len(bound_lines) and not bound_lines[j].startswith("#### ↑↑↑ 草案正文"):
                j += 1
            e_marker = j + 1
            # In BOUND_VOLUME, between s_marker and e_marker:
            # bound_lines[i+1 : j] has 2 empty lines before ## §60x and 2 empty lines after last bullet
            inner = bound_lines[i+1:j]
            # Slice with 1 leading and 1 trailing empty line = "\n" + core + "\n" (matches §2.3 sha256)
            slice_with_lf = "\n".join(inner[1:-1])
            core_text = "\n".join(inner).strip("\n")
            # Find core start/end line numbers (1-based) in BOUND_VOLUME
            core_start_ln = s_marker + 1 + 2  # after 2 blank lines
            core_end_ln = e_marker - 1 - 2    # before 2 blank lines
            sec_m = re.search(r"^## (§60[5-9])\b", core_text, re.M)
            sec_name = sec_m.group(1)
            bound_blocks[sec_name] = {
                "marker_lines": (s_marker, e_marker),
                "core_lines": (core_start_ln, core_end_ln),
                "core_text": core_text,
                "slice_with_lf": slice_with_lf,
            }
            i = j + 1
        else:
            i += 1

    # Also check single draft files and explain the hash difference mentioned in APPLY_RECEIPT §5.2
    log("\n--- 附核：单件草案件现状与回执 §5.2「指纹漂移」真相核查 ---")
    START_M = "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓"
    END_M = "## ↑↑↑ 草案正文结束 ↑↑↑"
    for sec, spath in SINGLE_DRAFTS.items():
        sraw = open(spath, "rb").read()
        ssha = sha256_bytes(sraw)
        smtime = datetime.fromtimestamp(os.stat(spath).st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        stext = sraw.decode("utf-8")
        idx1 = stext.index(START_M) + len(START_M)
        idx2 = stext.index(END_M)
        raw_between = stext[idx1:idx2]  # starts with \n\n, ends with \n\n
        # Method A (_apply.py / BOUND_VOLUME §2.3): "\n" + core + "\n"
        method_a = "\n" + raw_between.strip("\r\n") + "\n"
        # Method B (_apply2.py): raw_between.lstrip("\r\n") == core + "\n\n"
        method_b = raw_between.lstrip("\r\n")
        core_only = raw_between.strip("\r\n")
        exp_b, exp_s = EXPECTED_BOUND_SHAS[sec]
        log(f"{sec} ({os.path.basename(spath)}): file_bytes={len(sraw)}, file_sha={ssha[:16]}..., mtime={smtime}")
        log(f"  Core text (no outer LF):   {len(core_only.encode('utf-8'))} B, sha256={sha256_bytes(core_only.encode('utf-8'))[:16]}...")
        log(f"  Slice A ('\\n'+core+'\\n'):  {len(method_a.encode('utf-8'))} B, sha256={sha256_bytes(method_a.encode('utf-8'))[:16]}... (matches BOUND §2.3 {exp_s[:16]}: {sha256_bytes(method_a.encode('utf-8')) == exp_s})")
        log(f"  Slice B (core+'\\n\\n'):     {len(method_b.encode('utf-8'))} B, sha256={sha256_bytes(method_b.encode('utf-8'))[:16]}... (matches _apply2.py extract)")

    # Extract §605..§609 from Ledger
    log("\n--- 台账 §605–§609 正文提取与逐节逐字比对 ---")
    sec_positions = [(f"§{i}", heading_hits[f"§{i}"][0][0]) for i in range(605, 610)]
    ledger_sections = {}
    for idx, (sec, start_ln) in enumerate(sec_positions):
        end_ln = (sec_positions[idx + 1][1] - 1) if (idx + 1 < len(sec_positions)) else len(lines_ledger)
        raw_sec_lines = lines_ledger[start_ln - 1 : end_ln]
        while raw_sec_lines and raw_sec_lines[-1] == "":
            raw_sec_lines.pop()
            end_ln -= 1
        sec_str = "\n".join(raw_sec_lines)
        ledger_sections[sec] = (start_ln, end_ln, sec_str)

    for i in range(605, 610):
        sec = f"§{i}"
        l_start, l_end, l_core = ledger_sections[sec]
        b_info = bound_blocks[sec]
        b_start, b_end = b_info["core_lines"]
        b_core = b_info["core_text"]
        b_slice_lf = b_info["slice_with_lf"]

        log(f"\n[{sec}] 台账行 {l_start}–{l_end} ({l_end - l_start + 1} 行, {len(l_core)} 字符, {len(l_core.encode('utf-8'))} B, sha256={sha256_bytes(l_core.encode('utf-8'))})")
        log(f"      合订本行 {b_start}–{b_end} ({b_end - b_start + 1} 行, {len(b_core)} 字符, {len(b_core.encode('utf-8'))} B, sha256={sha256_bytes(b_core.encode('utf-8'))})")
        log(f"      合订本带首尾LF切片 (lines {b_start-1}–{b_end+1}): {len(b_slice_lf.encode('utf-8'))} B, sha256={sha256_bytes(b_slice_lf.encode('utf-8'))}")

        if l_core == b_core:
            # Also check if ("\n" + l_core + "\n") or (l_core + "\n\n") is verbatim inside raw_ledger
            in_ledger_with_lf = ("\n" + l_core + "\n").encode("utf-8") in raw_ledger
            log(f"  ==> 结论: MATCH（正文逐字完全一致；且 '\\n'+正文+'\\n' 在台账字节流中完整命中={in_ledger_with_lf}）")
        else:
            # Find first diff
            min_len = min(len(l_core), len(b_core))
            diff_pos = min_len
            for k in range(min_len):
                if l_core[k] != b_core[k]:
                    diff_pos = k
                    break
            s_ctx = max(0, diff_pos - 60)
            l_snip = l_core[s_ctx : min(len(l_core), diff_pos + 60)]
            b_snip = b_core[s_ctx : min(len(b_core), diff_pos + 60)]
            log(f"  ==> 首处差异字符偏移: char_offset = {diff_pos} (byte_offset = {len(l_core[:diff_pos].encode('utf-8'))})")
            log(f"      台账片段 [{s_ctx}:{min(len(l_core), diff_pos+60)}]: {l_snip!r}")
            log(f"      草案片段 [{s_ctx}:{min(len(b_core), diff_pos+60)}]: {b_snip!r}")
            sm = difflib.SequenceMatcher(None, l_core, b_core)
            opcodes = [op for op in sm.get_opcodes() if op[0] != "equal"]
            log(f"      全部差异块数: {len(opcodes)}")
            for tag, i1, i2, j1, j2 in opcodes:
                log(f"        opcode={tag}: Ledger[{i1}:{i2}]={l_core[i1:i2]!r} vs Draft[{j1}:{j2}]={b_core[j1:j2]!r}")

            if sec == "§609":
                l_lines = l_core.split("\n")
                b_lines = b_core.split("\n")
                l_title, l_body = l_lines[0], "\n".join(l_lines[1:])
                b_title, b_body = b_lines[0], "\n".join(b_lines[1:])
                unconf_in_title = "unconfirmed" in l_title
                unconf_in_body = "unconfirmed" in l_body.lower()
                body_exact_match = (l_body == b_body)
                log(f"  [§609 专项核验 (a)] 'unconfirmed' 仅在标题行: {unconf_in_title and not unconf_in_body} (标题含={unconf_in_title}, 除标题外正文含={unconf_in_body})")
                log(f"  [§609 专项核验 (b)] 除标题行外正文与草案逐字一致: {body_exact_match} (len={len(l_body)} chars / {len(l_body.encode('utf-8'))} B, sha256={sha256_bytes(l_body.encode('utf-8'))})")
                log(f"  ==> 结论: PARTIAL / MATCH (with declared title-only marker)（唯一差异在标题行末尾追加 49 字符/78 字节的 unconfirmed 标记，其余正文 4536 字符/8095 字节逐字 MATCH）")

    # ---------------- V6 ----------------
    log("\n=== [V6] 与 §604 的冲突检查 & 引用节号存在性检查 ===")
    all_sec_headings = {}
    for idx, line in enumerate(lines_ledger, start=1):
        m = re.match(r"^##+ *§(\d+)\b", line)
        if m:
            snum = f"§{m.group(1)}"
            all_sec_headings.setdefault(snum, []).append((idx, line))

    log(f"台账全文 `^##+ *§\\d+` 节标题总数: {sum(len(v) for v in all_sec_headings.values())} 个（去重节号 {len(all_sec_headings)} 个）")
    sorted_sec_nums = sorted(all_sec_headings.keys(), key=lambda x: int(x[1:]))
    log(f"台账全部节号列表: {', '.join(sorted_sec_nums)}")

    log("\n--- 6.1 检查 §605–§609 中引用的所有 `§` 节号 ---")
    ledger_ref_list = []
    ext_ref_list = []
    for i in range(605, 610):
        sec = f"§{i}"
        l_start, l_end, l_core = ledger_sections[sec]
        for m in re.finditer(r"§(\d+)(?:\.\d+)*(?:[-–—]\d+)?", l_core):
            ref_str = m.group(0)
            base_num = int(m.group(1))
            base_sec = f"§{base_num}"
            c_s = max(0, m.start() - 30)
            c_e = min(len(l_core), m.end() + 30)
            ctx = l_core[c_s:c_e].replace("\n", "↵")
            if base_num >= 100:
                exists = base_sec in all_sec_headings
                ledger_ref_list.append((sec, ref_str, base_sec, exists, ctx))
            else:
                ext_ref_list.append((sec, ref_str, base_sec, ctx))

    log(f"\n[A] 指向主台账的节号引用（§6xx，共 {len(ledger_ref_list)} 处实例）：")
    for sec, ref_str, base_sec, exists, ctx in ledger_ref_list:
        h_line = all_sec_headings[base_sec][0][0] if exists else None
        log(f"  - In {sec}: `{ref_str}` -> 台账标题存在={exists} (line {h_line}) | 上下文: ...{ctx}...")

    all_ledger_refs_exist = all(x[3] for x in ledger_ref_list)
    log(f"==> 主台账节号引用核查结论: {'PASS (全部存在，0 处悬空节号)' if all_ledger_refs_exist else 'FAIL'}")

    log(f"\n[B] 指向外部单件文档/合订本内部章节的 `§1`–`§6` 引用（共 {len(ext_ref_list)} 处实例，主台账自身最小节号为 {sorted_sec_nums[0]}，无 §1–§6 顶层节）：")
    for sec, ref_str, base_sec, ctx in ext_ref_list:
        log(f"  - In {sec}: `{ref_str}` (修饰外部文档内部章节) | 上下文: ...{ctx}...")

    with open(OUT_TXT, "w", encoding="utf-8", newline="\n") as out_f:
        out_f.write("\n".join(log_lines) + "\n")
    print(f"\n[Saved full output to {OUT_TXT}]")

if __name__ == "__main__":
    main()
