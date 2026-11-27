# 卡 R152-F35-SCOPE（执行员 · hy4flash-free · 只读）

## 任务
在 t628 本机只读复核四个数，全部用一条命令一次输出。禁止写任何文件（除 /tmp 与本卡指定的 _r152/sub_exec.txt）。

## 必须一次输出的证据
1. 会话根 /home/t628/projects/ra2-campaign-forge；v5.40 路径 lead/next_re_20261117_r14/R17_R112_FACTINDEX_V540/FACT_INDEX.tsv 的 字节数 与 sha256 前 16 位；数据行数。
2. 在 FACT_INDEX.tsv 里取 fact_id 为 F35 的那一行，把第 4 列（evidence_paths）按分号切分，逐项打印：序号 / 该项括号前的路径（反斜杠转斜杠）/ 该路径在当前盘 os.path.exists 的真假 / 括号内标注。最后打印 项数 与 存活数 与 失联数。
3. 对 11 个版本目录 lead/next_re_20261117_r14/R17_R1*_FACTINDEX_V5*/FACT_INDEX.tsv 逐个打印：版本目录名 / 字节数 / F35 第 4 列项数 / F35 失联项数。然后打印一条汇总：F35 项数等于 1 的版本清单，等于 5 的版本清单。
4. 在四个文件里 grep 三个串：唯一一项即 / 两条整行 / 整行证据链失联。文件为 lead/next_re_20261117_r14/R14_COMMON.md、lead/LEAD_LOCK、lead/GOAL_THREE_TARGETS_20261018.md、lead/next_re_20261117_r14/BOARD_ARCHIVE.md。逐条打印 文件名 / 行号 / 该行前 120 字，最后打印总命中数与按文件分组的计数。

## 硬要求
- 一条命令输出全部四节（python3 -c 或多行 heredoc 均可），不要分多次调用。
- 只读：不得修改任何文件，不得写 R17 五件套、不得改 FACT_INDEX、不得运行 check_disc.py。
- 把原始输出同时 tee 到 /home/t628/projects/ra2-campaign-forge/_r152/sub_exec.txt。
- 每条结论都必须来自实测打印值，不得估算、不得凭记忆。若某条实测失败，如实打印失败原因，不要改成看起来合理的数字。
