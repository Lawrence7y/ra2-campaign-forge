# R150-A 执行卡：FACT_INDEX 证据存活普查 + 外部 triage 口径对账（只读，独立复算）

## 角色与边界
你是执行员。只读，不写任何文件（除你自己的输出目录 /home/t628/projects/ra2-campaign-forge/_r150/sub_hy4/）。
不修改 R14_COMMON / 台账 / LEAD_LOCK / STATUS_BOARD / check_disc.py / FACT_INDEX.tsv。
一次取证纪律：把所有证据用尽量少的 python3 命令一次跑完并打印全部中间数，不要把一个事实拆成多次单点命令。

## 对象
- 清单：lead/next_re_20261117_r14/R17_R112_FACTINDEX_V540/FACT_INDEX.tsv（sha256 应为 fabd1e57 开头，88,786 B，55 行=表头+54 数据行，5 列，全 LF）
- 外部调研产物：_ext/f_partial_triage/TRIAGE.tsv 与 REPORT.md 与 triage.py

## 要独立复算并逐项报数（共 12 项）
1. FACT_INDEX 数据行数、列数、fact_id 是否 F01..F54 连续、sha256、字节数。
2. 第 4 列 evidence_paths 按分号切项的项数（报总数）。
3. 逐项解析：把每项在第一个左圆括号处切成路径，反斜杠换正斜杠；分别拼 (a) 仓库根 (b) 仓库根 + lead/ ，两者都不存在即判失联。报：失联项数、唯一失联路径数、唯一失联路径的逐条字面清单。
4. 逐行统计 存活项数 = 项数 - 失联项数；报出「存活项数 == 0」的行（应为 1 行）。该行的 fact_id 与 grade 原文。
5. 报出 grade 取值分布（逐值计数）。
6. 报出「部分失联行」= 存活项数 > 0 且 失联项数 > 0 的 fid 清单与条数。
7. 读 _ext/f_partial_triage/triage.py 里 FIX 常量指向的 FACT_INDEX 路径，报出该路径字面值与其 sha256；并与第 1 项 v5.40 的 sha256 比较是否同一文件。
8. 分别数 v5.32（triage 输入）与 v5.40 里 F35 行的 evidence_paths 项数，两个数都报。
9. 读 _ext/f_partial_triage/TRIAGE.tsv：报数据行数、三档（仍可核验/需重建/不可核验）逐档计数、fid 集合。
10. 把第 6 项（现盘部分失联集合）与第 9 项（triage 覆盖集合）求差集，双向都报（现盘有而 triage 没有的、triage 有而现盘没有的）。
11. 把 TRIAGE.tsv 第 4 列 alive_paths 里点名的每个路径，去掉尾部圆括号锚点（注意锚点里可能嵌套括号，例如路径 R14_COMMON.md 后跟 (§2.10 / 一 / (a′))，此时必须按「第一个左圆括号处切」而不是「剥最后一对括号」），判是否真在盘。报：点名件数、不存在件数与逐条字面。
12. 反控与正控各两条：正控用 lead/next_re_20261117_r14/R14_COMMON.md 必须判活；负控用自造路径 ZZZ_NOT_ON_DISK_QQQ.md 必须判死；负控用 lead/next_re_20261117_r14/COVERAGE/PANEL.md 必须判死；第二正控用 win 风格串 lead\next_re_20261117_r14\R14_COMMON.md 也必须判活。

## 输出格式
在 /home/t628/projects/ra2-campaign-forge/_r150/sub_hy4/r150x_exec.md 写一份七节报告：
第 1 节 命令原文与原始输出摘录；第 2..7 节每节一条结论 + 支撑该结论的原始数字。
每条结论必须能被我照着重跑一次得到同一数字。不确定的地方明确写「未复算」，不要猜。
卡面严禁出现反引号字符。
