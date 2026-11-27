ROLE: exec （执行员 · 独立复算，禁看主会话脚本）

任务：在仓库根 /home/t628/projects/ra2-campaign-forge 下，独立复算三件事实，全部用一条命令输出证据。

纪律：
1 一次取证。用 python3 单次运行打印全部结果，禁止把事实拆成多次单点命令。
2 禁止读取 _r159/ 目录下任何文件（那是主会话脚本，读了就不算独立）。
3 只读，禁止写入任何文件。禁止修改 check_disc.py / DISC_RECHECK.tsv / DISC_UNVERIFIABLE.tsv。
4 不要开启 md.detail=True 反汇编，本任务不需要反汇编。

被检对象：
A）lead/next_re_20261117_r14/check_disc.py 里的常量 C14_ROW_SHA（31 个 id 到 sha256 的字典）与 C14_TEXT_SHA256。
   门禁在 check_disc.py 内计算 C14 逐行哈希的口径是（第 1 列制表符 第 2 列制表符 第 3 列制表符 第 4 列），
   数据源是 lead/next_re_20261117_r14/DISC_RECHECK.tsv 的数据行（去掉表头，每行 7 列）。
   请逐个 id 判定：C14_ROW_SHA 里那条值，等于该行的「C14 口径哈希」（第1到4列），还是等于「C7 口径哈希」（第1列、第5列、第6列），还是两者都不等。
   报告三类各有多少条、分别是哪些 id。
B）同一个字典里 id 等于 20 的那条值，是不是某条历史口径的产物。做法：把第 20 行的第 6 列分别改写成
   GATE_VER = 'R140' 到 R160 的每一个版本（保持其余列不变），逐版本算 C7 口径哈希，看哪一版等于该值。
   同时给出第 20 行当前的 C14 口径哈希。
C）lead/next_re_20261117_r14/R17_R114_FACTINDEX_V542/FACT_INDEX.tsv 里 fact_id 为 F08 的那一行：
   第 4 列 evidence_paths 用分号分隔，逐项去掉圆括号注释、把反斜杠换成斜杠、拼到仓库根，逐项判定在盘还是不在盘。
   另外用 ls 报告 lead/next_re_20261117_r14/ 下所有形如 R17_LEDGER_数字 的目录名，并给出这些数字的最大值和最小值。

输出要求：一条命令一次打印 A/B/C 三段全部结果，每段带小数（行数、计数）。最后一行打印 SELFCHECK=OK。
