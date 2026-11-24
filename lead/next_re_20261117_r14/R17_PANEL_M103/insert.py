#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R17-PANEL-M103 :: PANEL.md insert-only merger.

Re-runnable: always reconstructs the new PANEL.md from the immutable
PANEL.before.md backup, so repeated runs yield the identical result.
Absolute boundary: L1 is a reverse-chronological note chain, so this
script only INSERTS into L1 (never replaces a whole line) and only
INSERTS the M103 body block before the M77 pin note.
"""
import hashlib
import os
import re
import sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
COVERAGE_DIR = os.path.join(PROJECT, 'lead', 'next_re_20261117_r14', 'COVERAGE')
PANEL = os.path.join(COVERAGE_DIR, 'PANEL.md')
BACKUP = os.path.join(HERE, 'PANEL.before.md')
COVERAGE_TSV = os.path.join(COVERAGE_DIR, 'coverage.tsv')
REPORT = os.path.join(HERE, 'REPORT.md')

# Baseline facts measured from disk at card opening (backup is byte-identical).
BASELINE_PANEL_BYTES = 205207
BASELINE_PANEL_SHA = '9a0be87e9bdde277e08b7145989bca132c6b253cd193034c205ea79dd848c1c9'
BASELINE_PANEL_MTIME = '2026-11-21 11:20:05.105192400 +0800'
EXPECTED_TSV_BYTES = 4147334
EXPECTED_TSV_SHA = 'c2ee063fd4f61f784585ef2abcc4ff563fa09ec1b1f7f5079643076e359c744a'

# L1 prepend: insert immediately after the literal header token `coverage`.
L1_PREFIX = '# PANEL — R14 coverage'
# Brief note following the established `M<number> ...；` convention.
# Required tokens present: M103, §2.7, [已证] 1,654, atlas 内 1,648, D-53.
L1_NOTE = (
    'M103 §2.6 两处表述更正成文 §2.7（D-1/D-2 字节核准；'
    '②-b 仍 [静态推断]，待 D-53；D-48 净收益 0；'
    '计数未变：全表 [已证] 1,654、atlas 内 1,648、atlas 外 6）；'
)

# Body note block (verbatim from card §2.1).
BODY_LINES = [
    '> ✅ **M103 披露：`R14_COMMON §2.6` 两处表述更正，新立 `§2.7`（R17，2026-11-21；D-1 / D-2 已字节核准）**',
    '>',
    '> ① **D-1（更正）**：`0x43F2B5` 的 `je 0x43F504` **不是「拒绝分支」**。字节 `0F 84 49 02 00 00`（+6+0x249 = 0x43F504）；`0x43F504` 起为 `mov eax,[esp+0x18]; inc esi; cmp esi,eax; mov [esp+0x1c],esi; jl 0x43F269`，即**循环增量 + 回边**。拒绝出口 `0x43F5D8` 的跳转源**恰 2 条**：`0x43F220`（`jne`）与 `0x43F5B1`（`je`，紧接 `mov al,[esp+0x23]; test al,al`）。',
    '> ⇒ **逐格 `0x47C620` 的调用不直接产生拒绝**；把「观测到的调用点身份」翻译成「哪一层拒绝」不能靠该分支。',
    '>',
    '> ② **D-2（更正）**：`0x449440` 的短路**不是「直接返回 7」**。两条短路边 `0x449459`(`74 38`)/`0x449460`(`74 31`) 均跳 `0x449493`，该块经 `call [edx+0xA8]`（`FF 92 A8 00 00 00`，BType 谓词）后由 `and al,0xF9; add eax,7` 映射为 **0 / 7**。',
    '>',
    '> ③ **对 ②-b 的影响**：两路径在闸核内共用同一 `0x47C620`，且 `0x449440`/`0x47C620`/`0x47C3D0` 三函数体内**非栈写 = 0**（写指令总数 / 非栈写 = 1/0、0/0、8/0）。⇒ ②-b 只能挂 `[静态推断]`，收口方式待 **D-53**（(A) 永久收口 / (B) 撤销 D-36(A)「不写线程上下文」单条）。',
    '> ⇒ 另：**D-48（`DebugActiveProcess`）对 ②-b 净收益 = 0**（调试器身份 ≠ 写内存/写上下文打断点的权利；10 通道中「能证明具体指令被执行过」= 0），**不得再把 D-48 当作 ②-b 的取证路径**。',
    '>',
    '> ④ **引用纪律（强制）**：凡引用 §2.6 关于「拒绝分支」「短路返回 7」的表述，**必须同引 `R14_COMMON §2.7`**；单独引 §2.6 该两处而不提更正 = 引用缺陷。',
    '>',
    '> ⑤ **本节不动任何计数**：本次是表述更正 + 披露，`coverage.tsv` 第 4/5 列未被本卡改动；`[已证]` 1,654、atlas 内 1,648、atlas 外 6、各子系统 proved/strict、名义/严格达标判定**全部不变**。',
    '>',
    '> ⑥ **旁附口径提示**：第 6 列（evidence_path）有 **11 行**含 `④` 字符（M94 指针修复追加的中文注记）⇒ **任何按「整行」统计 ④ 的做法会多计 11**；现行 ④ 三口径均限定第 4 列，不受影响，**不得改口径**。',
]

ANCHOR = '> 📌 **M77 并表实算说明**'   # unique; M103 block goes immediately before this line


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def fmt_mtime(path):
    ts = os.stat(path).st_mtime
    return datetime.fromtimestamp(ts, timezone(timedelta(hours=8))).isoformat(sep=' ')


def main():
    # ---------- load immutable baseline ----------
    with open(BACKUP, 'rb') as handle:
        before = handle.read()
    assert len(before) == BASELINE_PANEL_BYTES, 'backup byte count mismatch'
    assert sha256_bytes(before) == BASELINE_PANEL_SHA, 'backup sha256 mismatch'
    assert before.count(b'\r') == 0, 'baseline CR count != 0 (bare-LF assumption failed)'

    before_lines = before.split(b'\n')
    before_line0 = before_lines[0].decode('utf-8')
    assert before_line0.startswith(L1_PREFIX), 'L1 prefix not found'

    anchor_hits = [idx for idx, line in enumerate(before_lines)
                   if ANCHOR.encode('utf-8') in line]
    assert len(anchor_hits) == 1, f'anchor not unique: {anchor_hits}'
    anchor_idx = anchor_hits[0]
    body_line_count = len(BODY_LINES)

    # ---------- construct complete new byte array ----------
    new_line0 = before_line0[:len(L1_PREFIX)] + L1_NOTE + before_line0[len(L1_PREFIX):]
    new_line0_b = new_line0.encode('utf-8')
    body_b = [line.encode('utf-8') for line in BODY_LINES]

    after_lines = (
        [new_line0_b]
        + before_lines[1:anchor_idx]
        + body_b
        + before_lines[anchor_idx:]
    )
    after = b'\n'.join(after_lines)

    # ---------- assertions (before any disk write) ----------
    results = {}

    # a) line-count delta == inserted body-line count
    delta = after.count(b'\n') - before.count(b'\n')
    results['a'] = (delta == body_line_count,
                    f'line delta {delta} == inserted body lines {body_line_count}')

    # b) L1 M-number set superset of (before set ∪ {103})
    set_before = set(int(tok[1:]) for tok in re.findall(r'M\d+', before_line0))
    set_after = set(int(tok[1:]) for tok in re.findall(r'M\d+', new_line0))
    b_ok = set_after >= (set_before | {103})
    results['b'] = (b_ok, f'L1 M-set sizes: before={len(set_before)} / after={len(set_after)}; '
                          f'superset(before∪{{103}})={b_ok}')

    # c) all lines other than L1 and the insertion point are byte-identical
    prefix_same = after_lines[1:anchor_idx] == before_lines[1:anchor_idx]
    tail_same = after_lines[anchor_idx + body_line_count:] == before_lines[anchor_idx:]
    l1_changed = after_lines[0] != before_lines[0]
    diff_others = (
        sum(1 for idx in range(1, anchor_idx) if after_lines[idx] != before_lines[idx])
        + sum(1 for idx in range(len(before_lines) - anchor_idx)
              if after_lines[anchor_idx + body_line_count + idx] != before_lines[anchor_idx + idx])
    )
    c_ok = prefix_same and tail_same and l1_changed and diff_others == 0
    results['c'] = (c_ok, f'different lines: 1 (L1) + {diff_others} (others); '
                          f'L1 changed={l1_changed}, prefix_same={prefix_same}, tail_same={tail_same}')

    # d) §12.6 occurrence count unchanged
    needle_s126 = '§12.6'.encode('utf-8')
    s126_before = before.count(needle_s126)
    s126_after = after.count(needle_s126)
    results['d'] = (s126_before == s126_after,
                    f'§12.6 count {s126_before} -> {s126_after}')

    # e) full-text M103 occurrences >= 2
    m103_after = after.decode('utf-8').count('M103')
    m103_before = before.decode('utf-8').count('M103')
    results['e'] = (m103_after >= 2,
                    f'M103 occurrences {m103_before} -> {m103_after} (>= 2 required)')

    # extra checks
    cr_after = after.count(b'\r')
    results['cr'] = (cr_after == 0, f'CR count after = {cr_after} (must be 0)')

    rebuilt = b'\n'.join(
        [before_line0.encode('utf-8')]
        + after_lines[1:anchor_idx]
        + after_lines[anchor_idx + body_line_count:]
    )
    revert_ok = rebuilt == before
    results['revert'] = (revert_ok,
                         f'rebuild-without-insertions == before: {revert_ok} '
                         f'({sha256_bytes(rebuilt)[:12]} == {sha256_bytes(before)[:12]})')

    required_tokens = ['M103', '§2.7', '[已证] 1,654', 'atlas 内 1,648', 'D-53']
    missing = [tok for tok in required_tokens if tok not in new_line0]
    results['tokens'] = (not missing, f'L1 required tokens present; missing={missing}')

    failed = [key for key, (ok, _) in results.items() if not ok]
    for key, (ok, detail) in results.items():
        print(f'[{"PASS" if ok else "FAIL"}] {key}: {detail}')
    if failed:
        print('ASSERTION FAILURES:', failed)
        sys.exit(1)

    # ---------- one-time write ----------
    with open(PANEL, 'wb') as handle:
        handle.write(after)

    # ---------- read-back verification ----------
    with open(PANEL, 'rb') as handle:
        reread = handle.read()
    assert reread == after, 'read-back byte mismatch'
    print('[PASS] read-back: written bytes == in-memory new byte array')

    # ---------- coverage.tsv untouched proof ----------
    with open(COVERAGE_TSV, 'rb') as handle:
        tsv = handle.read()
    tsv_bytes = len(tsv)
    tsv_sha = sha256_bytes(tsv)
    tsv_ok = (tsv_bytes == EXPECTED_TSV_BYTES and tsv_sha == EXPECTED_TSV_SHA)
    print(f'[{"PASS" if tsv_ok else "FAIL"}] coverage.tsv: bytes={tsv_bytes} '
          f'sha256={tsv_sha[:12]}... (expected {EXPECTED_TSV_BYTES} / {EXPECTED_TSV_SHA[:12]}...)')

    # ---------- REPORT ----------
    after_mtime = fmt_mtime(PANEL)
    assertion_rows = '\n'.join(
        f'| {key} | {"PASS" if ok else "FAIL"} | {detail} |'
        for key, (ok, detail) in results.items()
    )
    report = f"""# R17-PANEL-M103 :: REPORT

