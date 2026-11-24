# R68-T2 · 5 处「永远通过」子项的只读审计

## 背景
check_disc.py 是纪律门禁。/home/t628/projects/ra2-campaign-forge/lead/LEAD_LOCK 第 2450 行（CM3 段）记了 5 处「永远通过」子项。本轮要逐项证实/证伪，并给最小修法建议。

## 5 处（原文见 LEAD_LOCK:2450，先自己读原文）
1 C7 的 bytes=N 分支全表 0 行使用（疑似死分支）
2 C11 的 frozen 分支：入档即计数、无 FAIL 出口，且补一条自述行即可「摘帽」
3 C11 的 claims-none：第 7 列写「无」即免检（11 条）
4 C9 的占位符是精确匹配（GARBAGE-CRITERION-OTHER 这类非占位垃圾照过）
5 C10 门自检只比常量与登记串，同一人可同改（实测改常量仍 ok(R58) exit 0）

## 你的任务（只读，严禁修改 live 文件；需要跑就把脚本复制到 /tmp 或 _r68_t2 临时目录里跑）
对 1..5 每一项，给出三样东西：
  (a) 盘上证据：具体 file:line 与代码片段
  (b) 一个「构造反控」：你实际构造了什么坏输入，让门禁照过；给出命令与实际输出（贴原文）
  (c) 最小修法：改哪几行、加什么判据，以及该修法自身的反控（用什么坏输入证明修后会被抓，用什么好输入证明修后不误伤）
禁止只做静态阅读就下结论 —— (b) 必须真跑。跑不了就明写「未跑，原因」。

## 硬约束
- 不许改 lead/next_re_20261117_r14 下的任何 live 文件（check_disc.py / recheck_verify.py / DISC_*.tsv / STATUS_BOARD.md / R14_COMMON.md / GOAL_THREE_TARGETS_20261018.md / LEAD_LOCK）。
- 复制到临时目录跑时，若脚本里 ROOT 是 D:\ 路径，可只替换 ROOT 与路径分隔符两处，须在报告里写明你替换了什么、为什么这不改变判据。
- 交付：REPORT.md 写在本卡同目录（_cards/R68-T2-REPORT.md）。每个结论后面必须跟「盘上原文」或「实际输出」。
