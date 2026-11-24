# D-22 三条事实独立核证

核证日期：2026-11-06。先读 `lead/PENDING_DECISIONS.md:22` 的 D-22 全文（至 64 行），再读 `lead/re_line_20261105/D22_RULING/TASK.md`。本报告只核 F1/F2/F3，不作路线裁决。

结论：**F1 CONFIRMED；F2 REFUTED（107 份与约 42 小时混用了范围）；F3 CONFIRMED（确认「零崩溃结论未独立验证」）。**

## 实跑命令与完整输出入口

以下命令均在本次 ask 实跑；根目录为 `D:/Project/ra2-campaign-forge`，全仓枚举不排除任何目录。

```bash
find D:/Project/ra2-campaign-forge -type f -name 'except_post_*.txt' -print0 | xargs -0 sha256sum
find D:/Project/ra2-campaign-forge -type f -name 'EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt' -print
find D:/Project/ra2-campaign-forge -type f -name 'except_post_*.txt' -printf 'x\n' | wc -l
find D:/Project/ra2-campaign-forge -type f -name 'except_post_*.txt' -printf '%T@ %TY-%Tm-%TdT%TH:%TM:%TS %p\n' | sort -n
set -o pipefail
find D:/Project/ra2-campaign-forge -type f '(' -name 'except_post_*.txt' -o -name 'EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt' ')' -print0 | python -I -X utf8 D:/Project/ra2-campaign-forge/lead/re_line_20261105/D22_RULING/_d22_facts.py
```

文件系统计数输出 `113`；逐份 `sha256sum` 输出全部为 `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`。探针最终命令成功退出；完整逐份哈希、字节比较和 mtime 落在同目录 `_d22_facts_out.txt:10` 至 122 行（共 113 行），摘要位于 123–130 行。探针以二进制 stdin 接收 `find -print0`，没有 `subprocess(text=True)`，没有导入 ra2tool.Engine。

## F1 — CONFIRMED

目标文件唯一：`out/re_work/work_chain/CONTINUE_20261003/lead/boot_hang_triage_20261018/EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt`。

输出 `_d22_facts_out.txt:4`、`:6`、`:7`、`:124`：目标件 1 份、26,405 B；全仓找到 113 份 except_post，同哈希 113/113，逐字节全文相同 113/113，distinct 哈希数 1。满足 TASK.md:20 的三个条件（N≥100、distinct=1、全文全等）。

独立于哈希的比较代码见 `_d22_facts.py:45`：对每份完整读取后的 `data` 与目标 `baseline` 作 bytes 全文相等比较，没有将哈希等同于字节比较。

107 份属于 `out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip` 子树（输出 `:126`），其外 6 份为 `lead/qc161_u0400_trip` 的 5 份及 `out/re_work/work_chain/CONTINUE_20261003/lead/q161` 的 1 份（完整清单 `:10` 起，5 份摘要 `:130`）。

与 RE 转述差异：none。此处证实文件内容一致，不单凭这项检查证明复制机制或所有对局均无崩溃。

## F2 — REFUTED

反驳对象为 `lead/PENDING_DECISIONS.md:35` 的「107 份 mtime 从 2026-10-18 04:41 到 2026-10-19 22:39（42 小时）」。所有 113 份的 mtime 已逐份列于 `_d22_facts_out.txt:10` 起，既给出 UTC、UTC+08:00，也保留 `st_mtime_ns`；跨度用纳秒整数之差计算（`_d22_facts.py:56` 至 58）。下表时间采用 UTC+08:00；显示时间四舍五入到微秒，原始纳秒值保留在输出中。

| 范围 | 数量 | 最早 mtime | 最晚 mtime | 跨度小时 |
|---|---:|---|---|---:|
| 全仓 | 113 | 2026-10-17 08:14:58.812503 | 2026-11-04 18:26:58.694975 | 442.1999673533889 |
| out/.../qc161_u0400_trip 全子树 | 107 | 2026-10-17 08:14:58.812503 | 2026-11-04 18:26:58.694975 | 442.1999673533889 |
| 同一 out 子树的根层直接文件 | 44 | 2026-10-18 04:41:21.592521 | 2026-10-19 22:39:27.821394 | 41.96839690922222 |

数据证据：`_d22_facts_out.txt:124`、`:126`、`:128`。因此约 42 小时的数值有真实对应范围，但对应的是根层 44 份，不是子树 107 份。

全仓与 107 份子树共同最早件：`out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T5/except_post_20261017T081458810997.txt`，`st_mtime_ns=1792196098812502800`。共同最晚件：同子树 `l3_1101v4h/except_post_20261104T182658693950.txt`，`st_mtime_ns=1793788018694975000`。文件系统 find 的全部 mtime 排序也得到这两个端点。

最早件四字段为 `Eip:007CFC9F`、`Esp:00F9C614`、`Ebp:00F9C634`、`EFlags:00000286`，与目标件全部相同（输出 `:8` 与 `:124`）；`00000286` 的数值即 0x286。44 份根层最早件的四字段也相同（`:128`）。寄存器一致性得到确认，时间范围转述需改正。

mtime 是当前文件系统元数据，不自动等于异常发生时间，也不单凭 mtime 和寄存器一致性证明 harness 的具体复制/续写机制；该机制本次未验。

## F3 — CONFIRMED（确认未独立验证）

已完整读取 `lead/GOAL_THREE_TARGETS_20261018.md` §555（5466–5580 行）。按 TASK.md:21 的判决语义，确认的是「§555 的零崩溃结论未独立验证」，不是确认 37 趟实际零崩溃。

原文 `lead/GOAL_THREE_TARGETS_20261018.md:5564` 至 5566：

> 我亲验了 3 项：37 个目录数、final_exit 直方图（逐值逐目录全对）、107 份 except_post 单一哈希 6694b75e…。其余（归因判定、8 条改判、19 三趟的脚本差异）采信回件与复核员，我未逐份重读 console。

原文 `:5569`：

> 但我没有在回件后独立核验归因，只核了计数。

第 3 条诚实账原文 `:5570` 至 5571：

> 「游戏崩溃 0 趟」这条结论我未独立验证（需要逐趟读 console 与字段）。我验证的是它的必要条件（107 份 except 单一哈希）。

所以 §555 自述亲验的是目录数量、退出码计数及 except 单一哈希；归因、八条改判、脚本差异没有由该节作者逐份重读 console 独立验证。该节性质表自身还列「无法判定 29」（`:5523`）；标题的「零趟游戏崩溃」（`:5473`）不能扩成实际无崩溃的充分证明。缺少可信的新异常件，不等于排除其他崩溃形态。

本次核证亲自重算 F1/F2，亲读 §555 文字及其局限；**没有重跑 37 目录/退出码普查，没有逐趟读取 37 个 archive 的 console 与字段，也没有复核各趟归因**。这些检查本次未运行，37 趟实际是否均无崩溃仍为未验。与 D-22 第三条转述差异：none。

## 执行边界与过程记录

零真机、零采样注入、不读活进程内存；E3 继续暂停（D-13）。写入仅为本目录的 FACTCHECK.md、_d22_facts.py、_d22_facts_out.txt。未 commit、未 push；未修改任何既有证据件或台账。

安全检查器先后拦截了含 subprocess 参数列表的两次候选写入，即使第二次已明确 shell=False；随后改用无子进程的探针。os.walk(bytes) 初版全仓运行超时转后台，后主动停止，未据此报告结果。最终采用完整全仓 find 的 NUL 分隔二进制输出，经管道交给隔离 Python；最终命令成功并生成本报告所引的完整输出。没有将被拦截或已停止的尝试算作通过。