角色：合并员 / `PANEL.md` 唯一写者（`work/cn:hy4flash-free`）。日期：2026-11-21（R17 第 1 轮）。
卡面：`_cards/R17-PANEL-M103.md`。本卡动作 = 两处纯插入（insert only），未 replace 整行、未删除任何既有字节。

## 0. 绝对边界遵守情况

- 只改 `COVERAGE/PANEL.md`；未改 `coverage.tsv`、`R14_COMMON.md`、台账、看板、`LEAD_LOCK`、`PENDING_DECISIONS.md`、`_cards\\`。
- L1 按倒序前插链规则，在 `# PANEL — R14 coverage` 的 `coverage` 之后插入 M103 备注；**未整行 replace**。
- 正文块插在 M102 块最后一行之后、`📌 M77 并表实算说明` 行之前（锚点唯一定位，实测行号 = {anchor_idx + 1}）。
- 未读 `EVIDENCE\\` 原始输出、未跑反汇编；文件行尾实测 bare LF（CR = 0），写盘后仍为 0。

## 1. 改前 / 改后指标

| 项 | 改前（`PANEL.before.md` = 开卡时 `COVERAGE/PANEL.md`） | 改后（现 `COVERAGE/PANEL.md`） |
|---|---|---|
| 路径 | `lead/next_re_20261117_r14/COVERAGE/PANEL.md` | 同左 |
| mtime | `{BASELINE_PANEL_MTIME}` | `{after_mtime}` |
| 字节 | `{len(before):,}` | `{len(after):,}`（`+{len(after)-len(before):,}`） |
| sha256 | `{sha256_bytes(before)}`（前 12：`{sha256_bytes(before)[:12]}`） | `{sha256_bytes(after)}`（前 12：`{sha256_bytes(after)[:12]}`） |
| 换行数（`\\n`） | `{before.count(chr(10).encode()):,}` | `{after.count(chr(10).encode()):,}` |
| CR 计数 | `{before.count(chr(13).encode())}` | `{after.count(chr(13).encode())}` |
| 末尾 LF | `{before.endswith(chr(10).encode())}` | `{after.endswith(chr(10).encode())}` |

