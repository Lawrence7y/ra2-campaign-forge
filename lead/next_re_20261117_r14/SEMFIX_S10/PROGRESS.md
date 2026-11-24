补写 25 行 one_line_semantics（grade/name/subsystem 零变更）

- 卡号：SEMFIX-S10 ｜ 执行员：agent-66 ｜ 完成：2026-11-18
- 写域：SEMFIX_S10\ + _ghidra\SEMFIX-S10\；目标 ra2youli\gamemd.exe 只读（未写）
- 环境：系统 Python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26（未建 venv / 未 pip install）

## 必读与判据
- R14_COMMON.md §8.6 六条判据已读；D-42 ③b 四充分条件：①跳表/switch 多路 ②可证伪错误码/返回 ③内存形状断言 ④完整循环 I/O。
- CARD.md 已读：只改第 4 列，25 行 grade 均 [已证]、P1。
- 原料：AUDIT_SEM_SELF\ROW_VERDICTS.tsv 的 criterion 列（逐行转写，未贴证据流水）。

## 步骤（全部完成）
1. ⑨ 停机核验：25 行盘上均 [已证]、均 S10（0 反例）。
2. 定位权威盘：COVERAGE\coverage.tsv（8 列，SHA256 f7080727…d2f08e，未改；不在写域）。
3. capstone 反汇编 25 个函数体（W130_atlas 给 size），落 EVIDENCE\DISASM_25.txt/.json（4234 条指令）。
4. 逐行转写语义：功能总述 + ③b 条件号 + 指令偏移；写入 coverage_delta.tsv。
5. ⑮ 体内出现：全 25 行抽检，177/177 = 100% 的 0x 地址/偏移在对应函数体真出现（EVIDENCE\BODY_HIT_CHECK.txt）。
6. 零变更自证：grade/name/subsystem/evidence_path 与盘逐字比对 0 差异（EVIDENCE\ZERO_CHANGE_CHECK.txt）。

## 核心数字
- ① 补写行数：25
- ② 语义字符数：min 154 / max 233（全部 ≥80）
- ③ ⑤ 体内命中率：177/177 = 100%（全 25 行，阈值 ≥5 行）
- ④ grade/name 零变更：25/25，mismatch=0

## 交付物
- coverage_delta.tsv（8 列，25 行 + 表头）
- EVIDENCE\：DISASM_25.txt / DISASM_25.json / SEMANTICS_CHECK.txt / BODY_HIT_CHECK.txt / ZERO_CHANGE_CHECK.txt
- work\：dump_disasm.py / verify_offsets.py / verify_final.py / build_delta.py / verify_delta.py / body_hit_check.py

## 判据分布（criterion）
③b④ 完整循环 I/O：6 行；③b② 可证伪返回：4 行；③b① 多路/跳表/守卫：14 行；③b①+③b③：1 行。
