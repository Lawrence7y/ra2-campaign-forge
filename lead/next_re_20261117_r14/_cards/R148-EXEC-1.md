# 调度卡 R148-EXEC-1：FACT_INDEX 四条正文事实的独立执行复算（不引用主会话中间量）

## 目标
在 t628 本机纯静态，用一条命令输出全部证据，独立复算四条将被写进 FACT_INDEX 正文的事实。
你**不许读** _r148 目录下的任何主会话脚本，必须自己写。

## 二进制与路径
- gamemd.exe：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
- 库根：/home/t628/projects/ra2-campaign-forge
- FACT_INDEX：lead/next_re_20261117_r14/R17_R111_FACTINDEX_V539/FACT_INDEX.tsv

## 必须交付的七个数（每个都要能复现）
1. F23 算术：6+2+3 与 6+2+3+3，各自与 12 的关系（哪个小于、哪个大于）。
2. F23 失联件：全库按精确文件名 coverage.tsv 命中几个？按精确字节数 4147334 命中几个？
   两个父目录 lead/next_re_20261117_r14/COVERAGE 与 lead/next_re_20261112_r10 是否存在？
3. F35 一手判据：lead/next_re_20261117_r14/RULING_R15_20261119/work/strict_panel.py
   的第 78 行原文是什么？该行里的方括号字面是否为 [未证]（不是裸子串 未证）？
   该文件头第 14 行散文写什么？同一判据在该文件内出现几次？
4. F35 同判据脚本：_cards/M59-MERGE 下 precheck.py / simulate.py / verify.py
   三个文件各自含 未证 的行号与原文（注意：判据可能写成 [未证] not in r[3]，不是 sem）。
   _cards/M59-MERGE/merge_panel.py 是否含该判据（这是反控，期望不含）？
5. F35 两个输入：COVERAGE/coverage.tsv 与 lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv
   是否存在？
6. F24 清单：R17_R101_TIER_FINAL_4417/tier_final_4417.tsv 的行数（不含表头）与
   bytes 列求和，分别是多少？
7. F29 序列：17 字节 8B44240483C00450FF15C8117E00C20400 在 .text 节内出现几次？
   在其它节出现几次？（必须逐节切片搜，不许整文件搜）

## 硬纪律
- 只读：不许修改任何既有文件。产物只能写 /home/t628/projects/ra2-campaign-forge/_r148/r148x_exec.md。
- 卡面与产物不得出现反引号。
- 一条命令输出全部证据，禁止把一个事实拆成多次单点命令。
- 禁止对整段 .text 开 capstone detail=True；本卡只需纯字节搜索，不需要反汇编。
- 预算 8 分钟。超时如实报告。

## 输出格式
一张表：编号 | 名称 | 你实测的值 | 你用的判据一句话。
最后一段写：你在哪一个数字上最没把握，为什么。
