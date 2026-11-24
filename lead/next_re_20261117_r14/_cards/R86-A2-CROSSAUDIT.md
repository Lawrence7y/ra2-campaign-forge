# R86-A2 跨家族审计卡（hy4 审 · 与前一支 deepseek 审计不同轴）

## 你的角色
你是第二支跨家族审计员，家族与前一员不同。主会话本轮有两条**自陷式**主张（自己给自己划限制），你的任务是查这两条限制是否**被诚实执行**、以及主会话有没有用「已经写了限制」来掩盖本可避免的错。

## 纪律（硬性）
- 全程只读，**不得修改任何文件**。不要把结论写成文件，只打印到 stdout。
- 不得 import 被审脚本（clock_r86.py、falsify_r86.py、why_rerun_r86.py、archive_r86.py、write_r86.py）。
- 凡是没实测的，写「未实测」。**禁止基于主会话叙述下结论。**

## 被审对象
工作目录 /home/t628/projects/ra2-campaign-forge。主审脚本在 _r86/ 下。四件套已落盘：R14_COMMON.md 的 2.90 节、GOAL_THREE_TARGETS_20261018.md 的 §1139、LEAD_LOCK 的 DM 段、STATUS_BOARD.md 的第 86 轮段。

## 主张 A（自陷 1）
「门禁 check_disc.py 的 5 条 FAIL 卡了 18 轮。本轮裁定根因不是那 5 行写错，而是窗口表整体错位一轮。但我同时登记：门禁层无法区分『重映射窗口』与『放宽到全天』，两者都让恰好那 5 行通过。所以门禁变绿不是语义证据。」

你要查：
A1. 「放宽到全天同样恰好 5 行」是否真实？请你**自己构造**一次放宽（可以在临时副本上改，绝对不要动 live 文件；建议把 recheck_verify.py 复制到 /tmp 下改 ROUND_WINDOWS）并跑一遍，报告通过的行号集合。
A2. 如果放宽后通过的**多于** 5 行 → 主张 A 的「不可区分」不成立，请直说。
A3. 主审有没有把这条限制**用足**：即在四件套正文里，是否明确写出「所以本次不能凭门禁变绿宣称问题已解决」？请 grep 四件套确认措辞，引原文。

## 主张 B（自陷 2）
「本轮没有改动任何 live 判据：recheck_verify.py 的窗口表与 R73 前置备份 SUPERSEDED.before_r73_pathfix_recheck_verify.py_20261122_230601.bak 的 _ROUND_ROWS 块 diff 为空。」

你要查：
B1. 亲自做这个 diff，确认是否为空。
B2. 检查 check_disc.py 与 recheck_verify.py 的 mtime 是否早于本轮开始（本轮主会话任务 #71/#72 起始时刻可在 /home/t628/apps/harness/data/harness.db 的 tasks 表查）。
B3. 四件套里凡出现「本轮未改判据」这类说法，是否都能被文件 mtime 支持。

## 主张 C（自错记账的完整性）
主会话在四件套里记了 6 处自错。你要查：**有没有漏记的自错**。线索：
C1. 主会话曾把自测项数写成 24（实际 28）、合计 64（实际 126），并做了两次就地更正写入。请用 ls -la 查 R17_LEAD_BASELINE 下 R86.fixcount* 备份文件，确认这两次更正确实发生，且四件套现在写的是 126。
C2. 查 _r86/ 下各脚本自身的 PASS/FAIL 计数，与四件套里登记的表（clock 21 / falsify 11 / why_rerun 8 / archive 28 / write 58）逐项核对。**若有一项对不上，就是漏记或错记。**
C3. 查四件套里所有出现的数字，抽查至少 10 个，看是否与脚本实测一致。

## 输出格式
正常打印即可，按 A1-A3 / B1-B3 / C1-C3 分节，每条给：结论、你跑的命令、实测数字。

## 预算
8 分钟。超时如实标注。重点目录：/home/t628/projects/ra2-campaign-forge/_r86/、/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/、/home/t628/apps/harness/data/harness.db。
