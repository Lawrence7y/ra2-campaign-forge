# R153 执行卡（hy4flash-free）· 只读核验两件事，一条命令出全部证据

## 禁区
- 只读。不得修改任何文件，不得创建 FACT_INDEX 新版本，不得跑 check_disc.py 的写操作。
- 不得读 harness / server.py / re_guardian.py / re-tool 源码。
- 一轮内用一条 bash 命令输出全部证据，禁止把一件事拆成多次单点命令。

## 任务一 · 「33 个锚点」与脚本实测是否一致
在 /home/t628/projects/ra2-campaign-forge 下：
1. 用 python3 AST 读 _r146/r149a_lostpath.py 里的 ANCHOR 字典，逐 fid 打印锚点列表长度与总和。
2. 读 _r146/r149a_lostpath.json，打印 anchor 各 fid 的 anchors 长度与总和，以及 fails 字段。
3. 统计字面串「33 个锚点」在下列文件的命中行号（1-based）：
   lead/GOAL_THREE_TARGETS_20261018.md、lead/next_re_20261117_r14/BOARD_ARCHIVE.md、
   lead/next_re_20261117_r14/COMPACT_STATE.md、lead/next_re_20261117_r14/R14_COMMON.md、
   lead/LEAD_LOCK、lead/next_re_20261117_r14/STATUS_BOARD.md。
4. 反控：自造串 ZZZ_R153_EXEC_QQQ 在同一批文件的命中数必须为 0。

## 任务二 · F08 的第二项证据到底缺什么
1. 打印 lead/GOAL_THREE_TARGETS_20261018.md 里 ## §1064 段的字节数与 ### 子项标题清单。
2. 在该段内分别统计三个字面串出现次数：0x47C3D0、0x6F322F、0x6F2B40。
3. 在 lead/next_re_20261117_r14/R14_COMMON.md 的 ## 2.9 段的「### 一 ·」子块内分别
   统计同三个串的出现次数。
4. 打印 lead/next_re_20261117_r14/R17_R113_FACTINDEX_V541/FACT_INDEX.tsv 里 fact_id 为 F08
   那行的第 4 列（evidence_paths）全文。
5. 反控：自造地址 0x42424242 在 §1064 段内必须 0 命中。

## 输出格式
分四节：任务一读数 / 任务一字面传播 / 任务二读数 / 反控结果。
每个数字后面写它是怎么算出来的（哪个文件哪一段）。不要给建议、不要改文件、不要写结论性判断。
