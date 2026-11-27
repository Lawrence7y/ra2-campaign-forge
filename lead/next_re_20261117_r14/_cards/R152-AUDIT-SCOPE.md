# 卡 R152-AUDIT-SCOPE（审计员 · deepseek · 只读复核）

## 任务
只读复核以下五条主张，逐条给出 成立 / 部分成立 / 不成立 并附你自己的实测值。禁止写任何文件（除 /tmp 与 /home/t628/projects/ra2-campaign-forge/_r152/sub_audit.txt）。

## 待复核主张
主张1：在 v5.40 的 F35 行里，第 2 列（statement）断言「本条 evidence_paths 5 项里只有 COVERAGE/PANEL.md 失联」「不再是整行证据链失联项」，而同一行第 5 列（limitations）仍断言「evidence_paths 唯一一项即该已失文件」「与 F23 并列两条整行证据链失联项」。两处主张互相矛盾，且 limitations 那处在 v5.40 事实为假（实测 5 项、仅 1 项失联）。
主张2：该「唯一一项 / 两条整行」表述只在 V530 到 V533 四个版本成立（F35 第 4 列恰 1 项且该项失联）；从 V534 起 F35 第 4 列变为 5 项，整行全失联的事实项只剩 F23。
主张3：三个串 唯一一项即 / 两条整行 / 整行证据链失联 在 R14_COMMON.md、LEAD_LOCK、GOAL_THREE_TARGETS_20261018.md、BOARD_ARCHIVE.md 四文件里共命中 9 行，其中只有 2 行在同句里带版本作用域（出现 v5.2x 或 v5.3x 字样），另 7 行不带作用域。
主张4：v5.40 的 F24 行两列（statement 与 limitations）里完全不含 sha256 或 sha 字样，也不含任何 64 位十六进制串；即该条语料值至今没有「清单 sha + 测量时刻」的可重跑入口。
主张5：列举 F35 在 v5.40 的 5 个 evidence_paths 项中，在盘的是 RULING_R15_20261119/work/strict_panel.py 与 _cards/M59-MERGE/precheck.py、simulate.py、verify.py 四项；失联的是 COVERAGE/PANEL.md。故 F35 不是整行失联项。

## 硬要求
- 一条命令输出全部实测（python3 多行 heredoc），不要分多次调用。
- 只读：不得修改任何文件（五件套 / FACT_INDEX / check_disc.py 均不得写），不得运行 check_disc.py。
- 输出 tee 到 _r152/sub_audit.txt。
- 若某条主张的措辞与你的实测方向相反，必须指出并给出你自己的实测数，不要为了顺从而判成立。
