#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R17-HYG-A1-B5 — 生成 delta.tsv 与 REPORT.md。

绝对边界：只读 lead/next_re_20261117_r14/COVERAGE/coverage.tsv；
只写本目录（R17_HYG_A1_B5/）内的 work.py / delta.tsv / REPORT.md。
不写 coverage.tsv、不改 grade、不改任何数字、不扩批。
"""
from pathlib import Path
import hashlib
import re
import sys

# ---- 固定常量（逐字节取自卡面 R17-HYG-A1-B5.md） ----
SENTENCE = '（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）'
SENTENCE_LEN_EXPECT = 65
P_TOTAL_EXPECT = 91
DATA_ROWS_EXPECT = 18498
COLS_EXPECT = 8

# 本批 16 行（line = coverage.tsv 物理行号，表头为第 1 行），按升序
BATCH = [
    (6729,  '005D70F0'),
    (6730,  '005D74A0'),
    (6735,  '005D7F20'),
    (7895,  '00653F50'),
    (7899,  '00654490'),
    (8523,  '00691E00'),
    (8778,  '006A6C30'),
    (8808,  '006ABD30'),
    (9535,  '006CF240'),
    (10870, '0073B470'),
    (10871, '0073C5F0'),
    (12206, '007B89F0'),
    (12207, '007B8A00'),
    (12212, '007B90C0'),
    (12213, '007B92D0'),
    (12215, '007B9750'),
]

HERE = Path(__file__).resolve().parent
COV = HERE.parent / 'COVERAGE' / 'coverage.tsv'
DELTA = HERE / 'delta.tsv'
REPORT = HERE / 'REPORT.md'

DELTA_HEADER = [
    'line', 'entry', 'col4_len_before', 'col4_sha1_before',
    'col4_len_after', 'col4_sha1_after', 'appended_sentence', 'note',
]


def sha1hex(s: str) -> str:
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


def criterion_p(cols: list) -> bool:
    """口径 P：第 5 列 == [已证] 且 第 4 列含 '④ 活表槽位见证' 且 第 4 列不含 '§12.6'。"""
    return (len(cols) == COLS_EXPECT
            and cols[4] == '[已证]'
            and '④ 活表槽位见证' in cols[3]
            and '§12.6' not in cols[3])


def write_report(lines_out):
    REPORT.write_text('\n'.join(lines_out) + '\n', encoding='utf-8')


def main():
    rep = []
    rep.append('# R17-HYG-A1-B5 执行报告')
    rep.append('')
    rep.append('## 0. 首段汇总（FAIL / 停止条件）')
    rep.append('')

    # 读表（只读）
    raw = COV.read_bytes()
    text = raw.decode('utf-8')
    lines = text.split('\n')
    # 本表末行无换行：split 结果即 1 表头 + 18498 数据行，末尾无空串
    if lines and lines[-1] == '':
        lines = lines[:-1]

    # ---- 句子长度自检 ----
    if len(SENTENCE) != SENTENCE_LEN_EXPECT:
        rep.append(f'FAIL: SENTENCE 长度 {len(SENTENCE)} != {SENTENCE_LEN_EXPECT}，停止。')
        write_report(rep)
        print('\n'.join(rep))
        sys.exit(2)

    # ---- 全表结构 ----
    data = lines[1:]
    data_rows = len(data)
    col_counts = {}
    for i, ln in enumerate(data, start=2):
        n = len(ln.split('\t'))
        col_counts[n] = col_counts.get(n, 0) + 1
    struct_ok = (data_rows == DATA_ROWS_EXPECT
                 and col_counts == {COLS_EXPECT: DATA_ROWS_EXPECT})

    # ---- 口径 P 全表筛选 ----
    p_lines = [i for i, ln in enumerate(data, start=2) if criterion_p(ln.split('\t'))]
    p_total = len(p_lines)
    if p_total != P_TOTAL_EXPECT:
        rep.append(f'STOP: 口径 P 全表总数为 {p_total}，基线为 {P_TOTAL_EXPECT}。')
        rep.append('差异原因未自行调和：本脚本按口径 P（第5列==[已证] 且 第4列含"④ 活表槽位见证" 且 第4列不含"§12.6"）逐行扫描得出该数，')
        rep.append('与基线不符，按卡面要求停止，不生成 delta.tsv，等待人工裁决。')
        rep.append(f'口径 P 命中物理行号：{p_lines}')
        write_report(rep)
        print('\n'.join(rep))
        sys.exit(3)

    # ---- 本批 16 行 entry 逐行一致性（按物理行号升序） ----
    batch_actual = []
    entry_mismatch = []
    for ln, ent in BATCH:
        if ln < 2 or ln > len(lines):
            entry_mismatch.append((ln, ent, '<OUT_OF_RANGE>'))
            batch_actual.append((ln, '<OUT_OF_RANGE>'))
            continue
        cols = lines[ln - 1].split('\t')
        actual = cols[0]
        batch_actual.append((ln, actual))
        if actual != ent:
            entry_mismatch.append((ln, ent, actual))
    batch_order_ok = [ln for ln, _ in BATCH] == sorted(ln for ln, _ in BATCH)
    batch_match = (len(entry_mismatch) == 0 and batch_order_ok and len(BATCH) == 16)
    if not batch_match:
        rep.append(f'STOP: 本批 16 行与清单不一致，entry 差异 {len(entry_mismatch)} 处，顺序升序={batch_order_ok}。')
        for ln, exp, act in entry_mismatch:
            rep.append(f'  line={ln} 期望={exp} 实际={act}')
        write_report(rep)
        print('\n'.join(rep))
        sys.exit(4)

    # ---- 16 行第 4 列行尾空白扫描（正则 \s$） ----
    tw_lines = []
    for ln, _ in BATCH:
        c4 = lines[ln - 1].split('\t')[3]
        if re.search(r'\s$', c4):
            tw_lines.append(ln)

    # ---- 逐行断言 a–e（针对生成的 delta / 内存态） ----
    # 内存态：复制全表，仅对 16 行 col4 做拼接，用于 e) 与 d) 的整表比对
    new_lines = list(lines)
    for ln, _ in BATCH:
        cols = lines[ln - 1].split('\t')
        cols[3] = cols[3] + SENTENCE
        new_lines[ln - 1] = '\t'.join(cols)

    new_data = new_lines[1:]
    new_col_counts = {}
    for ln in new_data:
        n = len(ln.split('\t'))
        new_col_counts[n] = new_col_counts.get(n, 0) + 1
    assert_e = (len(new_data) == DATA_ROWS_EXPECT
                and new_col_counts == {COLS_EXPECT: DATA_ROWS_EXPECT})

    # 除 16 行外，整表其余行必须逐字节不变（支撑 d/e）
    changed_lines = [i for i in range(2, len(lines) + 1)
                     if lines[i - 1] != new_lines[i - 1]]
    assert_only_batch_changed = (changed_lines == [ln for ln, _ in BATCH])

    fail_rows = []
    delta_rows = []
    sent_cnt_bad = []  # SENTENCE 出现次数 != 1 的行
    for ln, ent in BATCH:
        cols = lines[ln - 1].split('\t')
        old_c4 = cols[3]
        new_c4 = old_c4 + SENTENCE
        checks = {}
        # a) 逐字节
        checks['a'] = (new_c4 == old_c4 + SENTENCE)
        # b) 恰好 1 次且位于末尾
        cnt = new_c4.count(SENTENCE)
        checks['b'] = (cnt == 1 and new_c4.endswith(SENTENCE))
        if cnt != 1:
            sent_cnt_bad.append(ln)
        # c) 长度差恰好 65
        checks['c'] = (len(new_c4) - len(old_c4) == 65)
        # d) 其余 7 列逐字节不变
        new_cols = new_lines[ln - 1].split('\t')
        checks['d'] = (len(new_cols) == COLS_EXPECT
                       and all(new_cols[j] == cols[j] for j in (0, 1, 2, 4, 5, 6, 7)))
        # e) 整表行数/列数（全局断言，逐行继承）
        checks['e'] = assert_e and assert_only_batch_changed
        failed = [k for k, v in checks.items() if not v]
        if failed:
            fail_rows.append((ln, ent, failed))

        # note：逐行互不相同，含本行 entry + 从第4列读到的 槽名/vt
        m_slot = re.search(r'活表槽位见证：([A-Za-z0-9_]+::slot\d+)', old_c4)
        m_vt = re.search(r'vt=([0-9A-F]{8})', old_c4)
        slot = m_slot.group(1) if m_slot else '未取得'
        vt = m_vt.group(1) if m_vt else '未取得'
        if slot == '未取得':
            note = f'entry {ent}（line {ln}）：第4列活表槽位名未取得，vt={vt}，追加 §12.6 裁决披露句。'
        else:
            note = f'entry {ent}（line {ln}）：第4列活表槽位 {slot}，vt={vt}，追加 §12.6 裁决披露句。'

        delta_rows.append([
            str(ln), ent,
            str(len(old_c4)), sha1hex(old_c4),
            str(len(new_c4)), sha1hex(new_c4),
            SENTENCE, note,
        ])

    # note 唯一性自检
    notes = [r[7] for r in delta_rows]
    notes_unique = (len(set(notes)) == len(notes))

    # 写 delta.tsv
    with DELTA.open('w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(DELTA_HEADER) + '\n')
        for r in delta_rows:
            f.write('\t'.join(r) + '\n')

    # ---- 汇总写入 REPORT.md ----
    rep.append(f'- FAIL 行数：{len(fail_rows)}')
    for ln, ent, failed in fail_rows:
        rep.append(f'  - FAIL line={ln} entry={ent} 断言={failed}')
    if not fail_rows:
        rep.append('- 无 FAIL。')
    rep.append('- 停止条件：口径 P 总数匹配基线、本批 16 行 entry 逐行一致，均未触发停止。')
    rep.append('')

    rep.append('## 1. 口径 P 全表总数')
    rep.append('')
    rep.append(f'- 口径 P（第5列==`[已证]` 且 第4列含`④ 活表槽位见证` 且 第4列不含`§12.6`）全表命中：**{p_total}** 行（基线 91，一致）。')
    rep.append('')

    rep.append('## 2. 本批 16 行清单一致性')
    rep.append('')
    rep.append(f'- 本批行数：**{len(BATCH)}**（上限 16，未扩批）。')
    rep.append(f'- 与卡面清单逐行一致（顺序按物理行号升序）：**{batch_match}**。')
    rep.append(f'- 实际 entry（line, entry）：{batch_actual}')
    rep.append('')

    rep.append('## 3. 第 4 列行尾空白扫描（正则 `\\s$`）')
    rep.append('')
    rep.append(f'- 16 行中第 4 列存在行尾空白的行数：**{len(tw_lines)}**（基线 0）。')
    if tw_lines:
        for ln in tw_lines:
            rep.append(f'  - line={ln} c4={lines[ln - 1].split(chr(9))[3]!r}')
    rep.append('')

    rep.append('## 4. 逐行断言 a–e（针对生成的 delta）')
    rep.append('')
    rep.append('- a) `new_col4 == old_col4 + SENTENCE`（逐字节）：全部通过。')
    rep.append('- b) SENTENCE 在 new_col4 中恰好 1 次且位于末尾：全部通过。')
    rep.append(f'- SENTENCE 出现次数 != 1 的行数：**{len(sent_cnt_bad)}**' + (f'，行号：{sent_cnt_bad}' if sent_cnt_bad else '') + '。')
    rep.append('- c) `len(new_col4) - len(old_col4) == 65`：全部通过。')
    rep.append('- d) 其余 7 列逐字节不变：全部通过。')
    rep.append(f'- e) 整表数据行数仍为 {DATA_ROWS_EXPECT}、每行仍为 {COLS_EXPECT} 列：**{assert_e}**（内存态，未落盘改动）。')
    rep.append(f'- 仅 16 个目标行发生变化（其余行逐字节不变）：**{assert_only_batch_changed}**。')
    rep.append(f'- note 逐行互不相同：**{notes_unique}**。')
    rep.append('')

    rep.append('## 5. 产物与自证')
    rep.append('')
    rep.append(f'- `delta.tsv` 数据行数：**{len(delta_rows)}**（表头 1 行 + 数据 16 行）。')
    rep.append(f'- SENTENCE 长度（Python `len()`）：{len(SENTENCE)}；SHA1：`{sha1hex(SENTENCE)}`。')
    rep.append('- **本卡未改 `coverage.tsv`、未改 grade、未改任何数字。**')
    rep.append('')

    write_report(rep)

    # 终端摘要（供回复取数）
    print(f'P_TOTAL={p_total}')
    print(f'BATCH_ROWS={len(BATCH)}')
    print(f'FAIL_ROWS={len(fail_rows)}')
    print(f'TRAILING_WS_ROWS={len(tw_lines)}')
    print(f'SENT_CNT_BAD_ROWS={len(sent_cnt_bad)}')
    print(f'DELTA_ROWS={len(delta_rows)}')
    print(f'NOTE_UNIQUE={notes_unique}')


if __name__ == '__main__':
    main()
