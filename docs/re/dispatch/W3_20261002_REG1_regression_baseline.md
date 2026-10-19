# W3-REG1 派工单 · 全程序验证器回归基线（post-CS1/CS2/APP1/DOC1 时点快照）

> 派发：2026-10-02 19:5x（Lead）· 执行：WorkBuddy（新会话）· 预估 60–90 分钟
> 目的：终局验收前的一次**全量回归基线** —— 每个已验收包的验证器在"当前时点"各是什么状态，一表打尽。

## 任务

1. **发现**：递归扫描 `out/re_work/`（含 qc/W3_20261001、qc/W3_20261002、zcode_live、workbuddy）下**全部 `verify_*.py`**，另加 `tools/verify_anchors.py` 与 YR 侧 TOC 门（若存在；以实际扫描为准，不许凭本卡清单）。发现清单必须与你报告里的执行清单**一一对应**（漏跑 = 不完）。
2. **逐个执行**：每个验证器**新鲜实跑**（记录开跑时间戳、EXIT、输出尾部），单个超时 10 分钟记 TIMEOUT（不算 FAIL）。**禁止**拿旧日志/旧 exitcode 冒充实跑结果 —— baseline 里每个条目必须带本轮时间戳。
3. **分类**：
   - `GREEN`（EXIT=0）
   - `RED_KNOWN`：已登记的已知红 —— 目前应只有 `verify_c1`（7 条残红，已归属 CS2 并发，CS1b 卡正在重钉）——**必须引登记出处**（CS1_REPORT ④）；
   - `RED_UNEXPECTED`：**任何不在已登记清单里的红** ⇒ 逐条查成因（谁改了什么、破坏了哪条断言），**如实报告，不许修**（修复不是本卡的事，写进报告等 Lead 派卡）；
   - `TIMEOUT` / `INSTRUMENT_FAILED`（跑不起来/空扫描）单列。
4. **活性与负控（必须做，缺一不算完）**：
   - **抽 3 个验证器复跑第二遍** ⇒ 两遍 EXIT 一致（稳定性）；
   - **负控 1 起**：挑一个**自包含的小验证器**，整目录复制进你的写域，改坏一个期望常量 ⇒ **副本必须 FAIL**、**原件复跑必须 PASS** —— 证明你记录的 EXIT 来自真实执行而非旧文件；
   - 若大面积（>1/3）验证器秒退且报 import/路径错误 ⇒ 一律 `INSTRUMENT_FAILED`，先查环境再重跑，**不许把环境故障记成 RED**。
5. **顺带采集终局数字**（SYN v2 要用，全部现读现抄、不许推算）：两份 ATLAS 的当前大小/sha/mtime、`verify_anchors` 当前读数、36+ 已收口包清单对照（以 dispatch 台账 §477 之前各验收节为准）。

## 铁律

- **写域仅** `out/re_work/workbuddy/W3_20261002/reg1_regression/`。目标目录**唯一允许的写入 = 验证器自带的日志落盘**（last_run/stdout 摘录类），除此之外对 `out/re_work/` 其余一切零写入；ATLAS、game.exe、dispatch 台账零写入。
- 验证器**只读不改** —— 发现某验证器本身有 bug，写进报告，不许动手。
- 空扫描 = INSTRUMENT_FAILED；`[]` 不许冒充通过。
- 可用子代理/并行则并行跑（注意各自写域隔离），但 baseline 必须是**单一汇总文件**。

## 交付

`out/re_work/workbuddy/W3_20261002/reg1_regression/`：`REG1_REPORT.md` + `reg1_baseline.json`（发现清单=执行清单，逐条 time/EXIT/class）+ `verify_reg1.py`（断言：发现数==执行数、无漏跑、负控与稳定性证据在档、RED_UNEXPECTED 分类完整）+ 原始输出。完成后回报 `[0]`：verifier 总数 / GREEN / RED_KNOWN / RED_UNEXPECTED / TIMEOUT 计数 + 负控结果 + verdict tally 原文。
