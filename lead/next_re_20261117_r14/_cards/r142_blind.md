# R142 盲测复算卡（规则 D：独立实现，禁止读主会话脚本）

## 你的任务
在本仓库 /home/t628/projects/ra2-campaign-forge 上，独立复算下面 8 个数字。**禁止**读取或运行 _r142/r142a_tier_audit.py 与 _r142/r142b_version_drift.py（那是被审计对象）。请自己写一个新脚本放在 _r142/sub/ 下。

## 输入（只读这两个文件）
1. 台账：lead/next_re_20261117_r14/R17_R111_FACTINDEX_V539/FACT_INDEX.tsv（制表符分隔，列 fact_id/statement/grade/evidence_paths/limitations）
2. 外部 triage：_ext/f_partial_triage/TRIAGE.tsv（列 fid/lost_primary/lost_side/alive_paths/verdict/basis）

## 判定口径（必须照此实现）
路径存活判定：把字段按分号切成路径；路径里的反斜杠转成正斜杠；若路径含左圆括号，只取左括号之前的部分；去掉首尾空白；以仓库根为基准做 os.path.exists。空串跳过。
一个 fact 的存活计数 alive = 存活路径条数，总数 n = 路径总条数。
分类：dead 当 alive==0；alive 当 alive==n；partial 当 0 < alive < n。

## 要复算的 8 项
1. 台账行数。
2. 在 v5.39 台账上，partial 分类的 fact 个数。
3. dead 分类的 fact_id 列表。
4. TRIAGE.tsv 里 alive_paths 声明的路径总条数，以及其中实际不在盘的有几条。
5. TRIAGE.tsv 里 lost_primary 声明的路径总条数，以及其中实际仍在盘的有几条。
6. TRIAGE.tsv 里 lost_primary 字段为空的 fid 有哪些；这些 fid 各自被标成什么 verdict。
7. 在盘上 10 个版本目录（lead/next_re_20261117_r14/R17_R1??_FACTINDEX_V5??/FACT_INDEX.tsv）里，逐个版本算 partial 个数，给出按版本号升序的计数序列。
8. 上述序列里，TRIAGE.tsv 的 32 个 fid 集合与各版本 partial 集合的差集分别是什么（只报非空差集的版本号与差集内容）。

## 输出要求
- 用一条命令跑完，把结果打印成 JSON，同时写到 _r142/sub/sub_result.json。
- 在最后附带一节 SELF-CHECK，逐项写「我算出的值」。
- 不要修改任何既有文件；只在 _r142/sub/ 下新建文件。
- 卡面严禁出现反引号字符（你的产出文件不受此限）。