行数增量 = `{delta}` = 插入正文块行数 `{body_line_count}`（L1 备注为行内插入，不增行）。

## 2. 断言 a–e 实测值

| 断言 | 结果 | 实测值 |
|---|---|---|
{assertion_rows}

- a) 行数增量 == 插入内容行数：**PASS**。
- b) L1 M 号集合 ⊇ 改前集合 ∪ {{103}}：**PASS**（集合大小 改前 `{len(set_before)}` / 改后 `{len(set_after)}`；改前集合 = {sorted(set_before)}）。
- c) 除 L1 与插入点外其余各行逐字节相同：**PASS**（不同行数 = 1（L1）+ {diff_others}）。
- d) `§12.6` 出现次数不变：**PASS**（`{s126_before}` → `{s126_after}`；本卡不碰第 4 列，PANEL 内计数仅如实报告）。
- e) 全文 `M103` 出现次数 ≥ 2：**PASS**（`{m103_after}`）。
- 附加：CR 计数写盘后仍为 0：**PASS**；去掉两处插入可逐字节还原改前：**PASS**；L1 五个必需 token 齐备：**PASS**。

## 3. 插入内容定位

- L1：在 `# PANEL — R14 coverage` 之后前插 `M103 §2.6 两处表述更正成文 §2.7（…D-53…）；`，位于原首条备注 `M77 并表` 之前。
- 正文：M103 披露块 `{body_line_count}` 行，插在 M102 块末行（原第 {anchor_idx} 行）之后、`📌 M77 并表实算说明`（原第 {anchor_idx + 1} 行）之前。

## 4. coverage.tsv 未变证明

- 开卡时：`{EXPECTED_TSV_BYTES:,} B / sha256 {EXPECTED_TSV_SHA}`
- 写盘后复查：`{tsv_bytes:,} B / sha256 {tsv_sha}`
- 结论：一致（{tsv_ok}），本卡未碰 `coverage.tsv`，亦未被并发改写。

## 5. 复跑

`python insert.py`：从 `PANEL.before.md` 重建，断言全 PASS 后一次性写盘并读回复验。
"""
    with open(REPORT, 'w', encoding='utf-8') as handle:
        handle.write(report)
    print('[PASS] REPORT.md written')


if __name__ == '__main__':
    main()
