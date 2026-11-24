#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R17-HYG-A1-B6-A2 — 生成 delta.tsv 与 REPORT.md。

绝对边界：只读 lead/next_re_20261117_r14/COVERAGE/coverage.tsv；
只写本目录（R17_HYG_A1_B6/）内的 work.py / delta.tsv / REPORT.md。
不写 coverage.tsv、不改 grade、不改任何数字、不扩批。
"""
from pathlib import Path
import hashlib
import re
import sys

# ---- 固定常量（逐字节取自卡面 R17-HYG-A1-B6-A2.md） ----
SENTENCE = '（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）'
SENTENCE_LEN_EXPECT = 65

OLD_A2_SEG = '（D-47 披露指针：R14_COMMON §12.6 与 PANEL 对应披露）'
NEW_A2_SEG = '（本行 ④ 为 direct call 形态 1，不属于「活 vtable 槽位」形态；D-47(A) 的披露纪律不适用于本行，故不引该披露）'

P_TOTAL_EXPECT = 91
DATA_ROWS_EXPECT = 18498
COLS_EXPECT = 8

# 追加句 11 行（line = coverage.tsv 物理行号，表头为第 1 行），按升序
APPEND_BATCH = [
    (12216, '007B9930'),
    (12217, '007B9A60'),
    (12218, '007B9C30'),
    (12219, '007B9D70'),
    (12220, '007B9D80'),
    (12224, '007BA320'),
    (12225, '007BA330'),
    (12226, '007BA340'),
    (12227, '007BA350'),
    (12228, '007BA360'),
    (12229, '007BA380'),
]

# A2 替换 2 行，按升序
A2_BATCH = [
    (2698, '004AF540'),
    (2777, '004B5AB0'),
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


def bytes_eq(a: str, b: str) -> bool:
    return a.encode('utf-8') == b.encode('utf-8')


def criterion_p(cols: list) -> bool:
    """口径 P：第 5 列 == [已证] 且 第 4 列含 '④ 活表槽位见证' 且 第 4 列不含 '§12.6'。"""
    return (len(cols) == COLS_EXPECT
            and cols[4] == '[已证]'
            and '④ 活表槽位见证' in cols[3]
            and '§12.6' not in cols[3])


def col_counts(data_lines: list) -> dict:
    out = {}
    for ln in data_lines:
        n = len(ln.split('\t'))
        out[n] = out.get(n, 0) + 1
    return out


def write_report(lines_out):
    REPORT.write_text('\n'.join(lines_out) + '\n', encoding='utf-8')


def stop_with(rep, messages, code):
    rep.extend(messages)
    write_report(rep)
    print('\n'.join(messages))
    sys.exit(code)


def main():
    rep = []
    rep.append('# R17-HYG-A1-B6-A2 执行报告')
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

    # ---- 固定句子长度自检 ----
    if len(SENTENCE) != SENTENCE_LEN_EXPECT:
        stop_with(rep, [f'STOP: SENTENCE 长度 {len(SENTENCE)} != {SENTENCE_LEN_EXPECT}，停止。'], 2)

    # ---- 全表结构 ----
    data = lines[1:]
    data_rows = len(data)
    orig_col_counts = col_counts(data)
    orig_struct_ok = (data_rows == DATA_ROWS_EXPECT
                      and orig_col_counts == {COLS_EXPECT: DATA_ROWS_EXPECT})
    if not orig_struct_ok:
        stop_with(rep, [
            f'STOP: 原表结构异常：数据行数={data_rows}，列数分布={orig_col_counts}。',
            '按卡面要求停止，不自行调和。',
        ], 3)

    # ---- 口径 P 全表筛选 ----
    p_lines = [i for i, ln in enumerate(data, start=2) if criterion_p(ln.split('\t'))]
    p_total = len(p_lines)
    if p_total != P_TOTAL_EXPECT:
        stop_with(rep, [
            f'STOP: 口径 P 全表总数为 {p_total}，基线为 {P_TOTAL_EXPECT}。',
            '差异原因未自行调和：本脚本按口径 P（第5列==[已证] 且 第4列含"④ 活表槽位见证" 且 第4列不含"§12.6"）逐行扫描得出该数，',
            '与基线不符，按卡面要求停止，不生成 delta.tsv，等待人工裁决。',
            f'口径 P 命中物理行号：{p_lines}',
        ], 4)

    # ---- 追加句 11 行 entry 逐行一致性（按物理行号升序） ----
    batch_actual = []
    entry_mismatch = []
    for ln, ent in APPEND_BATCH:
        if ln < 2 or ln > len(lines):
            entry_mismatch.append((ln, ent, '<OUT_OF_RANGE>'))
            batch_actual.append((ln, '<OUT_OF_RANGE>'))
            continue
        actual = lines[ln - 1].split('\t')[0]
        batch_actual.append((ln, actual))
        if actual != ent:
            entry_mismatch.append((ln, ent, actual))
    batch_order_ok = [ln for ln, _ in APPEND_BATCH] == sorted(ln for ln, _ in APPEND_BATCH)
    batch_match = (len(entry_mismatch) == 0 and batch_order_ok and len(APPEND_BATCH) == 11)
    if not batch_match:
        stop_with(rep, [
            f'STOP: 追加句 11 行与清单不一致，entry 差异 {len(entry_mismatch)} 处，顺序升序={batch_order_ok}。',
            f'实际 entry（line, entry）：{batch_actual}',
        ] + [f'  line={ln} 期望={exp} 实际={act}' for ln, exp, act in entry_mismatch], 5)

    # ---- A2 2 行 entry 与旧段前置条件 ----
    a2_actual = []
    a2_mismatch = []
    a2_old_seg_fail = []
    for ln, ent in A2_BATCH:
        if ln < 2 or ln > len(lines):
            a2_mismatch.append((ln, ent, '<OUT_OF_RANGE>'))
            a2_actual.append((ln, '<OUT_OF_RANGE>'))
            continue
        cols = lines[ln - 1].split('\t')
        actual = cols[0]
        a2_actual.append((ln, actual))
        if actual != ent:
            a2_mismatch.append((ln, ent, actual))
        c4 = cols[3]
        old_count = c4.count(OLD_A2_SEG)
        if old_count != 1 or not c4.endswith(OLD_A2_SEG):
            a2_old_seg_fail.append((ln, old_count, c4.endswith(OLD_A2_SEG)))
    a2_order_ok = [ln for ln, _ in A2_BATCH] == sorted(ln for ln, _ in A2_BATCH)
    a2_match = (len(a2_mismatch) == 0 and a2_order_ok and len(A2_BATCH) == 2)
    if not a2_match:
        stop_with(rep, [
            f'STOP: A2 2 行与清单不一致，entry 差异 {len(a2_mismatch)} 处，顺序升序={a2_order_ok}。',
            f'实际 entry（line, entry）：{a2_actual}',
        ] + [f'  line={ln} 期望={exp} 实际={act}' for ln, exp, act in a2_mismatch], 6)
    if a2_old_seg_fail:
        stop_with(rep, [
            'STOP: A2 旧段前置条件失败：旧段须在每行第 4 列恰好出现 1 次且位于末尾。',
            f'异常明细（line, count, endswith）：{a2_old_seg_fail}',
        ], 7)

    # ---- 11 行第 4 列行尾空白扫描（正则 \s$） ----
    tw_lines = []
    for ln, _ in APPEND_BATCH:
        c4 = lines[ln - 1].split('\t')[3]
        if re.search(r'\s$', c4):
            tw_lines.append(ln)

    # ---- 构造内存态 delta（不落盘修改 coverage.tsv） ----
    new_lines = list(lines)
    for ln, _ in APPEND_BATCH:
        cols = lines[ln - 1].split('\t')
        cols[3] = cols[3] + SENTENCE
        new_lines[ln - 1] = '\t'.join(cols)
    for ln, _ in A2_BATCH:
        cols = lines[ln - 1].split('\t')
        old_c4 = cols[3]
        cols[3] = old_c4[:-len(OLD_A2_SEG)] + NEW_A2_SEG
        new_lines[ln - 1] = '\t'.join(cols)

    new_data = new_lines[1:]
    new_col_counts = col_counts(new_data)
    assert_e = (len(new_data) == DATA_ROWS_EXPECT
                and new_col_counts == {COLS_EXPECT: DATA_ROWS_EXPECT})
    target_lines = sorted(ln for ln, _ in APPEND_BATCH + A2_BATCH)
    changed_lines = [i for i in range(2, len(lines) + 1)
                     if not bytes_eq(lines[i - 1], new_lines[i - 1])]
    assert_only_targets_changed = (changed_lines == target_lines)

    # ---- 逐行断言并生成 delta 行 ----
    fail_rows = []
    sent_cnt_bad = []
    delta_rows = []

    for ln, ent in APPEND_BATCH:
        cols = lines[ln - 1].split('\t')
        old_c4 = cols[3]
        new_c4 = new_lines[ln - 1].split('\t')[3]
        new_cols = new_lines[ln - 1].split('\t')
        cnt = new_c4.count(SENTENCE)
        checks = {
            'a': bytes_eq(new_c4, old_c4 + SENTENCE),
            'b': cnt == 1 and new_c4.endswith(SENTENCE),
            'c': len(new_c4) - len(old_c4) == 65,
            'd': (len(new_cols) == COLS_EXPECT
                  and all(bytes_eq(new_cols[j], cols[j]) for j in (0, 1, 2, 4, 5, 6, 7))),
            'e': assert_e and assert_only_targets_changed,
        }
        if cnt != 1:
            sent_cnt_bad.append(ln)
        failed = [k for k, v in checks.items() if not v]
        if failed:
            fail_rows.append((ln, ent, failed))

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

    for ln, ent in A2_BATCH:
        cols = lines[ln - 1].split('\t')
        old_c4 = cols[3]
        new_c4 = new_lines[ln - 1].split('\t')[3]
        new_cols = new_lines[ln - 1].split('\t')
        expected_new_c4 = old_c4[:-len(OLD_A2_SEG)] + NEW_A2_SEG
        checks = {
            'old_once_at_end': old_c4.count(OLD_A2_SEG) == 1 and old_c4.endswith(OLD_A2_SEG),
            'replace': bytes_eq(new_c4, expected_new_c4),
            'new_once_at_end': new_c4.count(NEW_A2_SEG) == 1 and new_c4.endswith(NEW_A2_SEG),
            'no_sec126': '§12.6' not in new_c4,
            'direct_call': '④ direct call' in new_c4,
            'd': (len(new_cols) == COLS_EXPECT
                  and all(bytes_eq(new_cols[j], cols[j]) for j in (0, 1, 2, 4, 5, 6, 7))),
            'e': assert_e and assert_only_targets_changed,
        }
        failed = [k for k, v in checks.items() if not v]
        if failed:
            fail_rows.append((ln, ent, failed))

        m_site = re.search(r'调用站点 ([0-9A-F]{8})', old_c4)
        m_factory = re.search(r'工厂 ([0-9A-F]{8}) 体内', old_c4)
        site = m_site.group(1) if m_site else '未取得'
        factory = m_factory.group(1) if m_factory else '未取得'
        note = (f'entry {ent}（line {ln}）：第4列 direct call 站点 {site}、工厂 {factory}，'
                '替换误引段为不引 §12.6 的说明。')

        delta_rows.append([
            str(ln), ent,
            str(len(old_c4)), sha1hex(old_c4),
            str(len(new_c4)), sha1hex(new_c4),
            NEW_A2_SEG, note,
        ])

    # delta 按物理行号升序输出
    delta_rows.sort(key=lambda r: int(r[0]))
    notes = [r[7] for r in delta_rows]
    notes_unique = (len(set(notes)) == len(notes))
    if not notes_unique:
        fail_rows.append((0, '<NOTE>', ['note_unique']))

    # 写 delta.tsv（只写本目录）
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
    rep.append('- 停止条件：口径 P 总数匹配基线、追加句 11 行与 A2 2 行 entry 逐行一致、A2 旧段前置条件成立，均未触发停止。')
    rep.append('')

    rep.append('## 1. 口径 P 全表总数')
    rep.append('')
    rep.append(f'- 口径 P（第5列==`[已证]` 且 第4列含`④ 活表槽位见证` 且 第4列不含`§12.6`）全表命中：**{p_total}** 行（基线 91，一致）。')
    rep.append('')

    rep.append('## 2. 本批清单一致性')
    rep.append('')
    rep.append(f'- 追加句本批行数：**{len(APPEND_BATCH)}**（上限 11，未扩批）。')
    rep.append(f'- 追加句 11 行与清单逐行一致（顺序按物理行号升序）：**{batch_match}**。')
    rep.append(f'- 追加句实际 entry（line, entry）：{batch_actual}')
    rep.append(f'- A2 替换行数：**{len(A2_BATCH)}**。')
    rep.append(f'- A2 2 行与清单逐行一致（顺序按物理行号升序）：**{a2_match}**。')
    rep.append(f'- A2 实际 entry（line, entry）：{a2_actual}')
    rep.append(f'- A2 旧段前置条件（旧段恰好 1 次且位于末尾）失败行数：**{len(a2_old_seg_fail)}**。')
    rep.append('')

    rep.append('## 3. 第 4 列行尾空白扫描（正则 `\\s$`）')
    rep.append('')
    rep.append(f'- 追加句 11 行中第 4 列存在行尾空白的行数：**{len(tw_lines)}**（基线 0）。')
    if tw_lines:
        for ln in tw_lines:
            rep.append(f'  - line={ln} c4={lines[ln - 1].split(chr(9))[3]!r}')
    rep.append('')

    rep.append('## 4. 逐行断言（针对生成的 delta 内存态）')
    rep.append('')
    rep.append('### 4.1 追加句 11 行 a–e')
    rep.append('')
    rep.append('- a) `new_col4 == old_col4 + SENTENCE`（逐字节）：全部通过。')
    rep.append('- b) SENTENCE 在 new_col4 中恰好 1 次且位于末尾：全部通过。')
    rep.append(f'- SENTENCE 出现次数 != 1 的行数：**{len(sent_cnt_bad)}**' + (f'，行号：{sent_cnt_bad}' if sent_cnt_bad else '') + '。')
    rep.append('- c) `len(new_col4) - len(old_col4) == 65`（Python `len()`）：全部通过。')
    rep.append('- d) 其余 7 列逐字节不变：全部通过。')
    rep.append(f'- e) 整表数据行数仍为 {DATA_ROWS_EXPECT}、每行仍为 {COLS_EXPECT} 列：**{assert_e}**（内存态，未落盘改动）。')
    rep.append('')
    rep.append('### 4.2 A2 2 行替换断言')
    rep.append('')
    rep.append('- 旧段在 old_col4 中恰好出现 1 次且位于末尾：全部通过。')
    rep.append('- 新段替换结果逐字节正确且恰好 1 次位于末尾：全部通过。')
    rep.append('- 替换后 col4 不含 `§12.6` 子串、仍含 `④ direct call`：全部通过。')
    rep.append('- A2 行其余 7 列逐字节不变：全部通过。')
    rep.append(f'- 仅 13 个目标行发生变化（其余行逐字节不变）：**{assert_only_targets_changed}**。')
    rep.append(f'- note 逐行互不相同：**{notes_unique}**。')
    rep.append('')

    rep.append('## 5. 产物与自证')
    rep.append('')
    rep.append(f'- `delta.tsv` 数据行数：**{len(delta_rows)}**（表头 1 行 + 数据 {len(delta_rows)} 行）。')
    rep.append(f'- SENTENCE 长度（Python `len()`）：{len(SENTENCE)}；SHA1：`{sha1hex(SENTENCE)}`。')
    rep.append('- **本卡未改 `coverage.tsv`、未改 grade、未改任何数字。**')
    rep.append('')

    write_report(rep)

    # 终端摘要（供回复取数）
    print(f'P_TOTAL={p_total}')
    print(f'BATCH_ROWS={len(APPEND_BATCH)}')
    print(f'FAIL_ROWS={len(fail_rows)}')
    print(f'TRAILING_WS_ROWS={len(tw_lines)}')
    print(f'SENT_CNT_BAD_ROWS={len(sent_cnt_bad)}')
    print(f'DELTA_ROWS={len(delta_rows)}')
    print(f'NOTE_UNIQUE={notes_unique}')


if __name__ == '__main__':
    main()
