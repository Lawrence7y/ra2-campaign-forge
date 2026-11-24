# R37 · 子代理派发台账（并发 5/5）

本轮按「子代理并发上限 5、主会话不直接推进逆向工作」的规则，把实质工作全部外派。

| # | 名字 | 模型（provider / model） | 家族 | 任务 | 卡面 |
|---|---|---|---|---|---|
| T1 | `t1-iat` | `magpie-anthropic` / `work/cn:deepseek-v4.1-flash` | deepseek | 判定 `0x7E11C8` 的导入函数名，确认「InterlockedIncrement」有无字节支撑 | `_cards\R37-T1-IAT.md` |
| T2 | `t2-recount` | `magpie-anthropic` / `work/cn:hy4flash` | hy4 | 从 `reconcile.tsv` / `reverse_map.tsv` 复算 `F14` 的数（220 / 32 / 26 / 15 vs 17） | `_cards\R37-T2-RECOUNT.md` |
| T3 | `t3-auditc` | `magpie-anthropic` / `work/cn:deepseek-v4.1-flash` | deepseek | 跨家族审计我的列间一致性检查器 `checkC.py` | `_cards\R37-T3-AUDITC.md` |
| T4 | `t4-glm8` | `magpie-anthropic` / `zcode/GLM-5.3-Flash` | GLM | 8 项纯文本/表格/路径核对（看板第 36 轮段 vs 源文件） | `_cards\R37-T4-GLM8.md` |
| T5 | `t5-scale` | `magpie-anthropic` / `work/cn:hy4flash-free` | hy4 | 独立复算 `F24` 的搜索规模（23,791 / 1.29 GB / 58 倍） | `_cards\R37-T5-SCALE.md` |

## 家族分配与跨家族要求

- 执行员家族：deepseek（T1）、hy4（T2、T5）
- 审计员：deepseek（T3）——**审的是 Lead 的检查器**，非审自己产物
- GLM 仅做纯文本 8 项，严格遵守「≤8 项 / 禁字节 / 禁汇编 / 禁函数入口 / 禁宿主身份」限制

## 复算义务（§2.12 规则 D）

审计员与执行员的结论**一律须由 Lead 复算后才可采纳**。前两轮实测：两轮 adequacy 审计共判 13 条 PARTIAL，复算后驳回 9 条。
本轮不预设「他们会错」，但也不预设「他们会对」——逐条复算，**既不为凑数驳回、也不为省事采信**。

## 本会话已发生的事故（供后续轮次避坑）

1. R35：`make_v511.py` 断言 `54*4` 个 tab（漏算表头），应为 `55*4`。
2. R35：标记复核脚本把台账卡 `R17_LEDGER_1063` 误纳入 FACT_INDEX 筛选条件。
3. R36：`checkB` 正则四连错（`COVERAGE` 子串误配 / 漏裸卡号 / `###` 三级标题未匹配 / 文件名带扩展名未归一）。
4. R36：追加脚本用 `str.replace` 改目标路径，差一个空格导致**静默失配、把 §2.22 追加了两遍**；靠「字节增量 +6,084 与上轮同值」这条线索发现并回滚。
5. R36：归档脚本后置断言「标题不应再出现在看板」——指针行本身含标题，断言必假。
6. R37：`checkC` 的 C3 只认十六进制，漏掉锚里用**十进制**记的地址（`va=7839744` = `0x77A000`）。
7. R37：`retro.py` 格式化占位符少一个（rows 未占位）。

⇒ 全部是**我自己的**检查器/脚本错，没有一次是文件错。**检查器的输出必须先自证，再当缺陷清单用。**
